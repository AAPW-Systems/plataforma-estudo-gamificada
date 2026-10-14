"""Regras puras dos parâmetros do FSRS (RF-010, RN-26, CB-29)."""

from __future__ import annotations

from decimal import Decimal


def precisa_nova_versao(retencao_vigente: Decimal, retencao_nova: Decimal) -> bool:
    """Só uma retenção de valor diferente cria versão: salvar o mesmo valor não cria."""
    return retencao_nova != retencao_vigente


def proxima_versao(versao_vigente: int) -> int:
    """Versões são sequenciais e sem lacuna, começando em 1."""
    if versao_vigente < 1:
        raise ValueError("a versão vigente começa em 1")
    return versao_vigente + 1
