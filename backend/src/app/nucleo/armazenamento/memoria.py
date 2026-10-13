"""Adaptador em memória, para testes (DTEC 010)."""

from __future__ import annotations

from app.nucleo.armazenamento.interface import validar_chave, validar_prefixo


class ArmazenamentoMemoria:
    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}

    def colocar(self, chave: str, dados: bytes) -> None:
        """Auxiliar de teste: grava um objeto (a operação `gravar` chega com a 002)."""
        self.objetos[validar_chave(chave)] = dados

    async def existe(self, chave: str) -> bool:
        return validar_chave(chave) in self.objetos

    async def apagar_prefixo(self, prefixo: str) -> int:
        validar_prefixo(prefixo)
        chaves = [chave for chave in self.objetos if chave.startswith(prefixo)]
        for chave in chaves:
            del self.objetos[chave]
        return len(chaves)
