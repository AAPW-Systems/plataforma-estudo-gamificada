"""T009: participante dos cartões no registro da exclusão (DTEC 027, 021 e 038).

Contagens por situação, impacto e marcação "Fonte apagada" na exclusão da fonte, exclusão da
matéria e da conta, e a trava das linhas antes de contar (emenda de 15/10/2026 da DTEC 027).
"""

from __future__ import annotations

import psycopg
import pytest
from psycopg import errors
from sqlalchemy import delete, event, func, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from structlog.testing import capture_logs

import app.fontes.registros  # noqa: F401  (registra `fontes` no registro de exclusão)
import app.materias.registros  # noqa: F401  (registra `materias` no registro de exclusão)
from app.cartoes.modelos import Cartao, OrigemCartao, SituacaoCartao
from app.cartoes.registros import (
    ORDEM_EXCLUSAO,
    PRIORIDADE_PARTICIPANTE,
    apagar_dados_usuario,
    participante_cartoes,
)
from app.fontes.modelos import Fonte
from app.identidade.modelos import Usuario
from app.materias.modelos import Materia
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao
from app.nucleo.exclusao import registro_exclusao
from app.nucleo.participantes_acervo import (
    ContagensAcervo,
    ModoCartoes,
    ParticipanteComTravaDeMateria,
    registro_acervo,
)
from tests import fabricas_cartoes as fab
from tests.apoio_cartoes import AGORA, semear_estudante, semear_fonte, semear_materia
from tests.fabricas_cartoes import CartaoFicticio, cartao_ficticio

pytestmark = pytest.mark.integration

ATIVO, SUSPENSO = SituacaoCartao.ATIVO, SituacaoCartao.SUSPENSO


def _itens(origem: OrigemCartao, ativos: int, suspensos: int) -> list[CartaoFicticio]:
    return [cartao_ficticio(origem=origem, situacao=ATIVO) for _ in range(ativos)] + [
        cartao_ficticio(origem=origem, situacao=SUSPENSO) for _ in range(suspensos)
    ]


# --- Registro ------------------------------------------------------------------------------------


def test_participante_esta_registrado_antes_de_fontes_e_a_exclusao_antes_de_fontes_e_materias() -> (
    None
):
    nomes = registro_acervo.nomes()
    assert "cartoes" in nomes
    assert nomes.index("cartoes") < nomes.index("fontes"), "cartões antes de `fontes` (DTEC 027)"
    assert 100 <= PRIORIDADE_PARTICIPANTE <= 799, "faixa dos cartões e gerações"
    dominios = [p.dominio for p in registro_exclusao.em_ordem()]
    assert dominios.index("cartoes") < dominios.index("fontes") < dominios.index("materias")
    assert ORDEM_EXCLUSAO < 400, "antes das fontes (400) e das matérias (500)"


def test_participante_implementa_o_gancho_de_trava_da_matéria() -> None:
    assert isinstance(participante_cartoes, ParticipanteComTravaDeMateria)


# --- contar_por_materia --------------------------------------------------------------------------


