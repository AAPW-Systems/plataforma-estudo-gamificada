"""Fila de tarefas no PostgreSQL com Procrastinate (DTEC 006 e emenda da DTEC 002).

`enfileirar` grava a tarefa na conexão da transação corrente da sessão: se a transação
for desfeita, a tarefa some com ela; se for confirmada, a tarefa fica visível ao worker.
"""

from __future__ import annotations

from typing import Any

from procrastinate import App, PsycopgConnector
from procrastinate.tasks import Task
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.banco import conexao_psycopg
from app.nucleo.configuracao import obter_configuracao

# Módulos com tarefas, importados pelo worker ao iniciar.
MODULOS_TAREFAS: list[str] = ["app.identidade.tarefas"]


def _criar_pool(**opcoes: Any) -> AsyncConnectionPool:
    # A configuração é lida só ao abrir o pool (no worker), não ao importar as tarefas.
    return AsyncConnectionPool(
        conninfo=obter_configuracao().conninfo(),
        kwargs={"application_name": "plataforma-worker"},
        **opcoes,
    )


# A API enfileira pela conexão da própria transação e não abre o pool; o worker abre.
app_fila = App(connector=PsycopgConnector(pool_factory=_criar_pool), import_paths=MODULOS_TAREFAS)


async def enfileirar(
    sessao: AsyncSession,
    tarefa: Task[Any, Any, Any],
    *,
    lock: str | None = None,
    queueing_lock: str | None = None,
    **argumentos: Any,
) -> int:
    """Enfileira `tarefa` na transação corrente de `sessao`; devolve o id do job."""
    conexao = await conexao_psycopg(sessao)
    opcoes: dict[str, Any] = {"connection": conexao}
    if lock is not None:
        opcoes["lock"] = lock
    if queueing_lock is not None:
        opcoes["queueing_lock"] = queueing_lock
    return await tarefa.configure(**opcoes).defer_async(**argumentos)
