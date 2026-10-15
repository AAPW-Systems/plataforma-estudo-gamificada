"""Rotas HTTP das matérias (spec 002): criar, listar, consultar, renomear e excluir."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Path, Response

from app.identidade.dependencias import UsuarioAtual
from app.materias.dependencias import Servico
from app.materias.dtos import (
    ExclusaoMateriaEntradaDTO,
    ImpactoExclusaoMateriaDTO,
    ListaMateriasDTO,
    MateriaDTO,
    MateriaEntradaDTO,
)
from app.materias.mapeadores import (
    impacto_do_dto,
    impacto_para_dto,
    materia_para_dto,
    materias_para_dto,
)
from app.nucleo.dtos import ErroDTO

roteador = APIRouter(prefix="/api/v1", tags=["materias"])

_ERRO: dict[str, Any] = {"model": ErroDTO}
# O caminho público é camelCase (`{materiaId}`), como no contrato; o parâmetro Python, snake_case.
MateriaId = Annotated[UUID, Path(alias="materiaId", description="`public_id` da matéria")]
_RESPOSTAS_CSRF: dict[int | str, dict[str, Any]] = {400: _ERRO, 403: _ERRO}


@roteador.get("/materias", operation_id="listarMaterias", responses={401: _ERRO})
async def listar_materias(atual: UsuarioAtual, servico: Servico) -> ListaMateriasDTO:
    return materias_para_dto(await servico.listar(atual.usuario.id))


@roteador.post(
    "/materias",
    status_code=201,
    operation_id="criarMateria",
    responses={**_RESPOSTAS_CSRF, 401: _ERRO, 409: _ERRO, 422: _ERRO},
)
async def criar_materia(
    entrada: MateriaEntradaDTO, atual: UsuarioAtual, servico: Servico
) -> MateriaDTO:
    return materia_para_dto(await servico.criar(atual.usuario.id, entrada.nome))


@roteador.get(
    "/materias/{materiaId}",
    operation_id="consultarMateria",
    responses={401: _ERRO, 404: _ERRO},
)
async def consultar_materia(
    materia_id: MateriaId, atual: UsuarioAtual, servico: Servico
) -> MateriaDTO:
    return materia_para_dto(await servico.consultar(atual.usuario.id, materia_id))


@roteador.patch(
    "/materias/{materiaId}",
    operation_id="renomearMateria",
    responses={**_RESPOSTAS_CSRF, 401: _ERRO, 404: _ERRO, 409: _ERRO, 422: _ERRO},
)
async def renomear_materia(
    materia_id: MateriaId, entrada: MateriaEntradaDTO, atual: UsuarioAtual, servico: Servico
) -> MateriaDTO:
    return materia_para_dto(await servico.renomear(atual.usuario.id, materia_id, entrada.nome))


@roteador.get(
    "/materias/{materiaId}/impacto-exclusao",
    operation_id="consultarImpactoExclusaoMateria",
    responses={401: _ERRO, 404: _ERRO},
)
async def consultar_impacto_exclusao_materia(
    materia_id: MateriaId, atual: UsuarioAtual, servico: Servico
) -> ImpactoExclusaoMateriaDTO:
    return impacto_para_dto(await servico.impacto_exclusao(atual.usuario.id, materia_id))


@roteador.post(
    "/materias/{materiaId}/exclusao",
    status_code=204,
    operation_id="excluirMateria",
    response_class=Response,
    responses={**_RESPOSTAS_CSRF, 401: _ERRO, 404: _ERRO, 409: _ERRO, 422: _ERRO},
)
async def excluir_materia(
    materia_id: MateriaId,
    entrada: ExclusaoMateriaEntradaDTO,
    atual: UsuarioAtual,
    servico: Servico,
) -> Response:
    await servico.excluir(
        usuario_id=atual.usuario.id,
        public_id=materia_id,
        nome_confirmacao=entrada.nome_confirmacao,
        impacto_confirmado=impacto_do_dto(entrada.impacto_confirmado),
    )
    return Response(status_code=204)
