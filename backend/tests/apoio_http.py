"""Apoio aos testes de API: clientes HTTP com cookies e CSRF reais, e atalhos de fluxo.

O cliente é HTTPS (`https://teste`) porque os cookies `__Host-` são `Secure`. Ele repete o
cabeçalho `X-CSRF-Token` a partir do cookie nas requisições que alteram estado, como faz o
frontend; para testar a ausência do cabeçalho, envie `headers={"X-CSRF-Token": ""}` ou use
um cliente criado com `csrf_automatico=False`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from typing import Any

import httpx
from argon2 import PasswordHasher
from fastapi import FastAPI

from tests.contrato import validar_corpo_erro
from tests.fabricas import DadosConta

ORIGEM = "https://teste"
COOKIE_SESSAO = "__Host-sessao"
COOKIE_CSRF = "__Host-csrf"


def hasher_rapido() -> PasswordHasher:
    # Mínimos do argon2-cffi/libargon2: memória de pelo menos 8 KiB por faixa.
    return PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)


@asynccontextmanager
async def abrir_cliente(
    app: FastAPI,
    *,
    ip: str = "127.0.0.1",
    csrf_automatico: bool = True,
    cabecalhos: Mapping[str, str] | None = None,
) -> AsyncIterator[httpx.AsyncClient]:
    async def enviar_csrf(request: httpx.Request) -> None:
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            token = cliente_http.cookies.get(app.state.configuracao.cookie_csrf_nome)
            if token is not None and "X-CSRF-Token" not in request.headers:
                request.headers["X-CSRF-Token"] = token

    async def validar_erro(response: httpx.Response) -> None:
        """Todo corpo de erro observado nos testes valida contra o esquema `Erro` (T037)."""
        # `/health/ready` responde 503 com o esquema `Saude`, não com `Erro` (contrato).
        if response.status_code >= 400 and not response.request.url.path.startswith("/health"):
            await response.aread()
            validar_corpo_erro(response.json())

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=(ip, 50000)),
        base_url=ORIGEM,
        headers={"Origin": ORIGEM, "Sec-Fetch-Site": "same-origin", **(cabecalhos or {})},
        event_hooks={
            "request": [enviar_csrf] if csrf_automatico else [],
            "response": [validar_erro],
        },
    ) as cliente_http:
        yield cliente_http


async def obter_csrf(cliente: httpx.AsyncClient) -> httpx.Response:
    resposta = await cliente.get("/api/v1/auth/csrf")
    assert resposta.status_code == 204, resposta.text
    return resposta


async def cadastrar(
    cliente: httpx.AsyncClient, conta: DadosConta | Mapping[str, Any], **extras: Any
) -> httpx.Response:
    """Cadastro como o SPA faz: pede o CSRF e envia o corpo."""
    await obter_csrf(cliente)
    corpo = dict(conta.cadastro() if isinstance(conta, DadosConta) else conta)
    return await cliente.post("/api/v1/auth/cadastro", json={**corpo, **extras})


async def entrar(
    cliente: httpx.AsyncClient, conta: DadosConta | Mapping[str, Any]
) -> httpx.Response:
    await obter_csrf(cliente)
    corpo = conta.entrada() if isinstance(conta, DadosConta) else conta
    return await cliente.post("/api/v1/auth/entrada", json=dict(corpo))


async def sair(cliente: httpx.AsyncClient) -> httpx.Response:
    return await cliente.post("/api/v1/auth/saida")


def sem_id_requisicao(corpo: Mapping[str, Any]) -> dict[str, Any]:
    """O corpo de erro sem o `idRequisicao`, que difere a cada requisição."""
    return {chave: valor for chave, valor in corpo.items() if chave != "idRequisicao"}


def cookies_da_resposta(resposta: httpx.Response) -> dict[str, str]:
    """Os `Set-Cookie` crus, por nome do cookie (atributos incluídos)."""
    cookies: dict[str, str] = {}
    for bruto in resposta.headers.get_list("set-cookie"):
        cookies[bruto.split("=", 1)[0]] = bruto
    return cookies
