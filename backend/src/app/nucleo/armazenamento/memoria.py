"""Adaptador em memória, para testes (DTEC 010)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from app.nucleo.armazenamento.interface import (
    ObjetoArmazenado,
    ObjetoInexistente,
    validar_chave,
    validar_prefixo,
)


class ArmazenamentoMemoria:
    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}
        self.criacoes: dict[str, datetime] = {}

    def colocar(self, chave: str, dados: bytes, criado_em: datetime | None = None) -> None:
        """Auxiliar de teste: grava um objeto, opcionalmente com data de criação antiga."""
        validar_chave(chave)
        self.objetos[chave] = dados
        self.criacoes[chave] = criado_em or datetime.now(UTC)

    async def gravar(self, chave: str, origem: Path) -> None:
        validar_chave(chave)
        dados = await asyncio.to_thread(origem.read_bytes)
        self.colocar(chave, dados)

    async def ler_para_arquivo(self, chave: str, destino: Path) -> None:
        validar_chave(chave)
        if chave not in self.objetos:
            raise ObjetoInexistente(chave)
        await asyncio.to_thread(destino.write_bytes, self.objetos[chave])

    async def apagar(self, chave: str) -> bool:
        validar_chave(chave)
        self.criacoes.pop(chave, None)
        return self.objetos.pop(chave, None) is not None

    async def existe(self, chave: str) -> bool:
        return validar_chave(chave) in self.objetos

    async def apagar_prefixo(self, prefixo: str) -> int:
        validar_prefixo(prefixo)
        chaves = [chave for chave in self.objetos if chave.startswith(prefixo)]
        for chave in chaves:
            del self.objetos[chave]
            self.criacoes.pop(chave, None)
        return len(chaves)

    async def listar_prefixo(self, prefixo: str) -> list[ObjetoArmazenado]:
        validar_prefixo(prefixo)
        return [
            ObjetoArmazenado(chave, self.criacoes[chave])
            for chave in sorted(self.objetos)
            if chave.startswith(prefixo)
        ]
