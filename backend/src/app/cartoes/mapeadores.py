"""Conversões puras entre o domínio dos cartões e os DTOs."""

from __future__ import annotations

from app.cartoes import dominio
from app.cartoes.dominio import LimitesTexto
from app.cartoes.dtos import CartaoDTO, LimitesCartaoDTO, ListaCartoesDTO, ReferenciaFonteDTO
from app.cartoes.repositorios import LinhaCartao
from app.cartoes.servicos import PaginaCartoes


def cartao_para_dto(linha: LinhaCartao) -> CartaoDTO:
    cartao = linha.cartao
    referencia = (
        ReferenciaFonteDTO(
            fonte_id=linha.fonte_public_id,
            titulo=cartao.referencia_titulo,
            nome_arquivo=cartao.referencia_nome_arquivo or "",
            enviada_em=cartao.referencia_enviada_em or cartao.criado_em,
            fonte_apagada=dominio.fonte_apagada(cartao.referencia_titulo, cartao.fonte_id),
        )
        if cartao.referencia_titulo is not None
        else None
    )
    return CartaoDTO(
        id=cartao.public_id,
        materia_id=linha.materia_public_id,
        frente=cartao.frente,
        verso=cartao.verso,
        explicacao=cartao.explicacao,
        origem=cartao.origem,
        verificado=dominio.verificado(cartao.origem),
        situacao=cartao.situacao,
        referencia=referencia,
        criado_em=cartao.criado_em,
        atualizado_em=cartao.atualizado_em,
    )


def pagina_para_dto(pagina: PaginaCartoes) -> ListaCartoesDTO:
    return ListaCartoesDTO(
        itens=[cartao_para_dto(linha) for linha in pagina.itens],
        proximo_cursor=pagina.proximo_cursor,
        total=pagina.total,
    )


def limites_para_dto(limites: LimitesTexto) -> LimitesCartaoDTO:
    return LimitesCartaoDTO(
        frente_max=limites.frente,
        verso_max=limites.verso,
        explicacao_max=limites.explicacao,
        busca_max=dominio.BUSCA_MAXIMA,
    )
