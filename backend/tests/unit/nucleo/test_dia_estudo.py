"""DTEC 048: o dia de estudo vira às 4h no fuso do estudante, calculado num único ponto (RN-15).

A 004 cria o módulo (limite de gerações e orçamento da IA); a 005 e a 006 o reutilizam.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.nucleo.dia_estudo import dia_estudo, inicio_dia, proxima_virada

pytestmark = pytest.mark.unit

RECIFE = "America/Recife"
SAO_PAULO = "America/Sao_Paulo"


def _utc(
    ano: int, mes: int, dia: int, hora: int = 0, minuto: int = 0, segundo: int = 0
) -> datetime:
    return datetime(ano, mes, dia, hora, minuto, segundo, tzinfo=UTC)


@pytest.mark.parametrize(
    "instante,esperado",
    [
        (_utc(2026, 10, 20, 6, 59, 59), date(2026, 10, 19)),  # 03:59:59 em Recife
        (_utc(2026, 10, 20, 7, 0, 0), date(2026, 10, 20)),  # 04:00 em Recife
        (_utc(2026, 10, 21, 2, 59, 59), date(2026, 10, 20)),  # 23:59:59
        (_utc(2026, 10, 21, 3, 0, 0), date(2026, 10, 20)),  # meia-noite ainda é o dia anterior
    ],
)
def test_virada_as_4h_no_fuso(instante: datetime, esperado: date) -> None:
    assert dia_estudo(instante, RECIFE) == esperado


def test_o_mesmo_instante_cai_em_dias_diferentes_conforme_o_fuso() -> None:
    instante = _utc(2026, 10, 20, 5, 0)  # 02:00 em Recife; 14:00 em Tóquio
    assert dia_estudo(instante, RECIFE) == date(2026, 10, 19)
    assert dia_estudo(instante, "Asia/Tokyo") == date(2026, 10, 20)


def test_inicio_e_proxima_virada_em_utc() -> None:
    assert inicio_dia(date(2026, 10, 20), RECIFE) == _utc(2026, 10, 20, 7)
    assert proxima_virada(_utc(2026, 10, 20, 12), RECIFE) == _utc(2026, 10, 21, 7)
    assert proxima_virada(_utc(2026, 10, 20, 6, 59), RECIFE) == _utc(2026, 10, 20, 7)


def test_horario_de_verao_que_muda_a_meia_noite() -> None:
    """São Paulo em 2018: o verão começou em 04/11 (00h→01h) e terminou em 17/02/2019 (00h→23h)."""
    assert inicio_dia(date(2018, 11, 3), SAO_PAULO) == _utc(2018, 11, 3, 7)  # UTC-3
    assert inicio_dia(date(2018, 11, 4), SAO_PAULO) == _utc(2018, 11, 4, 6)  # UTC-2
    assert proxima_virada(_utc(2018, 11, 3, 12), SAO_PAULO) == _utc(2018, 11, 4, 6)
    # o dia do fim do verão tem 25 horas, e a virada continua às 4h locais
    assert inicio_dia(date(2019, 2, 16), SAO_PAULO) == _utc(2019, 2, 16, 6)
    assert inicio_dia(date(2019, 2, 17), SAO_PAULO) == _utc(2019, 2, 17, 7)
    assert dia_estudo(_utc(2019, 2, 17, 6, 30), SAO_PAULO) == date(2019, 2, 16)
    # Santiago também muda à meia-noite
    santiago = "America/Santiago"
    assert dia_estudo(inicio_dia(date(2024, 9, 8), santiago), santiago) == date(2024, 9, 8)


def test_hora_das_4h_inexistente_vira_o_primeiro_instante_valido_depois() -> None:
    """Baku, 29/03/2015: das 04:00 pulou para as 05:00 (UTC+4 → UTC+5)."""
    baku = ZoneInfo("Asia/Baku")
    inicio = inicio_dia(date(2015, 3, 29), "Asia/Baku")
    assert inicio == _utc(2015, 3, 29, 0)
    assert inicio.astimezone(baku).hour == 5
    assert dia_estudo(inicio, "Asia/Baku") == date(2015, 3, 29)
    assert dia_estudo(inicio - timedelta(microseconds=1), "Asia/Baku") == date(2015, 3, 28)


def test_hora_das_4h_repetida_usa_a_primeira_ocorrencia() -> None:
    """Baku, 25/10/2015: das 05:00 voltou para as 04:00 (UTC+5 → UTC+4)."""
    inicio = inicio_dia(date(2015, 10, 25), "Asia/Baku")
    assert inicio == _utc(2015, 10, 24, 23)  # 04:00 com UTC+5
    assert dia_estudo(inicio, "Asia/Baku") == date(2015, 10, 25)
    assert dia_estudo(inicio - timedelta(microseconds=1), "Asia/Baku") == date(2015, 10, 24)


FUSOS = st.sampled_from([RECIFE, SAO_PAULO, "America/Santiago", "Asia/Baku", "Asia/Tokyo"])
INSTANTES = st.datetimes(
    min_value=datetime(2010, 1, 1), max_value=datetime(2035, 12, 31), timezones=st.just(UTC)
)


@given(instante=INSTANTES, fuso=FUSOS)
def test_todo_instante_esta_entre_o_inicio_do_seu_dia_e_a_proxima_virada(
    instante: datetime, fuso: str
) -> None:
    dia = dia_estudo(instante, fuso)
    assert inicio_dia(dia, fuso) <= instante < proxima_virada(instante, fuso)
    assert dia_estudo(inicio_dia(dia, fuso), fuso) == dia
    assert dia_estudo(proxima_virada(instante, fuso), fuso) == dia + timedelta(days=1)


def test_instante_sem_fuso_e_recusado() -> None:
    with pytest.raises(ValueError, match="fuso"):
        dia_estudo(datetime(2026, 10, 20, 12), RECIFE)  # noqa: DTZ001


def test_dia_inteiro_pulado_vira_o_primeiro_instante_do_dia_seguinte() -> None:
    """Apia, 30/12/2011 não existiu (UTC−10 → UTC+14 à meia-noite). A leitura ingênua das 4h
    cairia nas 4h do dia 31; o primeiro instante válido depois delas é a meia-noite do dia 31."""
    inicio = inicio_dia(date(2011, 12, 30), "Pacific/Apia")
    assert inicio == _utc(2011, 12, 30, 10)
    assert inicio < inicio_dia(date(2011, 12, 31), "Pacific/Apia") == _utc(2011, 12, 30, 14)
