"""Participante de `materias` no registro de exclusão da conta (DTEC 021).

As matérias saem depois das fontes e dos cartões (ordem 500), porque as FKs compostas deles
para a matéria usam `restrict`; e antes de `revisao` (900) e da `identidade` (950).
"""

from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.materias.modelos import Materia
from app.nucleo.exclusao import registro_exclusao

ORDEM_EXCLUSAO = 500


async def apagar_dados_usuario(sessao: AsyncSession, usuario_id: int) -> None:
    await sessao.execute(delete(Materia).where(Materia.usuario_id == usuario_id))


registro_exclusao.registrar(ORDEM_EXCLUSAO, "materias", apagar_dados_usuario)
