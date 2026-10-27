"""T008: cursor opaco da listagem (DTEC 034): ida e volta, adulteração e filtros diferentes."""

from __future__ import annotations

import base64
import struct
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.cartoes.cursor import (
    CursorInvalido,
    PosicaoCursor,
    codificar,
    decodificar,
    resumo_dos_filtros,
)

pytestmark = pytest.mark.unit

SEGREDO = b"segredo-de-teste-com-mais-de-32-bytes-0123456789"
MATERIA = uuid.UUID("2b1f6f0e-3c8a-4d2e-9f61-7a0c5d9b8e14")
RESUMO = resumo_dos_filtros(1, MATERIA)
EPOCA = datetime(1970, 1, 1, tzinfo=UTC)
POSICAO = PosicaoCursor(criado_em=datetime(2026, 10, 20, 12, 0, 0, 123456, tzinfo=UTC), id=4242)


def test_ida_e_volta_preserva_a_posicao_com_microssegundos() -> None:
    cursor = codificar(POSICAO, resumo=RESUMO, segredo=SEGREDO)
    assert decodificar(cursor, resumo=RESUMO, segredo=SEGREDO) == POSICAO


@given(
    micros=st.integers(min_value=0, max_value=253_402_300_799_999_999),
    identificador=st.integers(min_value=1, max_value=2**62),
    busca=st.text(max_size=20),
)
def test_ida_e_volta_para_qualquer_posicao(micros: int, identificador: int, busca: str) -> None:
    posicao = PosicaoCursor(criado_em=EPOCA + timedelta(microseconds=micros), id=identificador)
    resumo = resumo_dos_filtros(7, MATERIA, busca=busca)
    assert (
        decodificar(
            codificar(posicao, resumo=resumo, segredo=SEGREDO), resumo=resumo, segredo=SEGREDO
        )
        == posicao
    )


def test_o_cursor_e_texto_url_seguro_curto_e_nao_mostra_a_chave() -> None:
    cursor = codificar(POSICAO, resumo=RESUMO, segredo=SEGREDO)
    assert cursor.isascii() and len(cursor) <= 64
    assert all(c.isalnum() or c in "-_" for c in cursor), "base64url sem preenchimento"
    bruto = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
    micros = (POSICAO.criado_em - EPOCA) // timedelta(microseconds=1)
    claro = struct.pack(">qq", micros, POSICAO.id)
    assert claro not in bruto, "o `id` interno e o instante não saem em claro (só `public_id` sai)"
    assert struct.pack(">q", POSICAO.id) not in bruto


def test_o_cursor_muda_com_a_posicao_e_com_o_resumo() -> None:
    outro = PosicaoCursor(POSICAO.criado_em, POSICAO.id + 1)
    cursor = codificar(POSICAO, resumo=RESUMO, segredo=SEGREDO)
    assert cursor != codificar(outro, resumo=RESUMO, segredo=SEGREDO)
    assert cursor != codificar(
        POSICAO, resumo=resumo_dos_filtros(1, MATERIA, busca="x"), segredo=SEGREDO
    )


def _adulterar(cursor: str, posicao: int) -> str:
    troca = "A" if cursor[posicao] != "A" else "B"
    return cursor[:posicao] + troca + cursor[posicao + 1 :]


@pytest.mark.parametrize("posicao", [0, 5, 20, 21, 30, 42])
def test_cursor_adulterado_em_qualquer_posicao_e_recusado(posicao: int) -> None:
    cursor = codificar(POSICAO, resumo=RESUMO, segredo=SEGREDO)
    assert len(cursor) > posicao
    with pytest.raises(CursorInvalido):
        decodificar(_adulterar(cursor, posicao), resumo=RESUMO, segredo=SEGREDO)


def test_texto_diferente_que_decodifica_para_os_mesmos_bytes_e_recusado() -> None:
    """Os 2 bits sobrando do último caractere são ignorados pelo decodificador; aqui não valem."""
    alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    cursor = codificar(POSICAO, resumo=RESUMO, segredo=SEGREDO)
    indice = alfabeto.index(cursor[-1])
    gemeos = [
        alfabeto[(indice & ~3) | extra] for extra in range(4) if (indice & ~3) | extra != indice
    ]
    assert gemeos
    for gemeo in gemeos:
        assert base64.urlsafe_b64decode(cursor + "=") == base64.urlsafe_b64decode(
            cursor[:-1] + gemeo + "="
        ), "pré-condição: os dois textos têm os mesmos bytes"
        with pytest.raises(CursorInvalido):
            decodificar(cursor[:-1] + gemeo, resumo=RESUMO, segredo=SEGREDO)


