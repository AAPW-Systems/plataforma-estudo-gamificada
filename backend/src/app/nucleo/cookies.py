"""Cookies de sessão e anti-CSRF (DTEC 023)."""

from __future__ import annotations

from starlette.responses import Response

from app.nucleo.configuracao import Configuracao


def definir_cookie_sessao(resposta: Response, configuracao: Configuracao, token: str) -> None:
    resposta.set_cookie(
        configuracao.cookie_sessao_nome,
        token,
        max_age=configuracao.sessao_dias_maximo * 86_400,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )


def definir_cookie_csrf(resposta: Response, configuracao: Configuracao, token: str) -> None:
    # Legível pelo JavaScript: o cliente repete o valor no cabeçalho X-CSRF-Token.
    resposta.set_cookie(
        configuracao.cookie_csrf_nome,
        token,
        path="/",
        secure=True,
        httponly=False,
        samesite="lax",
    )


def apagar_cookies(resposta: Response, configuracao: Configuracao) -> None:
    for nome, httponly in (
        (configuracao.cookie_sessao_nome, True),
        (configuracao.cookie_csrf_nome, False),
    ):
        resposta.delete_cookie(nome, path="/", secure=True, httponly=httponly, samesite="lax")
