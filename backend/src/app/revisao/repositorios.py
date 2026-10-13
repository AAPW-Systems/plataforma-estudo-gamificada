"""Versões dos parâmetros do FSRS (T034; RF-010, CB-29)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.revisao.modelos import ParametrosFsrs


class RepositorioParametrosFsrs:
    def __init__(self, sessao: AsyncSession) -> None:
        self._sessao = sessao

    async def criar(
        self,
        *,
        usuario_id: int,
        versao: int,
        pesos: list[float],
        retencao_desejada: Decimal,
        passos_aprendizado_s: list[int],
        passos_reaprendizado_s: list[int],
        intervalo_maximo_dias: int,
        fuzzing: bool,
        versao_biblioteca: str,
        agora: datetime,
    ) -> ParametrosFsrs:
        """Grava uma versão nova; as anteriores nunca são alteradas."""
        parametros = ParametrosFsrs(
            usuario_id=usuario_id,
            versao=versao,
            origem="padrao",
            pesos=pesos,
            retencao_desejada=retencao_desejada,
            passos_aprendizado_s=passos_aprendizado_s,
            passos_reaprendizado_s=passos_reaprendizado_s,
            intervalo_maximo_dias=intervalo_maximo_dias,
            fuzzing=fuzzing,
            versao_biblioteca=versao_biblioteca,
            criado_em=agora,
        )
        self._sessao.add(parametros)
        await self._sessao.flush()
        return parametros

    async def buscar_vigente(self, usuario_id: int) -> ParametrosFsrs | None:
        consulta = (
            select(ParametrosFsrs)
            .where(ParametrosFsrs.usuario_id == usuario_id)
            .order_by(ParametrosFsrs.versao.desc())
            .limit(1)
            .execution_options(populate_existing=True)
        )
        return (await self._sessao.execute(consulta)).scalar_one_or_none()
