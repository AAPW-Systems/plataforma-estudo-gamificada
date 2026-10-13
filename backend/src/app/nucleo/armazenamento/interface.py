"""Interface de armazenamento de objetos (DTEC 010 e 021).

Na 001 a interface só tem o que a exclusão da conta precisa (`apagar_prefixo`); gravar e
ler chegam com a spec 002. Toda chave começa por `usuarios/{public_id}/` (DTEC 021) e é
validada aqui, antes de chegar a qualquer adaptador, contra *path traversal*.
"""

from __future__ import annotations

import re
from typing import Protocol

_SEGMENTO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ChaveInvalida(ValueError):
    pass


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
    async def apagar_prefixo(self, prefixo: str) -> int:
        """Apaga todos os objetos sob `prefixo`; devolve quantos apagou. Idempotente."""
        ...

    async def existe(self, chave: str) -> bool: ...
