"""Exclusão dos dados do domínio `ia` com a conta (DTEC 021 e 039): consumo e ciências."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ia.repositorios import RepositorioConsumoIa
from app.nucleo.exclusao import registro_exclusao

# Sem dependência de ordem com os outros domínios (a FK para a geração é `set null`); antes de
# `identidade` (950), que apaga o usuário.
ORDEM_EXCLUSAO = 600


async def apagar_dados_usuario(sessao: AsyncSession, usuario_id: int) -> None:
    await RepositorioConsumoIa(sessao).apagar_do_usuario(usuario_id)


registro_exclusao.registrar(ORDEM_EXCLUSAO, "ia", apagar_dados_usuario)
