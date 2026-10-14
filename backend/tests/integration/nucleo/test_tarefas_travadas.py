"""Jobs travados voltam à fila (DTEC 030, T007).

Um worker que morre deixa o job em `doing`, sem sinal de vida. A tarefa periódica o devolve à
fila; como as tarefas do projeto são idempotentes, repetir é seguro.
"""

from __future__ import annotations

import pytest
from procrastinate import App
from sqlalchemy import text

from app.nucleo.banco import FabricaSessoes
from app.nucleo.fila import app_fila, reenfileirar_travadas

pytestmark = pytest.mark.integration

NOME = "nucleo.reenfileirar_tarefas_travadas"


def test_a_tarefa_roda_a_cada_10_minutos_com_trava_de_fila_propria() -> None:
    periodicas = {
        nome: tarefa.cron for (nome, _), tarefa in app_fila.periodic_registry.periodic_tasks.items()
    }
    assert periodicas[NOME] == "*/10 * * * *"
    assert app_fila.tasks[NOME].queueing_lock == NOME


async def _criar_job(fabrica: FabricaSessoes, *, segundos_sem_sinal: int | None) -> int:
    """Cria um job `doing`; sem worker (`None`) ou com um worker de sinal mais ou menos antigo."""
    async with fabrica() as sessao, sessao.begin():
        id_worker = None
        if segundos_sem_sinal is not None:
            id_worker = (
                await sessao.execute(
                    text(
                        "INSERT INTO procrastinate_workers (last_heartbeat) "
                        "VALUES (now() - make_interval(secs => :s)) RETURNING id"
                    ),
                    {"s": segundos_sem_sinal},
                )
            ).scalar_one()
        id_job = (
            await sessao.execute(
                text(
                    "INSERT INTO procrastinate_jobs (queue_name, task_name, status, worker_id) "
                    "VALUES ('default', 'testes.qualquer', 'doing', :w) RETURNING id"
                ),
                {"w": id_worker},
            )
        ).scalar_one()
        return int(id_job)


async def _estado(fabrica: FabricaSessoes, id_job: int) -> tuple[str, int | None]:
    async with fabrica() as sessao:
        linha = (
            await sessao.execute(
                text("SELECT status::text, worker_id FROM procrastinate_jobs WHERE id = :i"),
                {"i": id_job},
            )
        ).one()
        return linha[0], linha[1]


async def _trabalhadores(fabrica: FabricaSessoes) -> int:
    async with fabrica() as sessao:
        total = (
            await sessao.execute(text("SELECT count(*) FROM procrastinate_workers"))
        ).scalar_one()
        return int(total)


async def test_job_de_worker_sem_sinal_de_vida_volta_para_a_fila(
    fila: App, fabrica_real: FabricaSessoes
) -> None:
    id_job = await _criar_job(fabrica_real, segundos_sem_sinal=600)

    assert await reenfileirar_travadas(fila, 60) == 1

    status, worker = await _estado(fabrica_real, id_job)
    assert status == "todo"
    assert worker is None
    # O worker morto também é removido.
    assert await _trabalhadores(fabrica_real) == 0


async def test_job_sem_worker_associado_tambem_volta_para_a_fila(
    fila: App, fabrica_real: FabricaSessoes
) -> None:
    id_job = await _criar_job(fabrica_real, segundos_sem_sinal=None)
    assert await reenfileirar_travadas(fila, 60) == 1
    assert (await _estado(fabrica_real, id_job))[0] == "todo"


async def test_job_de_worker_vivo_nao_e_tocado(fila: App, fabrica_real: FabricaSessoes) -> None:
    id_job = await _criar_job(fabrica_real, segundos_sem_sinal=5)

    assert await reenfileirar_travadas(fila, 60) == 0

    assert (await _estado(fabrica_real, id_job))[0] == "doing"
    assert await _trabalhadores(fabrica_real) == 1


async def test_o_limite_vem_da_configuracao_de_segundos_travado(
    fila: App, fabrica_real: FabricaSessoes
) -> None:
    id_job = await _criar_job(fabrica_real, segundos_sem_sinal=30)
    assert await reenfileirar_travadas(fila, 60) == 0
    assert await reenfileirar_travadas(fila, 20) == 1
    assert (await _estado(fabrica_real, id_job))[0] == "todo"
