"""Conversões puras entre o domínio das fontes e os DTOs."""

from __future__ import annotations

from uuid import UUID

from app.fontes import dominio
from app.fontes.dominio import CodigoFalha, EstadoFonte
from app.fontes.dtos import (
    ContagensExclusaoFonteDTO,
    FonteDTO,
    ImpactoExclusaoFonteDTO,
    ListaFontesDTO,
)
from app.fontes.modelos import Fonte
from app.nucleo.participantes_acervo import ContagensAcervo


def fonte_para_dto(fonte: Fonte, materia_public_id: UUID) -> FonteDTO:
    estado = EstadoFonte(fonte.estado)
    codigo = CodigoFalha(fonte.codigo_falha) if fonte.codigo_falha else None
    return FonteDTO(
        id=fonte.public_id,
        materia_id=materia_public_id,
        titulo=fonte.titulo,
        nome_arquivo=fonte.nome_arquivo,
        tipo_midia=fonte.tipo_midia,  # type: ignore[arg-type]  # o CHECK do banco só admite os três
        tamanho_bytes=fonte.tamanho_bytes,
        estado=estado,
        codigo_falha=codigo,
        mensagem_falha=dominio.mensagem_do_estado(estado, codigo),
        pode_tentar_novamente=dominio.pode_tentar_novamente(estado, codigo),
        total_paginas=fonte.total_paginas,
        total_trechos=fonte.total_trechos,
        enviada_em=fonte.criado_em,
        processada_em=fonte.processada_em,
    )


def fontes_para_dto(fontes: list[Fonte], materia_public_id: UUID) -> ListaFontesDTO:
    return ListaFontesDTO(itens=[fonte_para_dto(f, materia_public_id) for f in fontes])


def contagens_do_dto(dto: ContagensExclusaoFonteDTO) -> ContagensAcervo:
    return ContagensAcervo(
        cartoes_gerados_aceitos=dto.cartoes_gerados_aceitos,
        cartoes_aguardando_revisao=dto.cartoes_aguardando_revisao,
        cartoes_referencia=dto.cartoes_referencia,
    )


def impacto_para_dto(
    titulo: str, estado: EstadoFonte, contagens: ContagensAcervo
) -> ImpactoExclusaoFonteDTO:
    return ImpactoExclusaoFonteDTO(
        titulo=titulo,
        estado=estado,
        # O DTO de contagens também é corpo de entrada (só camelCase): constrói-se por alias.
        contagens=ContagensExclusaoFonteDTO.model_validate(
            {
                "cartoesGeradosAceitos": contagens.cartoes_gerados_aceitos,
                "cartoesAguardandoRevisao": contagens.cartoes_aguardando_revisao,
                "cartoesReferencia": contagens.cartoes_referencia,
            }
        ),
    )
