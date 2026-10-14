"""Participante da identidade no registro de exclusão da conta (DTEC 021, T056).

Sessões e o próprio usuário saem por último (ordem 950): os domínios que dependem do usuário
(`revisao`, em 900, e os das specs seguintes) apagam antes.
"""

from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.identidade.modelos import Sessao, Usuario
from app.nucleo.exclusao import registro_exclusao

ORDEM_EXCLUSAO = 950


async def apagar_dados_usuario(sessao: AsyncSession, usuario_id: int) -> None:
    await sessao.execute(delete(Sessao).where(Sessao.usuario_id == usuario_id))
    await sessao.execute(delete(Usuario).where(Usuario.id == usuario_id))


registro_exclusao.registrar(ORDEM_EXCLUSAO, "identidade", apagar_dados_usuario)
