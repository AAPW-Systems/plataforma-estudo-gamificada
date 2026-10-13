"""Proteção das requisições que alteram estado: Origin, Sec-Fetch-Site e CSRF (RF-011, DTEC 023).

Ordem de verificação: `Origin` → `Sec-Fetch-Site` → token anti-CSRF. Clientes que não são
navegadores (sem `Origin` nem `Sec-Fetch-Site`) passam pelas duas primeiras e ainda
dependem do token, que um site de terceiros não consegue ler nem enviar.
"""

from __future__ import annotations

from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.nucleo.configuracao import Configuracao
from app.nucleo.erros import AcessoNegado, CodigoErro, ErroAplicacao, resposta_erro
from app.nucleo.seguranca.csrf import verificar_token, vinculo_dos_cookies

METODOS_SEGUROS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
CABECALHO_CSRF = "x-csrf-token"

MENSAGEM_ORIGEM = "Esta origem não tem permissão para enviar a requisição."


class MiddlewareProtecaoCsrf:
    def __init__(self, app: ASGIApp, configuracao: Configuracao) -> None:
        self.app = app
        self.origens = frozenset(configuracao.origens_permitidas)
        self.nome_cookie_sessao = configuracao.cookie_sessao_nome
        self.nome_cookie_csrf = configuracao.cookie_csrf_nome
        self.segredo = configuracao.segredo

    def _avaliar(self, scope: Scope) -> ErroAplicacao | None:
        cabecalhos = Headers(scope=scope)

        origens = cabecalhos.getlist("origin")
        if len(origens) > 1 or (origens and origens[0] not in self.origens):
            return AcessoNegado(MENSAGEM_ORIGEM, codigo=CodigoErro.ORIGEM_NAO_PERMITIDA)

        sites = cabecalhos.getlist("sec-fetch-site")
        if len(sites) > 1 or (sites and sites[0] != "same-origin"):
            return AcessoNegado(MENSAGEM_ORIGEM, codigo=CodigoErro.ORIGEM_NAO_PERMITIDA)

        cookies = Request(scope).cookies
        vinculo = vinculo_dos_cookies(cookies, self.nome_cookie_sessao)
        if not verificar_token(
            self.segredo,
            vinculo,
            cookies.get(self.nome_cookie_csrf),
            cabecalhos.get(CABECALHO_CSRF),
        ):
            return AcessoNegado(codigo=CodigoErro.CSRF_INVALIDO)
        return None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] in METODOS_SEGUROS:
            await self.app(scope, receive, send)
            return
        erro = self._avaliar(scope)
        if erro is not None:
            await resposta_erro(scope, erro)(scope, receive, send)
            return
        await self.app(scope, receive, send)
