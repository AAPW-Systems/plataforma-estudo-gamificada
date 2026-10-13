"""Cálculo dos bloqueios por tentativas (RQ-003, DTEC 020), em funções puras.

O bloqueio nasce na L-ésima falha dentro da janela e dura `bloqueio` a partir dela.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.identidade import dominio

pytestmark = pytest.mark.unit

T0 = datetime(2026, 10, 13, 12, 0, tzinfo=UTC)
JANELA = timedelta(minutes=15)
BLOQUEIO = timedelta(minutes=15)


def _falhas(*minutos: float) -> list[datetime]:
    return [T0 + timedelta(minutes=m) for m in minutos]


def test_ate_quatro_falhas_nao_bloqueiam() -> None:
    assert (
        dominio.bloqueado_ate(_falhas(0, 1, 2, 3), limite=5, janela=JANELA, bloqueio=BLOQUEIO)
        is None
    )


def test_cinco_falhas_na_janela_bloqueiam_por_quinze_minutos_a_partir_da_quinta() -> None:
    ate = dominio.bloqueado_ate(_falhas(0, 1, 2, 3, 4), limite=5, janela=JANELA, bloqueio=BLOQUEIO)
    assert ate == T0 + timedelta(minutes=19)


def test_falhas_espalhadas_por_mais_que_a_janela_nao_bloqueiam() -> None:
    assert (
        dominio.bloqueado_ate(_falhas(0, 4, 8, 12, 16), limite=5, janela=JANELA, bloqueio=BLOQUEIO)
        is None
    )


def test_cinco_falhas_exatamente_na_borda_da_janela_nao_bloqueiam() -> None:
    # Quinta falha 15 minutos depois da primeira: a primeira já saiu da janela.
    assert (
        dominio.bloqueado_ate(_falhas(0, 3, 6, 9, 15), limite=5, janela=JANELA, bloqueio=BLOQUEIO)
        is None
    )


def test_bloqueio_pode_durar_mais_que_a_janela() -> None:
    ate = dominio.bloqueado_ate(
        _falhas(0, 1, 2, 3, 4), limite=5, janela=JANELA, bloqueio=timedelta(minutes=60)
    )
    assert ate == T0 + timedelta(minutes=64)


def test_novo_bloqueio_estende_o_anterior() -> None:
    falhas = _falhas(0, 1, 2, 3, 4, 20, 21, 22, 23, 24)
    ate = dominio.bloqueado_ate(falhas, limite=5, janela=JANELA, bloqueio=BLOQUEIO)
    assert ate == T0 + timedelta(minutes=39)


def test_entrada_desordenada_e_aceita() -> None:
    falhas = _falhas(4, 0, 3, 1, 2)
    assert dominio.bloqueado_ate(
        falhas, limite=5, janela=JANELA, bloqueio=BLOQUEIO
    ) == T0 + timedelta(minutes=19)


def test_limite_de_um_bloqueia_na_primeira_falha() -> None:
    assert dominio.bloqueado_ate(_falhas(0), limite=1, janela=JANELA, bloqueio=BLOQUEIO) == (
        T0 + BLOQUEIO
    )


@given(st.lists(st.integers(min_value=0, max_value=600), max_size=40), st.integers(1, 10))
def test_bloqueio_nunca_ocorre_com_menos_falhas_que_o_limite(
    minutos: list[int], limite: int
) -> None:
    ate = dominio.bloqueado_ate(
        [T0 + timedelta(minutes=m) for m in minutos],
        limite=limite,
        janela=JANELA,
        bloqueio=BLOQUEIO,
    )
    if len(minutos) < limite:
        assert ate is None
    elif ate is not None:
        assert ate > T0


# --- Cadastros por endereço (10 por hora) -------------------------------------------------

HORA = timedelta(hours=1)


def test_cadastros_abaixo_do_limite_estao_liberados() -> None:
    cadastros = [T0 + timedelta(minutes=m) for m in range(9)]
    assert (
        dominio.liberado_cadastro_em(
            cadastros, agora=T0 + timedelta(minutes=10), limite=10, janela=HORA
        )
        is None
    )


def test_decimo_cadastro_na_hora_bloqueia_ate_o_mais_antigo_sair_da_janela() -> None:
    cadastros = [T0 + timedelta(minutes=m) for m in range(10)]
    liberado = dominio.liberado_cadastro_em(
        cadastros, agora=T0 + timedelta(minutes=30), limite=10, janela=HORA
    )
    assert liberado == T0 + HORA


def test_excesso_de_cadastros_espera_o_suficiente_para_voltar_ao_limite() -> None:
    cadastros = [T0 + timedelta(minutes=m) for m in range(12)]
    liberado = dominio.liberado_cadastro_em(
        cadastros, agora=T0 + timedelta(minutes=30), limite=10, janela=HORA
    )
    assert liberado == T0 + timedelta(minutes=2) + HORA


def test_cadastros_fora_da_janela_nao_contam() -> None:
    cadastros = [T0 - timedelta(hours=2) for _ in range(20)]
    assert dominio.liberado_cadastro_em(cadastros, agora=T0, limite=10, janela=HORA) is None


# --- Chave da conta (HMAC) ----------------------------------------------------------------


def test_chave_da_conta_e_hmac_sha256_do_email_normalizado() -> None:
    segredo = b"segredo-de-teste-com-mais-de-32-bytes-0123"
    chave = dominio.chave_da_conta(segredo, "ana@exemplo.com")
    assert len(chave) == 32
    assert chave == dominio.chave_da_conta(segredo, "ana@exemplo.com")
    assert chave != dominio.chave_da_conta(segredo, "bia@exemplo.com")
    assert chave != dominio.chave_da_conta(
        b"outro-segredo-com-mais-de-32-bytes-9876", "ana@exemplo.com"
    )
    esperado = hmac.new(segredo, b"chave-conta-v1|ana@exemplo.com", hashlib.sha256).digest()
    assert chave == esperado


def test_chave_da_conta_nao_contem_o_email_em_claro() -> None:
    chave = dominio.chave_da_conta(b"s" * 40, "ana@exemplo.com")
    assert b"ana" not in chave and b"exemplo" not in chave


def test_normalizar_email_de_entrada_trata_malformado_sem_erro() -> None:
    assert dominio.normalizar_email_de_entrada("  ANA@Exemplo.com ") == "ana@exemplo.com"
    assert dominio.normalizar_email_de_entrada(" Isso Nao E Email ") == "isso nao e email"
