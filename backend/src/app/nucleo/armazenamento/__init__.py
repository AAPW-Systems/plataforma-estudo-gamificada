"""Armazenamento de objetos (DTEC 010): disco no MVP, memória nos testes."""

from __future__ import annotations

from app.nucleo.armazenamento.disco import ArmazenamentoDisco
from app.nucleo.armazenamento.interface import (
    Armazenamento,
    ChaveInvalida,
    prefixo_usuario,
    validar_chave,
    validar_prefixo,
)
from app.nucleo.armazenamento.memoria import ArmazenamentoMemoria
from app.nucleo.configuracao import Configuracao

__all__ = [
    "Armazenamento",
    "ArmazenamentoDisco",
    "ArmazenamentoMemoria",
    "ChaveInvalida",
    "criar_armazenamento",
    "prefixo_usuario",
    "validar_chave",
    "validar_prefixo",
]


def criar_armazenamento(configuracao: Configuracao) -> Armazenamento:
    if configuracao.armazenamento_adaptador == "memoria":
        return ArmazenamentoMemoria()
    return ArmazenamentoDisco(configuracao.armazenamento_diretorio)
