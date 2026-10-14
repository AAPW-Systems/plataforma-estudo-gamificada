"""DTOs de transporte das matérias: camelCase no JSON, `extra="forbid"` na entrada.

O limite de tamanho do nome entra no OpenAPI (`json_schema_extra`), mas quem o impõe é o
domínio, sobre o texto já normalizado (um nome com espaços nas pontas pode caber em 60).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.materias.dominio import NOME_MAXIMO
from app.nucleo.dtos import EntradaDTO, ModeloDTO


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
