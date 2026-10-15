"""O que `fontes` registra no núcleo: participante da exclusão do acervo e da conta.

- **Participante** (DTEC 027): conta as fontes por matéria e, na exclusão da matéria, apaga os
  objetos (antes das linhas, DTEC 025) e as linhas das fontes; roda por último (prioridade 900),
  depois dos participantes de cartões e gerações.
- **Exclusão da conta** (DTEC 021): apaga as fontes (os trechos vão em cascata). Os objetos saem
  pela tarefa `apagar_objetos_usuario`, que já existe.
"""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.fontes.modelos import Fonte
from app.nucleo.armazenamento import Armazenamento
from app.nucleo.exclusao import registro_exclusao
from app.nucleo.participantes_acervo import ContagensAcervo, ModoCartoes, registro_acervo

PRIORIDADE_PARTICIPANTE = 900
ORDEM_EXCLUSAO = 400  # antes de `materias` (500): a FK composta é `restrict`


class ParticipanteFontes:
    """A exclusão de matéria precisa do armazenamento; ele é entregue pelo serviço da matéria."""

    def __init__(self) -> None:
        self.armazenamento: Armazenamento | None = None

    async def contar_por_materia(
        self, sessao: AsyncSession, usuario_id: int
    ) -> dict[int, ContagensAcervo]:
        consulta = (
            select(Fonte.materia_id, func.count())
            .where(Fonte.usuario_id == usuario_id)
            .group_by(Fonte.materia_id)
        )
        linhas = (await sessao.execute(consulta)).all()
        return {materia_id: ContagensAcervo(fontes=total) for materia_id, total in linhas}

    async def impacto_fonte(
        self, sessao: AsyncSession, usuario_id: int, fonte_id: int
    ) -> ContagensAcervo:
        return ContagensAcervo()

    async def ao_excluir_fonte(
        self, sessao: AsyncSession, usuario_id: int, fonte_id: int, modo: ModoCartoes
    ) -> None:
        """A exclusão da fonte apaga o objeto e a linha no próprio serviço (DTEC 031)."""

    async def travar_para_exclusao_de_materia(
        self, sessao: AsyncSession, usuario_id: int, materia_id: int
    ) -> None:
        """`FOR UPDATE` nas fontes da matéria, em ordem de `id` (sem *deadlock*, DTEC 031)."""
        consulta = (
            select(Fonte.id)
            .where(Fonte.usuario_id == usuario_id, Fonte.materia_id == materia_id)
            .order_by(Fonte.id)
            .with_for_update()
        )
        await sessao.execute(consulta)

    async def ao_excluir_materia(
        self, sessao: AsyncSession, usuario_id: int, materia_id: int
    ) -> None:
        """Apaga os objetos e as linhas das fontes da matéria (objetos antes das linhas)."""
        if self.armazenamento is None:
            # Sem armazenamento, apagar só as linhas deixaria objetos órfãos: falha em vez disso.
            raise RuntimeError("o armazenamento não foi entregue ao participante de fontes")
        consulta = (
            select(Fonte.chave_objeto)
            .where(Fonte.usuario_id == usuario_id, Fonte.materia_id == materia_id)
            .order_by(Fonte.id)
        )
        for chave in (await sessao.execute(consulta)).scalars().all():
            await self.armazenamento.apagar(chave)
        await sessao.execute(
            delete(Fonte).where(Fonte.usuario_id == usuario_id, Fonte.materia_id == materia_id)
        )


participante_fontes = ParticipanteFontes()


async def apagar_dados_usuario(sessao: AsyncSession, usuario_id: int) -> None:
    await sessao.execute(delete(Fonte).where(Fonte.usuario_id == usuario_id))


registro_acervo.registrar(PRIORIDADE_PARTICIPANTE, "fontes", participante_fontes)
registro_exclusao.registrar(ORDEM_EXCLUSAO, "fontes", apagar_dados_usuario)
