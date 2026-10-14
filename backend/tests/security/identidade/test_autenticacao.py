"""Segurança da autenticação (T031; RF-003 a RF-005, RF-011, RQ-001 a RQ-003, CS-003).

Cobre enumeração de contas (corpo, status e tempo), limites de tentativas, atributos da
sessão e dos cookies, CSRF, papel e ausência da senha no banco e nos logs.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import statistics
import time
from collections.abc import Iterator

import httpx
import pytest
import structlog
from argon2 import PasswordHasher
from fastapi import FastAPI
from sqlalchemy import func, select, text

from app.identidade.modelos import Sessao, TentativaAcesso, Usuario
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao
from app.nucleo.relogio import RelogioControlavel
from app.nucleo.seguranca.senhas import ServicoSenhas
from app.principal import criar_aplicacao
from tests.apoio_http import (
    COOKIE_CSRF,
    COOKIE_SESSAO,
    abrir_cliente,
    cadastrar,
    cookies_da_resposta,
    entrar,
    obter_csrf,
    sair,
    sem_id_requisicao,
)
from tests.fabricas import dados_conta

pytestmark = pytest.mark.security

SENHA_ERRADA = "senha-incorreta-123"


async def _contar(fabrica: FabricaSessoes, entidade: type) -> int:
    async with unidade_de_trabalho(fabrica) as sessao:
        return (await sessao.execute(select(func.count()).select_from(entidade))).scalar_one()


async def _conta_pronta(cliente: httpx.AsyncClient):  # type: ignore[no-untyped-def]
    conta = dados_conta()
    assert (await cadastrar(cliente, conta)).status_code == 201
    await sair(cliente)
    return conta


@pytest.fixture
def saida_de_logs(aplicacao: FastAPI) -> Iterator[io.StringIO]:
    """O texto que a aplicação realmente emite (depois do mascaramento), como JSON por linha."""
    raiz = logging.getLogger()
    formatador = next(
        h.formatter
        for h in raiz.handlers
        if isinstance(h.formatter, structlog.stdlib.ProcessorFormatter)
    )
    fluxo = io.StringIO()
    capturador = logging.StreamHandler(fluxo)
    capturador.setFormatter(formatador)
    raiz.addHandler(capturador)
    try:
        yield fluxo
    finally:
        raiz.removeHandler(capturador)


# --- Enumeração de contas (RF-004, CS-003) -----------------------------------------------


async def test_entrada_tem_corpo_e_status_identicos_para_conta_inexistente_e_senha_errada(
    cliente: httpx.AsyncClient,
) -> None:
    conta = await _conta_pronta(cliente)
    respostas = [
        await entrar(cliente, {"email": conta.email, "senha": SENHA_ERRADA}),
        await entrar(cliente, {"email": "nao.existe@exemplo.com", "senha": SENHA_ERRADA}),
        await entrar(cliente, {"email": "isto nao e um email", "senha": SENHA_ERRADA}),
        await entrar(cliente, {"email": "x" * 254, "senha": SENHA_ERRADA}),
    ]
    assert {r.status_code for r in respostas} == {401}
    corpos = [sem_id_requisicao(r.json()) for r in respostas]
    assert all(c == corpos[0] for c in corpos)
    cabecalhos = [
        {
            k: v
            for k, v in r.headers.items()
            if k.lower() not in {"x-request-id", "content-length", "date"}
        }
        for r in respostas
    ]
    assert all(c == cabecalhos[0] for c in cabecalhos), "nem os cabeçalhos denunciam a conta"


async def test_entrada_com_senha_de_substituto_isolado_nao_quebra_nem_distingue(
    cliente: httpx.AsyncClient,
) -> None:
    conta = await _conta_pronta(cliente)
    for email in (conta.email, "nao.existe@exemplo.com"):
        await obter_csrf(cliente)
        resposta = await cliente.post(
            "/api/v1/auth/entrada",
            content=json.dumps({"email": email, "senha": "abc\ud800def"}),
            headers={"Content-Type": "application/json"},
        )
        assert resposta.status_code == 401
        assert resposta.json()["codigo"] == "credenciais_invalidas"


async def test_tempo_de_resposta_nao_revela_se_o_email_tem_conta(
    configuracao: Configuracao, fabrica_sessoes: FabricaSessoes, relogio: RelogioControlavel
) -> None:
    """CS-003: o e-mail sem conta paga a verificação contra o hash fictício.

    Usa um Argon2id de custo moderado (cerca de dezenas de milissegundos), para que o custo do
    hash domine o ruído do restante; limites altos para medir sem cair no bloqueio.
    """
    moderado = ServicoSenhas(4, PasswordHasher(time_cost=2, memory_cost=16384, parallelism=1))
    configuracao_alta = configuracao.model_copy(
        update={"limite_falhas_conta": 1000, "limite_falhas_ip": 1000}
    )
    app = criar_aplicacao(
        configuracao_alta, fabrica_sessoes=fabrica_sessoes, relogio=relogio, servico_senhas=moderado
    )
    async with app.router.lifespan_context(app), abrir_cliente(app) as cliente:
        conta = await _conta_pronta(cliente)
        await obter_csrf(cliente)
        existente = {"email": conta.email, "senha": SENHA_ERRADA}

        async def medir(corpo: dict[str, str]) -> float:
            await obter_csrf(cliente)
            inicio = time.perf_counter()
            resposta = await cliente.post("/api/v1/auth/entrada", json=corpo)
            duracao = time.perf_counter() - inicio
            assert resposta.status_code == 401
            return duracao

        for _ in range(3):  # aquecimento
            await medir(existente)
        com_conta: list[float] = []
        sem_conta: list[float] = []
        for i in range(15):  # intercalado, para que a deriva do ambiente afete os dois igualmente
            com_conta.append(await medir(existente))
            sem_conta.append(
                await medir({"email": f"fantasma.{i}@exemplo.com", "senha": SENHA_ERRADA})
            )

    mediana_com, mediana_sem = statistics.median(com_conta), statistics.median(sem_conta)
    assert mediana_com > 0.010, "o teste só vale se o custo do hash aparece na medição"
    diferenca = abs(mediana_com - mediana_sem) / max(mediana_com, mediana_sem)
    assert diferenca < 0.25, (
        f"medianas: {mediana_com * 1000:.1f} ms com conta e {mediana_sem * 1000:.1f} ms sem conta"
    )


# --- Limites de tentativas (RF-005, RQ-003) ----------------------------------------------


async def test_bloqueio_por_conta_vale_igual_para_email_com_e_sem_conta(
    cliente: httpx.AsyncClient,
) -> None:
    conta = await _conta_pronta(cliente)
    bloqueios = {}
    for email in (conta.email, "fantasma@exemplo.com"):
        for _ in range(5):
            assert (
                await entrar(cliente, {"email": email, "senha": SENHA_ERRADA})
            ).status_code == 401
        sexta = await entrar(cliente, {"email": email, "senha": "outra-senha-qualquer"})
        assert sexta.status_code == 429
        bloqueios[email] = sexta
    com, sem = bloqueios[conta.email], bloqueios["fantasma@exemplo.com"]
    assert sem_id_requisicao(com.json()) == sem_id_requisicao(sem.json())
    assert abs(int(com.headers["Retry-After"]) - int(sem.headers["Retry-After"])) <= 1


async def test_bloqueio_por_conta_nao_afeta_outras_contas(cliente: httpx.AsyncClient) -> None:
    ana = await _conta_pronta(cliente)
    bia = await _conta_pronta(cliente)
    for _ in range(5):
        await entrar(cliente, {"email": ana.email, "senha": SENHA_ERRADA})
    assert (await entrar(cliente, ana)).status_code == 429
    assert (await entrar(cliente, bia)).status_code == 200


async def test_bloqueio_por_endereco_apos_20_falhas_mesmo_com_senha_certa(
    cliente: httpx.AsyncClient, relogio: RelogioControlavel
) -> None:
    conta = await _conta_pronta(cliente)
    for i in range(20):  # e-mails diferentes: nenhuma conta chega ao próprio limite
        assert (
            await entrar(cliente, {"email": f"alvo.{i}@exemplo.com", "senha": SENHA_ERRADA})
        ).status_code == 401
    bloqueada = await entrar(cliente, conta)
    assert bloqueada.status_code == 429
    assert bloqueada.json()["codigo"] == "muitas_tentativas"

    relogio.avancar(minutes=15, seconds=1)
    assert (await entrar(cliente, conta)).status_code == 200


async def test_endereco_bloqueado_nao_afeta_outro_endereco(
    aplicacao: FastAPI, cliente: httpx.AsyncClient
) -> None:
    conta = await _conta_pronta(cliente)
    for i in range(20):
        await entrar(cliente, {"email": f"alvo.{i}@exemplo.com", "senha": SENHA_ERRADA})
    assert (await entrar(cliente, conta)).status_code == 429
    async with abrir_cliente(aplicacao, ip="198.51.100.20") as outro:
        assert (await entrar(outro, conta)).status_code == 200


async def test_limite_de_10_cadastros_por_hora_por_endereco(
    cliente: httpx.AsyncClient, relogio: RelogioControlavel
) -> None:
    for _ in range(10):
        assert (await cadastrar(cliente, dados_conta())).status_code == 201
    bloqueado = await cadastrar(cliente, dados_conta())
    assert bloqueado.status_code == 429
    assert bloqueado.json()["codigo"] == "muitas_tentativas"
    assert 1 <= int(bloqueado.headers["Retry-After"]) <= 3600

    relogio.avancar(hours=1, seconds=1)
    assert (await cadastrar(cliente, dados_conta())).status_code == 201


async def test_cadastro_recusado_por_validacao_nao_consome_o_limite(
    cliente: httpx.AsyncClient,
) -> None:
    for _ in range(15):
        assert (
            await cadastrar(cliente, {**dados_conta().cadastro(), "senha": "123"})
        ).status_code == 422
    assert (await cadastrar(cliente, dados_conta())).status_code == 201


async def test_tentativas_guardam_so_a_chave_hmac_e_nunca_o_email(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    await entrar(cliente, {"email": "visivel@exemplo.com", "senha": SENHA_ERRADA})
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        linha = (await sessao.execute(select(TentativaAcesso))).scalar_one()
        despejo = (
            await sessao.execute(text("SELECT row_to_json(t)::text FROM tentativas_acesso t"))
        ).scalar_one()
    assert len(linha.chave_conta or b"") == 32
    assert "visivel" not in despejo and "exemplo.com" not in despejo


# --- Sessão e cookies (RF-006, RQ-001) ---------------------------------------------------


async def test_cada_entrada_cria_um_identificador_novo(cliente: httpx.AsyncClient) -> None:
    conta = await _conta_pronta(cliente)
    tokens = []
    for _ in range(3):
        assert (await entrar(cliente, conta)).status_code == 200
        tokens.append(cliente.cookies[COOKIE_SESSAO])
        # Sem sair: a entrada seguinte parte de um navegador que já tinha uma sessão.
    assert len(set(tokens)) == 3


async def test_cadastro_nao_reaproveita_o_identificador_de_uma_sessao_existente(
    cliente: httpx.AsyncClient,
) -> None:
    assert (await cadastrar(cliente, dados_conta())).status_code == 201
    antigo = cliente.cookies[COOKIE_SESSAO]
    assert (await cadastrar(cliente, dados_conta())).status_code == 201
    assert cliente.cookies[COOKIE_SESSAO] != antigo


async def test_identificador_da_sessao_cliente_nao_e_aceito_se_o_servidor_nao_o_emitiu(
    cliente: httpx.AsyncClient,
) -> None:
    """Fixação de sessão: um identificador escolhido por quem ataca não vale nada."""
    forjado = base64.urlsafe_b64encode(b"A" * 32).rstrip(b"=").decode()
    cliente.cookies.set(COOKIE_SESSAO, forjado, domain="teste")
    resposta = await cliente.get("/api/v1/perfil")
    assert resposta.status_code == 401


async def test_atributos_dos_cookies_de_sessao_e_csrf(cliente: httpx.AsyncClient) -> None:
    resposta = await cadastrar(cliente, dados_conta())
    cookies = cookies_da_resposta(resposta)
    sessao, csrf = cookies[COOKIE_SESSAO], cookies[COOKIE_CSRF]

    atributos_sessao = {parte.strip().lower() for parte in sessao.split(";")[1:]}
    assert {"httponly", "secure", "path=/", "samesite=lax", "max-age=2592000"} <= atributos_sessao
    assert not any(a.startswith("domain") for a in atributos_sessao), "__Host- proíbe Domain"

    atributos_csrf = {parte.strip().lower() for parte in csrf.split(";")[1:]}
    assert {"secure", "path=/", "samesite=lax"} <= atributos_csrf
    assert "httponly" not in atributos_csrf, "o JavaScript precisa ler o token anti-CSRF"
    assert not any(a.startswith("domain") for a in atributos_csrf)


async def test_identificador_tem_256_bits_e_o_banco_guarda_so_o_sha256(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    await cadastrar(cliente, dados_conta())
    token = cliente.cookies[COOKIE_SESSAO]
    assert len(base64.urlsafe_b64decode(token + "=")) == 32
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        guardado = (await sessao.execute(select(Sessao.token_hash))).scalar_one()
        despejo = (
            await sessao.execute(text("SELECT row_to_json(s)::text FROM sessoes s"))
        ).scalar_one()
    assert guardado == hashlib.sha256(token.encode()).digest()
    assert token not in despejo


async def test_resposta_401_apaga_os_cookies(cliente: httpx.AsyncClient) -> None:
    resposta = await cliente.get("/api/v1/perfil")
    assert resposta.status_code == 401
    cookies = cookies_da_resposta(resposta)
    assert COOKIE_SESSAO in cookies and COOKIE_CSRF in cookies
    assert all("max-age=0" in valor.lower() for valor in cookies.values())


async def test_sair_apaga_os_cookies_e_revoga_no_servidor(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    await cadastrar(cliente, dados_conta())
    resposta = await sair(cliente)
    assert resposta.status_code == 204
    assert all("max-age=0" in v.lower() for v in cookies_da_resposta(resposta).values())
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        assert (await sessao.execute(select(Sessao.revogada_em))).scalar_one() is not None


# --- CSRF e papel (RF-003, RF-011) -------------------------------------------------------


@pytest.mark.parametrize(
    "caminho,corpo",
    [
        ("/api/v1/auth/cadastro", dados_conta().cadastro()),
        ("/api/v1/auth/entrada", {"email": "a@exemplo.com", "senha": "qualquer-senha"}),
    ],
)
async def test_cadastro_e_entrada_exigem_o_token_anti_csrf(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes, caminho: str, corpo: dict[str, str]
) -> None:
    sem_cookie = await cliente.post(caminho, json=corpo)
    assert sem_cookie.status_code == 403 and sem_cookie.json()["codigo"] == "csrf_invalido"

    await obter_csrf(cliente)
    sem_cabecalho = await cliente.post(caminho, json=corpo, headers={"X-CSRF-Token": ""})
    assert sem_cabecalho.status_code == 403

    forjado = await cliente.post(caminho, json=corpo, headers={"X-CSRF-Token": "a.b"})
    assert forjado.status_code == 403
    assert await _contar(fabrica_sessoes, Usuario) == 0


async def test_origem_estranha_e_recusada_no_cadastro(
    aplicacao: FastAPI, fabrica_sessoes: FabricaSessoes
) -> None:
    async with abrir_cliente(
        aplicacao, cabecalhos={"Origin": "https://atacante.example"}
    ) as cliente:
        resposta = await cadastrar(cliente, dados_conta())
    assert resposta.status_code == 403
    assert resposta.json()["codigo"] == "origem_nao_permitida"
    assert await _contar(fabrica_sessoes, Usuario) == 0


@pytest.mark.parametrize(
    "extra",
    [{"papel": "admin"}, {"papel": "estudante"}, {"id": 1}, {"metaDiaria": 5}, {"publicId": "x"}],
)
async def test_nenhum_campo_extra_e_aceito_no_cadastro(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes, extra: dict[str, object]
) -> None:
    resposta = await cadastrar(cliente, dados_conta(), **extra)
    assert resposta.status_code == 422
    assert next(iter(extra)) in {c["campo"] for c in resposta.json()["campos"]}
    assert await _contar(fabrica_sessoes, Usuario) == 0


async def test_todo_cadastro_publico_cria_estudante(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    assert (await cadastrar(cliente, dados_conta())).status_code == 201
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        assert (await sessao.execute(select(Usuario.papel))).scalar_one() == "estudante"


# --- Dados sensíveis (RQ-001, RQ-002) ----------------------------------------------------


async def test_logs_nao_registram_senha_email_cookie_nem_corpo(
    cliente: httpx.AsyncClient, saida_de_logs: io.StringIO
) -> None:
    conta = dados_conta()
    assert (await cadastrar(cliente, conta)).status_code == 201
    token_sessao = cliente.cookies[COOKIE_SESSAO]
    token_csrf = cliente.cookies[COOKIE_CSRF]
    await sair(cliente)
    await entrar(cliente, {"email": conta.email, "senha": SENHA_ERRADA})
    await entrar(cliente, {"email": "fantasma@exemplo.com", "senha": SENHA_ERRADA})
    for _ in range(5):
        await entrar(cliente, {"email": conta.email, "senha": SENHA_ERRADA})
    await entrar(cliente, conta)

    saida = saida_de_logs.getvalue()
    assert saida, "a aplicação deveria ter registrado as requisições"
    for segredo in (
        conta.senha,
        SENHA_ERRADA,
        conta.email,
        "fantasma@exemplo.com",
        token_sessao,
        token_csrf,
    ):
        assert segredo not in saida, f"vazou em log: {segredo[:12]}…"
    assert conta.nome not in saida, "nome do estudante é dado pessoal"
    for evento in ("conta_criada", "entrada_recusada", "bloqueio_aplicado", "sessao_revogada"):
        assert evento in saida, f"evento esperado ausente: {evento}"


async def test_corpo_de_erro_nunca_devolve_a_senha(cliente: httpx.AsyncClient) -> None:
    senha = "123"
    resposta = await cadastrar(cliente, {**dados_conta().cadastro(), "senha": senha})
    assert resposta.status_code == 422
    assert '"123"' not in resposta.text


async def test_perfil_nunca_expoe_hash_nem_ids_internos(cliente: httpx.AsyncClient) -> None:
    resposta = await cadastrar(cliente, dados_conta())
    texto = resposta.text.lower()
    for proibido in ("senha", "hash", "argon2", '"id"', "public", "usuario_id"):
        assert proibido not in texto
