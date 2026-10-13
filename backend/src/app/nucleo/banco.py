"""Acesso ao PostgreSQL: engine assíncrono sobre psycopg 3 e unidade de trabalho.

O psycopg 3 é o único driver (emenda da DTEC 002): a mesma conexão da transação do
SQLAlchemy é entregue ao Procrastinate, de modo que uma tarefa só entra na fila se a
transação que a criou for confirmada.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import psycopg
from sqlalchemy import URL, MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.nucleo.configuracao import Configuracao

type FabricaSessoes = async_sessionmaker[AsyncSession]

# Nomes estáveis de restrições: as migrações e o ORM concordam sem depender do Postgres.
CONVENCAO_NOMES = {
    "ix": "%(table_name)s_%(column_0_N_name)s_idx",
    "uq": "%(table_name)s_%(column_0_N_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCAO_NOMES)


def url_banco(configuracao: Configuracao, banco: str | None = None) -> URL:
    return URL.create(
        "postgresql+psycopg",
        username=configuracao.postgres_user,
        password=configuracao.postgres_password.get_secret_value(),
        host=configuracao.postgres_host,
        port=configuracao.postgres_port,
        database=banco or configuracao.postgres_db,
    )


def criar_engine(configuracao: Configuracao, banco: str | None = None) -> AsyncEngine:
    return create_async_engine(
        url_banco(configuracao, banco),
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={
            # Instantes sempre em UTC na sessão; a conversão para o fuso do estudante é da app.
            "options": "-c timezone=UTC -c statement_timeout=15000",
            "application_name": "plataforma-api",
        },
    )


def criar_fabrica(engine: AsyncEngine) -> FabricaSessoes:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@asynccontextmanager
async def unidade_de_trabalho(fabrica: FabricaSessoes) -> AsyncIterator[AsyncSession]:
    """Uma transação: confirma ao sair sem erro e desfaz em qualquer exceção."""
    async with fabrica() as sessao, sessao.begin():
        yield sessao


async def conexao_psycopg(sessao: AsyncSession) -> psycopg.AsyncConnection[object]:
    """A conexão psycopg da transação corrente da sessão (para enfileirar na mesma transação)."""
    conexao = await sessao.connection()
    bruta = await conexao.get_raw_connection()
    driver = bruta.driver_connection
    if not isinstance(driver, psycopg.AsyncConnection):
        raise TypeError("a sessão não usa o driver psycopg assíncrono")
    return driver
