"""US1: criar conta e entrar, cenários 1 a 8 (T030; RF-001 a RF-006, RF-009, RF-012, RF-013).

De ponta a ponta pela API, com cookies e CSRF reais. O cenário 8 (aviso de privacidade) é
da interface e fica em `FormularioCadastro.test.tsx` (T038).
"""

from __future__ import annotations

from datetime import timedelta

import httpx
import pytest
from sqlalchemy import func, select, text

from app.identidade.modelos import Sessao, Usuario
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.relogio import RelogioControlavel
from app.revisao.modelos import ParametrosFsrs
from tests.apoio_http import (
    COOKIE_CSRF,
    COOKIE_SESSAO,
    cadastrar,
    entrar,
    obter_csrf,
    sair,
    sem_id_requisicao,
)
from tests.fabricas import dados_conta

pytestmark = pytest.mark.functional

CHAVES_DO_PERFIL = {
    "nome",
    "email",
    "papel",
    "fuso",
    "metaDiaria",
    "tamanhoLicao",
    "limiteNovosDia",
    "retencaoDesejada",
    "criadoEm",
}


async def _contar(fabrica: FabricaSessoes, entidade: type) -> int:
    async with unidade_de_trabalho(fabrica) as sessao:
        return (await sessao.execute(select(func.count()).select_from(entidade))).scalar_one()


# --- Cenário 1 ---------------------------------------------------------------------------


async def test_cenario1_cadastro_cria_estudante_com_padroes_e_ja_entra(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes, relogio: RelogioControlavel
) -> None:
    conta = dados_conta(fuso="America/Recife")
    resposta = await cadastrar(cliente, conta)

    assert resposta.status_code == 201, resposta.text
    perfil = resposta.json()
    assert set(perfil) == CHAVES_DO_PERFIL, "nenhum id interno nem hash sai pela API"
    assert perfil["nome"] == conta.nome
    assert perfil["email"] == conta.email
    assert perfil["papel"] == "estudante"
    assert perfil["fuso"] == "America/Recife"
    assert (perfil["metaDiaria"], perfil["tamanhoLicao"], perfil["limiteNovosDia"]) == (20, 10, 20)
    assert perfil["retencaoDesejada"] == 0.9
    assert perfil["criadoEm"].startswith(relogio.agora().strftime("%Y-%m-%dT%H:%M:%S"))
    assert COOKIE_SESSAO in cliente.cookies and COOKIE_CSRF in cliente.cookies

    # Já está dentro: a sessão aberta pelo cadastro dá acesso ao perfil.
    perfil_consultado = await cliente.get("/api/v1/perfil")
    assert perfil_consultado.status_code == 200
    assert perfil_consultado.json() == perfil


