"""Parâmetros do FSRS do estudante (T035; RF-010, RN-26, CB-29)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from importlib.metadata import version

from fsrs import Scheduler
from sqlalchemy.ext.asyncio import AsyncSession

from app.revisao import dominio
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


async def alterar_retencao(
    sessao: AsyncSession, usuario_id: int, retencao_nova: Decimal, agora: datetime
) -> Decimal:
    """Aplica a retenção desejada e devolve a vigente depois da alteração (RF-010, CB-29).

    Um valor diferente grava a versão n+1, copiando os demais parâmetros da versão vigente; a
    versão n nunca é alterada, e o mesmo valor não cria versão. Quem chama já trava a linha do
    usuário (`FOR UPDATE`), o que serializa as trocas concorrentes: sem lacuna e sem repetição.
    """
    repositorio = RepositorioParametrosFsrs(sessao)
    vigente = await repositorio.buscar_vigente(usuario_id)
    if vigente is None:
        raise LookupError(f"o usuário {usuario_id} não tem parâmetros do FSRS")
    if not dominio.precisa_nova_versao(vigente.retencao_desejada, retencao_nova):
        return vigente.retencao_desejada
    nova = await repositorio.criar(
        usuario_id=usuario_id,
        versao=dominio.proxima_versao(vigente.versao),
        pesos=list(vigente.pesos),
        retencao_desejada=retencao_nova,
        passos_aprendizado_s=list(vigente.passos_aprendizado_s),
        passos_reaprendizado_s=list(vigente.passos_reaprendizado_s),
        intervalo_maximo_dias=vigente.intervalo_maximo_dias,
        fuzzing=vigente.fuzzing,
        versao_biblioteca=vigente.versao_biblioteca,
        agora=agora,
    )
    return nova.retencao_desejada
