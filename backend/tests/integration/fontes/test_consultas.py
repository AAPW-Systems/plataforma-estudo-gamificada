"""T005 (spec 004): leitura de fonte e trechos para a geração, sempre pelo dono (DTEC 019).

A geração lê o acervo só por `app/fontes/consultas.py`, sem tocar no ORM de `fontes`.
"""

from __future__ import annotations

import uuid

import psycopg
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.fontes.consultas import fonte_do_dono, trechos_da_fonte
from app.fontes.modelos import Fonte, Trecho
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao
from tests.apoio_cartoes import semear_estudante, semear_fonte
from tests.conftest import BANCO_TESTE

pytestmark = pytest.mark.integration

TEXTOS = [
    ("A célula é a unidade básica da vida.", 1),
    ("A mitocôndria produz ATP por respiração celular.", None),
    ("O núcleo guarda o material genético. 🧬", 2),
]


async def _semear(sessao: AsyncSession) -> tuple[int, int, Fonte]:
    usuario, materia = await semear_estudante(sessao)
    fonte = await semear_fonte(sessao, usuario.id, materia.id, titulo="Citologia")
    # inseridos fora de ordem: a leitura devolve pela `ordem`
    for ordem in (2, 0, 1):
        texto, pagina = TEXTOS[ordem]
        sessao.add(
            Trecho(
                fonte_id=fonte.id,
                ordem=ordem,
                texto=texto,
                pagina=pagina,
                inicio_caractere=ordem * 100,
                fim_caractere=ordem * 100 + len(texto),
            )
        )
    await sessao.flush()
    return usuario.id, materia.id, fonte


async def test_fonte_do_dono_devolve_o_que_a_geracao_precisa(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario_id, materia_id, fonte = await _semear(sessao)
        lida = await fonte_do_dono(sessao, usuario_id, fonte.public_id)
    assert lida is not None
    assert lida.id == fonte.id
    assert lida.public_id == fonte.public_id
    assert lida.materia_id == materia_id
    assert lida.estado == "concluido"
    assert (lida.titulo, lida.nome_arquivo) == ("Citologia", "citologia.pdf")
    assert lida.enviada_em == fonte.criado_em


async def test_fonte_alheia_ou_inexistente_nao_tem_resultado(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    """DTEC 019: o filtro de dono está na própria consulta."""
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        _, _, fonte = await _semear(sessao)
        intrusa, _ = await semear_estudante(sessao)
        assert await fonte_do_dono(sessao, intrusa.id, fonte.public_id) is None
        assert await fonte_do_dono(sessao, intrusa.id, uuid.uuid4()) is None


async def test_trechos_em_ordem_com_pagina_e_tamanho(fabrica_sessoes: FabricaSessoes) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario_id, _, fonte = await _semear(sessao)
        trechos = await trechos_da_fonte(sessao, usuario_id, fonte.id)
    assert [t.ordem for t in trechos] == [0, 1, 2]
    assert [(t.texto, t.pagina) for t in trechos] == TEXTOS
    # tamanho em code points, como o `char_length` do banco (o emoji conta 1)
    assert [t.tamanho for t in trechos] == [len(texto) for texto, _ in TEXTOS]
    assert len({t.id for t in trechos}) == 3


async def test_trechos_filtrados_pelos_ids_pedidos(fabrica_sessoes: FabricaSessoes) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario_id, _, fonte = await _semear(sessao)
        todos = await trechos_da_fonte(sessao, usuario_id, fonte.id)
        pedidos = [todos[2].id, todos[0].id]
        filtrados = await trechos_da_fonte(sessao, usuario_id, fonte.id, pedidos)
        nenhum = await trechos_da_fonte(sessao, usuario_id, fonte.id, [])
    assert [t.ordem for t in filtrados] == [0, 2]
    assert nenhum == []


async def test_trechos_de_fonte_alheia_nao_tem_resultado(fabrica_sessoes: FabricaSessoes) -> None:
    """Nenhum trecho alheio entra na janela, nem pedido pelo id (DTEC 019)."""
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario_id, _, fonte = await _semear(sessao)
        todos = await trechos_da_fonte(sessao, usuario_id, fonte.id)
        intrusa, materia_intrusa = await semear_estudante(sessao)
        propria = await semear_fonte(sessao, intrusa.id, materia_intrusa.id)
        assert await trechos_da_fonte(sessao, intrusa.id, fonte.id) == []
        assert await trechos_da_fonte(sessao, intrusa.id, propria.id, [t.id for t in todos]) == []


async def test_fonte_do_dono_trava_a_linha_para_compartilhar(
    configuracao: Configuracao, fabrica_real: FabricaSessoes
) -> None:
    """DTEC 031: com `FOR SHARE`, uma exclusão concorrente espera; sem trava, não."""
    async with unidade_de_trabalho(fabrica_real) as sessao:
        usuario_id, _, fonte = await _semear(sessao)
    public_id = fonte.public_id
    fonte_id = fonte.id

    def _tenta_travar_para_excluir() -> bool:
        with psycopg.connect(configuracao.conninfo(BANCO_TESTE)) as outra:
            outra.execute("SET lock_timeout = '200ms'")
            try:
                outra.execute("SELECT id FROM fontes WHERE id = %s FOR UPDATE", (fonte_id,))
            except psycopg.errors.LockNotAvailable:
                return False
            return True

    async with unidade_de_trabalho(fabrica_real) as sessao:
        assert await fonte_do_dono(sessao, usuario_id, public_id) is not None
        assert _tenta_travar_para_excluir() is False
    async with unidade_de_trabalho(fabrica_real) as sessao:
        assert await fonte_do_dono(sessao, usuario_id, public_id, travar=False) is not None
        assert _tenta_travar_para_excluir() is True
