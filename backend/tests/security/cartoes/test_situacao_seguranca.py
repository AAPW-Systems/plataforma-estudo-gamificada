"""Segurança de suspender, reativar e excluir cartões (T029; RQ-002, DTEC 019, 021 e 038)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import text
from structlog.testing import capture_logs

from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from tests.apoio_acervo import criar_conta, criar_materia, id_interno_da_materia
from tests.apoio_cartoes import criar_cartao
from tests.apoio_http import abrir_cliente, obter_csrf, sem_id_requisicao

pytestmark = pytest.mark.security

SENTINELA = "SENTINELA-DE-SITUACAO-40213"
# (método, sufixo do caminho do cartão)
ACOES = [("POST", "/suspensao"), ("POST", "/reativacao"), ("DELETE", "")]


@pytest.fixture
async def ana(acervo: FastAPI, cliente_real: httpx.AsyncClient) -> httpx.AsyncClient:
    await criar_conta(cliente_real)
    return cliente_real


@pytest.fixture
async def bia(acervo: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with abrir_cliente(acervo, ip="198.51.100.94") as cliente_bia:
        await criar_conta(cliente_bia)
        yield cliente_bia


def _comparavel(resposta: httpx.Response) -> tuple[int, dict[str, object], dict[str, str]]:
    cabecalhos = {
        k: v
        for k, v in resposta.headers.items()
        if k not in {"x-request-id", "date", "content-length"}
    }
    return resposta.status_code, sem_id_requisicao(resposta.json()), cabecalhos


async def _cartao_da_ana(ana: httpx.AsyncClient) -> dict[str, Any]:
    materia = await criar_materia(ana, "Biologia da Ana")
    corpo: dict[str, Any] = (
        await criar_cartao(ana, materia["id"], frente=f"Segredo da Ana {SENTINELA}")
    ).json()
    return corpo


async def _acao_de_outro_e_404(
    ana: httpx.AsyncClient, bia: httpx.AsyncClient, metodo: str, sufixo: str
) -> None:
    cartao = await _cartao_da_ana(ana)
    if sufixo == "/reativacao":  # para a reativação ter o que fazer
        await ana.post(f"/api/v1/cartoes/{cartao['id']}/suspensao")
    antes = (await ana.get(f"/api/v1/cartoes/{cartao['id']}")).json()

    de_outro = await bia.request(metodo, f"/api/v1/cartoes/{cartao['id']}{sufixo}")
    inexistente = await bia.request(metodo, f"/api/v1/cartoes/{uuid.uuid4()}{sufixo}")

    assert de_outro.status_code == 404
    assert _comparavel(de_outro) == _comparavel(inexistente)
    assert SENTINELA not in de_outro.text and cartao["id"] not in de_outro.text
    assert (await ana.get(f"/api/v1/cartoes/{cartao['id']}")).json() == antes, "nada mudou"
    # A rota existe para a dona.
    assert (await ana.request(metodo, f"/api/v1/cartoes/{cartao['id']}{sufixo}")).status_code in {
        200,
        204,
    }


# --- Isolamento (DTEC 019): nomes citados em CASOS_DE_ISOLAMENTO ---------------------------------


async def test_suspensao_de_cartao_de_outro_e_404(
    ana: httpx.AsyncClient, bia: httpx.AsyncClient
) -> None:
    await _acao_de_outro_e_404(ana, bia, "POST", "/suspensao")


async def test_reativacao_de_cartao_de_outro_e_404(
    ana: httpx.AsyncClient, bia: httpx.AsyncClient
) -> None:
    await _acao_de_outro_e_404(ana, bia, "POST", "/reativacao")


async def test_exclusao_de_cartao_de_outro_e_404(
    ana: httpx.AsyncClient, bia: httpx.AsyncClient
) -> None:
    await _acao_de_outro_e_404(ana, bia, "DELETE", "")


@pytest.mark.parametrize(("metodo", "sufixo"), ACOES)
async def test_identificador_malformado_e_404(
    ana: httpx.AsyncClient, metodo: str, sufixo: str
) -> None:
    referencia = await ana.request(metodo, f"/api/v1/cartoes/{uuid.uuid4()}{sufixo}")
    for identificador in ("nao-e-uuid", "123", "a" * 500):
        resposta = await ana.request(metodo, f"/api/v1/cartoes/{identificador}{sufixo}")
        assert resposta.status_code == 404, identificador
        assert sem_id_requisicao(resposta.json()) == sem_id_requisicao(referencia.json())


# --- Situações fora das visíveis (DTEC 038) -----------------------------------------------------


@pytest.mark.parametrize("situacao", ["aguardando_revisao", "recusado"])
async def test_cartao_aguardando_revisao_ou_recusado_nao_e_suspenso_reativado_nem_excluido(
    acervo: FastAPI, ana: httpx.AsyncClient, situacoes_da_004: None, situacao: str
) -> None:
    """Essas situações são da 004: a 003 responde `404` e não as tira nem as põe no estudo."""
    materia = await criar_materia(ana)
    fabrica: FabricaSessoes = acervo.state.fabrica_sessoes
    interno = await id_interno_da_materia(fabrica, materia["id"])
    async with unidade_de_trabalho(fabrica) as sessao:
        public_id = (
            await sessao.execute(
                text(
                    "INSERT INTO cartoes (usuario_id, materia_id, frente, verso, origem, situacao) "
                    "SELECT usuario_id, :m, 'Gerado', 'Gerado', 'gerado_verificado', "
                    "CAST(:s AS situacao_cartao) FROM materias WHERE id = :m RETURNING public_id"
                ),
                {"m": interno, "s": situacao},
            )
        ).scalar_one()

    for metodo, sufixo in ACOES:
        resposta = await ana.request(metodo, f"/api/v1/cartoes/{public_id}{sufixo}")
        assert resposta.status_code == 404, (metodo, sufixo)

    async with unidade_de_trabalho(fabrica) as sessao:
        restante = (
            await sessao.execute(
                text("SELECT situacao::text FROM cartoes WHERE public_id = :p"), {"p": public_id}
            )
        ).scalar_one()
    assert restante == situacao


# --- Logs sem conteúdo ---------------------------------------------------------------------------


async def test_logs_de_suspender_reativar_e_excluir_trazem_so_identificadores(
    ana: httpx.AsyncClient,
) -> None:
    cartao = await _cartao_da_ana(ana)
    with capture_logs() as registros:
        await ana.post(f"/api/v1/cartoes/{cartao['id']}/suspensao")
        await ana.post(f"/api/v1/cartoes/{cartao['id']}/suspensao")
        await ana.post(f"/api/v1/cartoes/{cartao['id']}/reativacao")
        await ana.delete(f"/api/v1/cartoes/{cartao['id']}")

    eventos = [r for r in registros if r["event"].startswith("cartao_")]
    assert [e["event"] for e in eventos] == [
        "cartao_suspenso",
        "cartao_situacao_sem_mudanca",
        "cartao_reativado",
        "cartao_excluido",
    ]
    for evento in eventos:
        assert set(evento) <= {
            "event",
            "log_level",
            "cartao_public_id",
            "usuario_public_id",
            "situacao",
        }, evento
    assert SENTINELA not in str(registros)


# --- Proteções herdadas -----------------------------------------------------------------------


@pytest.mark.parametrize(("metodo", "sufixo"), ACOES)
async def test_sem_sessao_responde_401(
    cliente_real: httpx.AsyncClient, metodo: str, sufixo: str
) -> None:
    await obter_csrf(cliente_real)
    resposta = await cliente_real.request(metodo, f"/api/v1/cartoes/{uuid.uuid4()}{sufixo}")
    assert resposta.status_code == 401
    assert resposta.json()["codigo"] == "nao_autenticado"


@pytest.mark.parametrize(("metodo", "sufixo"), ACOES)
async def test_sem_csrf_ou_de_origem_estranha_e_403_e_nada_muda(
    ana: httpx.AsyncClient, metodo: str, sufixo: str
) -> None:
    cartao = await _cartao_da_ana(ana)
    caminho = f"/api/v1/cartoes/{cartao['id']}{sufixo}"
    sem_csrf = await ana.request(metodo, caminho, headers={"X-CSRF-Token": ""})
    estranha = await ana.request(metodo, caminho, headers={"Origin": "https://malvado.exemplo"})
    assert (sem_csrf.status_code, sem_csrf.json()["codigo"]) == (403, "csrf_invalido")
    assert (estranha.status_code, estranha.json()["codigo"]) == (403, "origem_nao_permitida")
    assert (await ana.get(f"/api/v1/cartoes/{cartao['id']}")).json() == cartao


@pytest.mark.parametrize("sufixo", ["/suspensao", "/reativacao"])
async def test_suspensao_e_reativacao_nao_sao_guardadas_em_cache(
    ana: httpx.AsyncClient, sufixo: str
) -> None:
    cartao = await _cartao_da_ana(ana)
    resposta = await ana.post(f"/api/v1/cartoes/{cartao['id']}{sufixo}")
    assert resposta.headers["Cache-Control"] == "no-store"


# --- Exclusão da conta com cartões (DTEC 021; reexecução da T054 da 001) -------------------------


async def test_excluir_a_conta_apaga_os_cartoes_dela_e_preserva_os_de_outra_conta(
    acervo: FastAPI, bia: httpx.AsyncClient
) -> None:
    from tests.apoio_acervo import enviar
    from tests.fabricas_arquivos import validos
    from tests.security.identidade.test_exclusao_completa import tabelas_com_residuo

    fabrica: FabricaSessoes = acervo.state.fabrica_sessoes
    arquivo = next(a for a in validos() if a.nome == "resumo.txt")
    materia_bia = await criar_materia(bia, "Da Bia")
    da_bia = (await criar_cartao(bia, materia_bia["id"], frente="Da Bia")).json()

    async with abrir_cliente(acervo, ip="198.51.100.95") as carla:
        conta = await criar_conta(carla)
        biologia = await criar_materia(carla, "Biologia")
        quimica = await criar_materia(carla, "Química")
        fonte = (await enviar(carla, biologia["id"], arquivo)).json()
        com_fonte = (
            await criar_cartao(carla, biologia["id"], frente="Com fonte", fonteId=fonte["id"])
        ).json()
        await criar_cartao(carla, quimica["id"], frente="Sem fonte")
        suspenso = (await criar_cartao(carla, quimica["id"], frente="Suspenso")).json()
        await carla.post(f"/api/v1/cartoes/{suspenso['id']}/suspensao")
        async with unidade_de_trabalho(fabrica) as sessao:
            id_carla = (
                await sessao.execute(
                    text("SELECT usuario_id FROM cartoes WHERE public_id = :p"),
                    {"p": com_fonte["id"]},
                )
            ).scalar_one()
            # Pré-condição: a conta tem cartões ativos, suspensos e com referência.
            assert "cartoes" in await tabelas_com_residuo(sessao, id_carla)

        resposta = await carla.post("/api/v1/perfil/exclusao", json={"senhaAtual": conta.senha})
        assert resposta.status_code == 204

    async with unidade_de_trabalho(fabrica) as sessao:
        assert await tabelas_com_residuo(sessao, id_carla) == []
    assert (await bia.get(f"/api/v1/cartoes/{da_bia['id']}")).json() == da_bia
