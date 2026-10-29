"""Segurança da consulta e da edição de cartões (T023; RQ-002, DTEC 019 e 038)."""

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
from tests.apoio_cartoes import criar_cartao, semear_cartao_gerado
from tests.apoio_http import abrir_cliente, obter_csrf, sem_id_requisicao

pytestmark = pytest.mark.security

SENTINELA = "SENTINELA-DE-EDICAO-77120"


@pytest.fixture
async def ana(acervo: FastAPI, cliente_real: httpx.AsyncClient) -> httpx.AsyncClient:
    await criar_conta(cliente_real)
    return cliente_real


@pytest.fixture
async def bia(acervo: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with abrir_cliente(acervo, ip="198.51.100.93") as cliente_bia:
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


# --- Isolamento (DTEC 019) --------------------------------------------------------------------


async def test_consulta_de_cartao_de_outro_e_404(
    ana: httpx.AsyncClient, bia: httpx.AsyncClient
) -> None:
    cartao = await _cartao_da_ana(ana)
    assert (await ana.get(f"/api/v1/cartoes/{cartao['id']}")).status_code == 200

    de_outro = await bia.get(f"/api/v1/cartoes/{cartao['id']}")
    inexistente = await bia.get(f"/api/v1/cartoes/{uuid.uuid4()}")

    assert de_outro.status_code == 404
    assert _comparavel(de_outro) == _comparavel(inexistente)
    assert SENTINELA not in de_outro.text and cartao["id"] not in de_outro.text


async def test_edicao_de_cartao_de_outro_e_404(
    ana: httpx.AsyncClient, bia: httpx.AsyncClient
) -> None:
    cartao = await _cartao_da_ana(ana)

    de_outro = await bia.patch(f"/api/v1/cartoes/{cartao['id']}", json={"frente": "Invadido"})
    inexistente = await bia.patch(f"/api/v1/cartoes/{uuid.uuid4()}", json={"frente": "Invadido"})

    assert de_outro.status_code == 404
    assert _comparavel(de_outro) == _comparavel(inexistente)
    assert (await ana.get(f"/api/v1/cartoes/{cartao['id']}")).json() == cartao, "nada mudou"
    # A rota existe para a dona.
    assert (
        await ana.patch(f"/api/v1/cartoes/{cartao['id']}", json={"frente": "Dela"})
    ).status_code == 200


async def test_identificador_malformado_e_404_na_consulta_e_na_edicao(
    ana: httpx.AsyncClient,
) -> None:
    referencia = await ana.get(f"/api/v1/cartoes/{uuid.uuid4()}")
    for metodo, caminho in (
        ("GET", "/api/v1/cartoes/nao-e-uuid"),
        ("PATCH", "/api/v1/cartoes/123"),
        ("GET", "/api/v1/cartoes/" + "a" * 500),
    ):
        resposta = await ana.request(
            metodo, caminho, json={"frente": "x"} if metodo == "PATCH" else None
        )
        assert resposta.status_code == 404, (metodo, caminho)
        assert sem_id_requisicao(resposta.json()) == sem_id_requisicao(referencia.json())


# --- Situações fora das visíveis (DTEC 038) -----------------------------------------------------


@pytest.mark.parametrize("situacao", ["aguardando_revisao", "recusado"])
async def test_cartao_aguardando_revisao_ou_recusado_e_404_na_consulta_e_na_edicao(
    acervo: FastAPI, ana: httpx.AsyncClient, situacao: str
) -> None:
    materia = await criar_materia(ana)
    fabrica: FabricaSessoes = acervo.state.fabrica_sessoes
    interno = await id_interno_da_materia(fabrica, materia["id"])
    async with unidade_de_trabalho(fabrica) as sessao:
        public_id = await semear_cartao_gerado(sessao, interno, situacao)
    inexistente = await ana.get(f"/api/v1/cartoes/{uuid.uuid4()}")

    consulta = await ana.get(f"/api/v1/cartoes/{public_id}")
    edicao = await ana.patch(f"/api/v1/cartoes/{public_id}", json={"frente": "Aceito à força"})

    assert _comparavel(consulta) == _comparavel(inexistente)
    assert edicao.status_code == 404
    async with unidade_de_trabalho(fabrica) as sessao:
        frente = (
            await sessao.execute(
                text("SELECT frente FROM cartoes WHERE public_id = :p"), {"p": public_id}
            )
        ).scalar_one()
    assert frente == "Gerado"


# --- Logs sem conteúdo ---------------------------------------------------------------------------


async def test_logs_da_edicao_trazem_so_identificadores_e_se_a_origem_mudou(
    ana: httpx.AsyncClient,
) -> None:
    cartao = await _cartao_da_ana(ana)
    with capture_logs() as registros:
        await ana.patch(f"/api/v1/cartoes/{cartao['id']}", json={"verso": f"Novo {SENTINELA}"})
        await ana.patch(f"/api/v1/cartoes/{cartao['id']}", json={"verso": f"Novo {SENTINELA}"})
        await ana.patch(f"/api/v1/cartoes/{cartao['id']}", json={"frente": f"{SENTINELA} " * 400})

    eventos = [r for r in registros if r["event"].startswith("cartao_edi")]
    assert [e["event"] for e in eventos] == ["cartao_editado", "cartao_edicao_sem_mudanca"]
    assert eventos[0]["origem_mudou"] is False
    for evento in eventos:
        assert set(evento) <= {
            "event",
            "log_level",
            "cartao_public_id",
            "usuario_public_id",
            "origem_mudou",
        }, evento
    assert SENTINELA not in str(registros)


# --- Proteções herdadas -----------------------------------------------------------------------


@pytest.mark.parametrize("metodo", ["GET", "PATCH"])
async def test_sem_sessao_consulta_e_edicao_respondem_401(
    cliente_real: httpx.AsyncClient, metodo: str
) -> None:
    await obter_csrf(cliente_real)
    resposta = await cliente_real.request(
        metodo,
        f"/api/v1/cartoes/{uuid.uuid4()}",
        json={"frente": "x"} if metodo == "PATCH" else None,
    )
    assert resposta.status_code == 401
    assert resposta.json()["codigo"] == "nao_autenticado"


async def test_edicao_sem_csrf_ou_de_origem_estranha_e_403_e_nada_muda(
    ana: httpx.AsyncClient,
) -> None:
    cartao = await _cartao_da_ana(ana)
    sem_csrf = await ana.patch(
        f"/api/v1/cartoes/{cartao['id']}", json={"frente": "x"}, headers={"X-CSRF-Token": ""}
    )
    estranha = await ana.patch(
        f"/api/v1/cartoes/{cartao['id']}",
        json={"frente": "x"},
        headers={"Origin": "https://malvado.exemplo"},
    )
    assert (sem_csrf.status_code, sem_csrf.json()["codigo"]) == (403, "csrf_invalido")
    assert (estranha.status_code, estranha.json()["codigo"]) == (403, "origem_nao_permitida")
    assert (await ana.get(f"/api/v1/cartoes/{cartao['id']}")).json() == cartao
