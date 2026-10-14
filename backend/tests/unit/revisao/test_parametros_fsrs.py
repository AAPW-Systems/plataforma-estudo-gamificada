"""Regra de nova versão dos parâmetros do FSRS (T046; RF-010, RN-26, CB-29)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.revisao import dominio

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "atual,nova", [("0.90", "0.85"), ("0.90", "0.97"), ("0.70", "0.71"), ("0.90", "0.91")]
)
def test_valor_diferente_cria_nova_versao(atual: str, nova: str) -> None:
    assert dominio.precisa_nova_versao(Decimal(atual), Decimal(nova))


@pytest.mark.parametrize(
    "atual,nova", [("0.90", "0.90"), ("0.90", "0.9"), ("0.90", "0.900"), ("0.7", "0.70")]
)
def test_o_mesmo_valor_nao_cria_versao_qualquer_que_seja_a_escrita(atual: str, nova: str) -> None:
    assert not dominio.precisa_nova_versao(Decimal(atual), Decimal(nova))


def test_proxima_versao_nao_tem_lacuna() -> None:
    assert dominio.proxima_versao(1) == 2
    assert dominio.proxima_versao(41) == 42
    with pytest.raises(ValueError):
        dominio.proxima_versao(0)
