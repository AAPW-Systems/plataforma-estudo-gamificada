"""T021: a edição nunca escreve nas colunas do FSRS (CS-002, RF-005, RN-26; DTEC 037).

Escritas disjuntas por coluna: a edição grava só conteúdo, origem e `atualizado_em`; a revisão
(005) só o agendamento. As duas, em paralelo, sobrevivem.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import timedelta
from typing import Any

import psycopg
import pytest
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.cartoes.modelos import Cartao, EstadoFsrs, OrigemCartao
from app.cartoes.servicos import ServicoCartoes
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao
from app.nucleo.relogio import RelogioControlavel
from tests import fabricas_cartoes as fab
from tests.apoio_cartoes import AGORA, semear_estudante

pytestmark = pytest.mark.integration

COLUNAS_FSRS = (
    "estado_fsrs",
    "passo",
    "estabilidade",
    "dificuldade",
    "vencimento",
    "ultima_revisao",
)
# Colunas fixas deste módulo: nada vem de fora.
_CONSULTA_LINHA = (
    "SELECT frente, verso, explicacao, origem::text, atualizado_em, xmin::text, "  # noqa: S608
    + ", ".join(COLUNAS_FSRS)
    + " FROM cartoes WHERE id = :id"
)
USUARIO_PUBLICO = "00000000-0000-4000-8000-0000000000aa"


async def _linha(fabrica: FabricaSessoes, cartao_id: int) -> dict[str, Any]:
    async with unidade_de_trabalho(fabrica) as sessao:
        resultado = await sessao.execute(
            text(_CONSULTA_LINHA),
            {"id": cartao_id},
        )
        return dict(resultado.mappings().one())


def _fsrs(linha: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(linha[coluna] for coluna in COLUNAS_FSRS)


async def _semear(
    fabrica: FabricaSessoes, estado: EstadoFsrs, origem: OrigemCartao = OrigemCartao.CRIADO
) -> tuple[int, Cartao]:
    itens = [c for c in fab.gerar(12) if c.estado_fsrs is estado][:1]
    async with unidade_de_trabalho(fabrica) as sessao:
        usuario, materia = await semear_estudante(sessao)
        (cartao,) = await fab.inserir(
            sessao,
            usuario_id=usuario.id,
            materia_id=materia.id,
            # Com explicação, para que removê-la seja uma mudança efetiva.
            itens=[
                replace(
                    itens[0],
                    origem=origem,
                    com_referencia=False,
                    explicacao=itens[0].explicacao or "Explicação existente",
                )
            ],
            agora=AGORA,
        )
        return usuario.id, cartao


def _servico(fabrica: FabricaSessoes, configuracao: Configuracao) -> ServicoCartoes:
    return ServicoCartoes(fabrica, configuracao, RelogioControlavel(AGORA + timedelta(days=3)))


@pytest.mark.parametrize("estado", list(EstadoFsrs))
@pytest.mark.parametrize(
    "alteracoes",
    [{"frente": "Nova frente"}, {"verso": "Novo verso"}, {"explicacao": None}, {"explicacao": "x"}],
    ids=["frente", "verso", "remove-explicacao", "explicacao"],
)
async def test_todas_as_colunas_do_fsrs_ficam_iguais_depois_da_edicao(
    fabrica_sessoes: FabricaSessoes,
    configuracao: Configuracao,
    estado: EstadoFsrs,
    alteracoes: dict[str, str | None],
) -> None:
    usuario_id, cartao = await _semear(fabrica_sessoes, estado)
    antes = await _linha(fabrica_sessoes, cartao.id)

    await _servico(fabrica_sessoes, configuracao).editar(
        usuario_id=usuario_id,
        usuario_public_id=USUARIO_PUBLICO,
        public_id=cartao.public_id,
        alteracoes=alteracoes,
    )

    depois = await _linha(fabrica_sessoes, cartao.id)
    assert _fsrs(depois) == _fsrs(antes)
    assert depois["atualizado_em"] == AGORA + timedelta(days=3)


async def test_edicao_sem_mudanca_nao_escreve_nada(
    fabrica_sessoes: FabricaSessoes, configuracao: Configuracao
) -> None:
    """US2-3: nem `atualizado_em` nem a origem mudam; a linha nem é regravada (`xmin`)."""
    usuario_id, cartao = await _semear(
        fabrica_sessoes, EstadoFsrs.REVISAO, OrigemCartao.GERADO_VERIFICADO
    )
    antes = await _linha(fabrica_sessoes, cartao.id)

    linha = await _servico(fabrica_sessoes, configuracao).editar(
        usuario_id=usuario_id,
        usuario_public_id=USUARIO_PUBLICO,
        public_id=cartao.public_id,
        alteracoes={"frente": f"  {cartao.frente}\r\n", "explicacao": cartao.explicacao or ""},
    )

    depois = await _linha(fabrica_sessoes, cartao.id)
    assert depois == antes
    assert linha.cartao.origem is OrigemCartao.GERADO_VERIFICADO


async def test_o_update_da_edicao_nao_cita_nenhuma_coluna_do_fsrs(
    fabrica_sessoes: FabricaSessoes, configuracao: Configuracao, conexao: AsyncConnection
) -> None:
    usuario_id, cartao = await _semear(fabrica_sessoes, EstadoFsrs.REVISAO)
    comandos: list[str] = []

    def capturar(_conn: object, _cursor: object, statement: str, *_resto: object) -> None:
        if statement.lstrip().upper().startswith("UPDATE"):
            comandos.append(statement)

    event.listen(conexao.sync_engine, "before_cursor_execute", capturar)
    try:
        await _servico(fabrica_sessoes, configuracao).editar(
            usuario_id=usuario_id,
            usuario_public_id=USUARIO_PUBLICO,
            public_id=cartao.public_id,
            alteracoes={"verso": "Outro verso"},
        )
    finally:
        event.remove(conexao.sync_engine, "before_cursor_execute", capturar)
    assert len(comandos) == 1
    atribuicoes = comandos[0].split(" SET ", 1)[1].split(" WHERE ", 1)[0]
    for coluna in COLUNAS_FSRS:
        assert coluna not in atribuicoes, comandos[0]
    for coluna in ("frente", "verso", "explicacao", "origem", "atualizado_em"):
        assert coluna in atribuicoes


async def test_agendamento_e_edicao_em_paralelo_as_duas_sobrevivem(
    fabrica_real: FabricaSessoes, configuracao: Configuracao
) -> None:
    """Uma revisão simulada (conexão separada) segura a linha; a edição espera e não a desfaz."""
    usuario_id, cartao = await _semear(fabrica_real, EstadoFsrs.REVISAO)
    novo_vencimento = AGORA + timedelta(days=40)

    async with await psycopg.AsyncConnection.connect(configuracao.conninfo()) as revisao:
        await revisao.execute(
            "UPDATE cartoes SET estabilidade = 33.5, dificuldade = 4.2, vencimento = %s, "
            "ultima_revisao = %s WHERE id = %s",
            (novo_vencimento, AGORA, cartao.id),
        )
        edicao = asyncio.create_task(
            _servico(fabrica_real, configuracao).editar(
                usuario_id=usuario_id,
                usuario_public_id=USUARIO_PUBLICO,
                public_id=cartao.public_id,
                alteracoes={"frente": "Frente editada durante a revisão"},
            )
        )
        await asyncio.sleep(0.3)
        assert not edicao.done(), "a edição espera a revisão liberar a linha"
        await revisao.commit()
    await edicao

    depois = await _linha(fabrica_real, cartao.id)
    assert depois["frente"] == "Frente editada durante a revisão"
    assert (depois["estabilidade"], depois["dificuldade"]) == (33.5, 4.2)
    assert depois["vencimento"] == novo_vencimento


async def test_duas_edicoes_simultaneas_de_campos_diferentes_nao_se_desfazem(
    fabrica_real: FabricaSessoes, configuracao: Configuracao
) -> None:
    """A edição lê o cartão com `FOR UPDATE`: sem a trava, leria a frente antiga e a regravaria."""
    usuario_id, cartao = await _semear(fabrica_real, EstadoFsrs.APRENDIZADO)

    async with await psycopg.AsyncConnection.connect(configuracao.conninfo()) as outra_edicao:
        await outra_edicao.execute(
            "UPDATE cartoes SET frente = 'Frente da outra aba' WHERE id = %s", (cartao.id,)
        )
        edicao = asyncio.create_task(
            _servico(fabrica_real, configuracao).editar(
                usuario_id=usuario_id,
                usuario_public_id=USUARIO_PUBLICO,
                public_id=cartao.public_id,
                alteracoes={"verso": "Verso desta aba"},
            )
        )
        await asyncio.sleep(0.3)
        assert not edicao.done(), "a leitura espera a outra edição liberar a linha"
        await outra_edicao.commit()
    await edicao

    depois = await _linha(fabrica_real, cartao.id)
    assert (depois["frente"], depois["verso"]) == ("Frente da outra aba", "Verso desta aba")


async def test_revisao_depois_da_edicao_tambem_preserva_a_edicao(
    fabrica_real: FabricaSessoes, configuracao: Configuracao
) -> None:
    usuario_id, cartao = await _semear(fabrica_real, EstadoFsrs.APRENDIZADO)
    await _servico(fabrica_real, configuracao).editar(
        usuario_id=usuario_id,
        usuario_public_id=USUARIO_PUBLICO,
        public_id=cartao.public_id,
        alteracoes={"verso": "Verso editado"},
    )
    async with await psycopg.AsyncConnection.connect(configuracao.conninfo()) as revisao:
        await revisao.execute(
            "UPDATE cartoes SET estado_fsrs = 'revisao', passo = NULL, estabilidade = 3.1, "
            "dificuldade = 5.0 WHERE id = %s",
            (cartao.id,),
        )
        await revisao.commit()
    depois = await _linha(fabrica_real, cartao.id)
    assert depois["verso"] == "Verso editado"
    assert (depois["estado_fsrs"], depois["estabilidade"]) == ("revisao", 3.1)
