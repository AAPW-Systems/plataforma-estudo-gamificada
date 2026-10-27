"""Rotas HTTP dos cartões (spec 003): limites, listagem e criação."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Path, Query, Response

from app.cartoes.dependencias import Servico
from app.cartoes.dominio import PAGINA_MAXIMA, PAGINA_PADRAO
from app.cartoes.dtos import (
    CartaoDTO,
    CriacaoCartaoEntradaDTO,
    EdicaoCartaoEntradaDTO,
    LimitesCartaoDTO,
    ListaCartoesDTO,
)
from app.cartoes.mapeadores import cartao_para_dto, limites_para_dto, pagina_para_dto
from app.identidade.dependencias import UsuarioAtual
from app.nucleo.dtos import ErroDTO

roteador = APIRouter(prefix="/api/v1", tags=["cartoes"])

_ERRO: dict[str, Any] = {"model": ErroDTO}
# O caminho público é camelCase (`{materiaId}`), como no contrato; o parâmetro Python, snake_case.
MateriaId = Annotated[UUID, Path(alias="materiaId", description="`public_id` da matéria")]
CartaoId = Annotated[UUID, Path(alias="cartaoId", description="`public_id` do cartão")]
_RESPOSTAS_CSRF: dict[int | str, dict[str, Any]] = {400: _ERRO, 403: _ERRO}


@roteador.get("/cartoes/limites", operation_id="consultarLimitesCartao", responses={401: _ERRO})
async def consultar_limites(atual: UsuarioAtual, servico: Servico) -> LimitesCartaoDTO:
    """Limites de texto vigentes no ambiente (RF-001, D-004)."""
    return limites_para_dto(servico.limites())


@roteador.get(
    "/materias/{materiaId}/cartoes",
    operation_id="listarCartoes",
    responses={401: _ERRO, 404: _ERRO, 422: _ERRO},
)
async def listar_cartoes(
    materia_id: MateriaId,
    atual: UsuarioAtual,
    servico: Servico,
    cursor: Annotated[
        str | None,
        Query(
            max_length=512,
            description="`proximoCursor` da página anterior, com os mesmos filtros",
        ),
    ] = None,
    limite: Annotated[int, Query(ge=1, le=PAGINA_MAXIMA)] = PAGINA_PADRAO,
) -> ListaCartoesDTO:
    """Lista os cartões ativos e suspensos da matéria, do mais recente para o mais antigo."""
    pagina = await servico.listar(atual.usuario.id, materia_id, cursor=cursor, limite=limite)
    return pagina_para_dto(pagina)


@roteador.post(
    "/materias/{materiaId}/cartoes",
    status_code=201,
    operation_id="criarCartao",
    responses={**_RESPOSTAS_CSRF, 401: _ERRO, 404: _ERRO, 422: _ERRO},
)
async def criar_cartao(
    materia_id: MateriaId,
    entrada: CriacaoCartaoEntradaDTO,
    atual: UsuarioAtual,
    servico: Servico,
    resposta: Response,
) -> CartaoDTO:
    """Cria um cartão manual na matéria; com `fonteId`, a cita como referência (sem selo)."""
    linha = await servico.criar(
        usuario_id=atual.usuario.id,
        usuario_public_id=atual.usuario.public_id,
        materia_public_id=materia_id,
        frente=entrada.frente,
        verso=entrada.verso,
        explicacao=entrada.explicacao,
        fonte_public_id=entrada.fonte_id,
    )
    resposta.headers["Location"] = f"/api/v1/cartoes/{linha.cartao.public_id}"
    return cartao_para_dto(linha)


@roteador.get(
    "/cartoes/{cartaoId}",
    operation_id="consultarCartao",
    responses={401: _ERRO, 404: _ERRO},
)
async def consultar_cartao(cartao_id: CartaoId, atual: UsuarioAtual, servico: Servico) -> CartaoDTO:
    """Dados de um cartão ativo ou suspenso."""
    return cartao_para_dto(await servico.consultar(atual.usuario.id, cartao_id))


@roteador.patch(
    "/cartoes/{cartaoId}",
    operation_id="editarCartao",
    responses={**_RESPOSTAS_CSRF, 401: _ERRO, 404: _ERRO, 422: _ERRO},
)
async def editar_cartao(
    cartao_id: CartaoId, entrada: EdicaoCartaoEntradaDTO, atual: UsuarioAtual, servico: Servico
) -> CartaoDTO:
    """Edita frente, verso ou explicação, sem mudar o agendamento (US2; RF-005, RF-006)."""
    linha = await servico.editar(
        usuario_id=atual.usuario.id,
        usuario_public_id=atual.usuario.public_id,
        public_id=cartao_id,
        alteracoes=entrada.alteracoes(),
    )
    return cartao_para_dto(linha)
