"""DTOs de transporte das fontes: camelCase no JSON, `extra="forbid"` na entrada."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from app.fontes.dominio import TITULO_MAXIMO, CodigoFalha, EstadoFonte
from app.nucleo.dtos import EntradaDTO, ModeloDTO
from app.nucleo.participantes_acervo import ModoCartoes

# Inteiros de verdade e não negativos: "3", 3.0 e true não valem como contagem confirmada.
Contagem = Annotated[int, Field(ge=0, strict=True)]


class RenomeacaoFonteEntradaDTO(EntradaDTO):
    titulo: str = Field(json_schema_extra={"minLength": 1, "maxLength": TITULO_MAXIMO})


class FonteDTO(ModeloDTO):
    id: UUID
    materia_id: UUID
    titulo: str
    nome_arquivo: str
    tipo_midia: Literal["application/pdf", "text/plain", "text/markdown"]
    tamanho_bytes: int = Field(ge=1)
    estado: EstadoFonte
    codigo_falha: CodigoFalha | None
    mensagem_falha: str | None
    pode_tentar_novamente: bool
    total_paginas: int | None = Field(ge=1)
    total_trechos: int | None = Field(ge=0)
    enviada_em: datetime
    processada_em: datetime | None


class ListaFontesDTO(ModeloDTO):
    itens: list[FonteDTO]


class UsoAcervoDTO(ModeloDTO):
    tamanho_maximo_bytes: int
    extensoes_aceitas: list[str]
    paginas_maximas_pdf: int
    cota_materias: int
    total_materias: int = Field(ge=0)
    cota_fontes_por_materia: int
    cota_armazenamento_bytes: int
    uso_armazenamento_bytes: int = Field(ge=0)


class ContagensExclusaoFonteDTO(EntradaDTO):
    """O que a exclusão da fonte afeta; o diálogo mostra e a confirmação devolve (DTEC 031)."""

    cartoes_gerados_aceitos: Contagem = Field(
        description="Cartões gerados da fonte e já aceitos; seguem a escolha `modoCartoes`"
    )
    cartoes_aguardando_revisao: Contagem = Field(description="Sempre apagados")
    cartoes_referencia: Contagem = Field(
        description=(
            'Criados pelo estudante citando a fonte; sempre mantidos com "Fonte apagada" (D-009)'
        )
    )


class ImpactoExclusaoFonteDTO(ModeloDTO):
    titulo: str
    estado: EstadoFonte
    contagens: ContagensExclusaoFonteDTO


class ExclusaoFonteEntradaDTO(EntradaDTO):
    modo_cartoes: ModoCartoes = Field(
        description='"Manter os cartões" ou "Excluir os cartões junto" (RN-14)'
    )
    impacto_confirmado: ContagensExclusaoFonteDTO