async def test_conta_ativos_e_suspensos_separados_de_qualquer_origem(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, biologia = await semear_estudante(sessao)
        quimica = await semear_materia(sessao, usuario.id, "Química")
        vazia = await semear_materia(sessao, usuario.id, "Física")
        itens = (
            _itens(OrigemCartao.CRIADO, 3, 1)
            + _itens(OrigemCartao.EDITADO, 2, 2)
            + _itens(OrigemCartao.GERADO_VERIFICADO, 1, 1)
        )
        await fab.inserir(
            sessao, usuario_id=usuario.id, materia_id=biologia.id, itens=itens, agora=AGORA
        )
        await fab.inserir(
            sessao,
            usuario_id=usuario.id,
            materia_id=quimica.id,
            itens=_itens(OrigemCartao.CRIADO, 1, 0),
            agora=AGORA,
        )

        contagens = await participante_cartoes.contar_por_materia(sessao, usuario.id)

    assert contagens[biologia.id] == ContagensAcervo(cartoes_ativos=6, cartoes_suspensos=4)
    assert contagens[quimica.id] == ContagensAcervo(cartoes_ativos=1, cartoes_suspensos=0)
    assert vazia.id not in contagens, "matéria sem cartões vale zero (ausente)"


async def test_contagem_e_so_do_dono(fabrica_sessoes: FabricaSessoes) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        ana, materia_da_ana = await semear_estudante(sessao)
        bia, materia_da_bia = await semear_estudante(sessao)
        for usuario, materia, total in ((ana, materia_da_ana, 2), (bia, materia_da_bia, 5)):
            await fab.inserir(
                sessao,
                usuario_id=usuario.id,
                materia_id=materia.id,
                itens=_itens(OrigemCartao.CRIADO, total, 0),
                agora=AGORA,
            )
        da_ana = await participante_cartoes.contar_por_materia(sessao, ana.id)
    assert da_ana == {materia_da_ana.id: ContagensAcervo(cartoes_ativos=2)}


# --- impacto_fonte e ao_excluir_fonte ------------------------------------------------------------


type Cenario = tuple[Usuario, Materia, Fonte, Fonte, list[Cartao], list[Cartao], list[Cartao]]


async def _cenario_com_referencias(sessao: AsyncSession) -> Cenario:
    usuario, materia = await semear_estudante(sessao)
    citologia = await semear_fonte(sessao, usuario.id, materia.id, titulo="Citologia")
    genetica = await semear_fonte(sessao, usuario.id, materia.id, titulo="Genética")

    def ref(fonte: Fonte) -> fab.ReferenciaFonte:
        return fab.ReferenciaFonte(fonte.id, fonte.titulo, fonte.nome_arquivo, fonte.criado_em)

    com_citologia = await fab.inserir(
        sessao,
        usuario_id=usuario.id,
        materia_id=materia.id,
        itens=[cartao_ficticio(com_referencia=True), cartao_ficticio(com_referencia=True)],
        agora=AGORA,
        fonte=ref(citologia),
    )
    com_genetica = await fab.inserir(
        sessao,
        usuario_id=usuario.id,
        materia_id=materia.id,
        itens=[cartao_ficticio(com_referencia=True)],
        agora=AGORA,
        fonte=ref(genetica),
    )
    soltos = await fab.inserir(
        sessao,
        usuario_id=usuario.id,
        materia_id=materia.id,
        itens=[cartao_ficticio(), cartao_ficticio(situacao=SUSPENSO)],
        agora=AGORA,
    )
    return usuario, materia, citologia, genetica, com_citologia, com_genetica, soltos


async def test_impacto_da_fonte_conta_so_os_cartoes_que_a_citam(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, _, citologia, genetica, *_ = await _cenario_com_referencias(sessao)
        impacto = await participante_cartoes.impacto_fonte(sessao, usuario.id, citologia.id)
        outro = await participante_cartoes.impacto_fonte(sessao, usuario.id, genetica.id)
        de_outro_dono = await participante_cartoes.impacto_fonte(
            sessao, usuario.id + 999, citologia.id
        )
    assert impacto == ContagensAcervo(cartoes_referencia=2)
    assert outro == ContagensAcervo(cartoes_referencia=1)
    assert de_outro_dono == ContagensAcervo()


@pytest.mark.parametrize("modo", [ModoCartoes.MANTER, ModoCartoes.EXCLUIR])
async def test_excluir_fonte_anula_fonte_id_nos_dois_modos_e_mantem_a_copia(
    fabrica_sessoes: FabricaSessoes, modo: ModoCartoes
) -> None:
    """D-006: o cartão manual é sempre mantido, e `excluir` não o apaga."""
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        (
            usuario,
            materia,
            citologia,
            genetica,
            com_citologia,
            com_genetica,
            soltos,
        ) = await _cenario_com_referencias(sessao)
        antes = {c.id: c.atualizado_em for c in [*com_citologia, *com_genetica, *soltos]}
        ids_citologia = [c.id for c in com_citologia]
        ids_genetica = [c.id for c in com_genetica]
        ids_soltos = [c.id for c in soltos]
        citologia_id, genetica_id, usuario_id, materia_id = (
            citologia.id,
            genetica.id,
            usuario.id,
            materia.id,
        )

        with capture_logs() as registros:
            await participante_cartoes.ao_excluir_fonte(sessao, usuario_id, citologia_id, modo)
        sessao.expire_all()

        todos = {
            c.id: c
            for c in (await sessao.execute(select(Cartao).where(Cartao.materia_id == materia_id)))
            .scalars()
            .all()
        }
        assert len(todos) == 5, "nenhum cartão foi apagado"
        for cartao_id in ids_citologia:
            atual = todos[cartao_id]
            assert atual.fonte_id is None, "referência anulada"
            assert (atual.referencia_titulo, atual.referencia_nome_arquivo) == (
                "Citologia",
                "citologia.pdf",
            ), "a cópia da origem sobrevive"
            assert atual.referencia_enviada_em is not None
            assert atual.origem is OrigemCartao.CRIADO
        for cartao_id in ids_genetica:  # outra fonte, intocado
            assert todos[cartao_id].fonte_id == genetica_id
        for cartao_id in ids_soltos:
            assert todos[cartao_id].fonte_id is None
            assert todos[cartao_id].referencia_titulo is None
        assert {i: c.atualizado_em for i, c in todos.items()} == antes, "conteúdo não mudou"

        eventos = [r for r in registros if r["event"] == "cartoes_referencia_marcados"]
        assert [e["quantidade"] for e in eventos] == [2]
        assert "Citologia" not in str(registros)

        # Com a referência anulada, a fonte pode ser apagada (o `restrict` não a segura).
        await sessao.execute(delete(Fonte).where(Fonte.id == citologia_id))


async def test_sem_o_participante_a_exclusao_da_fonte_falha_por_restrict(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        _, _, citologia, *_ = await _cenario_com_referencias(sessao)
        with pytest.raises(Exception, match="cartoes_fonte_id_fkey"):
            await sessao.delete(citologia)
            await sessao.flush()


async def test_excluir_fonte_sem_referencias_nao_faz_nada_nem_registra_log(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, materia = await semear_estudante(sessao)
        fonte = await semear_fonte(sessao, usuario.id, materia.id)
        with capture_logs() as registros:
            await participante_cartoes.ao_excluir_fonte(
                sessao, usuario.id, fonte.id, ModoCartoes.MANTER
            )
    assert not [r for r in registros if r["event"] == "cartoes_referencia_marcados"]


async def test_excluir_fonte_de_outro_dono_nao_toca_nos_cartoes(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, _, citologia, *_ = await _cenario_com_referencias(sessao)
        await participante_cartoes.ao_excluir_fonte(
            sessao, usuario.id + 999, citologia.id, ModoCartoes.EXCLUIR
        )
        mantidos = (
            await sessao.execute(
                select(func.count()).select_from(Cartao).where(Cartao.fonte_id == citologia.id)
            )
        ).scalar_one()
    assert mantidos == 2


# --- ao_excluir_materia --------------------------------------------------------------------------


async def test_excluir_materia_apaga_so_os_cartoes_dela(fabrica_sessoes: FabricaSessoes) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, biologia = await semear_estudante(sessao)
        quimica = await semear_materia(sessao, usuario.id, "Química")
        outro, materia_do_outro = await semear_estudante(sessao)
        for dono, materia, total in (
            (usuario, biologia, 6),
            (usuario, quimica, 2),
            (outro, materia_do_outro, 3),
        ):
            await fab.inserir(
                sessao,
                usuario_id=dono.id,
                materia_id=materia.id,
                itens=fab.gerar(total),
                agora=AGORA,
            )

        with capture_logs() as registros:
            await participante_cartoes.ao_excluir_materia(sessao, usuario.id, biologia.id)

        restantes = dict(
            (
                await sessao.execute(
                    select(Cartao.materia_id, func.count()).group_by(Cartao.materia_id)
                )
            ).all()
        )
    assert restantes == {quimica.id: 2, materia_do_outro.id: 3}
    eventos = [r for r in registros if r["event"] == "cartoes_materia_apagados"]
    assert [e["quantidade"] for e in eventos] == [6]


async def test_excluir_materia_de_outro_dono_nao_apaga_nada(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, materia = await semear_estudante(sessao)
        await fab.inserir(
            sessao, usuario_id=usuario.id, materia_id=materia.id, itens=fab.gerar(4), agora=AGORA
        )
        await participante_cartoes.ao_excluir_materia(sessao, usuario.id + 999, materia.id)
        total = (await sessao.execute(select(func.count()).select_from(Cartao))).scalar_one()
    assert total == 4


# --- apagar_dados_usuario (DTEC 021) -------------------------------------------------------------


async def test_exclusao_da_conta_apaga_todos_os_cartoes_do_usuario_e_so_os_dele(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        ana, biologia = await semear_estudante(sessao)
        quimica = await semear_materia(sessao, ana.id, "Química")
        bia, materia_da_bia = await semear_estudante(sessao)
        fonte = await semear_fonte(sessao, ana.id, biologia.id)
        await fab.inserir(
            sessao,
            usuario_id=ana.id,
            materia_id=biologia.id,
            itens=fab.gerar(8),
            agora=AGORA,
            fonte=fab.ReferenciaFonte(fonte.id, fonte.titulo, fonte.nome_arquivo, AGORA),
        )
        await fab.inserir(
            sessao, usuario_id=ana.id, materia_id=quimica.id, itens=fab.gerar(3), agora=AGORA
        )
        await fab.inserir(
            sessao, usuario_id=bia.id, materia_id=materia_da_bia.id, itens=fab.gerar(5), agora=AGORA
        )

        await apagar_dados_usuario(sessao, ana.id)

        por_dono = dict(
            (
                await sessao.execute(
                    select(Cartao.usuario_id, func.count()).group_by(Cartao.usuario_id)
                )
            ).all()
        )
    assert por_dono == {bia.id: 5}


async def test_exclusao_completa_do_registro_roda_cartoes_antes_de_fontes_e_materias(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    """Na ordem do registro, as FKs `restrict` de cartões para fontes e matérias não atrapalham."""
    import app.fontes.registros  # noqa: F401
    import app.materias.registros  # noqa: F401

    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, materia = await semear_estudante(sessao)
        fonte = await semear_fonte(sessao, usuario.id, materia.id)
        await fab.inserir(
            sessao,
            usuario_id=usuario.id,
            materia_id=materia.id,
            itens=fab.gerar(12),
            agora=AGORA,
            fonte=fab.ReferenciaFonte(fonte.id, fonte.titulo, fonte.nome_arquivo, AGORA),
        )
        await registro_exclusao.apagar_dados_usuario(sessao, usuario.id)
        restos = [
            (await sessao.execute(select(func.count()).select_from(modelo))).scalar_one()
            for modelo in (Cartao, Materia)
        ]
    assert restos == [0, 0]


# --- Trava da matéria (emenda de 15/10/2026 da DTEC 027) -----------------------------------------


async def test_travar_para_exclusao_trava_os_cartoes_da_materia_e_so_eles(
    fabrica_real: FabricaSessoes, configuracao: Configuracao
) -> None:
    """Sem a trava, quem altera um cartão durante a contagem muda o que a exclusão apaga."""
    async with unidade_de_trabalho(fabrica_real) as sessao:
        usuario, biologia = await semear_estudante(sessao)
        quimica = await semear_materia(sessao, usuario.id, "Química")
        da_biologia = await fab.inserir(
            sessao, usuario_id=usuario.id, materia_id=biologia.id, itens=fab.gerar(4), agora=AGORA
        )
        da_quimica = await fab.inserir(
            sessao, usuario_id=usuario.id, materia_id=quimica.id, itens=fab.gerar(2), agora=AGORA
        )
        ids = (usuario.id, biologia.id, [c.id for c in da_biologia], [c.id for c in da_quimica])

    async with unidade_de_trabalho(fabrica_real) as sessao:
        await participante_cartoes.travar_para_exclusao_de_materia(sessao, ids[0], ids[1])
        async with await psycopg.AsyncConnection.connect(configuracao.conninfo()) as outra:
            for cartao_id in ids[2]:
                with pytest.raises(errors.LockNotAvailable):
                    await outra.execute(
                        "SELECT id FROM cartoes WHERE id = %s FOR UPDATE NOWAIT", (cartao_id,)
                    )
                await outra.rollback()
            # Outra matéria do mesmo estudante não é travada.
            for cartao_id in ids[3]:
                await outra.execute(
                    "SELECT id FROM cartoes WHERE id = %s FOR UPDATE NOWAIT", (cartao_id,)
                )


async def test_a_trava_vai_em_ordem_de_id(
    fabrica_sessoes: FabricaSessoes, conexao: AsyncConnection
) -> None:
    """Mesma ordem em toda transação: sem *deadlock* entre duas exclusões (DTEC 031)."""
    consultas: list[str] = []

    def capturar(_conn: object, _cursor: object, statement: str, *_resto: object) -> None:
        consultas.append(statement)

    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario, materia = await semear_estudante(sessao)
        sync_engine = conexao.sync_engine
        event.listen(sync_engine, "before_cursor_execute", capturar)
        try:
            await participante_cartoes.travar_para_exclusao_de_materia(
                sessao, usuario.id, materia.id
            )
        finally:
            event.remove(sync_engine, "before_cursor_execute", capturar)
    travas = [c for c in consultas if "FOR UPDATE" in c and "cartoes" in c]
    assert len(travas) == 1
    assert "ORDER BY cartoes.id" in travas[0]
