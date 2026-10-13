"""Ambiente do Alembic.

As migrações usam o psycopg 3 em modo síncrono (o mesmo driver da aplicação). O banco
alvo vem da configuração; `-x banco=<nome>` troca só o nome (ex.: `plataforma_teste`), e
os testes podem passar uma conexão pronta em `config.attributes["connection"]`.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import Connection, create_engine, pool

from app.modelos import Base
from app.nucleo.banco import url_banco
from app.nucleo.configuracao import obter_configuracao

config = context.config
target_metadata = Base.metadata


def _executar(conexao: Connection) -> None:
    context.configure(
        connection=conexao,
        target_metadata=target_metadata,
        compare_type=True,
        transaction_per_migration=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def executar_online() -> None:
    conexao_pronta = config.attributes.get("connection")
    if isinstance(conexao_pronta, Connection):
        _executar(conexao_pronta)
        return
    banco = context.get_x_argument(as_dictionary=True).get("banco")
    engine = create_engine(
        url_banco(obter_configuracao(), banco),
        poolclass=pool.NullPool,
        connect_args={"options": "-c timezone=UTC", "application_name": "plataforma-migrate"},
    )
    with engine.connect() as conexao:
        _executar(conexao)
    engine.dispose()


if context.is_offline_mode():
    raise SystemExit("Migrações offline não são usadas: rode `alembic upgrade head`.")
executar_online()
