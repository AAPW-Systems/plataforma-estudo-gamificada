"""Fixtures compartilhadas (plano da 001, "Banco nos testes").

- Banco `plataforma_teste`, no mesmo Postgres, recriado e migrado uma vez por execução.
- Cada teste roda numa transação externa com savepoints, desfeita ao final.
- Testes de concorrência usam `fabrica_real` (conexões reais) e limpam o que criam.

Regra para as próximas specs: só acrescentar fixtures (divisão da implementação do MVP).
"""

from __future__ import annotations

import ipaddress
import os
from collections.abc import AsyncIterator, Iterator

import httpx
import psycopg
import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from procrastinate import App, PsycopgConnector
from psycopg import sql
from pydantic_ai import models
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, async_sessionmaker

from app.nucleo.banco import FabricaSessoes, criar_engine, criar_fabrica
from app.nucleo.configuracao import Configuracao, obter_configuracao
from app.nucleo.relogio import RelogioControlavel
from app.nucleo.seguranca.senhas import ServicoSenhas
from tests.apoio_http import abrir_cliente, hasher_rapido

# Spec 004 (DTEC 047): a suíte nunca chama um provedor de IA real. O PydanticAI recusa qualquer
# requisição a modelo que não seja simulado, e o domínio `ia` usa o provedor `teste`.
os.environ["IA_PROVEDOR"] = "teste"
models.ALLOW_MODEL_REQUESTS = False

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
            "proxies_confiaveis": [ipaddress.ip_network("172.28.0.10/32")],
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
def servico_senhas() -> ServicoSenhas:
    """Argon2id com custo mínimo: os testes de API não pagam 64 MiB por senha.

    O perfil real da RFC 9106 é coberto em `tests/unit/nucleo/test_seguranca.py`.
    """
    return ServicoSenhas(4, hasher_rapido())


@pytest.fixture
async def aplicacao(
    configuracao: Configuracao,
    fabrica_sessoes: FabricaSessoes,
    relogio: RelogioControlavel,
    servico_senhas: ServicoSenhas,
) -> AsyncIterator[FastAPI]:
    from app.principal import criar_aplicacao

    app = criar_aplicacao(
        configuracao,
        fabrica_sessoes=fabrica_sessoes,
        relogio=relogio,
        servico_senhas=servico_senhas,
    )
    async with app.router.lifespan_context(app):
        yield app


@pytest.fixture
async def aplicacao_real(
    configuracao: Configuracao,
    fabrica_real: FabricaSessoes,
    relogio: RelogioControlavel,
    servico_senhas: ServicoSenhas,
) -> AsyncIterator[FastAPI]:
    """A aplicação sobre conexões reais, para concorrência (limpa o banco ao final)."""
    from app.principal import criar_aplicacao

    app = criar_aplicacao(
        configuracao, fabrica_sessoes=fabrica_real, relogio=relogio, servico_senhas=servico_senhas
    )
    async with app.router.lifespan_context(app):
        yield app


@pytest.fixture
async def cliente(aplicacao: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with abrir_cliente(aplicacao) as cliente_http:
        yield cliente_http


@pytest.fixture
async def cliente_real(aplicacao_real: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with abrir_cliente(aplicacao_real) as cliente_http:
        yield cliente_http


@pytest.fixture
async def fila(configuracao: Configuracao, fabrica_real: FabricaSessoes) -> AsyncIterator[App]:
    """O `app_fila` conectado ao banco de teste, para executar o worker em processo (spec 002).

    Os jobs ficam em `procrastinate_jobs`, que a `fabrica_real` esvazia ao final. Use
    `executar_jobs(fila)` para processar tudo o que está pendente e terminar.
    """
    from app.nucleo.fila import app_fila

    conector = PsycopgConnector(conninfo=configuracao.conninfo(BANCO_TESTE))
    with app_fila.replace_connector(conector) as app:
        async with app.open_async():
            yield app


async def executar_jobs(app: App) -> None:
    """Executa os jobs pendentes e volta (o worker termina quando alcança a fila)."""
    await app.run_worker_async(wait=False, install_signal_handlers=False)


@pytest.fixture
async def acervo(aplicacao_real: FastAPI, fila: App) -> AsyncIterator[FastAPI]:
    """API e worker em processo sobre o mesmo banco real e o mesmo armazenamento (spec 002).

    Os jobs enfileirados pela API só são visíveis ao worker com a transação confirmada, por
    isso estes testes usam conexões reais (`aplicacao_real`) e não savepoints. Depois de enviar,
    chame `executar_jobs(fila)` para processar o que estiver pendente.
    """
    from app.fontes import tarefas

    tarefas.usar_dependencias(
        tarefas.DependenciasTarefas(
            fabrica=aplicacao_real.state.fabrica_sessoes,
            armazenamento=aplicacao_real.state.armazenamento,
            configuracao=aplicacao_real.state.configuracao,
        )
    )
    try:
        yield aplicacao_real
    finally:
        tarefas.restaurar_dependencias()
