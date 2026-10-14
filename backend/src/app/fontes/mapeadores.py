"""Conversões puras entre o domínio das fontes e os DTOs."""

from __future__ import annotations

from uuid import UUID

from app.fontes import dominio
from app.fontes.dominio import CodigoFalha, EstadoFonte
from app.fontes.dtos import FonteDTO, ListaFontesDTO
from app.fontes.modelos import Fonte


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
