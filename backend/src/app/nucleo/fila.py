"""Fila de tarefas no PostgreSQL com Procrastinate (DTEC 006 e emenda da DTEC 002).

`enfileirar` grava a tarefa na conexão da transação corrente da sessão: se a transação
for desfeita, a tarefa some com ela; se for confirmada, a tarefa fica visível ao worker.
"""

from __future__ import annotations

from typing import Any

import structlog
from procrastinate import App, PsycopgConnector
from procrastinate.tasks import Task
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.banco import conexao_psycopg
from app.nucleo.configuracao import obter_configuracao

logger = structlog.get_logger(__name__)

# Módulos com tarefas, importados pelo worker ao iniciar.
MODULOS_TAREFAS: list[str] = ["app.identidade.tarefas", "app.fontes.tarefas"]


class ErroTransitorio(Exception):
    """Falha que pode passar sozinha (E/S do armazenamento, conexão com o banco).

    É a única que as tarefas com nova tentativa automática relançam (`retry_exceptions`,
    DTEC 030). Na última tentativa, quem a captura grava a falha técnica em vez de relançar.
    """


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


async def reenfileirar_travadas(app: App, segundos_sem_sinal: int) -> int:
    """Devolve à fila os jobs `doing` de workers sem sinal de vida; devolve quantos eram.

    Um worker que morre deixa o job em `doing` e, no domínio, o registro em `processando`
    (DTEC 030). Como toda tarefa do projeto é idempotente, repetir é seguro. Os workers mortos
    também são removidos da tabela de workers.
    """
    travados = list(
        await app.job_manager.get_stalled_jobs(seconds_since_heartbeat=segundos_sem_sinal)
    )
    for job in travados:
        await app.job_manager.retry_job(job)
    await app.job_manager.prune_stalled_workers(segundos_sem_sinal)
    return len(travados)


@app_fila.periodic(cron="*/10 * * * *")
@app_fila.task(
    name="nucleo.reenfileirar_tarefas_travadas",
    queueing_lock="nucleo.reenfileirar_tarefas_travadas",
    pass_context=False,
)
async def reenfileirar_tarefas_travadas(timestamp: int) -> None:
    """Tarefa periódica (a cada 10 minutos) que vale para todas as tarefas do projeto."""
    reenfileirados = await reenfileirar_travadas(
        app_fila, obter_configuracao().fila_segundos_travado
    )
    if reenfileirados:
        logger.warning("tarefas_travadas_reenfileiradas", quantidade=reenfileirados)
