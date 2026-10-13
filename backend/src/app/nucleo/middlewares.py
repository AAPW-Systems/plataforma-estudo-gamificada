"""Middlewares ASGI puros: correlação, cabeçalhos de segurança e limite de corpo.

Ordem na aplicação (de fora para dentro): correlação → cabeçalhos → limite de corpo →
erros inesperados → roteador. Assim toda resposta, inclusive 413 e 500, sai com
`X-Request-ID` e os cabeçalhos de segurança.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Iterable

import structlog
from starlette.datastructures import MutableHeaders
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.nucleo.erros import MENSAGEM_CORPO_GRANDE, RequisicaoMalformada, resposta_erro

logger = structlog.get_logger("app.requisicao")

CABECALHO_ID = "X-Request-ID"
LIMITE_CORPO_PADRAO = 64 * 1024


def _cabecalho(scope: Scope, nome: bytes) -> str | None:
    for chave, valor in scope.get("headers", ()):
        if chave == nome:
            return bytes(valor).decode("latin-1")
    return None


def _id_valido(valor: str | None) -> uuid.UUID | None:
    if not valor or len(valor) > 36:
        return None
    try:
        return uuid.UUID(valor)
    except ValueError:
        return None


class MiddlewareCorrelacao:
    """Aceita o `X-Request-ID` recebido só se for um UUID; senão gera outro.

    O identificador vai para `scope["state"]`, para o contexto dos logs e para a resposta.
    Ao fim, registra método, rota pelo modelo (sem valores), status e duração.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        id_requisicao = _id_valido(_cabecalho(scope, b"x-request-id")) or uuid.uuid4()
        scope.setdefault("state", {})["id_requisicao"] = id_requisicao
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(idRequisicao=str(id_requisicao))
        inicio = time.perf_counter()
        status = 500

        async def enviar(mensagem: Message) -> None:
            nonlocal status
            if mensagem["type"] == "http.response.start":
                status = mensagem["status"]
                MutableHeaders(scope=mensagem)[CABECALHO_ID] = str(id_requisicao)
            await send(mensagem)

        try:
            await self.app(scope, receive, enviar)
        finally:
            rota = scope.get("route")
            logger.info(
                "requisicao",
                metodo=scope["method"],
                rota=getattr(rota, "path", None) or "nao_encontrada",
                status=status,
                duracaoMs=round((time.perf_counter() - inicio) * 1000, 1),
            )
            structlog.contextvars.clear_contextvars()


class MiddlewareCabecalhosSeguranca:
    """Cabeçalhos de segurança em toda resposta e `no-store` na API (plano da 001)."""

    def __init__(self, app: ASGIApp, prefixos_sem_cache: Iterable[str] = ("/api/",)) -> None:
        self.app = app
        self.prefixos_sem_cache = tuple(prefixos_sem_cache)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        sem_cache = scope["path"].startswith(self.prefixos_sem_cache)

        async def enviar(mensagem: Message) -> None:
            if mensagem["type"] == "http.response.start":
                cabecalhos = MutableHeaders(scope=mensagem)
                cabecalhos["X-Content-Type-Options"] = "nosniff"
                cabecalhos["Referrer-Policy"] = "same-origin"
                cabecalhos["X-Frame-Options"] = "DENY"
                if sem_cache:
                    cabecalhos["Cache-Control"] = "no-store"
            await send(mensagem)

        await self.app(scope, receive, enviar)


class _CorpoGrandeDemais(StarletteHTTPException):
    """HTTPException para que o FastAPI a repasse ao ler o corpo, em vez de virar 400."""

    def __init__(self) -> None:
        super().__init__(status_code=413)


class MiddlewareLimiteCorpo:
    """Recusa com `413` o corpo acima do limite, pelo `Content-Length` ou durante a leitura.

    O código é o já existente `requisicao_malformada`; a 001 não define um código próprio.
    """

    def __init__(self, app: ASGIApp, limite_bytes: int = LIMITE_CORPO_PADRAO) -> None:
        self.app = app
        self.limite = limite_bytes

    async def _recusar(self, scope: Scope, receive: Receive, send: Send) -> None:
        resposta = resposta_erro(scope, RequisicaoMalformada(MENSAGEM_CORPO_GRANDE), status=413)
        await resposta(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declarado = _cabecalho(scope, b"content-length")
        if declarado is not None:
            if not declarado.isdigit():
                await resposta_erro(scope, RequisicaoMalformada())(scope, receive, send)
                return
            if int(declarado) > self.limite:
                await self._recusar(scope, receive, send)
                return

        recebidos = 0
        resposta_iniciada = False

        async def receber() -> Message:
            nonlocal recebidos
            mensagem = await receive()
            if mensagem["type"] == "http.request":
                recebidos += len(mensagem.get("body", b""))
                if recebidos > self.limite:
                    raise _CorpoGrandeDemais
            return mensagem

        async def enviar(mensagem: Message) -> None:
            nonlocal resposta_iniciada
            if mensagem["type"] == "http.response.start":
                resposta_iniciada = True
            await send(mensagem)

        try:
            await self.app(scope, receber, enviar)
        except _CorpoGrandeDemais:
            if resposta_iniciada:
                raise
            await self._recusar(scope, receive, send)
