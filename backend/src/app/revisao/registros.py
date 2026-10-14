"""Participante de `revisao` no registro de exclusão da conta (DTEC 021, T056)."""

from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.exclusao import registro_exclusao
from app.revisao.modelos import ParametrosFsrs

ORDEM_EXCLUSAO = 900


async def apagar_dados_usuario(sessao: AsyncSession, usuario_id: int) -> None:
    await sessao.execute(delete(ParametrosFsrs).where(ParametrosFsrs.usuario_id == usuario_id))


registro_exclusao.registrar(ORDEM_EXCLUSAO, "revisao", apagar_dados_usuario)
