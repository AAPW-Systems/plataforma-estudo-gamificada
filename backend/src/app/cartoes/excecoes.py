"""Exceções do domínio `cartoes`, convertidas no corpo `Erro` pelos handlers centrais."""

from __future__ import annotations

from collections.abc import Mapping

from app.nucleo.codigos import CodigoErro
from app.nucleo.erros import EntradaInvalida, ErroCampo

MENSAGEM_FONTE_INVALIDA = "Escolha uma fonte desta matéria."
MENSAGEM_CURSOR_INVALIDO = "O cursor não vale para esta lista. Recarregue a lista."


class TextoCartaoInvalido(EntradaInvalida):
    """422 com uma mensagem por campo de texto fora das regras (RF-001)."""

    def __init__(self, campos: Mapping[str, str]) -> None:
        super().__init__(campos=[ErroCampo(campo, mensagem) for campo, mensagem in campos.items()])


class FonteDeReferenciaInvalida(EntradaInvalida):
    """422 no campo `fonteId`: a mesma resposta para fonte inexistente, de outra matéria ou de outro
    estudante, para a API nunca confirmar que a fonte de outro existe (DTEC 019 e 035)."""

    def __init__(self) -> None:
        super().__init__(campos=[ErroCampo("fonteId", MENSAGEM_FONTE_INVALIDA)])


class CursorDeListaInvalido(EntradaInvalida):
    """422 `cursor_invalido`: cursor malformado, adulterado ou de outra lista (DTEC 034)."""

    codigo_padrao = CodigoErro.CURSOR_INVALIDO
    mensagem_padrao = MENSAGEM_CURSOR_INVALIDO
