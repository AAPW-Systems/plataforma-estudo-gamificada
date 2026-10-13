"""Fixtures compartilhadas (plano da 001, "Banco nos testes").

- Banco `plataforma_teste`, no mesmo Postgres, recriado e migrado uma vez por execução.
- Cada teste roda numa transação externa com savepoints, desfeita ao final.
- Testes de concorrência usam `fabrica_real` (conexões reais) e limpam o que criam.

Regra para as próximas specs: só acrescentar fixtures (divisão da implementação do MVP).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import httpx
import psycopg
import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, async_sessionmaker

from app.nucleo.banco import FabricaSessoes, criar_engine, criar_fabrica
from app.nucleo.configuracao import Configuracao, obter_configuracao
from app.nucleo.relogio import RelogioControlavel

BANCO_TESTE = "plataforma_teste"
SEGREDO_TESTE = "segredo-de-teste-com-mais-de-32-bytes-0123456789"


@pytest.fixture(scope="session")
def configuracao() -> Configuracao:
    """Configuração do ambiente de teste: banco próprio e armazenamento em memória."""
    base = obter_configuracao()
    return base.model_copy(
        update={
            "app_ambiente": "teste",
            "postgres_db": BANCO_TESTE,
            "armazenamento_adaptador": "memoria",
            "origens_permitidas": ["https://teste"],
        }
    )


def _recriar_banco(configuracao: Configuracao) -> None:
    administracao = obter_configuracao().conninfo()
    with psycopg.connect(administracao, autocommit=True) as conexao:
        conexao.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(BANCO_TESTE))
        )
        conexao.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(BANCO_TESTE)))


def executar_alembic(acao: str, destino: str) -> None:
    """Roda o Alembic (`upgrade` ou `downgrade`) contra o banco de teste."""
    config = Config("alembic.ini")
    config.attributes["banco"] = BANCO_TESTE
    getattr(command, acao)(config, destino)


@pytest.fixture(scope="session")
def banco_migrado(configuracao: Configuracao) -> Iterator[None]:
    _recriar_banco(configuracao)
    executar_alembic("upgrade", "head")
    yield


@pytest.fixture(scope="session")
async def engine(configuracao: Configuracao, banco_migrado: None) -> AsyncIterator[AsyncEngine]:
    engine = criar_engine(configuracao)
    yield engine
    await engine.dispose()


@pytest.fixture
async def conexao(engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    """Transação externa por teste; tudo o que o teste grava é desfeito ao final."""
    async with engine.connect() as conexao:
        transacao = await conexao.begin()
        try:
            yield conexao
        finally:
            if transacao.is_active:
                await transacao.rollback()


@pytest.fixture
def fabrica_sessoes(conexao: AsyncConnection) -> FabricaSessoes:
    """Sessões presas à transação do teste: cada `begin()` da aplicação vira um savepoint."""
    return async_sessionmaker(
        bind=conexao,
        expire_on_commit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )


@pytest.fixture
async def fabrica_real(engine: AsyncEngine) -> AsyncIterator[FabricaSessoes]:
    """Conexões reais, para concorrência; apaga ao final as linhas que os testes criaram."""
    yield criar_fabrica(engine)
    async with engine.begin() as conexao:
        tabelas = (
            await conexao.execute(
                text(
                    "SELECT string_agg(quote_ident(tablename), ', ') FROM pg_tables "
                    "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
                )
            )
        ).scalar_one()
        if tabelas:
            await conexao.execute(text(f"TRUNCATE {tabelas} RESTART IDENTITY CASCADE"))


@pytest.fixture
def relogio() -> RelogioControlavel:
    return RelogioControlavel()


@pytest.fixture(scope="session")
def segredo_teste() -> str:
    return SEGREDO_TESTE


@pytest.fixture
async def aplicacao(
    configuracao: Configuracao, fabrica_sessoes: FabricaSessoes, relogio: RelogioControlavel
) -> AsyncIterator[FastAPI]:
    from app.principal import criar_aplicacao

    app = criar_aplicacao(configuracao, fabrica_sessoes=fabrica_sessoes, relogio=relogio)
    async with app.router.lifespan_context(app):
        yield app


@pytest.fixture
async def cliente(aplicacao: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async def enviar_csrf(request: httpx.Request) -> None:
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            token = cliente_http.cookies.get(aplicacao.state.configuracao.cookie_csrf_nome)
            if token is not None and "X-CSRF-Token" not in request.headers:
                request.headers["X-CSRF-Token"] = token

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=aplicacao),
        base_url="https://teste",
        headers={"Origin": "https://teste", "Sec-Fetch-Site": "same-origin"},
        event_hooks={"request": [enviar_csrf]},
    ) as cliente_http:
        yield cliente_http
