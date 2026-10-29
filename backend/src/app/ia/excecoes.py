"""Falhas de uma chamada ao provedor, já classificadas (DTEC 040 e 043).

O `codigo` é o da falha da operação (`codigo_falha_geracao` na geração). A mensagem é genérica:
nenhum detalhe do provedor chega ao estudante nem ao log (RQ-005).
"""

from __future__ import annotations


class ErroIA(Exception):
    codigo: str = "provedor_indisponivel"

    def __init__(self) -> None:
        super().__init__(self.codigo)


class ProvedorIndisponivel(ErroIA):
    """O provedor recusou ou não atendeu; repetir o mesmo pedido não resolve."""

    codigo = "provedor_indisponivel"


class ErroTransitorioIA(ProvedorIndisponivel):
    """Timeout, conexão, 5xx ou 429 por minuto: a fila tenta de novo (até 2 vezes)."""


class LimiteProvedor(ErroIA):
    """A cota diária do provedor acabou: só volta no dia seguinte do provedor."""

    codigo = "limite_provedor"


class RespostaInvalida(ErroIA):
    """A saída não validou contra o esquema, mesmo depois do pedido de correção."""

    codigo = "resposta_invalida"


class OrcamentoEsgotado(ErroIA):
    """O orçamento de tokens do estudante no dia de estudo acabou."""

    codigo = "orcamento_esgotado"
