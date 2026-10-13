"""T022: saúde, documentação e composição da aplicação real."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast
from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI

from app.nucleo.configuracao import Configuracao
from app.principal import criar_aplicacao

pytestmark = pytest.mark.integration


async def test_saude(cliente: httpx.AsyncClient) -> None:
    """T022: processo, banco e esquema da fila acessíveis."""
    assert (await cliente.get("/health")).json() == {"estado": "ok"}
    resposta = await cliente.get("/health/ready")
    assert resposta.status_code == 200
    assert resposta.json() == {"estado": "ok", "verificacoes": {"banco": "ok", "fila": "ok"}}


async def test_banco_indisponivel(cliente: httpx.AsyncClient) -> None:
    """T022: falha real de conexão retorna 503 sem detalhes internos."""

    @asynccontextmanager
    async def indisponivel(fabrica: object) -> AsyncIterator[None]:
        if fabrica is not None:
            raise OSError("detalhe interno")
        yield  # pragma: no cover

    with patch("app.saude.servicos.abrir_conexao", indisponivel):
        resposta = await cliente.get("/health/ready")
    assert resposta.status_code == 503
    assert resposta.json()["estado"] == "indisponivel"
    assert "detalhe interno" not in resposta.text
    assert (await cliente.get("/health")).status_code == 200


async def test_ordem_middlewares(aplicacao: FastAPI, cliente: httpx.AsyncClient) -> None:
    """T022: respostas curtas 403, 413 e 500 mantêm correlação e segurança."""
    assert [cast(type[object], m.cls).__name__ for m in aplicacao.user_middleware] == [
        "MiddlewareCorrelacao",
        "MiddlewareCabecalhosSeguranca",
        "MiddlewareLimiteCorpo",
        "MiddlewareProtecaoCsrf",
        "MiddlewareErrosInesperados",
    ]

    @aplicacao.get("/api/teste-falha")
    async def falhar() -> None:
        raise RuntimeError("detalhe secreto")

    respostas = [
        await cliente.get("/api/teste-falha"),
        await cliente.post("/api/teste", content=b"x" * 65537),
        await cliente.post("/api/teste", json={}),
    ]
    assert [r.status_code for r in respostas] == [500, 413, 403]
    for resposta in respostas:
        assert resposta.headers["x-request-id"] == resposta.json()["idRequisicao"]
        assert resposta.headers["x-frame-options"] == "DENY"
        assert resposta.headers["cache-control"] == "no-store"
        assert "detalhe secreto" not in resposta.text


@pytest.mark.parametrize(
    "ambiente,esperado", [("desenvolvimento", 200), ("teste", 404), ("producao", 404)]
)
async def test_swagger_so_em_desenvolvimento(
    configuracao: Configuracao, ambiente: str, esperado: int
) -> None:
    app = criar_aplicacao(configuracao.model_copy(update={"app_ambiente": ambiente}))
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://teste"
        ) as cliente,
    ):
        assert (await cliente.get("/api/docs")).status_code == esperado
        assert (await cliente.get("/api/openapi.json")).status_code == esperado
