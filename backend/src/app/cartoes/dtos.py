"""DTOs de transporte dos cartões: camelCase no JSON, `extra="forbid"` na entrada.

Os `max_length` da entrada são só os tetos absolutos (DTEC 036): quem impõe os limites vigentes,
menores e configuráveis por ambiente, é o domínio, sobre o texto já normalizado.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from app.cartoes.dominio import BUSCA_MAXIMA, OrigemCartao, SituacaoCartao
from app.nucleo.configuracao import CARTAO_EXPLICACAO_TETO, CARTAO_FRENTE_TETO, CARTAO_VERSO_TETO
from app.nucleo.dtos import EntradaDTO, ModeloDTO
from app.nucleo.erros import EntradaInvalida


class CriacaoCartaoEntradaDTO(EntradaDTO):
    frente: str = Field(
        max_length=CARTAO_FRENTE_TETO,
        description="1 a `frenteMax` caracteres depois da normalização; o teto absoluto é 4.000",
    )
    verso: str = Field(
        max_length=CARTAO_VERSO_TETO,
        description="1 a `versoMax` caracteres depois da normalização; o teto absoluto é 8.000",
    )
    explicacao: str | None = Field(
        default=None,
        max_length=CARTAO_EXPLICACAO_TETO,
        description="Opcional; até `explicacaoMax` caracteres; vazia equivale a ausente",
    )
    fonte_id: UUID | None = Field(
        default=None,
        description="Fonte da mesma matéria, em qualquer estado, citada como referência (RF-002)",
    )


class EdicaoCartaoEntradaDTO(EntradaDTO):
    """Campos ausentes não mudam; `explicacao` nula ou vazia remove a explicação (US2)."""

    model_config = ConfigDict(json_schema_extra={"minProperties": 1})

    frente: str = Field(default=None, max_length=CARTAO_FRENTE_TETO)  # type: ignore[assignment]
    verso: str = Field(default=None, max_length=CARTAO_VERSO_TETO)  # type: ignore[assignment]
    explicacao: str | None = Field(
        default=None,
        max_length=CARTAO_EXPLICACAO_TETO,
        description="`null` ou vazia remove a explicação",
    )

    @field_validator("frente", "verso", mode="before")
    @classmethod
    def _nao_nulo(cls, valor: object) -> object:
        # Frente e verso podem faltar, mas não ser nulos: o cartão sempre tem os dois.
        if valor is None:
            raise ValueError("Informe o texto.")
        return valor

    def alteracoes(self) -> dict[str, str | None]:
        """Só os campos enviados, com os nomes do domínio.

        Corpo `{}` é um objeto legível, mas sem nada para editar: `422`, não o `400` que um
        validador de modelo daria (o erro dele não tem campo).
        """
        if not self.model_fields_set:
            raise EntradaInvalida("Informe ao menos um campo para editar.")
        return {campo: getattr(self, campo) for campo in self.model_fields_set}


class ReferenciaFonteDTO(ModeloDTO):
    """Descrição da origem copiada na criação; não muda com a renomeação nem com a exclusão."""

    fonte_id: UUID | None = Field(description="Nulo depois que a fonte foi excluída")
    titulo: str
    nome_arquivo: str
    enviada_em: datetime
    fonte_apagada: bool = Field(description='Exibe "Fonte apagada" junto da descrição (RF-009)')


class CartaoDTO(ModeloDTO):
    id: UUID
    materia_id: UUID
    frente: str = Field(description="Texto puro; quebras de linha como `\\n` (RQ-001)")
    verso: str
    explicacao: str | None
    origem: OrigemCartao
    verificado: bool = Field(
        description="Verdadeiro só com origem `gerado_verificado`; nunca em cartão do estudante"
    )
    situacao: SituacaoCartao
    referencia: ReferenciaFonteDTO | None = Field(
        description="Só em cartões criados pelo estudante que citam uma fonte"
    )
    criado_em: datetime
    atualizado_em: datetime


class ListaCartoesDTO(ModeloDTO):
    itens: list[CartaoDTO]
    proximo_cursor: str | None = Field(description="Nulo na última página (DTEC 034)")
    total: int = Field(ge=0, description="Cartões que atendem aos filtros, em todas as páginas")


class LimitesCartaoDTO(ModeloDTO):
    frente_max: int = Field(ge=1, le=CARTAO_FRENTE_TETO)
    verso_max: int = Field(ge=1, le=CARTAO_VERSO_TETO)
    explicacao_max: int = Field(ge=1, le=CARTAO_EXPLICACAO_TETO)
    # Estático: o teto do termo de busca não varia por ambiente (DTEC 033).
    busca_max: int = Field(ge=BUSCA_MAXIMA, le=BUSCA_MAXIMA)
