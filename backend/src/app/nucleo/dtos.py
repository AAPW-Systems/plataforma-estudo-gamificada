"""DTOs base: JSON em camelCase, Python em snake_case (DTEC 018)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.nucleo.codigos import CodigoErro


class ModeloDTO(BaseModel):
    """Base de toda resposta: serializa em camelCase."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
        frozen=True,
    )


class EntradaDTO(ModeloDTO):
    """Base de todo corpo de entrada: só camelCase e nenhum campo extra (RF-003)."""

    model_config = ConfigDict(extra="forbid", validate_by_name=False)


class ErroCampoDTO(ModeloDTO):
    model_config = ConfigDict(title="ErroCampo")

    campo: str
    mensagem: str


class ErroDTO(ModeloDTO):
    """Corpo único de erro do contrato (`Erro`)."""

    model_config = ConfigDict(title="Erro")

    codigo: CodigoErro
    mensagem: str
    campos: list[ErroCampoDTO] | None = None
    id_requisicao: UUID
