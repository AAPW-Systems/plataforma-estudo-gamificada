"""T008 (spec 004, DTEC 040): orçamento diário de tokens por estudante, no dia de estudo."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.ia.orcamento import inicio_do_orcamento, restante, tokens_da_chamada, volta_em

pytestmark = pytest.mark.unit


def test_o_orcamento_comeca_na_ultima_virada_das_4h_no_fuso() -> None:
    # 03:30 em Recife ainda é o dia anterior: o orçamento vale desde as 04:00 de ontem
    assert inicio_do_orcamento(datetime(2026, 10, 20, 6, 30, tzinfo=UTC), "America/Recife") == (
        datetime(2026, 10, 19, 7, tzinfo=UTC)
    )
    assert inicio_do_orcamento(datetime(2026, 10, 20, 7, 0, tzinfo=UTC), "America/Recife") == (
        datetime(2026, 10, 20, 7, tzinfo=UTC)
    )


def test_o_orcamento_volta_na_proxima_virada() -> None:
    assert volta_em(datetime(2026, 10, 20, 12, tzinfo=UTC), "America/Recife") == datetime(
        2026, 10, 21, 7, tzinfo=UTC
    )


def test_horario_de_verao_no_inicio_do_orcamento() -> None:
    instante = datetime(2018, 11, 4, 12, tzinfo=UTC)
    assert inicio_do_orcamento(instante, "America/Sao_Paulo") == datetime(
        2018, 11, 4, 6, tzinfo=UTC
    )


@pytest.mark.parametrize(
    "entrada,saida,total",
    [(100, 20, 120), (None, 20, 20), (100, None, 100), (None, None, 0), (0, 0, 0)],
)
def test_tokens_nulos_nao_contam(entrada: int | None, saida: int | None, total: int) -> None:
    """O provedor nem sempre informa os tokens (falhas): o nulo soma zero."""
    assert tokens_da_chamada(entrada, saida) == total


@pytest.mark.parametrize(
    "orcamento,consumido,esperado",
    [(1000, 0, 1000), (1000, 999, 1), (1000, 1000, 0), (1000, 5000, 0)],
)
def test_restante_nunca_e_negativo(orcamento: int, consumido: int, esperado: int) -> None:
    assert restante(orcamento, consumido) == esperado
