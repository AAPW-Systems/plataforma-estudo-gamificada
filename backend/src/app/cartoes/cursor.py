"""Cursor opaco da listagem por *keyset* (DTEC 034): posição, autenticação e filtros.

O cursor guarda a chave de ordenação do último item da página (`criado_em` e `id`) e vale só para
a mesma conta, matéria e filtros que o geraram. A posição vai mascarada e autenticada com o
segredo da aplicação: o `id` interno não sai da API (só `public_id` sai), e cursor adulterado,
inventado ou de outra lista responde `422 cursor_invalido`, sem revelar nada.
"""

from __future__ import annotations

import base64
import hmac
import json
import struct
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

_EPOCA = datetime(1970, 1, 1, tzinfo=UTC)
_MICROSSEGUNDO = timedelta(microseconds=1)
_MAXIMO_MICROS = (datetime.max.replace(tzinfo=UTC) - _EPOCA) // _MICROSSEGUNDO
_VERSAO = b"cartoes.cursor.v1"
_TAMANHO_POSICAO = 16
_TAMANHO_SELO = 16
_TAMANHO_TEXTO = 43  # 32 bytes em base64url, sem preenchimento


class CursorInvalido(Exception):  # noqa: N818
    """O cursor está malformado, foi adulterado ou pertence a outra lista."""


@dataclass(frozen=True, slots=True)
class PosicaoCursor:
    """Chave de ordenação do último item visto: a próxima página começa antes dela."""

    criado_em: datetime
    id: int


def resumo_dos_filtros(
    usuario_id: int,
    materia_public_id: UUID,
    *,
    busca: str | None = None,
    situacao: str | None = None,
    origem: str | None = None,
) -> str:
    """Identifica a lista do cursor: conta, matéria e cada filtro, sem ambiguidade entre eles."""
    return json.dumps(
        [usuario_id, str(materia_public_id), busca or None, situacao, origem],
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _chaves(resumo: str, segredo: bytes) -> tuple[bytes, bytes]:
    base = hmac.digest(segredo, _VERSAO + b"|" + resumo.encode(), "sha256")
    mascara = hmac.digest(base, b"mascara", "sha256")[:_TAMANHO_POSICAO]
    chave_do_selo = hmac.digest(base, b"selo", "sha256")
    return mascara, chave_do_selo


def _aplicar(mascara: bytes, dados: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(dados, mascara, strict=True))


def codificar(posicao: PosicaoCursor, *, resumo: str, segredo: bytes) -> str:
    """O cursor da posição, em base64url sem preenchimento (43 caracteres)."""
    if posicao.criado_em.tzinfo is None or posicao.id < 1:
        raise ValueError("posição do cursor inválida")
    micros = (posicao.criado_em - _EPOCA) // _MICROSSEGUNDO
    if not 0 <= micros <= _MAXIMO_MICROS:
        raise ValueError("posição do cursor fora do intervalo")
    mascara, chave_do_selo = _chaves(resumo, segredo)
    cifrado = _aplicar(mascara, struct.pack(">qq", micros, posicao.id))
    selo = hmac.digest(chave_do_selo, cifrado, "sha256")[:_TAMANHO_SELO]
    return base64.urlsafe_b64encode(cifrado + selo).rstrip(b"=").decode("ascii")


def decodificar(cursor: str, *, resumo: str, segredo: bytes) -> PosicaoCursor:
    """A posição do cursor, ou `CursorInvalido` para qualquer coisa que não o seja."""
    if len(cursor) != _TAMANHO_TEXTO or not cursor.isascii():
        raise CursorInvalido
    try:
        bruto = base64.urlsafe_b64decode(cursor + "=")
    except ValueError:
        raise CursorInvalido from None
    # Só a forma canônica vale: caracteres fora do alfabeto e bits sobrando são descartados na
    # decodificação, e dois textos diferentes não podem levar à mesma posição.
    if base64.urlsafe_b64encode(bruto).rstrip(b"=").decode("ascii") != cursor:
        raise CursorInvalido
    cifrado, selo = bruto[:_TAMANHO_POSICAO], bruto[_TAMANHO_POSICAO:]
    mascara, chave_do_selo = _chaves(resumo, segredo)
    esperado = hmac.digest(chave_do_selo, cifrado, "sha256")[:_TAMANHO_SELO]
    if not hmac.compare_digest(selo, esperado):
        raise CursorInvalido
    micros, identificador = struct.unpack(">qq", _aplicar(mascara, cifrado))
    if not 0 <= micros <= _MAXIMO_MICROS or identificador < 1:
        raise CursorInvalido
    return PosicaoCursor(_EPOCA + micros * _MICROSSEGUNDO, identificador)
