"""Composição da aplicação e de seus recursos (T022)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware import Middleware

from app.identidade.dominio import carregar_senhas_comuns
from app.identidade.rotas import roteador as identidade
from app.identidade.servicos import ServicoIdentidade
from app.nucleo.banco import FabricaSessoes, criar_engine, criar_fabrica
from app.nucleo.configuracao import Configuracao, obter_configuracao
from app.nucleo.erros import MiddlewareErrosInesperados, registrar_handlers
from app.nucleo.logs import configurar_logs
from app.nucleo.middlewares import (
    MiddlewareCabecalhosSeguranca,
    MiddlewareCorrelacao,
    MiddlewareLimiteCorpo,
)
from app.nucleo.openapi import instalar_openapi
from app.nucleo.relogio import Relogio, RelogioSistema
from app.nucleo.seguranca.protecao import MiddlewareProtecaoCsrf
from app.nucleo.seguranca.senhas import ServicoSenhas
from app.saude.rotas import roteador as saude


def criar_aplicacao(
    configuracao: Configuracao | None = None,
    *,
    fabrica_sessoes: FabricaSessoes | None = None,
    relogio: Relogio | None = None,
    servico_senhas: ServicoSenhas | None = None,
    senhas_comuns: frozenset[str] | None = None,
) -> FastAPI:
    configuracao = configuracao or obter_configuracao()

    @asynccontextmanager
    async def vida(app: FastAPI) -> AsyncIterator[None]:
        configurar_logs(configuracao.log_nivel)
        engine = criar_engine(configuracao) if fabrica_sessoes is None else None
        app.state.fabrica_sessoes = criar_fabrica(engine) if engine is not None else fabrica_sessoes
        # Sem a lista de senhas comuns (DTEC 022) ou com o Argon2 inviável, a app não sobe.
        senhas = servico_senhas or ServicoSenhas(configuracao.argon2_concorrencia)
        await senhas.preparar()
        app.state.identidade = ServicoIdentidade(
            fabrica=app.state.fabrica_sessoes,
            configuracao=configuracao,
            relogio=app.state.relogio,
            senhas=senhas,
            senhas_comuns=senhas_comuns or carregar_senhas_comuns(),
        )
        try:
            yield
        finally:
            if engine is not None:
                await engine.dispose()

    desenvolvimento = configuracao.app_ambiente == "desenvolvimento"
    app = FastAPI(
        title="Plataforma de estudos gamificada",
        version="0.1.0",
        docs_url="/api/docs" if desenvolvimento else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if desenvolvimento else None,
        lifespan=vida,
        middleware=[
            Middleware(MiddlewareCorrelacao),
            Middleware(MiddlewareCabecalhosSeguranca),
            Middleware(MiddlewareLimiteCorpo),
            Middleware(MiddlewareProtecaoCsrf, configuracao=configuracao),
            Middleware(MiddlewareErrosInesperados),
        ],
    )
    app.state.configuracao = configuracao
    app.state.relogio = relogio or RelogioSistema()
    registrar_handlers(app)
    app.include_router(saude)
    app.include_router(identidade)
    instalar_openapi(app)
    return app
