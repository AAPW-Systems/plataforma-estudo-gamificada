"""Tarefas da identidade (T054; DTEC 021 e 020): remoção de objetos e limpeza periódica."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from procrastinate import RetryStrategy
from sqlalchemy import select

from app.identidade import tarefas
from app.identidade.modelos import Sessao, TentativaAcesso, Usuario
from app.identidade.repositorios import (
    RepositorioSessoes,
    RepositorioTentativas,
    RepositorioUsuarios,
)
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.fila import app_fila

pytestmark = pytest.mark.integration

AGORA = datetime(2026, 10, 14, 12, 0, tzinfo=UTC)


def test_as_tarefas_estao_registradas_no_app_da_fila() -> None:
    nomes = set(app_fila.tasks)
    assert {"identidade.apagar_objetos_usuario", "identidade.limpar_registros_expirados"} <= nomes


def test_a_remocao_de_objetos_tem_novas_tentativas_com_espera_crescente() -> None:
    estrategia = app_fila.tasks["identidade.apagar_objetos_usuario"].retry_strategy
    assert isinstance(estrategia, RetryStrategy)
    assert estrategia.max_attempts == 5
    assert estrategia.exponential_wait > 0


def test_a_limpeza_roda_todo_dia_as_3h_utc() -> None:
    periodicas = {
        nome: tarefa.cron for (nome, _), tarefa in app_fila.periodic_registry.periodic_tasks.items()
    }
    assert periodicas["identidade.limpar_registros_expirados"] == "0 3 * * *"


async def test_limpeza_apaga_tentativas_com_mais_de_24h_e_sessoes_invalidas_ha_mais_de_30_dias(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario = await RepositorioUsuarios(sessao).criar(
            nome="Ana", email="ana@exemplo.com", senha_hash="x", fuso="UTC", agora=AGORA
        )
        tentativas = RepositorioTentativas(sessao)
        await tentativas.registrar(
            "falha_entrada", b"a" * 32, "203.0.113.1", AGORA - timedelta(hours=25)
        )
        await tentativas.registrar(
            "falha_entrada", b"a" * 32, "203.0.113.1", AGORA - timedelta(hours=23)
        )
        sessoes = RepositorioSessoes(sessao)
        expirada = await sessoes.criar(
            usuario_id=usuario.id,
            token_hash=b"\x01" * 32,
            agora=AGORA - timedelta(days=60),
            expira_em=AGORA - timedelta(days=31),
            ip=None,
            agente_usuario=None,
        )
        revogada = await sessoes.criar(
            usuario_id=usuario.id,
            token_hash=b"\x02" * 32,
            agora=AGORA - timedelta(days=40),
            expira_em=AGORA + timedelta(days=10),
            ip=None,
            agente_usuario=None,
        )
        await sessoes.revogar(revogada.id, AGORA - timedelta(days=31))
        recente = await sessoes.criar(
            usuario_id=usuario.id,
            token_hash=b"\x03" * 32,
            agora=AGORA - timedelta(days=2),
            expira_em=AGORA + timedelta(days=28),
            ip=None,
            agente_usuario=None,
        )
        revogada_agora = await sessoes.criar(
            usuario_id=usuario.id,
            token_hash=b"\x04" * 32,
            agora=AGORA - timedelta(days=5),
            expira_em=AGORA + timedelta(days=25),
            ip=None,
            agente_usuario=None,
        )
        await sessoes.revogar(revogada_agora.id, AGORA - timedelta(days=1))

    resultado = await tarefas.executar_limpeza(fabrica_sessoes, AGORA, dias_inatividade=14)

    assert resultado == tarefas.ResultadoLimpeza(tentativas=1, sessoes=2)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        restantes = {s.id for s in (await sessao.execute(select(Sessao))).scalars()}
        assert restantes == {recente.id, revogada_agora.id}
        assert expirada.id not in restantes and revogada.id not in restantes
        assert len(list((await sessao.execute(select(TentativaAcesso))).scalars())) == 1
        assert (await sessao.execute(select(Usuario))).scalars().one() is not None


async def test_limpeza_repetida_nao_faz_nada(fabrica_sessoes: FabricaSessoes) -> None:
    assert await tarefas.executar_limpeza(fabrica_sessoes, AGORA, dias_inatividade=14) == (
        tarefas.ResultadoLimpeza(tentativas=0, sessoes=0)
    )
