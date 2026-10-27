"""T020: mudança efetiva, regra de origem e validação parcial da edição (RF-005, RF-006, US2-3).

Regras puras (DTEC 036 a 038), reutilizadas pela 004 no "editar e aceitar".
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.cartoes.dominio import (
    LimitesTexto,
    TextoCartao,
    TextoInvalido,
    houve_mudanca,
    origem_apos_edicao,
    validar_edicao,
    validar_limites,
)
from app.cartoes.modelos import OrigemCartao

pytestmark = pytest.mark.unit

LIMITES = LimitesTexto(frente=1000, verso=2000, explicacao=1000)
ATUAL = TextoCartao("Qual organela produz ATP?", "A mitocôndria.", "Linha 1\nLinha 2")


# --- houve_mudanca ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "alteracoes",
    [
        {"frente": "  Qual organela produz ATP?  "},  # só espaços nas extremidades
        {"frente": "Qual organela produz ATP?\r\n"},
        {"explicacao": "Linha 1\r\nLinha 2"},  # \r\n no lugar de \n
        {"explicacao": "Linha 1\rLinha 2"},
        {"verso": "A mitocôndria."},  # mesma letra, forma decomposta (NFC)
        {"verso": "A mitocôndria.\x00"},  # controle removido
        {},
        {"frente": ATUAL.frente, "verso": ATUAL.verso, "explicacao": ATUAL.explicacao},
    ],
    ids=[
        "espacos-nas-pontas",
        "crlf-no-fim",
        "crlf-no-meio",
        "cr-no-meio",
        "nfd",
        "controle",
        "nada",
        "tudo-igual",
    ],
)
def test_texto_igual_depois_da_normalizacao_nao_e_mudanca(alteracoes: dict[str, str]) -> None:
    novo = validar_edicao(ATUAL, alteracoes, LIMITES)
    assert novo == ATUAL
    assert houve_mudanca(ATUAL, novo) is False


@pytest.mark.parametrize("vazia", ["", "   ", None, "\n\n", "​"])
def test_explicacao_vazia_e_nula_sao_iguais(vazia: str | None) -> None:
    sem = TextoCartao("f", "v", None)
    assert houve_mudanca(sem, validar_edicao(sem, {"explicacao": vazia}, LIMITES)) is False


@pytest.mark.parametrize(
    ("alteracoes", "esperado"),
    [
        (
            {"frente": "Outra pergunta"},
            TextoCartao("Outra pergunta", ATUAL.verso, ATUAL.explicacao),
        ),
        ({"verso": "Mitocôndria"}, TextoCartao(ATUAL.frente, "Mitocôndria", ATUAL.explicacao)),
        ({"explicacao": None}, TextoCartao(ATUAL.frente, ATUAL.verso, None)),
        ({"explicacao": ""}, TextoCartao(ATUAL.frente, ATUAL.verso, None)),
        ({"explicacao": "Nova"}, TextoCartao(ATUAL.frente, ATUAL.verso, "Nova")),
        ({"frente": "Qual organela produz ATP? "}, ATUAL),
        (
            {"frente": "qual organela produz ATP?"},
            TextoCartao("qual organela produz ATP?", ATUAL.verso, ATUAL.explicacao),
        ),
    ],
    ids=[
        "frente",
        "verso",
        "remove-com-nulo",
        "remove-com-vazio",
        "explicacao",
        "so-pontas",
        "caixa",
    ],
)
def test_edicao_parcial_muda_so_o_campo_enviado(
    alteracoes: dict[str, str | None], esperado: TextoCartao
) -> None:
    novo = validar_edicao(ATUAL, alteracoes, LIMITES)
    assert novo == esperado
    assert houve_mudanca(ATUAL, novo) is (esperado != ATUAL)


def test_caixa_diferente_e_mudanca() -> None:
    """A comparação é exata depois da normalização: maiúsculas contam (o estudante quis mudar)."""
    assert houve_mudanca(ATUAL, TextoCartao(ATUAL.frente.upper(), ATUAL.verso, ATUAL.explicacao))


@given(st.text(max_size=200), st.text(max_size=200))
def test_mudanca_e_simetrica_e_reflexiva(frente: str, verso: str) -> None:
    try:
        texto = validar_limites(frente or "f", verso or "v", None, LIMITES)
    except TextoInvalido:
        return
    assert houve_mudanca(texto, texto) is False
    outro = TextoCartao(texto.frente + "x", texto.verso, texto.explicacao)
    assert houve_mudanca(texto, outro) is houve_mudanca(outro, texto) is True


# --- validar_edicao: limites só nos campos enviados ------------------------------------------


def test_valida_so_os_campos_enviados_com_a_mensagem_de_cada_um() -> None:
    with pytest.raises(TextoInvalido) as erro:
        validar_edicao(ATUAL, {"verso": "   ", "explicacao": "e" * 1001}, LIMITES)
    assert erro.value.campos == {
        "verso": "Use de 1 a 2.000 caracteres.",
        "explicacao": "Use até 1.000 caracteres.",
    }


def test_campo_nao_enviado_nao_e_revalidado_contra_limite_menor() -> None:
    """Um limite reduzido depois não impede editar outro campo do mesmo cartão (D-004)."""
    antigo = TextoCartao("f" * 900, "v", None)
    menores = LimitesTexto(frente=10, verso=20, explicacao=10)
    novo = validar_edicao(antigo, {"verso": "outro"}, menores)
    assert novo == TextoCartao("f" * 900, "outro", None)


@pytest.mark.parametrize("campo", ["frente", "verso"])
def test_frente_e_verso_nao_podem_ficar_vazios_nem_nulos(campo: str) -> None:
    for vazio in ("", "  ", None):
        with pytest.raises(TextoInvalido) as erro:
            validar_edicao(ATUAL, {campo: vazio}, LIMITES)
        assert list(erro.value.campos) == [campo]


def test_campo_desconhecido_e_erro_de_programacao() -> None:
    with pytest.raises(KeyError):
        validar_edicao(ATUAL, {"origem": "gerado_verificado"}, LIMITES)


# --- origem_apos_edicao (RF-006, DTEC 038) ---------------------------------------------------


@pytest.mark.parametrize(
    ("origem", "mudou", "esperada"),
    [
        (OrigemCartao.GERADO_VERIFICADO, True, OrigemCartao.EDITADO),
        (OrigemCartao.GERADO_VERIFICADO, False, OrigemCartao.GERADO_VERIFICADO),
        (OrigemCartao.EDITADO, True, OrigemCartao.EDITADO),
        (OrigemCartao.EDITADO, False, OrigemCartao.EDITADO),
        (OrigemCartao.CRIADO, True, OrigemCartao.CRIADO),
        (OrigemCartao.CRIADO, False, OrigemCartao.CRIADO),
    ],
)
def test_tabela_da_origem_depois_da_edicao(
    origem: OrigemCartao, mudou: bool, esperada: OrigemCartao
) -> None:
    assert origem_apos_edicao(origem, mudou=mudou) is esperada


def test_a_origem_nunca_volta_a_gerado_e_verificado() -> None:
    for origem in OrigemCartao:
        for mudou in (True, False):
            if origem is not OrigemCartao.GERADO_VERIFICADO:
                assert origem_apos_edicao(origem, mudou=mudou) is not OrigemCartao.GERADO_VERIFICADO
