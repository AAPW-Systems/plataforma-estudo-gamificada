"""Orçamento diário de tokens por estudante, no dia de estudo (DTEC 040 e 048)."""

from __future__ import annotations

from datetime import datetime

from app.nucleo.dia_estudo import dia_estudo, inicio_dia, proxima_virada


def inicio_do_orcamento(agora: datetime, fuso: str) -> datetime:
    """A última virada das 4h no fuso do estudante: o consumo conta a partir dela."""
    return inicio_dia(dia_estudo(agora, fuso), fuso)


def volta_em(agora: datetime, fuso: str) -> datetime:
    """Quando o orçamento volta (o `Retry-After` do `429 orcamento_ia_esgotado`)."""
    return proxima_virada(agora, fuso)


def tokens_da_chamada(entrada: int | None, saida: int | None) -> int:
    """Os tokens de uma chamada; o que o provedor não informou não conta."""
    return (entrada or 0) + (saida or 0)


def restante(orcamento: int, consumido: int) -> int:
    return max(orcamento - consumido, 0)
