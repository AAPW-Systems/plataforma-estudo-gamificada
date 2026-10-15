"""Hifenização desfeita logo depois da extração do PDF (DTEC 029, emenda de 15/10/2026)."""

from __future__ import annotations

import re

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.fontes.extracao import desfazer_hifenizacao

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("uni-\ndade", "unidade"),
        (
            "A organização celular possui uni-\ndade em todos os seres.",
            "A organização celular possui unidade em todos os seres.",
        ),
        ("uni­\ndade", "unidade"),  # hífen suave
        ("uni‐\ndade", "unidade"),  # hífen Unicode
        ("uni‑\ndade", "unidade"),  # hífen sem quebra
        ("uni- \n dade", "unidade"),  # espaços em volta da quebra
        ("coração-\nzinho", "coraçãozinho"),  # letras acentuadas
        ("cé-\nlula e orga-\nnela", "célula e organela"),  # várias na mesma página
    ],
)
def test_junta_a_palavra_quebrada_no_fim_da_linha(entrada: str, esperado: str) -> None:
    assert desfazer_hifenizacao(entrada) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "Rio-\nGrande",  # a próxima linha começa em maiúscula: nome próprio composto
        "COVID-\n19",  # a próxima linha não começa em letra minúscula
        "2020-\nabril",  # o hífen não vem depois de letra
        "palavra-\n\nOutra",  # fim de parágrafo: há linha em branco
        "- item da lista\ncontinua",  # hífen no começo da linha
        "ida e volta - \nvolta",  # travessão solto entre espaços
        "sem hífen\nnem quebra",
        "tudo-junto na mesma linha",
        "",
    ],
)
def test_nao_mexe_no_que_nao_e_palavra_quebrada(texto: str) -> None:
    assert desfazer_hifenizacao(texto) == texto


def test_limite_conhecido_composto_com_hifen_no_fim_da_linha_tambem_e_juntado() -> None:
    """Caracterização: sem dicionário, "guarda-\\nchuva" vira "guardachuva".

    É o custo da regra simples escolhida por Artur Lins em 15/10/2026: texto citado com a
    palavra inteira vale mais que preservar o hífen de compostos quebrados na linha.
    """
    assert desfazer_hifenizacao("guarda-\nchuva") == "guardachuva"


def test_so_a_quebra_de_linha_e_o_hifen_saem() -> None:
    assert desfazer_hifenizacao("a\nuni-\ndade\nb") == "a\nunidade\nb"


@given(st.text(max_size=300))
def test_e_idempotente_e_nunca_aumenta_o_texto(texto: str) -> None:
    uma_vez = desfazer_hifenizacao(texto)
    assert desfazer_hifenizacao(uma_vez) == uma_vez
    assert len(uma_vez) <= len(texto)


@given(st.text(alphabet=st.characters(blacklist_characters="-­‐‑"), max_size=300))
def test_sem_hifen_o_texto_nao_muda(texto: str) -> None:
    assert desfazer_hifenizacao(texto) == texto


@given(st.text(max_size=300))
def test_nao_sobra_palavra_quebrada(texto: str) -> None:
    resultado = desfazer_hifenizacao(texto)
    assert not re.search(r"[^\W\d_][-­‐‑][ \t]*\n[ \t]*[a-zà-öø-ÿ]", resultado)
