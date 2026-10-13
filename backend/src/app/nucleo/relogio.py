"""Fonte única do instante atual, substituível nos testes (relógio controlável)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol


class Relogio(Protocol):
    def agora(self) -> datetime:
        """Instante atual em UTC, com fuso."""
        ...


class RelogioSistema:
    def agora(self) -> datetime:
        return datetime.now(UTC)


class RelogioControlavel:
    """Relógio parado que só anda quando o teste manda."""

    def __init__(self, inicio: datetime | None = None) -> None:
        self._agora = inicio or datetime(2026, 10, 13, 12, 0, tzinfo=UTC)
        if self._agora.tzinfo is None:
            raise ValueError("o relógio exige instante com fuso")

    def agora(self) -> datetime:
        return self._agora

    def avancar(self, **intervalo: float) -> datetime:
        self._agora += timedelta(**intervalo)
        return self._agora
