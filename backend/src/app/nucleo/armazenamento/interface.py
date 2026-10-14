"""Interface de armazenamento de objetos (DTEC 010 e 021).

A 001 trouxe `apagar_prefixo` (exclusão da conta); a 002 completa a interface com `gravar`,
`ler_para_arquivo`, `apagar` e `listar_prefixo` (DTEC 025). Toda chave começa por
`usuarios/{public_id}/` (DTEC 021) e é validada aqui, antes de chegar a qualquer adaptador,
contra *path traversal*. O conteúdo trafega por arquivos, nunca inteiro em memória.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

_SEGMENTO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ChaveInvalida(ValueError):
    pass


class ObjetoInexistente(LookupError):
    """A chave é válida, mas não há objeto nela (ex.: apagado antes de ser lido)."""


@dataclass(frozen=True, slots=True)
class ObjetoArmazenado:
    chave: str
    criado_em: datetime  # com fuso (UTC)


def _validar_segmentos(valor: str) -> list[str]:
    if not valor or len(valor) > 1024 or valor.startswith("/") or "\\" in valor:
        raise ChaveInvalida("chave de armazenamento inválida")
    segmentos = valor.split("/")
    if any(not _SEGMENTO.fullmatch(s) or s in {".", ".."} for s in segmentos):
        raise ChaveInvalida("chave de armazenamento inválida")
    return segmentos


def validar_chave(chave: str) -> str:
    _validar_segmentos(chave)
    return chave


def validar_prefixo(prefixo: str) -> str:
    """Um prefixo é uma sequência de segmentos válidos terminada em `/`."""
    if not prefixo.endswith("/"):
        raise ChaveInvalida("o prefixo deve terminar em '/'")
    _validar_segmentos(prefixo[:-1])
    return prefixo


def prefixo_usuario(public_id: str) -> str:
    return validar_prefixo(f"usuarios/{public_id}/")


class Armazenamento(Protocol):
    async def gravar(self, chave: str, origem: Path) -> None:
        """Grava o conteúdo do arquivo `origem` em `chave`, de forma atômica.

        Quem lê nunca vê um objeto pela metade; se a gravação falhar, o objeto anterior (se
        houver) continua intacto e nada temporário permanece.
        """
        ...

    async def ler_para_arquivo(self, chave: str, destino: Path) -> None:
        """Copia o objeto para `destino`. `ObjetoInexistente` se a chave não tem objeto."""
        ...

    async def apagar(self, chave: str) -> bool:
        """Apaga o objeto; idempotente. Devolve se havia algo para apagar."""
        ...

    async def apagar_prefixo(self, prefixo: str) -> int:
        """Apaga todos os objetos sob `prefixo`; devolve quantos apagou. Idempotente."""
        ...

    async def listar_prefixo(self, prefixo: str) -> list[ObjetoArmazenado]:
        """Objetos sob `prefixo`, em ordem de chave, com a data de criação (DTEC 025)."""
        ...

    async def existe(self, chave: str) -> bool: ...
