"""Registro de participantes da exclusão de fontes e matérias (DTEC 027, T005)."""

from __future__ import annotations

from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.participantes_acervo import ContagensAcervo, ModoCartoes, RegistroAcervo
from tests.participantes_falsos import ParticipanteFalso

pytestmark = pytest.mark.unit

SESSAO = cast(AsyncSession, object())


def test_soma_contagens_com_campos_ausentes_valendo_zero() -> None:
    a = ContagensAcervo(fontes=2)
    b = ContagensAcervo(cartoes_ativos=3, cartoes_suspensos=1, cartoes_referencia=4)
    c = ContagensAcervo(cartoes_aguardando_revisao=5, cartoes_gerados_aceitos=6)
    total = a + b + c
    assert total == ContagensAcervo(
        fontes=2,
        cartoes_ativos=3,
        cartoes_suspensos=1,
        cartoes_aguardando_revisao=5,
        cartoes_gerados_aceitos=6,
        cartoes_referencia=4,
    )
    assert ContagensAcervo() == ContagensAcervo(0, 0, 0, 0, 0, 0)


def test_soma_contagens_nao_altera_os_operandos() -> None:
    a = ContagensAcervo(fontes=1)
    _ = a + ContagensAcervo(fontes=2)
    assert a.fontes == 1


def test_o_modo_dos_cartoes_tem_so_manter_e_excluir() -> None:
    assert {m.value for m in ModoCartoes} == {"manter", "excluir"}


async def test_contar_por_materia_soma_os_participantes_e_materias_ausentes_valem_zero() -> None:
    registro = RegistroAcervo()
    registro.registrar(
        100, "cartoes", ParticipanteFalso(por_materia={1: ContagensAcervo(cartoes_ativos=3)})
    )
    registro.registrar(
        900,
        "fontes",
        ParticipanteFalso(por_materia={1: ContagensAcervo(fontes=2), 2: ContagensAcervo(fontes=1)}),
    )

    contagens = await registro.contar_por_materia(SESSAO, 7)

    assert contagens[1] == ContagensAcervo(fontes=2, cartoes_ativos=3)
    assert contagens[2] == ContagensAcervo(fontes=1)
    assert contagens.get(3, ContagensAcervo()) == ContagensAcervo()


async def test_impacto_da_fonte_soma_os_participantes() -> None:
    registro = RegistroAcervo()
    registro.registrar(
        100,
        "cartoes",
        ParticipanteFalso(
            impacto=ContagensAcervo(cartoes_gerados_aceitos=3, cartoes_aguardando_revisao=2)
        ),
    )
    registro.registrar(
        110, "extra", ParticipanteFalso(impacto=ContagensAcervo(cartoes_referencia=1))
    )
    assert await registro.impacto_fonte(SESSAO, 7, 11) == ContagensAcervo(
        cartoes_gerados_aceitos=3, cartoes_aguardando_revisao=2, cartoes_referencia=1
    )


async def test_exclusao_chama_os_participantes_por_prioridade_na_sessao_recebida() -> None:
    chamadas: list[tuple[str, str, object]] = []
    registro = RegistroAcervo()
    fontes = ParticipanteFalso(nome="fontes", chamadas=chamadas)
    cartoes = ParticipanteFalso(nome="cartoes", chamadas=chamadas)
    geracoes = ParticipanteFalso(nome="geracoes", chamadas=chamadas)
    registro.registrar(900, "fontes", fontes)
    registro.registrar(100, "cartoes", cartoes)
    registro.registrar(200, "geracoes", geracoes)

    await registro.ao_excluir_fonte(SESSAO, 7, 11, ModoCartoes.MANTER)
    await registro.ao_excluir_materia(SESSAO, 7, 5)

    assert [(nome, acao) for nome, acao, _ in chamadas] == [
        ("cartoes", "fonte"),
        ("geracoes", "fonte"),
        ("fontes", "fonte"),
        ("cartoes", "materia"),
        ("geracoes", "materia"),
        ("fontes", "materia"),
    ]
    # Toda chamada recebeu a mesma sessão (a transação de quem chama).
    assert all(sessao is SESSAO for _, _, sessao in chamadas)
    assert cartoes.exclusoes_de_fonte == [(7, 11, ModoCartoes.MANTER)]
    assert cartoes.exclusoes_de_materia == [(7, 5)]


def test_nome_ou_prioridade_repetidos_sao_recusados() -> None:
    registro = RegistroAcervo()
    participante = ParticipanteFalso()
    registro.registrar(100, "cartoes", participante)
    registro.registrar(100, "cartoes", participante)  # mesmo participante: idempotente
    with pytest.raises(ValueError, match="já registrado"):
        registro.registrar(200, "cartoes", ParticipanteFalso())
    with pytest.raises(ValueError, match="prioridade 100"):
        registro.registrar(100, "outro", ParticipanteFalso())


def test_remover_desfaz_o_registro_para_os_testes() -> None:
    registro = RegistroAcervo()
    registro.registrar(100, "x", ParticipanteFalso())
    registro.remover("x")
    registro.remover("x")  # idempotente
    assert registro.nomes() == []
