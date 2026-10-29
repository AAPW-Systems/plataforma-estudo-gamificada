"""Leitura do acervo para a geração de cartões (spec 004, T005).

A geração (`cartoes/geracao`) lê a fonte e os trechos só por aqui, sem conhecer o ORM de
`fontes`. Toda consulta filtra pelo dono na própria cláusula (DTEC 019): uma fonte ou um trecho de
outro estudante simplesmente não aparece.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.fontes.modelos import Fonte, Trecho


@dataclass(frozen=True, slots=True)
class FonteDaGeracao:
    id: int
    public_id: UUID
    materia_id: int
    estado: str
    titulo: str
    nome_arquivo: str
    enviada_em: datetime


@dataclass(frozen=True, slots=True)
class TrechoDaGeracao:
    id: int
    ordem: int
    texto: str
    pagina: int | None
    tamanho: int


async def fonte_do_dono(
    sessao: AsyncSession, usuario_id: int, public_id: UUID, *, travar: bool = True
) -> FonteDaGeracao | None:
    """A fonte do estudante, ou `None` se não existir ou for de outro dono.

    `travar` aplica `FOR SHARE` (DTEC 031): a exclusão da fonte espera o pedido ou a publicação
    terminar, e duas leituras não se bloqueiam.
    """
    consulta = select(
        Fonte.id,
        Fonte.public_id,
        Fonte.materia_id,
        Fonte.estado,
        Fonte.titulo,
        Fonte.nome_arquivo,
        Fonte.criado_em,
    ).where(Fonte.public_id == public_id, Fonte.usuario_id == usuario_id)
    if travar:
        consulta = consulta.with_for_update(read=True)
    linha = (await sessao.execute(consulta)).one_or_none()
    if linha is None:
        return None
    return FonteDaGeracao(
        id=linha.id,
        public_id=linha.public_id,
        materia_id=linha.materia_id,
        estado=str(linha.estado),
        titulo=linha.titulo,
        nome_arquivo=linha.nome_arquivo,
        enviada_em=linha.criado_em,
    )


async def trechos_da_fonte(
    sessao: AsyncSession,
    usuario_id: int,
    fonte_id: int,
    ids: Collection[int] | None = None,
) -> list[TrechoDaGeracao]:
    """Os trechos da fonte do estudante, em `ordem`; só os de `ids`, quando informado."""
    consulta = (
        select(
            Trecho.id,
            Trecho.ordem,
            Trecho.texto,
            Trecho.pagina,
            func.char_length(Trecho.texto).label("tamanho"),
        )
        .join(Fonte, Fonte.id == Trecho.fonte_id)
        .where(Trecho.fonte_id == fonte_id, Fonte.usuario_id == usuario_id)
        .order_by(Trecho.ordem)
    )
    if ids is not None:
        consulta = consulta.where(Trecho.id.in_(list(ids)))
    linhas = (await sessao.execute(consulta)).all()
    return [
        TrechoDaGeracao(
            id=linha.id,
            ordem=linha.ordem,
            texto=linha.texto,
            pagina=linha.pagina,
            tamanho=linha.tamanho,
        )
        for linha in linhas
    ]
