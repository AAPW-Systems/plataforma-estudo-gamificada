"""Conversões puras entre DTOs e objetos de domínio (T036)."""

from __future__ import annotations

from app.identidade.dtos import PerfilDTO
from app.identidade.servicos import PerfilConsultado


def perfil_para_dto(perfil: PerfilConsultado) -> PerfilDTO:
    usuario = perfil.usuario
    return PerfilDTO(
        nome=usuario.nome,
        email=usuario.email,
        papel=usuario.papel,  # type: ignore[arg-type]  # o enum do banco só admite os dois valores
        fuso=usuario.fuso,
        meta_diaria=usuario.meta_diaria,
        tamanho_licao=usuario.tamanho_licao,
        limite_novos_dia=usuario.limite_novos_dia,
        retencao_desejada=float(perfil.retencao_desejada),
        criado_em=usuario.criado_em,
    )
