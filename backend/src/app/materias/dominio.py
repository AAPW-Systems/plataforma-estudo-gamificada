"""Regras puras das matérias (RF-001, RF-011): sem banco e sem HTTP (DTEC 018)."""

from __future__ import annotations

from app.nucleo.texto import (
    ValorInvalido,
    normalizar,
    tem_caractere_proibido,
    tem_caractere_visivel,
)

NOME_MAXIMO = 60  # o mesmo valor está no esquema do contrato e no CHECK do banco


def normalizar_nome(valor: str) -> str:
    return normalizar(valor)


def validar_nome(valor: str) -> str:
    """Nome de 1 a 60 caracteres, em NFC, sem espaços nas extremidades nem caracteres proibidos."""
    nome = normalizar_nome(valor)
    if not nome or not tem_caractere_visivel(nome):
        raise ValorInvalido("Informe o nome.")
    if len(nome) > NOME_MAXIMO:
        raise ValorInvalido(f"Use no máximo {NOME_MAXIMO} caracteres.")
    if tem_caractere_proibido(nome):
        raise ValorInvalido("O nome tem caracteres que não podem ser usados.")
    return nome


def confirmacao_confere(digitado: str, nome: str) -> bool:
    """A exclusão da matéria pede o nome digitado (RF-011).

    Compara depois de NFC e sem espaços nas extremidades, **diferenciando** maiúsculas e
    minúsculas, por ser a confirmação de uma ação destrutiva (DTEC 031).
    """
    digitado_normalizado = normalizar(digitado)
    return bool(digitado_normalizado) and digitado_normalizado == normalizar(nome)
