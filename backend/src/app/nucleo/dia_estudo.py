"""Dia de estudo: vira às 4h no fuso do estudante (RN-15), calculado só aqui (DTEC 048).

Funções puras sobre `zoneinfo`. O SQL recebe só os limites já calculados (`inicio_dia` e
`proxima_virada`, em UTC) como parâmetros.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

HORA_DA_VIRADA = time(4)


def _exigir_fuso(instante: datetime) -> None:
    if instante.tzinfo is None or instante.utcoffset() is None:
        raise ValueError("o instante precisa de fuso (UTC)")


def dia_estudo(instante: datetime, fuso: str) -> date:
    """A data local de `instante − 4h` no fuso do estudante."""
    _exigir_fuso(instante)
    local = instante.astimezone(ZoneInfo(fuso)).replace(tzinfo=None)
    return (local - timedelta(hours=HORA_DA_VIRADA.hour)).date()


def inicio_dia(dia: date, fuso: str) -> datetime:
    """O instante UTC das 4h locais de `dia`.

    Numa hora repetida, vale a primeira ocorrência (`fold=0`). Numa hora inexistente (o relógio
    pulou as 4h), vale o primeiro instante válido depois dela: o da mudança de horário.
    """
    zona = ZoneInfo(fuso)
    parede = datetime.combine(dia, HORA_DA_VIRADA)
    candidato = parede.replace(tzinfo=zona).astimezone(UTC)
    if candidato.astimezone(zona).replace(tzinfo=None) == parede:
        return candidato
    # Hora inexistente: o instante procurado é o primeiro cuja hora local já passou das 4h. Ele
    # fica entre as duas leituras possíveis da hora (antes e depois da mudança).
    antes = parede.replace(tzinfo=zona, fold=1).astimezone(UTC)
    depois = parede.replace(tzinfo=zona, fold=0).astimezone(UTC)
    baixo, alto = min(antes, depois), max(antes, depois)
    while alto - baixo > timedelta(microseconds=1):
        meio = baixo + (alto - baixo) / 2
        if meio.astimezone(zona).replace(tzinfo=None) >= parede:
            alto = meio
        else:
            baixo = meio
    return alto


def proxima_virada(instante: datetime, fuso: str) -> datetime:
    """O instante UTC em que começa o próximo dia de estudo."""
    return inicio_dia(dia_estudo(instante, fuso) + timedelta(days=1), fuso)
