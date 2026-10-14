"""Adaptador de disco local (MVP, DTEC 010 e 025).

As chaves já chegam validadas; ainda assim, todo caminho é resolvido e conferido contra a
raiz, para que nenhuma chave (nem um link simbólico) escape do diretório configurado.
A gravação é atômica: copia para um temporário no mesmo diretório e troca com `os.replace`.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.nucleo.armazenamento.interface import (
    ChaveInvalida,
    ObjetoArmazenado,
    ObjetoInexistente,
    validar_chave,
    validar_prefixo,
)

_PREFIXO_TEMPORARIO = ".tmp-"
_PERMISSAO_ARQUIVO = 0o600
_PERMISSAO_DIRETORIO = 0o700


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

    async def gravar(self, chave: str, origem: Path) -> None:
        caminho = self.caminho_objeto(chave)
        await asyncio.to_thread(self._gravar, caminho, origem)

    def _gravar(self, caminho: Path, origem: Path) -> None:
        # Cada diretório é conferido contra a raiz depois de criado (links simbólicos).
        caminho.parent.mkdir(parents=True, exist_ok=True, mode=_PERMISSAO_DIRETORIO)
        if caminho.parent.resolve() != caminho.parent or self.raiz not in caminho.parents:
            raise ChaveInvalida("chave de armazenamento inválida")
        temporario = caminho.parent / f"{_PREFIXO_TEMPORARIO}{uuid.uuid4().hex}"
        try:
            descritor = os.open(
                temporario, os.O_WRONLY | os.O_CREAT | os.O_EXCL, _PERMISSAO_ARQUIVO
            )
            with os.fdopen(descritor, "wb") as saida, origem.open("rb") as entrada:
                shutil.copyfileobj(entrada, saida)
                saida.flush()
                os.fsync(saida.fileno())
            os.replace(temporario, caminho)
        except BaseException:
            with contextlib.suppress(FileNotFoundError):
                temporario.unlink()
            raise

    async def ler_para_arquivo(self, chave: str, destino: Path) -> None:
        caminho = self.caminho_objeto(chave)
        await asyncio.to_thread(self._ler, caminho, chave, destino)

    @staticmethod
    def _ler(caminho: Path, chave: str, destino: Path) -> None:
        if not caminho.is_file():
            raise ObjetoInexistente(chave)
        try:
            shutil.copyfile(caminho, destino)
        except FileNotFoundError as erro:  # apagado entre a conferência e a cópia
            destino.unlink(missing_ok=True)
            raise ObjetoInexistente(chave) from erro

    async def apagar(self, chave: str) -> bool:
        caminho = self.caminho_objeto(chave)
        return await asyncio.to_thread(self._apagar, caminho)

    @staticmethod
    def _apagar(caminho: Path) -> bool:
        try:
            caminho.unlink()
        except FileNotFoundError:
            return False
        return True

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

    async def listar_prefixo(self, prefixo: str) -> list[ObjetoArmazenado]:
        diretorio = self._caminho(validar_prefixo(prefixo).rstrip("/"))
        return await asyncio.to_thread(self._listar, diretorio)

    def _listar(self, diretorio: Path) -> list[ObjetoArmazenado]:
        if not diretorio.is_dir() or diretorio.is_symlink():
            return []
        itens: list[ObjetoArmazenado] = []
        for caminho in diretorio.rglob("*"):
            if caminho.is_symlink() or not caminho.is_file():
                continue
            if caminho.name.startswith(_PREFIXO_TEMPORARIO):
                continue
            criado_em = datetime.fromtimestamp(caminho.stat().st_mtime, tz=UTC)
            itens.append(ObjetoArmazenado(caminho.relative_to(self.raiz).as_posix(), criado_em))
        return sorted(itens, key=lambda item: item.chave)
