"""Parâmetros do FSRS do estudante (T035; RF-010, RN-26, CB-29)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from importlib.metadata import version

from fsrs import Scheduler
from sqlalchemy.ext.asyncio import AsyncSession

from app.revisao.modelos import ParametrosFsrs
from app.revisao.repositorios import RepositorioParametrosFsrs


async def criar_parametros_iniciais(
    sessao: AsyncSession, usuario_id: int, agora: datetime, retencao_desejada: Decimal
) -> ParametrosFsrs:
    """Versão 1: os pesos e os passos padrão da biblioteca fixada, com a retenção de D-001."""
    padrao = Scheduler()
    return await RepositorioParametrosFsrs(sessao).criar(
        usuario_id=usuario_id,
        versao=1,
        pesos=[float(peso) for peso in padrao.parameters],
        retencao_desejada=retencao_desejada,
        passos_aprendizado_s=[int(passo.total_seconds()) for passo in padrao.learning_steps],
        passos_reaprendizado_s=[int(passo.total_seconds()) for passo in padrao.relearning_steps],
        intervalo_maximo_dias=padrao.maximum_interval,
        fuzzing=padrao.enable_fuzzing,
        versao_biblioteca=version("fsrs"),
        agora=agora,
    )


async def retencao_vigente(sessao: AsyncSession, usuario_id: int) -> Decimal:
    """Retenção desejada da versão vigente; sem versão, é um defeito de dados e não um padrão."""
    vigente = await RepositorioParametrosFsrs(sessao).buscar_vigente(usuario_id)
    if vigente is None:
        raise LookupError(f"o usuário {usuario_id} não tem parâmetros do FSRS")
    return vigente.retencao_desejada
