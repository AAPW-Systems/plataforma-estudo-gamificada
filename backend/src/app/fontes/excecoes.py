"""Exceções do domínio `fontes`, convertidas no corpo `Erro` pelos handlers centrais."""

from __future__ import annotations

from app.fontes import dominio
from app.nucleo.codigos import CodigoErro
from app.nucleo.erros import Conflito, ConteudoMuitoGrande, EntradaInvalida, ErroCampo


class ArquivoRecusado(EntradaInvalida):
    """422 do envio com explicação específica (DTEC 028), junto do campo `arquivo`."""

    def __init__(self, codigo: CodigoErro, mensagem: str) -> None:
        super().__init__(mensagem, codigo=codigo, campos=[ErroCampo("arquivo", mensagem)])


class ArquivoMuitoGrande(ConteudoMuitoGrande):
    """413 do envio: acima do tamanho máximo (a mensagem cita o limite em vigor)."""

    def __init__(self, limite_bytes: int) -> None:
        super().__init__(dominio.mensagem_arquivo_grande(limite_bytes))


class FonteDuplicada(Conflito):
    """409: o mesmo conteúdo já está na matéria (D-004); a mensagem cita o título existente."""

    codigo_padrao = CodigoErro.FONTE_DUPLICADA

    def __init__(self, titulo_existente: str | None = None) -> None:
        mensagem = (
            dominio.mensagem_duplicada(titulo_existente)
            if titulo_existente
            else "Esta fonte já está nesta matéria."
        )
        super().__init__(mensagem)


class CotaFontesExcedida(Conflito):
    codigo_padrao = CodigoErro.COTA_FONTES_EXCEDIDA

    def __init__(self, limite: int) -> None:
        super().__init__(
            f"Você atingiu o limite de {limite} fontes nesta matéria. "
            "Exclua uma fonte para enviar outra."
        )


class CotaArmazenamentoExcedida(Conflito):
    codigo_padrao = CodigoErro.COTA_ARMAZENAMENTO_EXCEDIDA

    def __init__(self, limite_bytes: int) -> None:
        megabytes = dominio.formatar_megabytes(limite_bytes)
        super().__init__(
            f"Você atingiu o limite de armazenamento de {megabytes} MB. "
            "Exclua uma fonte para enviar outra."
        )


class ReprocessamentoIndisponivel(Conflito):
    """409: só uma fonte com falha técnica pode ser processada de novo (RF-007)."""

    codigo_padrao = CodigoErro.REPROCESSAMENTO_INDISPONIVEL
    mensagem_padrao = "Esta fonte não pode ser processada de novo."


class TituloInvalido(EntradaInvalida):
    """422 com a regra de título violada junto do campo `titulo`."""

    def __init__(self, mensagem: str) -> None:
        super().__init__(campos=[ErroCampo("titulo", mensagem)])
