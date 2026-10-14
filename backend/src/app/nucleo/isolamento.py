"""Execução isolada de arquivos não confiáveis (DTEC 024).

Um parser em C (PyMuPDF) não é interrompível por *thread*: um laço infinito ou uma explosão de
memória dentro dele derrubaria a API ou o worker. Aqui a função roda num processo filho criado
pelo contexto `spawn`, com teto de memória (`RLIMIT_AS`) e tempo limite; passado o tempo, o pai
mata o filho. O filho recebe argumentos pequenos (o caminho de um arquivo temporário, nunca o
conteúdo) e devolve só dados simples e serializáveis.

O módulo importa apenas a biblioteca padrão para o filho nascer rápido.
"""

from __future__ import annotations

import asyncio
import multiprocessing
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from multiprocessing.connection import Connection
from typing import Any

try:  # `resource` não existe fora de Unix; sem ele não há teto de memória (testes só em Linux).
    import resource
except ImportError:  # pragma: no cover
    resource = None  # type: ignore[assignment]

_MIB = 1024 * 1024


type ExecutorIsolado = Callable[..., Awaitable["ResultadoIsolado"]]
"""Tipo de `executar_isolado`; os chamadores o recebem por parâmetro para testar sem subprocesso."""


class StatusIsolado(StrEnum):
    OK = "ok"
    TEMPO_ESGOTADO = "tempo_esgotado"
    MEMORIA_ESGOTADA = "memoria_esgotada"
    ERRO = "erro"
    FALHA_PROCESSO = "falha_processo"


@dataclass(frozen=True, slots=True)
class ResultadoIsolado:
    """Resultado tipado da execução.

    `erro` guarda só o *nome* do tipo da exceção do filho: a mensagem pode conter caminho ou
    trecho do arquivo e nunca atravessa a fronteira (RQ-002).
    """

    status: StatusIsolado
    valor: Any = None
    erro: str | None = None


def _memoria_virtual_atual_bytes() -> int:
    """Tamanho virtual do processo (Linux); `RLIMIT_AS` conta o espaço de endereços inteiro."""
    try:
        with open("/proc/self/statm", encoding="ascii") as arquivo:
            paginas = int(arquivo.read().split()[0])
    except (OSError, ValueError, IndexError):
        return 0
    return paginas * resource.getpagesize() if resource is not None else 0


def _filho(
    saida: Connection,
    funcao: Callable[..., Any],
    argumentos: tuple[Any, ...],
    memoria_max_mb: int,
) -> None:
    limite_original: tuple[int, int] | None = None
    if resource is not None and sys.platform.startswith("linux"):
        limite_original = resource.getrlimit(resource.RLIMIT_AS)
        # O teto vale para o que a função aloca: soma-se o que o interpretador e as bibliotecas
        # já ocupam depois de importadas, que varia com a versão e com a biblioteca.
        teto = _memoria_virtual_atual_bytes() + memoria_max_mb * _MIB
        resource.setrlimit(resource.RLIMIT_AS, (teto, limite_original[1]))

    resultado: ResultadoIsolado
    try:
        resultado = ResultadoIsolado(StatusIsolado.OK, valor=funcao(*argumentos))
    except MemoryError:
        resultado = ResultadoIsolado(StatusIsolado.MEMORIA_ESGOTADA)
    except BaseException as excecao:  # tudo no filho vira resultado tipado
        resultado = ResultadoIsolado(StatusIsolado.ERRO, erro=type(excecao).__name__)

    # Devolve o teto original antes de serializar: o próprio resultado precisa de memória.
    if limite_original is not None and resource is not None:
        resource.setrlimit(resource.RLIMIT_AS, limite_original)
    try:
        saida.send(resultado)
    except BaseException as excecao:  # valor não serializável, por exemplo
        saida.send(ResultadoIsolado(StatusIsolado.ERRO, erro=type(excecao).__name__))
    finally:
        saida.close()


def _executar_bloqueando(
    funcao: Callable[..., Any],
    argumentos: tuple[Any, ...],
    tempo_limite_s: float,
    memoria_max_mb: int,
) -> ResultadoIsolado:
    contexto = multiprocessing.get_context("spawn")
    entrada, saida = contexto.Pipe(duplex=False)
    processo = contexto.Process(
        target=_filho, args=(saida, funcao, argumentos, memoria_max_mb), daemon=True
    )
    processo.start()
    saida.close()  # só o filho escreve; assim o fim do filho aparece como EOF no pai
    try:
        if not entrada.poll(tempo_limite_s):
            return ResultadoIsolado(StatusIsolado.TEMPO_ESGOTADO)
        try:
            resultado = entrada.recv()
        except (EOFError, OSError):
            return ResultadoIsolado(StatusIsolado.FALHA_PROCESSO)
        if not isinstance(resultado, ResultadoIsolado):  # pragma: no cover - defesa
            return ResultadoIsolado(StatusIsolado.FALHA_PROCESSO)
        return resultado
    finally:
        if processo.is_alive():
            processo.kill()
        processo.join(timeout=10)
        entrada.close()


async def executar_isolado(
    funcao: Callable[..., Any],
    argumentos: tuple[Any, ...] = (),
    *,
    tempo_limite_s: float,
    memoria_max_mb: int,
    semaforo: asyncio.Semaphore | None = None,
) -> ResultadoIsolado:
    """Executa `funcao(*argumentos)` num subprocesso com tempo e memória limitados.

    `funcao` precisa ser uma função de módulo (importável pelo filho) e os argumentos e o valor
    devolvido, serializáveis. Estouro de tempo ou de memória vira resultado tipado e nunca
    afeta o processo pai. O `semaforo`, quando dado, limita as execuções simultâneas.
    """
    if semaforo is None:
        return await asyncio.to_thread(
            _executar_bloqueando, funcao, argumentos, tempo_limite_s, memoria_max_mb
        )
    async with semaforo:
        return await asyncio.to_thread(
            _executar_bloqueando, funcao, argumentos, tempo_limite_s, memoria_max_mb
        )
