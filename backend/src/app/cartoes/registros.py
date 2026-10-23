"""O que `cartoes` registra no núcleo: participante da exclusão do acervo e da conta.

- **Participante** (DTEC 027 e 038): conta os cartões por situação, de qualquer origem; marca como
  "Fonte apagada" os cartões que citam uma fonte excluída (D-006); trava e apaga os cartões da
  matéria excluída. Roda antes do de `fontes` (prioridade 900), porque as FKs compostas de
  cartões para fontes e matérias usam `restrict`. A faixa de 100 a 799 é de cartões e gerações.
- **Exclusão da conta** (DTEC 021): apaga os cartões do usuário antes de `fontes` (400) e de
  `materias` (500).

Os logs levam só quantidades: nunca o texto do cartão nem o título da referência.
"""

from __future__ import annotations

from typing import Any, cast

import structlog
from sqlalchemy import CursorResult, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cartoes.modelos import Cartao, SituacaoCartao
from app.cartoes.repositorios import SITUACOES_VISIVEIS
from app.nucleo.exclusao import registro_exclusao
from app.nucleo.participantes_acervo import ContagensAcervo, ModoCartoes, registro_acervo

PRIORIDADE_PARTICIPANTE = 300
ORDEM_EXCLUSAO = 300

logger = structlog.get_logger(__name__)


def _linhas_afetadas(resultado: object) -> int:
    return cast("CursorResult[Any]", resultado).rowcount


class ParticipanteCartoes:
    async def contar_por_materia(
        self, sessao: AsyncSession, usuario_id: int
    ) -> dict[int, ContagensAcervo]:
        """Ativos e suspensos por matéria, de qualquer origem (emenda da DTEC 027)."""
        consulta = (
            select(Cartao.materia_id, Cartao.situacao, func.count())
            .where(Cartao.usuario_id == usuario_id, Cartao.situacao.in_(SITUACOES_VISIVEIS))
            .group_by(Cartao.materia_id, Cartao.situacao)
        )
        contagens: dict[int, ContagensAcervo] = {}
        for materia_id, situacao, total in await sessao.execute(consulta):
            parcial = (
                ContagensAcervo(cartoes_ativos=total)
                if situacao is SituacaoCartao.ATIVO
                else ContagensAcervo(cartoes_suspensos=total)
            )
            contagens[materia_id] = contagens.get(materia_id, ContagensAcervo()) + parcial
        return contagens

    async def impacto_fonte(
        self, sessao: AsyncSession, usuario_id: int, fonte_id: int
    ) -> ContagensAcervo:
        """Os cartões do estudante que citam a fonte; só os manuais têm referência (DTEC 035)."""
        consulta = (
            select(func.count())
            .select_from(Cartao)
            .where(Cartao.usuario_id == usuario_id, Cartao.fonte_id == fonte_id)
        )
        return ContagensAcervo(
            cartoes_referencia=int((await sessao.execute(consulta)).scalar_one())
        )

    async def ao_excluir_fonte(
        self, sessao: AsyncSession, usuario_id: int, fonte_id: int, modo: ModoCartoes
    ) -> None:
        """Anula `fonte_id` dos cartões que citam a fonte, em qualquer modo (D-006).

        As cópias da origem ficam, e o cartão passa a mostrar "Fonte apagada". O modo escolhido
        vale para os cartões gerados (004), não para os do estudante.
        """
        resultado = await sessao.execute(
            update(Cartao)
            .where(Cartao.usuario_id == usuario_id, Cartao.fonte_id == fonte_id)
            .values(fonte_id=None)
        )
        marcados = _linhas_afetadas(resultado)
        if marcados:
            logger.info("cartoes_referencia_marcados", quantidade=marcados)

    async def travar_para_exclusao_de_materia(
        self, sessao: AsyncSession, usuario_id: int, materia_id: int
    ) -> None:
        """`FOR UPDATE` nos cartões da matéria, em ordem de `id` (sem *deadlock*, DTEC 031).

        Sem isto, quem edita ou exclui um cartão enquanto a exclusão conta e confirma o impacto
        mudaria o que é apagado depois de o estudante tê-lo visto.
        """
        consulta = (
            select(Cartao.id)
            .where(Cartao.usuario_id == usuario_id, Cartao.materia_id == materia_id)
            .order_by(Cartao.id)
            .with_for_update()
        )
        await sessao.execute(consulta)

    async def ao_excluir_materia(
        self, sessao: AsyncSession, usuario_id: int, materia_id: int
    ) -> None:
        resultado = await sessao.execute(
            delete(Cartao).where(Cartao.usuario_id == usuario_id, Cartao.materia_id == materia_id)
        )
        apagados = _linhas_afetadas(resultado)
        if apagados:
            logger.info("cartoes_materia_apagados", quantidade=apagados)


participante_cartoes = ParticipanteCartoes()


async def apagar_dados_usuario(sessao: AsyncSession, usuario_id: int) -> None:
    await sessao.execute(delete(Cartao).where(Cartao.usuario_id == usuario_id))


registro_acervo.registrar(PRIORIDADE_PARTICIPANTE, "cartoes", participante_cartoes)
registro_exclusao.registrar(ORDEM_EXCLUSAO, "cartoes", apagar_dados_usuario)