async def test_cenario1_cria_a_versao_1_dos_parametros_do_fsrs(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    resposta = await cadastrar(cliente, dados_conta())
    assert resposta.status_code == 201
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        parametros = (await sessao.execute(select(ParametrosFsrs))).scalar_one()
    assert parametros.versao == 1 and parametros.origem == "padrao"
    assert len(parametros.pesos) == 21
    assert str(parametros.retencao_desejada) == "0.90"
    assert parametros.passos_aprendizado_s == [60, 600]
    assert parametros.passos_reaprendizado_s == [600]
    assert parametros.versao_biblioteca == "6.3.2"


@pytest.mark.parametrize("fuso", [None, "Marte/Phobos", "../../etc/passwd", ""])
async def test_cenario1_fuso_ausente_ou_invalido_vira_sao_paulo(
    cliente: httpx.AsyncClient, fuso: str | None
) -> None:
    corpo = dados_conta().cadastro()
    corpo.pop("fuso")
    if fuso is not None:
        corpo["fuso"] = fuso
    resposta = await cadastrar(cliente, corpo)
    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["fuso"] == "America/Sao_Paulo"


async def test_cenario1_normaliza_nome_e_email(cliente: httpx.AsyncClient) -> None:
    resposta = await cadastrar(
        cliente,
        {
            "nome": "  José da Silva  ",
            "email": "  Jose.Silva@Exemplo.COM ",
            "senha": "uma frase longa e incomum",
        },
    )
    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["nome"] == "José da Silva"
    assert resposta.json()["email"] == "jose.silva@exemplo.com"


# --- Cenário 2 ---------------------------------------------------------------------------


@pytest.mark.parametrize("senha", ["1234567", "12345678", "PASSWORD", "qwertyuiop"])
async def test_cenario2_senha_curta_ou_comum_e_recusada_junto_do_campo(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes, senha: str
) -> None:
    resposta = await cadastrar(cliente, {**dados_conta().cadastro(), "senha": senha})

    assert resposta.status_code == 422
    erro = resposta.json()
    assert erro["codigo"] == "dados_invalidos"
    assert [c["campo"] for c in erro["campos"]] == ["senha"]
    assert erro["campos"][0]["mensagem"]
    assert senha not in resposta.text.replace(erro["campos"][0]["mensagem"], "")
    assert await _contar(fabrica_sessoes, Usuario) == 0
    assert COOKIE_SESSAO not in cliente.cookies


async def test_cenario2_lista_todos_os_campos_invalidos_de_uma_vez(
    cliente: httpx.AsyncClient,
) -> None:
    resposta = await cadastrar(
        cliente,
        {"nome": "   ", "email": "isto-nao-e-email", "senha": "123", "fuso": "America/Recife"},
    )
    assert resposta.status_code == 422
    assert {c["campo"] for c in resposta.json()["campos"]} == {"nome", "email", "senha"}


async def test_cenario2_campo_obrigatorio_ausente_e_recusado(cliente: httpx.AsyncClient) -> None:
    resposta = await cadastrar(cliente, {"nome": "Ana", "email": "ana@exemplo.com"})
    assert resposta.status_code == 422
    assert resposta.json()["campos"] == [{"campo": "senha", "mensagem": "Campo obrigatório."}]


# --- Cenário 3 ---------------------------------------------------------------------------


async def test_cenario3_entrada_correta_inicia_sessao_e_chega_ao_perfil(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    conta = dados_conta()
    assert (await cadastrar(cliente, conta)).status_code == 201
    assert (await sair(cliente)).status_code == 204
    assert COOKIE_SESSAO not in cliente.cookies

    resposta = await entrar(cliente, conta)

    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["email"] == conta.email
    assert COOKIE_SESSAO in cliente.cookies
    assert (await cliente.get("/api/v1/perfil")).status_code == 200
    assert await _contar(fabrica_sessoes, Sessao) == 2, "uma sessão por entrada"


async def test_cenario3_entrada_ignora_caixa_e_espacos_do_email(
    cliente: httpx.AsyncClient,
) -> None:
    conta = dados_conta()
    assert (await cadastrar(cliente, conta)).status_code == 201
    await sair(cliente)
    resposta = await entrar(cliente, {"email": f"  {conta.email.upper()} ", "senha": conta.senha})
    assert resposta.status_code == 200


# --- Cenário 4 ---------------------------------------------------------------------------


async def test_cenario4_senha_errada_e_email_inexistente_tem_a_mesma_resposta(
    cliente: httpx.AsyncClient,
) -> None:
    conta = dados_conta()
    assert (await cadastrar(cliente, conta)).status_code == 201
    await sair(cliente)

    senha_errada = await entrar(cliente, {"email": conta.email, "senha": "senha-incorreta-123"})
    inexistente = await entrar(
        cliente, {"email": "ninguem@exemplo.com", "senha": "senha-incorreta-123"}
    )

    assert senha_errada.status_code == inexistente.status_code == 401
    assert sem_id_requisicao(senha_errada.json()) == sem_id_requisicao(inexistente.json())
    assert senha_errada.json()["codigo"] == "credenciais_invalidas"
    assert senha_errada.json()["mensagem"] == "E-mail ou senha incorretos."
    assert COOKIE_SESSAO not in cliente.cookies


# --- Cenário 5 ---------------------------------------------------------------------------


async def test_cenario5_sair_invalida_a_sessao_no_servidor(cliente: httpx.AsyncClient) -> None:
    assert (await cadastrar(cliente, dados_conta())).status_code == 201
    token = cliente.cookies[COOKIE_SESSAO]

    resposta = await sair(cliente)

    assert resposta.status_code == 204
    assert COOKIE_SESSAO not in cliente.cookies and COOKIE_CSRF not in cliente.cookies
    # Quem guardou o cookie antigo (outra aba, outro dispositivo) já não entra.
    cliente.cookies.set(COOKIE_SESSAO, token, domain="teste")
    reuso = await cliente.get("/api/v1/perfil")
    assert reuso.status_code == 401
    assert reuso.json()["codigo"] == "nao_autenticado"


async def test_cenario5_sair_e_idempotente_sem_sessao(cliente: httpx.AsyncClient) -> None:
    await obter_csrf(cliente)
    assert (await sair(cliente)).status_code == 204
    await obter_csrf(cliente)
    assert (await sair(cliente)).status_code == 204


# --- Cenário 6 ---------------------------------------------------------------------------


async def test_cenario6_sexta_tentativa_e_recusada_mesmo_com_a_senha_certa(
    cliente: httpx.AsyncClient, relogio: RelogioControlavel
) -> None:
    conta = dados_conta()
    assert (await cadastrar(cliente, conta)).status_code == 201
    await sair(cliente)

    for _ in range(5):
        assert (
            await entrar(cliente, {"email": conta.email, "senha": "errada-errada-1"})
        ).status_code == 401

    bloqueada = await entrar(cliente, conta)
    assert bloqueada.status_code == 429
    assert bloqueada.json()["codigo"] == "muitas_tentativas"
    espera = int(bloqueada.headers["Retry-After"])
    assert 1 <= espera <= 15 * 60
    assert COOKIE_SESSAO not in cliente.cookies

    # Passado o bloqueio, a senha certa volta a funcionar.
    relogio.avancar(minutes=15, seconds=1)
    assert (await entrar(cliente, conta)).status_code == 200


async def test_cenario6_entrada_correta_zera_as_falhas_da_conta(
    cliente: httpx.AsyncClient,
) -> None:
    conta = dados_conta()
    assert (await cadastrar(cliente, conta)).status_code == 201
    await sair(cliente)
    for _ in range(4):
        assert (
            await entrar(cliente, {"email": conta.email, "senha": "errada-errada-1"})
        ).status_code == 401
    assert (await entrar(cliente, conta)).status_code == 200
    await sair(cliente)
    # Se as falhas não tivessem sido zeradas, a próxima já cairia no limite.
    for _ in range(4):
        assert (
            await entrar(cliente, {"email": conta.email, "senha": "errada-errada-1"})
        ).status_code == 401
    assert (await entrar(cliente, conta)).status_code == 200


# --- Cenário 7 ---------------------------------------------------------------------------


async def test_cenario7_email_em_uso_sem_diferenciar_caixa(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    conta = dados_conta()
    assert (await cadastrar(cliente, conta)).status_code == 201
    await sair(cliente)

    outra = dados_conta(email=conta.email.upper())
    resposta = await cadastrar(cliente, outra)

    assert resposta.status_code == 409
    erro = resposta.json()
    assert erro["codigo"] == "email_em_uso"
    assert erro["campos"] == [{"campo": "email", "mensagem": "Este e-mail já está em uso."}]
    assert await _contar(fabrica_sessoes, Usuario) == 1
    assert COOKIE_SESSAO not in cliente.cookies


# --- Validade da sessão (RF-006) ---------------------------------------------------------


async def test_sessao_com_uso_regular_segue_valida_dentro_do_limite_absoluto(
    cliente: httpx.AsyncClient, relogio: RelogioControlavel
) -> None:
    assert (await cadastrar(cliente, dados_conta())).status_code == 201
    relogio.avancar(days=13, hours=23)
    assert (await cliente.get("/api/v1/perfil")).status_code == 200  # renova o uso
    relogio.avancar(days=13, hours=23)  # 27 dias e 22 horas depois da entrada
    assert (await cliente.get("/api/v1/perfil")).status_code == 200


async def test_sessao_expira_apos_14_dias_sem_uso(
    cliente: httpx.AsyncClient, relogio: RelogioControlavel
) -> None:
    assert (await cadastrar(cliente, dados_conta())).status_code == 201
    relogio.avancar(days=14, minutes=1)
    resposta = await cliente.get("/api/v1/perfil")
    assert resposta.status_code == 401
    assert resposta.json()["codigo"] == "nao_autenticado"


async def test_sessao_expira_30_dias_apos_a_entrada_mesmo_com_uso(
    cliente: httpx.AsyncClient, relogio: RelogioControlavel
) -> None:
    assert (await cadastrar(cliente, dados_conta())).status_code == 201
    for _ in range(3):
        relogio.avancar(days=9)
        assert (await cliente.get("/api/v1/perfil")).status_code == 200
    relogio.avancar(days=3, minutes=1)  # 30 dias e 1 minuto depois da entrada
    assert (await cliente.get("/api/v1/perfil")).status_code == 401


async def test_uso_da_sessao_so_e_gravado_uma_vez_por_minuto(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes, relogio: RelogioControlavel
) -> None:
    assert (await cadastrar(cliente, dados_conta())).status_code == 201
    criada = relogio.agora()
    relogio.avancar(seconds=30)
    await cliente.get("/api/v1/perfil")
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        assert (await sessao.execute(select(Sessao.ultimo_uso_em))).scalar_one() == criada
    relogio.avancar(seconds=31)
    await cliente.get("/api/v1/perfil")
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        assert (
            await sessao.execute(select(Sessao.ultimo_uso_em))
        ).scalar_one() == criada + timedelta(seconds=61)


# --- Perfil sem sessão -------------------------------------------------------------------


async def test_perfil_sem_sessao_responde_401_sem_dados(cliente: httpx.AsyncClient) -> None:
    resposta = await cliente.get("/api/v1/perfil")
    assert resposta.status_code == 401
    assert set(resposta.json()) == {"codigo", "mensagem", "idRequisicao"}
    assert resposta.json()["codigo"] == "nao_autenticado"


async def test_respostas_da_conta_nao_sao_guardadas_em_cache(cliente: httpx.AsyncClient) -> None:
    resposta = await cadastrar(cliente, dados_conta())
    assert resposta.headers["Cache-Control"] == "no-store"
    assert (await cliente.get("/api/v1/perfil")).headers["Cache-Control"] == "no-store"


async def test_o_banco_nao_guarda_a_senha_em_texto_legivel(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    conta = dados_conta()
    await cadastrar(cliente, conta)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        hash_guardado = (await sessao.execute(select(Usuario.senha_hash))).scalar_one()
        tudo = (
            await sessao.execute(text("SELECT row_to_json(u)::text FROM usuarios u"))
        ).scalar_one()
    assert hash_guardado.startswith("$argon2id$")
    assert conta.senha not in tudo
