"""Conversões puras entre o domínio das matérias e os DTOs."""

from __future__ import annotations

from app.materias.dominio import ImpactoMateria
from app.materias.dtos import (
    ContagensExclusaoMateriaDTO,
    ImpactoExclusaoMateriaDTO,
    ListaMateriasDTO,
    MateriaDTO,
)
from app.materias.servicos import ImpactoConsultado, MateriaConsultada


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


def impacto_do_dto(dto: ContagensExclusaoMateriaDTO) -> ImpactoMateria:
    return ImpactoMateria(
        fontes=dto.fontes,
        cartoes_ativos=dto.cartoes_ativos,
        cartoes_aguardando_revisao=dto.cartoes_aguardando_revisao,
    )


def impacto_para_dto(consultado: ImpactoConsultado) -> ImpactoExclusaoMateriaDTO:
    impacto = consultado.impacto
    return ImpactoExclusaoMateriaDTO(
        nome=consultado.nome,
        # O DTO de contagens também é corpo de entrada (só camelCase): constrói-se por alias.
        contagens=ContagensExclusaoMateriaDTO.model_validate(
            {
                "fontes": impacto.fontes,
                "cartoesAtivos": impacto.cartoes_ativos,
                "cartoesAguardandoRevisao": impacto.cartoes_aguardando_revisao,
            }
        ),
    )
