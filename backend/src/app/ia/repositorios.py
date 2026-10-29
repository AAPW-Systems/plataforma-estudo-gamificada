"""Consultas do domínio `ia`: consumo e ciência (DTEC 039 e 040)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ia.modelos import CienciaAvisoIa, ConsumoIa


class RepositorioConsumoIa:
    def __init__(self, sessao: AsyncSession) -> None:
        self._sessao = sessao

    async def tokens_desde(self, usuario_id: int, inicio: datetime) -> int:
        """Tokens do estudante desde `inicio` (índice `(usuario_id, criado_em)`); nulo soma 0."""
        consulta = select(
            func.coalesce(
                func.sum(
                    func.coalesce(ConsumoIa.tokens_entrada, 0)
                    + func.coalesce(ConsumoIa.tokens_saida, 0)
                ),
                0,
            )
        ).where(ConsumoIa.usuario_id == usuario_id, ConsumoIa.criado_em >= inicio)
        return int((await self._sessao.execute(consulta)).scalar_one())

    async def registrar(self, consumo: ConsumoIa) -> None:
        self._sessao.add(consumo)
        await self._sessao.flush()

    async def apagar_do_usuario(self, usuario_id: int) -> None:
        await self._sessao.execute(delete(ConsumoIa).where(ConsumoIa.usuario_id == usuario_id))
        await self._sessao.execute(
            delete(CienciaAvisoIa).where(CienciaAvisoIa.usuario_id == usuario_id)
        )
