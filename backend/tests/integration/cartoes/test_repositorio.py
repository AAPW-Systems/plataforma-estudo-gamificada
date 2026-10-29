"""T009: repositório dos cartões contra o PostgreSQL real (filtro de dono, lista, referência).

Cobre o que a US1 usa: criar, listar de forma paginada por cursor e buscar a fonte de referência.
A busca por texto e os filtros são da US4 (`test_busca.py`).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from psycopg import errors
from sqlalchemy import delete

from app.cartoes.cursor import PosicaoCursor
from app.cartoes.dominio import LimitesTexto, TextoCartao, estado_inicial, validar_limites
from app.cartoes.modelos import Cartao, EstadoFsrs, OrigemCartao, SituacaoCartao
from app.cartoes.repositorios import CopiaReferencia, RepositorioCartoes
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao
from app.nucleo.erros import RecursoNaoEncontrado
from tests import fabricas_cartoes as fab
from tests.apoio_cartoes import (
    AGORA,
    semear_cartao_gerado,
    semear_estudante,
    semear_fonte,
    semear_materia,
)

pytestmark = pytest.mark.integration

LIMITES = LimitesTexto(frente=1000, verso=2000, explicacao=1000)


def _texto(frente: str = "Qual organela produz ATP?", verso: str = "Mitocôndria") -> TextoCartao:
    return validar_limites(frente, verso, None, LIMITES)


# --- Criação -------------------------------------------------------------------------------------


async def test_cria_cartao_ativo_criado_novo_com_o_instante_da_criacao(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, materia = await semear_estudante(sessao)
        cartao = await RepositorioCartoes(sessao).criar(
            usuario_id=usuario.id,
            materia_id=materia.id,
            texto=validar_limites("  Frente\r\nem duas linhas ", "Verso", " Explicação ", LIMITES),
            estado=estado_inicial(AGORA),
            agora=AGORA,
        )
        assert cartao.public_id is not None and cartao.id > 0
        assert (cartao.frente, cartao.verso, cartao.explicacao) == (
            "Frente\nem duas linhas",
            "Verso",
            "Explicação",
        )
        assert (cartao.origem, cartao.situacao) == (OrigemCartao.CRIADO, SituacaoCartao.ATIVO)
        assert cartao.estado_fsrs is EstadoFsrs.APRENDIZADO and cartao.passo == 0
        assert cartao.estabilidade is None and cartao.dificuldade is None
        assert cartao.ultima_revisao is None
        assert cartao.vencimento == cartao.entrada_estudo_em == AGORA
        assert cartao.criado_em == cartao.atualizado_em == AGORA
        assert cartao.fonte_id is None and cartao.referencia_titulo is None


async def test_o_banco_recusa_cartao_numa_materia_de_outro_dono(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    """Defesa em profundidade: mesmo que o serviço errasse o dono, a FK composta recusa.

    Para o estudante, a matéria que não é dele não existe: o repositório devolve o 404 comum.
    """
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        ana, materia_da_ana = await semear_estudante(sessao)
        bia, _ = await semear_estudante(sessao)
        with pytest.raises(RecursoNaoEncontrado):
            await RepositorioCartoes(sessao).criar(
                usuario_id=bia.id,
                materia_id=materia_da_ana.id,
                texto=_texto(),
                estado=estado_inicial(AGORA),
                agora=AGORA,
            )
        assert ana.id != bia.id


# --- Referência à fonte (DTEC 035) ---------------------------------------------------------------


async def test_copia_da_referencia_vem_do_titulo_do_nome_e_da_data_do_envio(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, materia = await semear_estudante(sessao)
        fonte = await semear_fonte(
            sessao, usuario.id, materia.id, titulo="Citologia", nome_arquivo="aula-3.pdf"
        )
        copia = CopiaReferencia.da_fonte(fonte)
        assert copia == CopiaReferencia(
            fonte.id, "Citologia", "aula-3.pdf", datetime(2026, 10, 1, 9, 30, tzinfo=UTC)
        )
        cartao = await RepositorioCartoes(sessao).criar(
            usuario_id=usuario.id,
            materia_id=materia.id,
            texto=_texto(),
            estado=estado_inicial(AGORA),
            agora=AGORA,
            referencia=copia,
        )
        assert cartao.fonte_id == fonte.id
        assert (
            cartao.referencia_titulo,
            cartao.referencia_nome_arquivo,
            cartao.referencia_enviada_em,
        ) == ("Citologia", "aula-3.pdf", fonte.criado_em)
        assert cartao.origem is OrigemCartao.CRIADO, "a referência nunca vira evidência"


async def test_buscar_fonte_para_referencia_so_devolve_fonte_do_dono_e_da_materia(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        ana, biologia = await semear_estudante(sessao)
        quimica = await semear_materia(sessao, ana.id, "Química")
        bia, materia_da_bia = await semear_estudante(sessao)
        fonte = await semear_fonte(sessao, ana.id, biologia.id)
        fonte_alheia = await semear_fonte(sessao, bia.id, materia_da_bia.id)
        repositorio = RepositorioCartoes(sessao)

        achada = await repositorio.buscar_fonte_para_referencia(
            ana.id, biologia.id, fonte.public_id
        )
        assert achada is not None and achada.id == fonte.id
        assert (
            await repositorio.buscar_fonte_para_referencia(ana.id, quimica.id, fonte.public_id)
            is None
        ), "outra matéria"
        assert (
            await repositorio.buscar_fonte_para_referencia(
                bia.id, materia_da_bia.id, fonte.public_id
            )
            is None
        ), "outro dono"
        assert (
            await repositorio.buscar_fonte_para_referencia(
                ana.id, biologia.id, fonte_alheia.public_id
            )
            is None
        )
        assert (
            await repositorio.buscar_fonte_para_referencia(ana.id, biologia.id, uuid.uuid4())
            is None
        )


@pytest.mark.parametrize("estado", ["pendente", "processando", "concluido", "falhou"])
async def test_fonte_em_qualquer_estado_serve_de_referencia(
    fabrica_sessoes: FabricaSessoes, estado: str
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, materia = await semear_estudante(sessao)
        fonte = await semear_fonte(sessao, usuario.id, materia.id, estado=estado)
        achada = await RepositorioCartoes(sessao).buscar_fonte_para_referencia(
            usuario.id, materia.id, fonte.public_id
        )
        assert achada is not None


async def test_a_fonte_de_referencia_fica_travada_com_for_share(
    fabrica_real: FabricaSessoes, configuracao: Configuracao
) -> None:
    """A exclusão trava a fonte com `FOR UPDATE` (DTEC 031): precisa esperar quem a cita."""
    async with unidade_de_trabalho(fabrica_real) as sessao:
        usuario, materia = await semear_estudante(sessao)
        fonte = await semear_fonte(sessao, usuario.id, materia.id)
        ids = (usuario.id, materia.id, fonte.id, fonte.public_id)

    async with unidade_de_trabalho(fabrica_real) as sessao:
        achada = await RepositorioCartoes(sessao).buscar_fonte_para_referencia(
            ids[0], ids[1], ids[3]
        )
        assert achada is not None
        async with await psycopg.AsyncConnection.connect(configuracao.conninfo()) as outra:
            with pytest.raises(errors.LockNotAvailable):
                await outra.execute(
                    "SELECT id FROM fontes WHERE id = %s FOR UPDATE NOWAIT", (ids[2],)
                )
            await outra.rollback()
            # Quem só cita a mesma fonte não espera ninguém.
            await outra.execute("SELECT id FROM fontes WHERE id = %s FOR SHARE NOWAIT", (ids[2],))


# --- Listagem ------------------------------------------------------------------------------------


async def _semear_lista(fabrica: FabricaSessoes, quantidade: int) -> tuple[int, int, list[Cartao]]:
    async with unidade_de_trabalho(fabrica) as sessao:
        usuario, materia = await semear_estudante(sessao)
        cartoes = await fab.inserir(
            sessao,
            usuario_id=usuario.id,
            materia_id=materia.id,
            itens=fab.gerar(quantidade),
            agora=AGORA,
        )
        return usuario.id, materia.id, cartoes


async def test_lista_so_ativos_e_suspensos_do_mais_recente_para_o_mais_antigo(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    usuario_id, materia_id, cartoes = await _semear_lista(fabrica_sessoes, 12)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        linhas, ha_mais = await RepositorioCartoes(sessao).listar(usuario_id, materia_id, limite=50)
    assert [linha.cartao.id for linha in linhas] == [c.id for c in reversed(cartoes)]
    assert {linha.cartao.situacao for linha in linhas} == {
        SituacaoCartao.ATIVO,
        SituacaoCartao.SUSPENSO,
    }
    assert ha_mais is False
    assert all(linha.materia_public_id is not None for linha in linhas)


async def test_lista_so_do_dono_e_da_materia(fabrica_sessoes: FabricaSessoes) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        ana, biologia = await semear_estudante(sessao)
        quimica = await semear_materia(sessao, ana.id, "Química")
        bia, materia_da_bia = await semear_estudante(sessao)
        for usuario, materia in ((ana, biologia), (ana, quimica), (bia, materia_da_bia)):
            await fab.inserir(
                sessao,
                usuario_id=usuario.id,
                materia_id=materia.id,
                itens=fab.gerar(3),
                agora=AGORA,
            )
        repositorio = RepositorioCartoes(sessao)
        da_ana, _ = await repositorio.listar(ana.id, biologia.id)
        assert len(da_ana) == 3 and {linha.cartao.materia_id for linha in da_ana} == {biologia.id}
        assert await repositorio.contar(ana.id, biologia.id) == 3
        # a matéria da Bia consultada com o dono da Ana não devolve nada
        assert await repositorio.listar(ana.id, materia_da_bia.id) == ([], False)
        assert await repositorio.contar(ana.id, materia_da_bia.id) == 0


async def test_o_total_conta_todos_os_cartoes_visiveis_nao_so_a_pagina(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    usuario_id, materia_id, _ = await _semear_lista(fabrica_sessoes, 30)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        repositorio = RepositorioCartoes(sessao)
        pagina, ha_mais = await repositorio.listar(usuario_id, materia_id, limite=10)
        assert (len(pagina), ha_mais) == (10, True)
        assert await repositorio.contar(usuario_id, materia_id) == 30


async def test_ultima_pagina_exata_nao_anuncia_proxima(fabrica_sessoes: FabricaSessoes) -> None:
    usuario_id, materia_id, _ = await _semear_lista(fabrica_sessoes, 10)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        pagina, ha_mais = await RepositorioCartoes(sessao).listar(usuario_id, materia_id, limite=10)
    assert (len(pagina), ha_mais) == (10, False)


async def test_paginacao_percorre_tudo_sem_repetir_nem_pular(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    usuario_id, materia_id, cartoes = await _semear_lista(fabrica_sessoes, 25)
    vistos: list[int] = []
    posicao: PosicaoCursor | None = None
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        repositorio = RepositorioCartoes(sessao)
        while True:
            pagina, ha_mais = await repositorio.listar(
                usuario_id, materia_id, posicao=posicao, limite=7
            )
            vistos += [linha.cartao.id for linha in pagina]
            if not ha_mais:
                break
            ultimo = pagina[-1].cartao
            posicao = PosicaoCursor(ultimo.criado_em, ultimo.id)
    assert vistos == [c.id for c in reversed(cartoes)]


async def test_cartoes_com_o_mesmo_instante_desempatam_pelo_id(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    """Criados na mesma transação têm o mesmo `criado_em`; a ordem continua total."""
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, materia = await semear_estudante(sessao)
        repositorio = RepositorioCartoes(sessao)
        criados = [
            await repositorio.criar(
                usuario_id=usuario.id,
                materia_id=materia.id,
                texto=_texto(frente=f"Pergunta {i}"),
                estado=estado_inicial(AGORA),
                agora=AGORA,
            )
            for i in range(9)
        ]
        vistos: list[int] = []
        posicao: PosicaoCursor | None = None
        while True:
            pagina, ha_mais = await repositorio.listar(
                usuario.id, materia.id, posicao=posicao, limite=2
            )
            vistos += [linha.cartao.id for linha in pagina]
            if not ha_mais:
                break
            posicao = PosicaoCursor(pagina[-1].cartao.criado_em, pagina[-1].cartao.id)
    assert vistos == [c.id for c in reversed(criados)]


async def test_criacao_e_exclusao_entre_as_paginas_nao_repetem_nem_pulam_o_resto(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    usuario_id, materia_id, cartoes = await _semear_lista(fabrica_sessoes, 10)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        repositorio = RepositorioCartoes(sessao)
        primeira, _ = await repositorio.listar(usuario_id, materia_id, limite=4)
        ultimo = primeira[-1].cartao
        posicao = PosicaoCursor(ultimo.criado_em, ultimo.id)

        # Entre as páginas: um cartão novo (mais recente), a exclusão de um que já foi visto e a
        # de outro que ainda não foi.
        await repositorio.criar(
            usuario_id=usuario_id,
            materia_id=materia_id,
            texto=_texto(frente="Novo no meio"),
            estado=estado_inicial(AGORA + timedelta(minutes=5)),
            agora=AGORA + timedelta(minutes=5),
        )
        a_excluir_id = list(reversed(cartoes))[5].id  # ainda não visto
        await sessao.execute(
            delete(Cartao).where(Cartao.id.in_([primeira[0].cartao.id, a_excluir_id]))
        )

        segunda, ha_mais = await repositorio.listar(
            usuario_id, materia_id, posicao=posicao, limite=50
        )
    esperados = [c.id for c in list(reversed(cartoes))[4:] if c.id != a_excluir_id]
    assert [linha.cartao.id for linha in segunda] == esperados
    assert ha_mais is False
    assert "Novo no meio" not in {linha.cartao.frente for linha in segunda}


async def test_cartao_fora_das_situacoes_visiveis_nao_aparece_na_lista(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    """Aguardando revisão e recusado são da 004 e ficam fora da lista e da contagem (DTEC 038)."""

    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, materia = await semear_estudante(sessao)
        await fab.inserir(
            sessao, usuario_id=usuario.id, materia_id=materia.id, itens=fab.gerar(4), agora=AGORA
        )
        for situacao in ("aguardando_revisao", "recusado"):
            await semear_cartao_gerado(sessao, materia.id, situacao, frente="Invisível")
        repositorio = RepositorioCartoes(sessao)
        pagina, _ = await repositorio.listar(usuario.id, materia.id)
        assert len(pagina) == 4 and "Invisível" not in {linha.cartao.frente for linha in pagina}
        assert await repositorio.contar(usuario.id, materia.id) == 4


async def test_lista_traz_o_public_id_da_materia_e_o_da_fonte_de_referencia(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, materia = await semear_estudante(sessao)
        fonte = await semear_fonte(sessao, usuario.id, materia.id)
        repositorio = RepositorioCartoes(sessao)
        com = await repositorio.criar(
            usuario_id=usuario.id,
            materia_id=materia.id,
            texto=_texto(),
            estado=estado_inicial(AGORA),
            agora=AGORA,
            referencia=CopiaReferencia.da_fonte(fonte),
        )
        sem = await repositorio.criar(
            usuario_id=usuario.id,
            materia_id=materia.id,
            texto=_texto(),
            estado=estado_inicial(AGORA),
            agora=AGORA,
        )
        linhas, _ = await repositorio.listar(usuario.id, materia.id)
    por_id = {linha.cartao.id: linha for linha in linhas}
    assert por_id[com.id].fonte_public_id == fonte.public_id
    assert por_id[sem.id].fonte_public_id is None
    assert {linha.materia_public_id for linha in linhas} == {materia.public_id}
