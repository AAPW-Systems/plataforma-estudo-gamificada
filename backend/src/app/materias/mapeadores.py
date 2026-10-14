"""Conversões puras entre o domínio das matérias e os DTOs."""

from __future__ import annotations

from app.materias.dtos import ListaMateriasDTO, MateriaDTO
from app.materias.servicos import MateriaConsultada


def materia_para_dto(consultada: MateriaConsultada) -> MateriaDTO:
    materia, contagens = consultada.materia, consultada.contagens
    return MateriaDTO(
        id=materia.public_id,
        nome=materia.nome,
        total_fontes=contagens.fontes,
        cartoes_ativos=contagens.cartoes_ativos,
        cartoes_aguardando_revisao=contagens.cartoes_aguardando_revisao,
        criado_em=materia.criado_em,
        atualizado_em=materia.atualizado_em,
    )


def materias_para_dto(materias: list[MateriaConsultada]) -> ListaMateriasDTO:
    return ListaMateriasDTO(itens=[materia_para_dto(m) for m in materias])
