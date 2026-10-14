"""Exceções do domínio `materias`, convertidas no corpo `Erro` pelos handlers centrais."""

from __future__ import annotations

from app.nucleo.codigos import CodigoErro
from app.nucleo.erros import Conflito, EntradaInvalida, ErroCampo

MENSAGEM_NOME_EM_USO = "Você já tem uma matéria com esse nome."
MENSAGEM_CONFIRMACAO = "O nome digitado não confere com o nome da matéria."
MENSAGEM_DIGITE_O_NOME = "Digite o nome exatamente como aparece."


class NomeInvalido(EntradaInvalida):
    """422 com a regra de nome violada junto do campo `nome`."""

    def __init__(self, mensagem: str) -> None:
        super().__init__(campos=[ErroCampo("nome", mensagem)])


class MateriaNomeEmUso(Conflito):
    """409: o estudante já tem uma matéria com esse nome, sem diferenciar maiúsculas (RF-001)."""

    codigo_padrao = CodigoErro.MATERIA_NOME_EM_USO
    mensagem_padrao = MENSAGEM_NOME_EM_USO

    def __init__(self) -> None:
        super().__init__(campos=[ErroCampo("nome", MENSAGEM_NOME_EM_USO)])


class CotaMateriasExcedida(Conflito):
    """409: o estudante chegou ao limite de matérias (D-003, RF-012)."""

    codigo_padrao = CodigoErro.COTA_MATERIAS_EXCEDIDA

    def __init__(self, limite: int) -> None:
        super().__init__(
            f"Você atingiu o limite de {limite} matérias. Exclua uma matéria para criar outra."
        )
