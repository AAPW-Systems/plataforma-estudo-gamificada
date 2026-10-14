"""Execução isolada de arquivos não confiáveis (DTEC 024, T003).

O filho é um processo `spawn` real. Os casos de memória dependem de `RLIMIT_AS` e só rodam em
Linux (todo serviço roda em contêiner Linux, regra 11).
"""

from __future__ import annotations

import asyncio
import sys

import pytest

from app.nucleo.isolamento import ResultadoIsolado, StatusIsolado, executar_isolado
from tests import auxiliares_isolamento as aux

pytestmark = pytest.mark.integration

so_linux = pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="RLIMIT_AS só existe em Linux; os testes rodam no contêiner (DTEC 024)",
)


async def test_funcao_que_termina_devolve_o_resultado() -> None:
    resultado = await executar_isolado(aux.somar, (2, 3), tempo_limite_s=20, memoria_max_mb=256)
    assert resultado == ResultadoIsolado(StatusIsolado.OK, valor=5)


async def test_funcao_que_dorme_alem_do_limite_e_morta_e_devolve_tempo_esgotado() -> None:
    inicio = asyncio.get_running_loop().time()
    resultado = await executar_isolado(aux.dormir, (60,), tempo_limite_s=2, memoria_max_mb=256)
    decorrido = asyncio.get_running_loop().time() - inicio
    assert resultado.status is StatusIsolado.TEMPO_ESGOTADO
    assert resultado.valor is None
    # O filho foi morto de verdade: a chamada não esperou os 60 s da função.
    assert decorrido < 30


@so_linux
async def test_funcao_que_aloca_alem_do_teto_devolve_memoria_esgotada() -> None:
    resultado = await executar_isolado(
        aux.alocar_mb, (1024,), tempo_limite_s=30, memoria_max_mb=128
    )
    assert resultado.status is StatusIsolado.MEMORIA_ESGOTADA


@so_linux
async def test_alocacao_dentro_do_teto_funciona() -> None:
    resultado = await executar_isolado(aux.alocar_mb, (16,), tempo_limite_s=30, memoria_max_mb=256)
    assert resultado == ResultadoIsolado(StatusIsolado.OK, valor=16 * 1024 * 1024)


async def test_excecao_no_filho_vira_resultado_tipado_sem_a_mensagem() -> None:
    resultado = await executar_isolado(
        aux.levantar_erro, ("conteudo-secreto-do-arquivo",), tempo_limite_s=20, memoria_max_mb=256
    )
    assert resultado.status is StatusIsolado.ERRO
    assert resultado.erro == "ValueError"
    # A mensagem pode carregar caminho ou conteúdo do arquivo: nunca atravessa a fronteira.
    assert "conteudo-secreto" not in repr(resultado)


async def test_filho_que_morre_sem_responder_vira_falha_de_processo() -> None:
    resultado = await executar_isolado(
        aux.morrer_sem_resposta, (), tempo_limite_s=20, memoria_max_mb=256
    )
    assert resultado.status is StatusIsolado.FALHA_PROCESSO


async def test_resultado_nao_serializavel_vira_erro_e_nao_derruba_ninguem() -> None:
    resultado = await executar_isolado(
        aux.devolver_algo_nao_serializavel, (), tempo_limite_s=20, memoria_max_mb=256
    )
    assert resultado.status is StatusIsolado.ERRO


async def test_o_processo_pai_continua_respondendo_em_todos_os_casos() -> None:
    """Depois de timeout, memória e erro, uma chamada comum ainda funciona."""
    await executar_isolado(aux.dormir, (60,), tempo_limite_s=1, memoria_max_mb=256)
    await executar_isolado(aux.levantar_erro, ("x",), tempo_limite_s=20, memoria_max_mb=256)
    resultado = await executar_isolado(aux.somar, (1, 1), tempo_limite_s=20, memoria_max_mb=256)
    assert resultado.valor == 2


async def test_o_laco_de_eventos_nao_trava_enquanto_o_filho_trabalha() -> None:
    batidas = 0

    async def pulsar() -> None:
        nonlocal batidas
        while True:
            await asyncio.sleep(0.05)
            batidas += 1

    tarefa = asyncio.create_task(pulsar())
    try:
        await executar_isolado(aux.dormir, (1.5,), tempo_limite_s=30, memoria_max_mb=256)
    finally:
        tarefa.cancel()
    assert batidas >= 5


async def test_o_semaforo_limita_as_execucoes_simultaneas() -> None:
    semaforo = asyncio.Semaphore(1)
    resultados = await asyncio.gather(
        *(
            executar_isolado(
                aux.janela, (0.8,), tempo_limite_s=30, memoria_max_mb=256, semaforo=semaforo
            )
            for _ in range(3)
        )
    )
    janelas = sorted(r.valor for r in resultados)
    assert all(r.status is StatusIsolado.OK for r in resultados)
    for anterior, seguinte in zip(janelas, janelas[1:], strict=False):
        assert anterior[1] <= seguinte[0], "duas execuções se sobrepuseram com semáforo de 1"


async def test_sem_semaforo_as_execucoes_se_sobrepoem() -> None:
    """Contraprova do teste anterior: o semáforo é o que impede a sobreposição."""
    resultados = await asyncio.gather(
        *(
            executar_isolado(aux.janela, (1.5,), tempo_limite_s=30, memoria_max_mb=256)
            for _ in range(2)
        )
    )
    (inicio_a, fim_a), (inicio_b, fim_b) = (r.valor for r in resultados)
    assert max(inicio_a, inicio_b) < min(fim_a, fim_b)
