"""DTOs de transporte das matérias: camelCase no JSON, `extra="forbid"` na entrada.

O limite de tamanho do nome entra no OpenAPI (`json_schema_extra`), mas quem o impõe é o
domínio, sobre o texto já normalizado (um nome com espaços nas pontas pode caber em 60).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.materias.dominio import NOME_MAXIMO
from app.nucleo.dtos import EntradaDTO, ModeloDTO

# Inteiros de verdade e não negativos: "3", 3.0 e true não valem como contagem confirmada.
Contagem = Annotated[int, Field(ge=0, strict=True)]


class MateriaEntradaDTO(EntradaDTO):
    nome: str = Field(json_schema_extra={"minLength": 1, "maxLength": NOME_MAXIMO})


class MateriaDTO(ModeloDTO):
    id: UUID
    nome: str
    total_fontes: int = Field(ge=0)
    cartoes_ativos: int = Field(ge=0)
    cartoes_aguardando_revisao: int = Field(ge=0)
    criado_em: datetime
    atualizado_em: datetime


class ListaMateriasDTO(ModeloDTO):
    itens: list[MateriaDTO]


class ContagensExclusaoMateriaDTO(EntradaDTO):
    """O que a exclusão da matéria apaga; o diálogo mostra e a confirmação devolve (DTEC 031)."""

    fontes: Contagem
    cartoes_ativos: Contagem = Field(
        description="Cartões ativos e suspensos da matéria, que serão apagados"
    )
    cartoes_aguardando_revisao: Contagem


class ImpactoExclusaoMateriaDTO(ModeloDTO):
    nome: str = Field(description="Nome que o estudante deve digitar para confirmar")
    contagens: ContagensExclusaoMateriaDTO


class ExclusaoMateriaEntradaDTO(EntradaDTO):
    """O nome é comparado pelo domínio (NFC, extremidades, caixa), não pelo esquema."""

    nome_confirmacao: str = Field(
        json_schema_extra={"minLength": 1, "maxLength": NOME_MAXIMO},
        description=(
            "Comparado com o nome depois de NFC e sem espaços nas extremidades, "
            "diferenciando maiúsculas e minúsculas"
        ),
    )
    impacto_confirmado: ContagensExclusaoMateriaDTO
