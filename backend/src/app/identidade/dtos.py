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


class PerfilAlteracaoDTO(EntradaDTO):
    """Alteração parcial: só os campos enviados mudam (`model_fields_set`); ao menos um.

    O domínio impõe os limites (tudo ou nada, todos os erros de uma vez); aqui só se garante
    o tipo: inteiros de verdade (sem `"5"`, `5.5` nem `true`) e número JSON finito para a retenção
    (sem `"0.9"`).
    """

    nome: str | None = Field(
        default=None,
        json_schema_extra={
            "minLength": preferencias.NOME_MINIMO,
            "maxLength": preferencias.NOME_MAXIMO,
        },
    )
    fuso: str | None = Field(
        default=None, json_schema_extra={"maxLength": preferencias.FUSO_MAXIMO}
    )
    meta_diaria: int | None = Field(
        default=None,
        strict=True,
        json_schema_extra={
            "minimum": preferencias.META_DIARIA.minimo,
            "maximum": preferencias.META_DIARIA.maximo,
        },
    )
    tamanho_licao: int | None = Field(
        default=None,
        strict=True,
        json_schema_extra={
            "minimum": preferencias.TAMANHO_LICAO.minimo,
            "maximum": preferencias.TAMANHO_LICAO.maximo,
        },
    )
    limite_novos_dia: int | None = Field(
        default=None,
        strict=True,
        json_schema_extra={
            "minimum": preferencias.LIMITE_NOVOS_DIA.minimo,
            "maximum": preferencias.LIMITE_NOVOS_DIA.maximo,
        },
    )
    retencao_desejada: float | None = Field(
        default=None,
        strict=True,
        allow_inf_nan=False,
        json_schema_extra={
            "minimum": float(preferencias.RETENCAO_DESEJADA.minimo),
            "maximum": float(preferencias.RETENCAO_DESEJADA.maximo),
            "multipleOf": 0.01,
        },
    )
