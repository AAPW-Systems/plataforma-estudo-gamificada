"""Padrões e limites do domínio `identidade` (D-001; QA-23 e QA-24).

Fonte única: o banco repete os limites como `CHECK` (migração `0002`), os DTOs os usam nos
esquemas e o OpenAPI os expõe ao frontend (`limites.gerado.ts`). Mudar um valor aqui exige
uma migração que acompanhe o `CHECK`.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class LimiteInteiro:
    padrao: int
    minimo: int
    maximo: int

    def contem(self, valor: int) -> bool:
        return self.minimo <= valor <= self.maximo


@dataclass(frozen=True, slots=True)
class LimiteDecimal:
    padrao: Decimal
    minimo: Decimal
    maximo: Decimal
    casas: int

    def contem(self, valor: Decimal) -> bool:
        return self.minimo <= valor <= self.maximo


NOME_MINIMO = 1
NOME_MAXIMO = 100
EMAIL_MAXIMO = 254
SENHA_MINIMA = 8
SENHA_MAXIMA = 128
FUSO_MAXIMO = 64
FUSO_PADRAO = "America/Sao_Paulo"

META_DIARIA = LimiteInteiro(padrao=20, minimo=1, maximo=200)
TAMANHO_LICAO = LimiteInteiro(padrao=10, minimo=5, maximo=50)
LIMITE_NOVOS_DIA = LimiteInteiro(padrao=20, minimo=0, maximo=100)
RETENCAO_DESEJADA = LimiteDecimal(
    padrao=Decimal("0.90"), minimo=Decimal("0.70"), maximo=Decimal("0.97"), casas=2
)
