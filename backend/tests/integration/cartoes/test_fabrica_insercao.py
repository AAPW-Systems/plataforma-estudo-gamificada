"""T004: os cartões da fábrica entram no banco (CHECK e FKs de verdade) e a CLI os semeia."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from app.cartoes.modelos import Cartao, EstadoFsrs, OrigemCartao, SituacaoCartao
from app.fontes.modelos import Fonte
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao
from tests import fabricas_cartoes as fab
from tests.apoio_cartoes import AGORA, semear_estudante, semear_fonte

pytestmark = pytest.mark.integration


async def _estudante(sessao: AsyncSession, email: str | None = None) -> tuple[int, int]:
    usuario, materia = await semear_estudante(sessao, email=email)
    return usuario.id, materia.id


async def _fonte(sessao: AsyncSession, usuario_id: int, materia_id: int) -> Fonte:
    return await semear_fonte(sessao, usuario_id, materia_id)


async def test_os_120_cartoes_da_fabrica_respeitam_check_e_fks_do_banco(
    fabrica_sessoes: FabricaSessoes, conexao: AsyncConnection
) -> None:
    itens = fab.gerar(120)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario_id, materia_id = await _estudante(sessao)
        fonte = await _fonte(sessao, usuario_id, materia_id)
        inseridos = await fab.inserir(
            sessao,
            usuario_id=usuario_id,
            materia_id=materia_id,
            itens=itens,
            agora=AGORA,
            fonte=fab.ReferenciaFonte(fonte.id, fonte.titulo, fonte.nome_arquivo, AGORA),
        )
        assert len(inseridos) == 120
        total = (
            await sessao.execute(
                select(func.count()).select_from(Cartao).where(Cartao.materia_id == materia_id)
            )
        ).scalar_one()
        assert total == 120
        referenciados = [c for c in inseridos if c.fonte_id is not None]
        assert referenciados and all(c.origem is OrigemCartao.CRIADO for c in referenciados)
        assert all(
            (c.entrada_estudo_em is not None) == (c.situacao in set(SituacaoCartao))
            for c in inseridos
        )
        novos = [c for c in inseridos if c.estado_fsrs is EstadoFsrs.APRENDIZADO]
        assert novos and all(c.ultima_revisao is None and c.estabilidade is None for c in novos)


async def test_a_ordem_de_criacao_e_crescente_com_o_indice_da_lista(
    fabrica_sessoes: FabricaSessoes, conexao: AsyncConnection
) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario_id, materia_id = await _estudante(sessao)
        inseridos = await fab.inserir(
            sessao, usuario_id=usuario_id, materia_id=materia_id, itens=fab.gerar(10), agora=AGORA
        )
        criados = [c.criado_em for c in inseridos]
        assert criados == sorted(criados) and len(set(criados)) == 10
        assert all(c.entrada_estudo_em == c.criado_em for c in inseridos)
        assert criados[-1] <= AGORA


async def test_banco_aceita_limites_exatos_e_um_acima_porque_so_impoe_os_tetos(
    fabrica_sessoes: FabricaSessoes, conexao: AsyncConnection
) -> None:
    """Os limites vigentes (1.000/2.000/1.000) são da aplicação; o banco só impõe os tetos."""
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario_id, materia_id = await _estudante(sessao)
        itens = [
            fab.cartao_no_limite(1000, 2000, 1000),
            fab.cartao_acima_do_limite("frente", 1000, 2000, 1000),
        ]
        inseridos = await fab.inserir(
            sessao, usuario_id=usuario_id, materia_id=materia_id, itens=itens, agora=AGORA
        )
        assert [len(c.frente) for c in inseridos] == [1000, 1001]


# --- Linha de comando ---------------------------------------------------------------------------


@pytest.fixture
def config_cli(configuracao: Configuracao, banco_migrado: None) -> Configuracao:
    """A CLI só roda em desenvolvimento; aponta para o banco de teste."""
    return configuracao.model_copy(update={"app_ambiente": "desenvolvimento"})


async def test_cli_semeia_os_cartoes_na_materia_da_conta_exemplo(
    config_cli: Configuracao, fabrica_real: FabricaSessoes, capsys: pytest.CaptureFixture[str]
) -> None:
    email = f"semeada.{uuid.uuid4().hex[:8]}@exemplo.com"
    async with unidade_de_trabalho(fabrica_real) as sessao:
        usuario_id, materia_id = await _estudante(sessao, email)
        await _fonte(sessao, usuario_id, materia_id)

    codigo = await fab.executar(
        ["--email", email.upper(), "--materia", "biologia", "--quantidade", "120"], config_cli
    )

    assert codigo == 0
    assert "120" in capsys.readouterr().out
    async with unidade_de_trabalho(fabrica_real) as sessao:
        cartoes = (
            (await sessao.execute(select(Cartao).where(Cartao.materia_id == materia_id)))
            .scalars()
            .all()
        )
        assert len(cartoes) == 120
        assert {c.usuario_id for c in cartoes} == {usuario_id}
        assert any(c.fonte_id is not None for c in cartoes), "usa a fonte da matéria, se houver"
        assert {c.situacao for c in cartoes} == set(SituacaoCartao)


async def test_cli_recusa_conta_ou_materia_inexistente_sem_criar_nada(
    config_cli: Configuracao, fabrica_real: FabricaSessoes, capsys: pytest.CaptureFixture[str]
) -> None:
    email = f"vazia.{uuid.uuid4().hex[:8]}@exemplo.com"
    async with unidade_de_trabalho(fabrica_real) as sessao:
        await _estudante(sessao, email)

    sem_conta = await fab.executar(
        ["--email", "ninguem@exemplo.com", "--materia", "Biologia"], config_cli
    )
    sem_materia = await fab.executar(["--email", email, "--materia", "Química"], config_cli)

    assert (sem_conta, sem_materia) == (1, 1)
    erros = capsys.readouterr().err
    assert "conta" in erros and "matéria" in erros
    async with unidade_de_trabalho(fabrica_real) as sessao:
        assert (await sessao.execute(select(func.count()).select_from(Cartao))).scalar_one() == 0
