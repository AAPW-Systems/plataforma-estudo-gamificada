"""Regras puras das matérias (RF-001; T014): normalização, limites e confirmação pelo nome."""

from __future__ import annotations

import unicodedata

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.materias import dominio
from app.nucleo.participantes_acervo import ContagensAcervo
from app.nucleo.texto import ValorInvalido

pytestmark = pytest.mark.unit


def test_nome_valido_e_devolvido_normalizado() -> None:
    assert dominio.validar_nome("  Biologia  ") == "Biologia"


@pytest.mark.parametrize("tamanho", [1, 2, 59, 60])
def test_nomes_de_1_a_60_caracteres_sao_aceitos(tamanho: int) -> None:
    assert len(dominio.validar_nome("a" * tamanho)) == tamanho


@pytest.mark.parametrize("nome", ["", " ", "   \t ", " ", "​", "​​"])
def test_nome_vazio_ou_sem_caractere_visivel_e_recusado(nome: str) -> None:
    with pytest.raises(ValorInvalido, match="Informe o nome"):
        dominio.validar_nome(nome)


def test_nome_com_61_caracteres_e_recusado() -> None:
    with pytest.raises(ValorInvalido, match="no máximo 60"):
        dominio.validar_nome("a" * 61)


def test_o_limite_conta_depois_de_remover_os_espacos_das_extremidades() -> None:
    assert dominio.validar_nome("  " + "a" * 60 + "  ") == "a" * 60


def test_o_limite_conta_caracteres_depois_do_nfc_e_nao_pontos_de_codigo_soltos() -> None:
    decomposto = unicodedata.normalize("NFD", "é" * 60)
    assert len(decomposto) == 120
    nome = dominio.validar_nome(decomposto)
    assert nome == "é" * 60
    assert unicodedata.is_normalized("NFC", nome)


@pytest.mark.parametrize(
    "nome",
    [
        "Bio\nlogia",
        "Bio\tlogia",
        "Bio\x00logia",
        "Bio\x7flogia",
        "Bio\x85logia",  # controle C1
        "Bio‮logia",  # inversão de direção
        "Bio⁦logia",  # isolamento de direção
        "Biologia",  # uso privado
        "Bio\ud800logia",  # substituto isolado (não codifica em UTF-8)
    ],
)
def test_caracteres_de_controle_direcao_e_invalidos_sao_recusados(nome: str) -> None:
    with pytest.raises(ValorInvalido, match="caracteres que não podem"):
        dominio.validar_nome(nome)


@pytest.mark.parametrize("nome", ["Cálculo II", "日本語", "Português 📚", "Matemática & Lógica"])
def test_letras_acentos_e_emoji_sao_aceitos(nome: str) -> None:
    assert dominio.validar_nome(nome) == nome


def test_marcas_de_direcao_de_alfabetos_rtl_sao_aceitas() -> None:
    assert dominio.validar_nome("עברית‏") == "עברית‏"


@given(st.text(max_size=200))
def test_validar_nome_e_total_e_idempotente(texto: str) -> None:
    try:
        nome = dominio.validar_nome(texto)
    except ValorInvalido:
        return
    assert 1 <= len(nome) <= 60
    assert nome == nome.strip()
    assert unicodedata.is_normalized("NFC", nome)
    assert dominio.validar_nome(nome) == nome
    nome.encode("utf-8")  # sempre codificável


# --- Confirmação da exclusão pelo nome (RF-011) -------------------------------------------------


def test_confirmacao_exata_confere() -> None:
    assert dominio.confirmacao_confere("Biologia", "Biologia")


def test_confirmacao_ignora_espacos_nas_extremidades() -> None:
    assert dominio.confirmacao_confere("  Biologia\t", "Biologia")


def test_confirmacao_aceita_forma_decomposta_unicode() -> None:
    assert dominio.confirmacao_confere(unicodedata.normalize("NFD", "Física"), "Física")


@pytest.mark.parametrize("digitado", ["biologia", "BIOLOGIA", "Biologi", "Biologia 2", ""])
def test_confirmacao_diferencia_caixa_e_exige_o_nome_inteiro(digitado: str) -> None:
    assert not dominio.confirmacao_confere(digitado, "Biologia")


def test_confirmacao_nao_aceita_espacos_internos_diferentes() -> None:
    assert not dominio.confirmacao_confere("Cálculo  II", "Cálculo II")


# --- Impacto da exclusão da matéria (DTEC 027 emenda, DTEC 031) ---------------------------------


def test_impacto_soma_ativos_e_suspensos_e_mantem_fontes_e_aguardando() -> None:
    impacto = dominio.impacto_da_materia(
        ContagensAcervo(
            fontes=2,
            cartoes_ativos=5,
            cartoes_suspensos=2,
            cartoes_aguardando_revisao=3,
            cartoes_gerados_aceitos=4,  # afetados na exclusão da fonte, não entram na da matéria
            cartoes_referencia=1,
        )
    )
    assert impacto == dominio.ImpactoMateria(
        fontes=2, cartoes_ativos=7, cartoes_aguardando_revisao=3
    )


def test_impacto_de_materia_vazia_vale_zero_e_compara_por_valor() -> None:
    assert dominio.impacto_da_materia(ContagensAcervo()) == dominio.ImpactoMateria(0, 0, 0)
    assert dominio.ImpactoMateria(1, 2, 3) != dominio.ImpactoMateria(1, 2, 4)
