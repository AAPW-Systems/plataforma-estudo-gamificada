"""Enfileiramento atômico com a transação (emenda da DTEC 002; T017)."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.fila import app_fila, enfileirar

pytestmark = pytest.mark.integration


@app_fila.task(name="testes.tarefa_de_teste", pass_context=False)
async def tarefa_de_teste(valor: int) -> None:
    """Tarefa usada só para observar a fila; nunca é executada nos testes."""


class _Falha(Exception):
    pass


async def _jobs(fabrica: FabricaSessoes) -> list[tuple[str, dict[str, int]]]:
    async with fabrica() as sessao:
        linhas = await sessao.execute(
            text("SELECT task_name, args FROM procrastinate_jobs ORDER BY id")
        )
        return [(linha.task_name, linha.args) for linha in linhas]


async def test_rollback_nao_deixa_tarefa_na_fila(fabrica_real: FabricaSessoes) -> None:
    with pytest.raises(_Falha):
        async with unidade_de_trabalho(fabrica_real) as sessao:
            await enfileirar(sessao, tarefa_de_teste, valor=1)
            raise _Falha
    assert await _jobs(fabrica_real) == []


async def test_commit_deixa_tarefa_na_fila(fabrica_real: FabricaSessoes) -> None:
    async with unidade_de_trabalho(fabrica_real) as sessao:
        id_job = await enfileirar(sessao, tarefa_de_teste, valor=2)
        # Antes do commit, outra conexão não enxerga a tarefa.
        assert await _jobs(fabrica_real) == []
    assert id_job > 0
    assert await _jobs(fabrica_real) == [("testes.tarefa_de_teste", {"valor": 2})]


async def test_queueing_lock_impede_duplicata_na_fila(fabrica_real: FabricaSessoes) -> None:
    from procrastinate.exceptions import AlreadyEnqueued

    async with unidade_de_trabalho(fabrica_real) as sessao:
        await enfileirar(sessao, tarefa_de_teste, queueing_lock="unico", valor=3)
    with pytest.raises(AlreadyEnqueued):
        async with unidade_de_trabalho(fabrica_real) as sessao:
            await enfileirar(sessao, tarefa_de_teste, queueing_lock="unico", valor=4)
    assert len(await _jobs(fabrica_real)) == 1
