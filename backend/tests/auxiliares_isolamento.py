"""Funções executadas no subprocesso dos testes de isolamento (DTEC 024).

Ficam fora do arquivo de teste para que o filho (contexto `spawn`) as importe sem carregar o
pytest. Só stdlib.
"""

from __future__ import annotations

import time


def somar(a: int, b: int) -> int:
    return a + b


def dormir(segundos: float) -> str:
    time.sleep(segundos)
    return "acordou"


def alocar_mb(megabytes: int) -> int:
    bloco = bytearray(megabytes * 1024 * 1024)
    return len(bloco)


def levantar_erro(mensagem: str) -> None:
    raise ValueError(mensagem)


def janela(segundos: float) -> tuple[float, float]:
    """Dorme e devolve o início e o fim, para provar se duas execuções se sobrepuseram."""
    inicio = time.time()
    time.sleep(segundos)
    return inicio, time.time()


def devolver_algo_nao_serializavel() -> object:
    return lambda: None


def morrer_sem_resposta() -> None:
    import os

    os._exit(3)
