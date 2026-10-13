"""Logs mascarados e middlewares de correlação, cabeçalhos e corpo (RQ-002; plano da 001)."""

from __future__ import annotations

import io
import json
import logging
import uuid
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import structlog
from fastapi import FastAPI, Request
from structlog.testing import capture_logs

from app.nucleo.erros import MiddlewareErrosInesperados, registrar_handlers
from app.nucleo.logs import REMOVIDO, configurar_logs, mascarar_dados_sensiveis
from app.nucleo.middlewares import (
    MiddlewareCabecalhosSeguranca,
    MiddlewareCorrelacao,
    MiddlewareLimiteCorpo,
)

pytestmark = pytest.mark.unit


def _criar_app() -> FastAPI:
    app = FastAPI()
    registrar_handlers(app)
    app.add_middleware(MiddlewareErrosInesperados)
    app.add_middleware(MiddlewareLimiteCorpo)
    app.add_middleware(MiddlewareCabecalhosSeguranca)
    app.add_middleware(MiddlewareCorrelacao)

    @app.post("/api/v1/auth/eco")
    async def eco(request: Request) -> dict[str, int]:
        return {"bytes": len(await request.body())}

    @app.get("/api/v1/itens/{item_id}")
    async def item(item_id: str) -> dict[str, str]:
        return {"id": item_id}

    @app.get("/health")
    async def saude() -> dict[str, str]:
        return {"estado": "ok"}

    return app


@pytest.fixture
async def cliente() -> AsyncIterator[httpx.AsyncClient]:
    transporte = httpx.ASGITransport(app=_criar_app())
    async with httpx.AsyncClient(transport=transporte, base_url="http://teste") as cliente:
        yield cliente


# --- Mascaramento (RQ-002) -------------------------------------------------------------


@pytest.mark.parametrize(
    "chave",
    [
        "senha",
        "senhaAtual",
        "nova_senha",
        "password",
        "cookie",
        "Set-Cookie",
        "X-CSRF-Token",
        "email",
        "corpo",
        "body",
        "authorization",
    ],
)
def test_chaves_sensiveis_sao_mascaradas(chave: str) -> None:
    evento = mascarar_dados_sensiveis(None, "info", {"event": "x", chave: "valor-secreto"})
    assert evento[chave] == REMOVIDO


def test_mascaramento_alcanca_estruturas_aninhadas() -> None:
    evento = mascarar_dados_sensiveis(
        None,
        "info",
        {
            "event": "x",
            "cabecalhos": {"cookie": "__Host-sessao=abc", "accept": "json"},
            "lista": [{"senha": "123"}, ("ok",)],
        },
    )
    assert evento["cabecalhos"] == {"cookie": REMOVIDO, "accept": "json"}
    assert evento["lista"] == [{"senha": REMOVIDO}, ("ok",)]


@pytest.fixture
def saida_logs() -> Iterator[io.StringIO]:
    configurar_logs("INFO")
    buffer = io.StringIO()
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setStream(buffer)
    yield buffer
    structlog.reset_defaults()
    logging.getLogger().handlers.clear()


def test_saida_json_numa_linha_sem_dados_sensiveis(saida_logs: io.StringIO) -> None:
    structlog.get_logger("teste").info(
        "conta_criada", senha="nao-pode-aparecer", email="ana@exemplo.com", usuario="u1"
    )
    logging.getLogger("uvicorn.error").info("biblioteca %s", "externa")
    linhas = [json.loads(linha) for linha in saida_logs.getvalue().strip().splitlines()]
    assert linhas[0]["event"] == "conta_criada"
    assert linhas[0]["senha"] == REMOVIDO and linhas[0]["email"] == REMOVIDO
    assert linhas[0]["level"] == "info" and linhas[0]["timestamp"].endswith("Z")
    assert linhas[1]["event"] == "biblioteca externa"
    saida = json.dumps(linhas)
    assert "nao-pode-aparecer" not in saida and "ana@exemplo.com" not in saida


# --- Correlação ------------------------------------------------------------------------


async def test_x_request_id_valido_e_preservado(cliente: httpx.AsyncClient) -> None:
    recebido = str(uuid.uuid4())
    resposta = await cliente.get("/health", headers={"X-Request-ID": recebido})
    assert resposta.headers["x-request-id"] == recebido


@pytest.mark.parametrize("valor", ["abc", "1; DROP TABLE", "x" * 500, ""])
async def test_x_request_id_invalido_e_substituido(cliente: httpx.AsyncClient, valor: str) -> None:
    resposta = await cliente.get("/health", headers={"X-Request-ID": valor})
    uuid.UUID(resposta.headers["x-request-id"])
    assert resposta.headers["x-request-id"] != valor


async def test_id_do_corpo_de_erro_e_o_mesmo_do_cabecalho(cliente: httpx.AsyncClient) -> None:
    resposta = await cliente.get("/rota-inexistente")
    assert resposta.json()["idRequisicao"] == resposta.headers["x-request-id"]


async def test_log_da_requisicao_registra_a_rota_pelo_modelo(cliente: httpx.AsyncClient) -> None:
    with capture_logs() as registros:
        await cliente.get("/api/v1/itens/valor-do-estudante")
    [registro] = [r for r in registros if r["event"] == "requisicao"]
    assert registro["rota"] == "/api/v1/itens/{item_id}"
    assert registro["status"] == 200 and registro["metodo"] == "GET"
    assert "valor-do-estudante" not in json.dumps(registro)


# --- Cabeçalhos de segurança -------------------------------------------------------------


@pytest.mark.parametrize("caminho", ["/health", "/api/v1/itens/1", "/rota-inexistente"])
async def test_cabecalhos_de_seguranca_em_toda_resposta(
    cliente: httpx.AsyncClient, caminho: str
) -> None:
    resposta = await cliente.get(caminho)
    assert resposta.headers["x-content-type-options"] == "nosniff"
    assert resposta.headers["referrer-policy"] == "same-origin"
    assert resposta.headers["x-frame-options"] == "DENY"


async def test_api_responde_com_no_store(cliente: httpx.AsyncClient) -> None:
    assert (await cliente.get("/api/v1/itens/1")).headers["cache-control"] == "no-store"
    assert "cache-control" not in (await cliente.get("/health")).headers


# --- Limite de corpo ---------------------------------------------------------------------


async def test_corpo_no_limite_e_aceito(cliente: httpx.AsyncClient) -> None:
    resposta = await cliente.post("/api/v1/auth/eco", content=b"a" * 64 * 1024)
    assert resposta.json() == {"bytes": 65536}


async def test_corpo_acima_de_64_kib_e_recusado_pelo_content_length(
    cliente: httpx.AsyncClient,
) -> None:
    resposta = await cliente.post("/api/v1/auth/eco", content=b"a" * (64 * 1024 + 1))
    assert resposta.status_code == 413
    assert resposta.json()["codigo"] == "requisicao_malformada"
    assert resposta.headers["x-content-type-options"] == "nosniff"


async def test_corpo_acima_de_64_kib_sem_content_length_e_recusado(
    cliente: httpx.AsyncClient,
) -> None:
    async def partes() -> AsyncIterator[bytes]:
        for _ in range(70):
            yield b"a" * 1024

    resposta = await cliente.post("/api/v1/auth/eco", content=partes())
    assert resposta.status_code == 413
    assert resposta.json()["codigo"] == "requisicao_malformada"


async def test_content_length_invalido_e_recusado(cliente: httpx.AsyncClient) -> None:
    resposta = await cliente.post(
        "/api/v1/auth/eco", content=b"{}", headers={"content-length": "-1"}
    )
    assert resposta.status_code == 400
