"""T006 (spec 004): as fontes fictícias da geração passam pelos CHECKs e FKs do banco."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select

from app.fontes.consultas import trechos_da_fonte
from app.fontes.modelos import Fonte, Trecho
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao
from tests import fabricas_geracao as fab
from tests.apoio_cartoes import semear_estudante

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("tema", ["biologia", "historia", "instrucao", "contradicao", "longa"])
async def test_fonte_concluida_com_os_trechos_do_tema(
    fabrica_sessoes: FabricaSessoes, tema: fab.Tema
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, materia = await semear_estudante(sessao)
        fonte, trechos = await fab.semear_fonte_concluida(
            sessao, usuario.id, materia.id, tema, tamanho_mb=0.1
        )
        lidos = await trechos_da_fonte(sessao, usuario.id, fonte.id)
    assert fonte.estado == "concluido"
    assert fonte.total_trechos == len(trechos) == len(lidos)
    assert [t.texto for t in lidos] == [t.texto for t in trechos]


async def test_o_mesmo_tema_duas_vezes_na_mesma_materia(fabrica_sessoes: FabricaSessoes) -> None:
    """O hash do conteúdo é único por matéria; a fábrica não tropeça nele."""
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, materia = await semear_estudante(sessao)
        await fab.semear_fonte_concluida(sessao, usuario.id, materia.id)
        await fab.semear_fonte_concluida(sessao, usuario.id, materia.id)


async def test_cli_cria_a_fonte_longa_na_materia_da_conta_exemplo(
    configuracao: Configuracao, fabrica_real: FabricaSessoes, capsys: pytest.CaptureFixture[str]
) -> None:
    email = f"longa.{uuid.uuid4().hex[:8]}@exemplo.com"
    async with unidade_de_trabalho(fabrica_real) as sessao:
        usuario, materia = await semear_estudante(sessao, email=email)
    config_cli = configuracao.model_copy(update={"app_ambiente": "desenvolvimento"})

    codigo = await fab.executar(
        ["--email", email.upper(), "--materia", "biologia", "--tamanho-mb", "0.2"], config_cli
    )

    assert codigo == 0
    assert "trechos" in capsys.readouterr().out
    async with unidade_de_trabalho(fabrica_real) as sessao:
        fonte = (
            await sessao.execute(select(Fonte).where(Fonte.materia_id == materia.id))
        ).scalar_one()
        total = (
            await sessao.execute(
                select(func.count()).select_from(Trecho).where(Trecho.fonte_id == fonte.id)
            )
        ).scalar_one()
    assert fonte.usuario_id == usuario.id
    assert fonte.estado == "concluido"
    assert fonte.total_trechos is not None
    assert total == fonte.total_trechos > 50


async def test_cli_recusa_conta_ou_materia_inexistente(
    configuracao: Configuracao, fabrica_real: FabricaSessoes
) -> None:
    email = f"vazia.{uuid.uuid4().hex[:8]}@exemplo.com"
    async with unidade_de_trabalho(fabrica_real) as sessao:
        await semear_estudante(sessao, email=email)
    config_cli = configuracao.model_copy(update={"app_ambiente": "desenvolvimento"})
    assert await fab.executar(["--email", f"x{email}", "--materia", "Biologia"], config_cli) == 1
    assert await fab.executar(["--email", email, "--materia", "Química"], config_cli) == 1
