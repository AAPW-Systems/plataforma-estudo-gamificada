"""Ponto de entrada do worker do Procrastinate: `python -m app.worker` (serviço `worker`)."""

from __future__ import annotations

import asyncio

import structlog

from app.nucleo.configuracao import obter_configuracao
from app.nucleo.fila import app_fila
from app.nucleo.logs import configurar_logs

logger = structlog.get_logger(__name__)


async def executar() -> None:
    configuracao = obter_configuracao()
    configurar_logs(configuracao.log_nivel)
    async with app_fila.open_async():
        logger.info("worker_iniciado", tarefas=sorted(app_fila.tasks))
        await app_fila.run_worker_async(install_signal_handlers=True)


if __name__ == "__main__":
    asyncio.run(executar())
