"""DTOs de transporte da identidade (T036): camelCase no JSON, `extra="forbid"` na entrada.

Os limites de tamanho entram no esquema OpenAPI (`json_schema_extra`) para o frontend os
ler (`limites.gerado.ts`), mas quem os impõe é o domínio, que valida o texto já
normalizado e informa todos os campos inválidos de uma vez (cenário 2 da US1).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.identidade import preferencias
from app.nucleo.dtos import EntradaDTO, ModeloDTO


class CadastroEntradaDTO(EntradaDTO):
    nome: str = Field(
        json_schema_extra={
            "minLength": preferencias.NOME_MINIMO,
            "maxLength": preferencias.NOME_MAXIMO,
        }
    )
    email: str = Field(
        json_schema_extra={"format": "email", "maxLength": preferencias.EMAIL_MAXIMO}
    )
    senha: str = Field(
        repr=False,
        json_schema_extra={
            "minLength": preferencias.SENHA_MINIMA,
            "maxLength": preferencias.SENHA_MAXIMA,
            "writeOnly": True,
        },
    )
    fuso: str | None = Field(
        default=None, json_schema_extra={"maxLength": preferencias.FUSO_MAXIMO}
    )


class EntradaEntradaDTO(EntradaDTO):
    email: str = Field(json_schema_extra={"maxLength": preferencias.EMAIL_MAXIMO})
    senha: str = Field(
        repr=False,
        json_schema_extra={
            "minLength": 1,
            "maxLength": preferencias.SENHA_MAXIMA,
            "writeOnly": True,
        },
    )


class PerfilDTO(ModeloDTO):
    nome: str
    email: str = Field(json_schema_extra={"format": "email"})
    papel: Literal["estudante", "admin"]
    fuso: str
    meta_diaria: int
    tamanho_licao: int
    limite_novos_dia: int
    retencao_desejada: float
    criado_em: datetime
