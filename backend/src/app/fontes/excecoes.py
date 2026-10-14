"""Exceções do domínio `fontes`, convertidas no corpo `Erro` pelos handlers centrais."""

from __future__ import annotations

from app.fontes import dominio
from app.nucleo.codigos import CodigoErro
from app.nucleo.erros import ConteudoMuitoGrande, EntradaInvalida, ErroCampo


class ArquivoRecusado(EntradaInvalida):
    """422 do envio com explicação específica (DTEC 028), junto do campo `arquivo`."""

    def __init__(self, codigo: CodigoErro, mensagem: str) -> None:
        super().__init__(mensagem, codigo=codigo, campos=[ErroCampo("arquivo", mensagem)])


class ArquivoMuitoGrande(ConteudoMuitoGrande):
    """413 do envio: acima do tamanho máximo (a mensagem cita o limite em vigor)."""

    def __init__(self, limite_bytes: int) -> None:
        super().__init__(dominio.mensagem_arquivo_grande(limite_bytes))
