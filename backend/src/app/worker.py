"""Ponto de entrada do worker do Procrastinate: `python -m app.worker` (serviço `worker`)."""

from __future__ import annotations

import asyncio

import structlog

from app.ia.configuracao import obter_configuracao_ia
from app.nucleo.configuracao import Configuracao, obter_configuracao
from app.nucleo.fila import app_fila
from app.nucleo.logs import configurar_logs

logger = structlog.get_logger(__name__)


def carregar_tarefas() -> None:
    """Importa os módulos de tarefas (`MODULOS_TAREFAS`).

    O Procrastinate só faz isso sozinho pela linha de comando dele; aqui o worker é próprio,
    e sem esta chamada ele iniciaria sem as tarefas dos domínios (e falharia os jobs).
    """
    app_fila.perform_import_paths()  # type: ignore[no-untyped-call]


def validar_configuracao() -> Configuracao:
    """Valida a configuração geral e a da IA antes de aceitar jobs (o worker chama o provedor)."""
    configuracao = obter_configuracao()
    obter_configuracao_ia()
    return configuracao


async def executar() -> None:
    configuracao = validar_configuracao()
    configurar_logs(configuracao.log_nivel)
    carregar_tarefas()
    async with app_fila.open_async():
        logger.info("worker_iniciado", tarefas=sorted(app_fila.tasks))
        await app_fila.run_worker_async(install_signal_handlers=True)


if __name__ == "__main__":
    asyncio.run(executar())
