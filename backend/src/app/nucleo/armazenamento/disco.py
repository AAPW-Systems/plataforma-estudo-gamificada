"""Adaptador de disco local (MVP, DTEC 010).

As chaves já chegam validadas; ainda assim, todo caminho é resolvido e conferido contra a
raiz, para que nenhuma chave (nem um link simbólico) escape do diretório configurado.
"""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from app.nucleo.armazenamento.interface import ChaveInvalida, validar_chave, validar_prefixo


class ArmazenamentoDisco:
    def __init__(self, raiz: Path) -> None:
        self.raiz = raiz.resolve()

    def _caminho(self, relativo: str) -> Path:
        caminho = (self.raiz / relativo).resolve()
        if caminho != self.raiz and self.raiz not in caminho.parents:
            raise ChaveInvalida("chave de armazenamento inválida")
        return caminho

    def caminho_objeto(self, chave: str) -> Path:
        return self._caminho(validar_chave(chave))

    async def existe(self, chave: str) -> bool:
        caminho = self.caminho_objeto(chave)
        return await asyncio.to_thread(caminho.is_file)

    async def apagar_prefixo(self, prefixo: str) -> int:
        diretorio = self._caminho(validar_prefixo(prefixo).rstrip("/"))
        return await asyncio.to_thread(self._apagar_diretorio, diretorio)

    def _apagar_diretorio(self, diretorio: Path) -> int:
        if not diretorio.exists():
            return 0
        if diretorio.is_symlink() or not diretorio.is_dir():
            raise ChaveInvalida("prefixo não aponta para um diretório")
        quantidade = sum(1 for item in diretorio.rglob("*") if item.is_file())
        shutil.rmtree(diretorio)
        return quantidade