def test_alfabeto_padrao_do_base64_nao_vale_no_lugar_do_url_seguro() -> None:
    cursor = codificar(POSICAO, resumo=RESUMO, segredo=SEGREDO)
    padrao = cursor.replace("-", "+").replace("_", "/")
    if padrao == cursor:  # este cursor não usa os dois símbolos: força um com eles
        for numero in range(1, 5000):
            cursor = codificar(
                PosicaoCursor(POSICAO.criado_em, numero), resumo=RESUMO, segredo=SEGREDO
            )
            padrao = cursor.replace("-", "+").replace("_", "/")
            if padrao != cursor:
                break
    assert padrao != cursor
    with pytest.raises(CursorInvalido):
        decodificar(padrao, resumo=RESUMO, segredo=SEGREDO)


@pytest.mark.parametrize(
    "cursor",
    [
        "",
        " ",
        "!!!",
        "abc",
        "====",
        "áéí",
        "a" * 5000,
        "\n",
        "+/+/+/+/+/+/+/+/+/+/+/+/+/+/+/+/+/+/+/+/+/+",  # alfabeto padrão, não o URL-seguro
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",  # base64 válido, selo errado
        "😀",
    ],
)
def test_cursor_malformado_e_recusado(cursor: str) -> None:
    with pytest.raises(CursorInvalido):
        decodificar(cursor, resumo=RESUMO, segredo=SEGREDO)


def test_cursor_truncado_ou_com_sobra_e_recusado() -> None:
    cursor = codificar(POSICAO, resumo=RESUMO, segredo=SEGREDO)
    for alterado in (cursor[:-1], cursor[:-4], cursor + "A", cursor + "AAAA", cursor[1:]):
        with pytest.raises(CursorInvalido):
            decodificar(alterado, resumo=RESUMO, segredo=SEGREDO)


@given(st.text(max_size=200))
def test_texto_qualquer_nunca_passa_por_cursor_nem_levanta_outro_erro(texto: str) -> None:
    with pytest.raises(CursorInvalido):
        decodificar(texto, resumo=RESUMO, segredo=SEGREDO)


@pytest.mark.parametrize(
    "outro",
    [
        resumo_dos_filtros(1, MATERIA, busca="celula"),
        resumo_dos_filtros(1, MATERIA, situacao="suspenso"),
        resumo_dos_filtros(1, MATERIA, origem="criado"),
        resumo_dos_filtros(2, MATERIA),  # outra conta
        resumo_dos_filtros(1, uuid.UUID(int=1)),  # outra matéria
    ],
    ids=["busca", "situacao", "origem", "outra-conta", "outra-materia"],
)
def test_cursor_de_outros_filtros_conta_ou_materia_e_recusado(outro: str) -> None:
    cursor = codificar(POSICAO, resumo=outro, segredo=SEGREDO)
    with pytest.raises(CursorInvalido):
        decodificar(cursor, resumo=RESUMO, segredo=SEGREDO)


def test_cursor_de_outro_segredo_e_recusado() -> None:
    cursor = codificar(POSICAO, resumo=RESUMO, segredo=b"outro-segredo-com-mais-de-32-bytes!!!!!")
    with pytest.raises(CursorInvalido):
        decodificar(cursor, resumo=RESUMO, segredo=SEGREDO)


@pytest.mark.parametrize("identificador", [0, -3])
def test_nao_se_codifica_posicao_invalida(identificador: int) -> None:
    with pytest.raises(ValueError, match="posição"):
        codificar(PosicaoCursor(POSICAO.criado_em, identificador), resumo=RESUMO, segredo=SEGREDO)
    with pytest.raises(ValueError, match="posição"):
        codificar(
            PosicaoCursor(datetime(2026, 10, 20, 12, 0), 1),  # noqa: DTZ001
            resumo=RESUMO,
            segredo=SEGREDO,
        )


# --- Resumo dos filtros --------------------------------------------------------------------------


def test_resumo_depende_de_conta_materia_e_de_cada_filtro() -> None:
    base = resumo_dos_filtros(1, MATERIA)
    assert base == resumo_dos_filtros(1, MATERIA), "determinístico"
    variacoes = {
        resumo_dos_filtros(2, MATERIA),
        resumo_dos_filtros(1, uuid.UUID(int=9)),
        resumo_dos_filtros(1, MATERIA, busca="a"),
        resumo_dos_filtros(1, MATERIA, situacao="ativo"),
        resumo_dos_filtros(1, MATERIA, origem="editado"),
    }
    assert len(variacoes | {base}) == 6


def test_resumo_nao_confunde_valores_com_separadores_parecidos() -> None:
    assert resumo_dos_filtros(1, MATERIA, busca="a|ativo") != resumo_dos_filtros(
        1, MATERIA, busca="a", situacao="ativo"
    )
    assert resumo_dos_filtros(1, MATERIA, busca="") == resumo_dos_filtros(1, MATERIA, busca=None)
