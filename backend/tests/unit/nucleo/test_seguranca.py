"""Sessão, CSRF e Argon2 (T020; DTEC 023, RF-006, RF-011, RQ-001, CS-003)."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import threading
import time
from collections.abc import AsyncIterator
from datetime import timedelta

import httpx
import pytest
from argon2 import PasswordHasher, Type, extract_parameters
from fastapi import FastAPI

from app.nucleo.configuracao import Configuracao
from app.nucleo.erros import registrar_handlers
from app.nucleo.relogio import RelogioControlavel
from app.nucleo.seguranca.csrf import (
    VINCULO_PRE_SESSAO,
    emitir_token,
    verificar_token,
    vinculo_da_sessao,
    vinculo_dos_cookies,
)
from app.nucleo.seguranca.protecao import MiddlewareProtecaoCsrf
from app.nucleo.seguranca.senhas import ServicoSenhas
from app.nucleo.seguranca.sessoes import (
    calcular_expiracao,
    deve_renovar_uso,
    gerar_token,
    hash_token,
    sessao_valida,
    token_bem_formado,
)

pytestmark = pytest.mark.unit

SEGREDO = b"s" * 32


# --- Sessão -------------------------------------------------------------------------------


def test_token_de_sessao_tem_256_bits_e_e_unico() -> None:
    tokens = {gerar_token() for _ in range(200)}
    assert len(tokens) == 200
    token = next(iter(tokens))
    assert len(token) == 43
    assert len(base64.urlsafe_b64decode(token + "=")) == 32
    assert token_bem_formado(token)


def test_hash_do_token_e_sha256_do_identificador() -> None:
    token = gerar_token()
    assert hash_token(token) == hashlib.sha256(token.encode()).digest()
    assert len(hash_token(token)) == 32
    assert hash_token(token) != hash_token(gerar_token())


@pytest.mark.parametrize(
    "valor", [None, "", "curto", "a" * 42, "a" * 44, "a" * 42 + "=", "a" * 42 + " ", "é" * 43]
)
def test_token_mal_formado_e_recusado_sem_consulta(valor: str | None) -> None:
    assert not token_bem_formado(valor)


def _valida(relogio: RelogioControlavel, **mudancas: object) -> bool:
    inicio = relogio.agora()
    parametros: dict[str, object] = {
        "agora": relogio.agora(),
        "expira_em": calcular_expiracao(inicio, 30),
        "ultimo_uso_em": inicio,
        "revogada_em": None,
        "dias_inatividade": 14,
    }
    parametros.update(mudancas)
    return sessao_valida(**parametros)  # type: ignore[arg-type]


def test_sessao_recem_criada_e_valida(relogio: RelogioControlavel) -> None:
    assert _valida(relogio)


def test_sessao_expira_por_inatividade_em_14_dias(relogio: RelogioControlavel) -> None:
    inicio = relogio.agora()
    relogio.avancar(days=14, seconds=-1)
    assert _valida(relogio, ultimo_uso_em=inicio)
    relogio.avancar(seconds=1)
    assert not _valida(relogio, ultimo_uso_em=inicio)


def test_uso_recente_estende_a_inatividade_mas_nao_alem_de_30_dias(
    relogio: RelogioControlavel,
) -> None:
    inicio = relogio.agora()
    expira_em = calcular_expiracao(inicio, 30)
    relogio.avancar(days=13)
    ultimo_uso = relogio.agora()
    relogio.avancar(days=13)  # 26 dias: 13 desde o último uso, ainda válida
    assert _valida(relogio, expira_em=expira_em, ultimo_uso_em=ultimo_uso)
    ultimo_uso = relogio.agora()
    relogio.avancar(days=4)  # 30 dias desde a entrada: expiração absoluta
    assert not _valida(relogio, expira_em=expira_em, ultimo_uso_em=ultimo_uso)


def test_sessao_expira_no_limite_absoluto_mesmo_com_uso_constante(
    relogio: RelogioControlavel,
) -> None:
    inicio = relogio.agora()
    expira_em = calcular_expiracao(inicio, 30)
    relogio.avancar(days=30, seconds=-1)
    assert _valida(relogio, expira_em=expira_em, ultimo_uso_em=relogio.agora())
    relogio.avancar(seconds=1)
    assert not _valida(relogio, expira_em=expira_em, ultimo_uso_em=relogio.agora())


def test_sessao_revogada_nunca_volta_a_valer(relogio: RelogioControlavel) -> None:
    assert not _valida(relogio, revogada_em=relogio.agora())


def test_ultimo_uso_so_e_renovado_uma_vez_por_minuto(relogio: RelogioControlavel) -> None:
    ultimo = relogio.agora()
    relogio.avancar(seconds=59)
    assert not deve_renovar_uso(ultimo, relogio.agora())
    relogio.avancar(seconds=1)
    assert deve_renovar_uso(ultimo, relogio.agora())
    assert not deve_renovar_uso(relogio.agora(), relogio.agora() + timedelta(seconds=1))


# --- CSRF ---------------------------------------------------------------------------------


def test_token_csrf_emitido_para_um_vinculo_e_aceito_nele() -> None:
    token = emitir_token(SEGREDO, VINCULO_PRE_SESSAO)
    assert verificar_token(SEGREDO, VINCULO_PRE_SESSAO, token, token)


def test_tokens_csrf_sao_unicos() -> None:
    assert len({emitir_token(SEGREDO, VINCULO_PRE_SESSAO) for _ in range(100)}) == 100


def test_token_de_outra_sessao_e_recusado() -> None:
    sessao_a = vinculo_da_sessao(hash_token(gerar_token()))
    sessao_b = vinculo_da_sessao(hash_token(gerar_token()))
    token_de_a = emitir_token(SEGREDO, sessao_a)
    assert verificar_token(SEGREDO, sessao_a, token_de_a, token_de_a)
    assert not verificar_token(SEGREDO, sessao_b, token_de_a, token_de_a)


def test_token_de_pre_sessao_nao_vale_numa_sessao_e_vice_versa() -> None:
    sessao = vinculo_da_sessao(hash_token(gerar_token()))
    pre = emitir_token(SEGREDO, VINCULO_PRE_SESSAO)
    com_sessao = emitir_token(SEGREDO, sessao)
    assert not verificar_token(SEGREDO, sessao, pre, pre)
    assert not verificar_token(SEGREDO, VINCULO_PRE_SESSAO, com_sessao, com_sessao)


def test_token_assinado_com_outro_segredo_e_recusado() -> None:
    token = emitir_token(b"o" * 32, VINCULO_PRE_SESSAO)
    assert not verificar_token(SEGREDO, VINCULO_PRE_SESSAO, token, token)


def test_cookie_e_cabecalho_precisam_ser_iguais() -> None:
    um = emitir_token(SEGREDO, VINCULO_PRE_SESSAO)
    outro = emitir_token(SEGREDO, VINCULO_PRE_SESSAO)
    assert not verificar_token(SEGREDO, VINCULO_PRE_SESSAO, um, outro)


@pytest.mark.parametrize(
    "mudanca",
    [
        lambda t: t[:-1] + ("A" if t[-1] != "A" else "B"),  # assinatura adulterada
        lambda t: ("A" if t[0] != "A" else "B") + t[1:],  # parte aleatória adulterada
        lambda t: t.split(".")[0],  # sem assinatura
        lambda t: "." + t.split(".")[1],  # sem parte aleatória
        lambda t: "x" * 500,
        lambda t: "",
        lambda t: "é." + t.split(".")[1],
    ],
)
def test_token_adulterado_ou_malformado_e_recusado(mudanca: object) -> None:
    token = emitir_token(SEGREDO, VINCULO_PRE_SESSAO)
    adulterado = mudanca(token)  # type: ignore[operator]
    assert not verificar_token(SEGREDO, VINCULO_PRE_SESSAO, adulterado, adulterado)


@pytest.mark.parametrize("cookie_ou_cabecalho", [(None, "x"), ("x", None), (None, None), ("", "")])
def test_token_ausente_e_recusado(cookie_ou_cabecalho: tuple[str | None, str | None]) -> None:
    cookie, cabecalho = cookie_ou_cabecalho
    assert not verificar_token(SEGREDO, VINCULO_PRE_SESSAO, cookie, cabecalho)


def test_vinculo_dos_cookies_usa_a_sessao_so_se_o_cookie_for_bem_formado() -> None:
    token = gerar_token()
    assert vinculo_dos_cookies({"s": token}, "s") == vinculo_da_sessao(hash_token(token))
    assert vinculo_dos_cookies({"s": "lixo"}, "s") == VINCULO_PRE_SESSAO
    assert vinculo_dos_cookies({}, "s") == VINCULO_PRE_SESSAO


# --- Middleware de proteção (Origin, Sec-Fetch-Site e CSRF) ----------------------------


def _configuracao() -> Configuracao:
    return Configuracao(
        postgres_user="u",
        postgres_password="p",  # type: ignore[arg-type]
        postgres_db="d",
        segredo_aplicacao=SEGREDO.decode(),  # type: ignore[arg-type]
        origens_permitidas=["https://app.exemplo.com"],
    )


CONFIG = _configuracao()


@pytest.fixture
async def cliente() -> AsyncIterator[httpx.AsyncClient]:
    app = FastAPI()
    registrar_handlers(app)
    app.add_middleware(MiddlewareProtecaoCsrf, configuracao=CONFIG)

    @app.get("/ler")
    async def ler() -> dict[str, bool]:
        return {"ok": True}

    @app.api_route("/alterar", methods=["POST", "PATCH", "PUT", "DELETE"])
    async def alterar() -> dict[str, bool]:
        return {"ok": True}

    transporte = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transporte, base_url="https://app.exemplo.com") as c:
        yield c


def _cabecalhos(token: str | None, *, sessao: str | None = None, **extras: str) -> dict[str, str]:
    cookies = []
    if token is not None:
        cookies.append(f"{CONFIG.cookie_csrf_nome}={token}")
    if sessao is not None:
        cookies.append(f"{CONFIG.cookie_sessao_nome}={sessao}")
    cabecalhos = dict(extras)
    if cookies:
        cabecalhos["Cookie"] = "; ".join(cookies)
    if token is not None:
        cabecalhos["X-CSRF-Token"] = token
    return cabecalhos


def _token_pre() -> str:
    return emitir_token(CONFIG.segredo, VINCULO_PRE_SESSAO)


async def test_leitura_nao_exige_token(cliente: httpx.AsyncClient) -> None:
    assert (await cliente.get("/ler")).status_code == 200


@pytest.mark.parametrize("metodo", ["POST", "PATCH", "PUT", "DELETE"])
async def test_metodos_que_alteram_estado_exigem_token(
    cliente: httpx.AsyncClient, metodo: str
) -> None:
    sem = await cliente.request(metodo, "/alterar")
    assert sem.status_code == 403
    assert sem.json()["codigo"] == "csrf_invalido"
    com = await cliente.request(metodo, "/alterar", headers=_cabecalhos(_token_pre()))
    assert com.status_code == 200


async def test_cabecalho_sem_cookie_e_recusado(cliente: httpx.AsyncClient) -> None:
    token = _token_pre()
    resposta = await cliente.post("/alterar", headers={"X-CSRF-Token": token})
    assert resposta.status_code == 403


async def test_token_de_outra_sessao_e_recusado_com_403(cliente: httpx.AsyncClient) -> None:
    sessao_a, sessao_b = gerar_token(), gerar_token()
    token_de_b = emitir_token(CONFIG.segredo, vinculo_da_sessao(hash_token(sessao_b)))
    token_de_a = emitir_token(CONFIG.segredo, vinculo_da_sessao(hash_token(sessao_a)))
    recusada = await cliente.post("/alterar", headers=_cabecalhos(token_de_b, sessao=sessao_a))
    assert recusada.status_code == 403 and recusada.json()["codigo"] == "csrf_invalido"
    aceita = await cliente.post("/alterar", headers=_cabecalhos(token_de_a, sessao=sessao_a))
    assert aceita.status_code == 200


async def test_token_de_pre_sessao_nao_vale_com_sessao_aberta(cliente: httpx.AsyncClient) -> None:
    resposta = await cliente.post(
        "/alterar", headers=_cabecalhos(_token_pre(), sessao=gerar_token())
    )
    assert resposta.status_code == 403


@pytest.mark.parametrize(
    "origem", ["https://malicioso.exemplo", "null", "http://app.exemplo.com", ""]
)
async def test_origin_fora_da_lista_e_recusado(cliente: httpx.AsyncClient, origem: str) -> None:
    resposta = await cliente.post("/alterar", headers=_cabecalhos(_token_pre(), Origin=origem))
    assert resposta.status_code == 403
    assert resposta.json()["codigo"] == "origem_nao_permitida"


async def test_origin_permitida_e_ausente_passam(cliente: httpx.AsyncClient) -> None:
    permitida = await cliente.post(
        "/alterar", headers=_cabecalhos(_token_pre(), Origin="https://app.exemplo.com")
    )
    assert permitida.status_code == 200
    ausente = await cliente.post("/alterar", headers=_cabecalhos(_token_pre()))
    assert ausente.status_code == 200


@pytest.mark.parametrize("site", ["cross-site", "same-site", "none", ""])
async def test_sec_fetch_site_diferente_de_same_origin_e_recusado(
    cliente: httpx.AsyncClient, site: str
) -> None:
    resposta = await cliente.post(
        "/alterar", headers=_cabecalhos(_token_pre(), **{"Sec-Fetch-Site": site})
    )
    assert resposta.status_code == 403
    assert resposta.json()["codigo"] == "origem_nao_permitida"


async def test_sec_fetch_site_same_origin_passa(cliente: httpx.AsyncClient) -> None:
    resposta = await cliente.post(
        "/alterar", headers=_cabecalhos(_token_pre(), **{"Sec-Fetch-Site": "same-origin"})
    )
    assert resposta.status_code == 200


async def test_origin_valido_nao_dispensa_o_token(cliente: httpx.AsyncClient) -> None:
    resposta = await cliente.post("/alterar", headers={"Origin": "https://app.exemplo.com"})
    assert resposta.status_code == 403
    assert resposta.json()["codigo"] == "csrf_invalido"


async def test_erro_de_csrf_tem_corpo_padrao_com_id_de_requisicao(
    cliente: httpx.AsyncClient,
) -> None:
    corpo = (await cliente.post("/alterar")).json()
    assert set(corpo) == {"codigo", "mensagem", "idRequisicao"}


# --- Argon2 -------------------------------------------------------------------------------


async def test_hash_usa_o_perfil_de_pouca_memoria_da_rfc_9106() -> None:
    servico = ServicoSenhas(concorrencia=1)
    hash_ = await servico.gerar_hash("uma frase longa e incomum")
    parametros = extract_parameters(hash_)
    assert parametros.type is Type.ID
    assert (parametros.time_cost, parametros.memory_cost, parametros.parallelism) == (3, 65536, 4)
    assert hash_.startswith("$argon2id$")
    assert "uma frase" not in hash_


async def test_verificacao_aceita_a_senha_certa_e_recusa_as_demais() -> None:
    servico = ServicoSenhas(concorrencia=2)
    hash_ = await servico.gerar_hash("senha certa")
    assert await servico.verificar(hash_, "senha certa")
    assert not await servico.verificar(hash_, "senha errada")
    assert not await servico.verificar(hash_, "senha certa ")  # a senha não é normalizada


async def test_hash_corrompido_nunca_autentica() -> None:
    servico = ServicoSenhas(concorrencia=1)
    assert not await servico.verificar("isto-nao-e-um-hash", "qualquer")
    assert servico.precisa_novo_hash("isto-nao-e-um-hash")


async def test_hash_com_parametros_antigos_pede_novo_hash() -> None:
    fraco = PasswordHasher(time_cost=1, memory_cost=16, parallelism=1)
    servico = ServicoSenhas(concorrencia=1)
    assert servico.precisa_novo_hash(fraco.hash("x"))
    assert not servico.precisa_novo_hash(await servico.gerar_hash("x"))


async def test_hash_ficticio_recusa_sempre_e_e_calculado_uma_vez() -> None:
    servico = ServicoSenhas(concorrencia=1)
    assert not await servico.verificar_ficticia("qualquer coisa")
    primeiro = servico._ficticio  # noqa: SLF001
    assert primeiro is not None and extract_parameters(primeiro).memory_cost == 65536
    assert not await servico.verificar_ficticia("outra")
    assert servico._ficticio == primeiro  # noqa: SLF001


async def test_hash_ficticio_calculado_uma_unica_vez_sob_concorrencia() -> None:
    chamadas = 0

    class Contador(PasswordHasher):
        def hash(self, password: str | bytes, *, salt: bytes | None = None) -> str:
            nonlocal chamadas
            chamadas += 1
            return super().hash(password, salt=salt)

    servico = ServicoSenhas(
        concorrencia=4, hasher=Contador(time_cost=1, memory_cost=16, parallelism=1)
    )
    await asyncio.gather(*(servico.verificar_ficticia("x") for _ in range(8)))
    assert chamadas == 1


async def test_semaforo_limita_os_calculos_simultaneos() -> None:
    simultaneos = 0
    maximo = 0
    trava = threading.Lock()

    class Medidor(PasswordHasher):
        def hash(self, password: str | bytes, *, salt: bytes | None = None) -> str:
            nonlocal simultaneos, maximo
            with trava:
                simultaneos += 1
                maximo = max(maximo, simultaneos)
            time.sleep(0.05)
            with trava:
                simultaneos -= 1
            return "$argon2id$fake"

    servico = ServicoSenhas(concorrencia=2, hasher=Medidor())
    await asyncio.gather(*(servico.gerar_hash("x") for _ in range(10)))
    assert maximo == 2
