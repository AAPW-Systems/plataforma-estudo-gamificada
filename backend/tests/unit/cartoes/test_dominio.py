"""T008: normalização, limites, estado inicial, rótulos e derivados dos cartões (RF-001, RF-003,
RF-009, RF-011; DTEC 036 e 037). Regras puras, sem banco nem HTTP.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fsrs import Card, State
from hypothesis import given
from hypothesis import strategies as st

from app.cartoes import dominio
from app.cartoes.dominio import (
    LimitesTexto,
    TextoInvalido,
    estado_inicial,
    fonte_apagada,
    normalizar_texto_cartao,
    rotulo_origem,
    validar_limites,
    verificado,
)
from app.cartoes.modelos import EstadoFsrs, OrigemCartao

pytestmark = pytest.mark.unit

LIMITES = LimitesTexto(frente=1000, verso=2000, explicacao=1000)
AGORA = datetime(2026, 10, 20, 12, 0, 0, 123456, tzinfo=UTC)
normalizar = normalizar_texto_cartao

# --- Normalização (RF-011, DTEC 036) -------------------------------------------------------------


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("Mitocôndria", "Mitocôndria"),
        ("é", "é"),  # NFC: "e" mais acento combinante vira "é"
        ("a\r\nb", "a\nb"),
        ("a\rb", "a\nb"),
        ("a\r\n\r\nb\rc\n", "a\n\nb\nc"),
        ("a\x00b\x07c\x1bd\x7fe\x85f\x9fg", "abcdefg"),  # controles C0, DEL e C1 saem
        ("a\tb", "a\tb"),  # tabulação é conteúdo
        ("  \n\t texto \t\n  ", "texto"),  # extremidades
        (" texto ", "texto"),
        ("linha 1\n\nlinha 3", "linha 1\n\nlinha 3"),  # quebras internas, inclusive em branco
        ("a   b", "a   b"),  # espaços internos
        ("a\n\n\n\nb", "a\n\n\n\nb"),
        ("", ""),
        ("   ", ""),
        ("\n\r\n\t ", ""),
        ("\x00\x07", ""),
        ("a\ud800b", "ab"),  # substituto isolado não codifica em UTF-8 nem entra no Postgres
        ("‮abc‬", "‮abc‬"),  # bidirecionais ficam (podem ser legítimos)
        ("a​b", "a​b"),  # largura zero fica
        ("<script>alert(1)</script>", "<script>alert(1)</script>"),  # marcação é texto
        ("100% _ \\ literal", "100% _ \\ literal"),
        ("🧬 DNA", "🧬 DNA"),
    ],
)
def test_normalizacao_de_texto(entrada: str, esperado: str) -> None:
    assert normalizar(entrada) == esperado


def test_controles_removidos_nao_deixam_sequencia_nao_normalizada() -> None:
    """Tirar um controle entre "e" e o acento combinante precisa terminar em NFC."""
    assert normalizar("e\x00́") == "é"


@given(st.text())
def test_normalizacao_e_idempotente(texto: str) -> None:
    uma_vez = normalizar(texto)
    assert normalizar(uma_vez) == uma_vez


@given(
    st.lists(
        st.tuples(
            st.text(alphabet=st.characters(categories=("L", "N")), min_size=1, max_size=8),
            st.integers(min_value=1, max_value=4),
            st.sampled_from(["\n", "\r\n", "\r"]),
        ),
        min_size=1,
        max_size=8,
    )
)
def test_nenhuma_quebra_interna_e_perdida(blocos: list[tuple[str, int, str]]) -> None:
    """Palavras separadas por `k` quebras (em qualquer convenção) mantêm as `k` quebras."""
    texto = blocos[0][0]
    esperadas = 0
    for palavra, quebras, tipo in blocos[1:]:
        texto += tipo * quebras + palavra
        esperadas += quebras
    assert normalizar(texto).count("\n") == esperadas


@given(st.text())
def test_resultado_nao_tem_controle_nem_retorno_de_carro_nem_extremidades_em_branco(
    texto: str,
) -> None:
    resultado = normalizar(texto)
    assert "\r" not in resultado
    assert all(ord(c) not in range(0x20) or c in "\n\t" for c in resultado)
    assert resultado == resultado.strip()


# --- Limites (RF-001, D-004) ---------------------------------------------------------------------


def _validar(frente: str = "f", verso: str = "v", explicacao: str | None = None) -> object:
    return validar_limites(frente, verso, explicacao, LIMITES)


@pytest.mark.parametrize(
    ("campo", "limite"), [("frente", 1000), ("verso", 2000), ("explicacao", 1000)]
)
@pytest.mark.parametrize(
    "unidade",
    ["a", "ç", "🧬", "é"],
    ids=["ascii", "cedilha", "emoji", "combinante"],
)
def test_aceita_de_1_ate_o_maximo_em_code_points(campo: str, limite: int, unidade: str) -> None:
    """Emoji vale 1 e "e" mais acento combinante vale 1 (NFC), como na interface."""
    for tamanho in (1, limite):
        texto = unidade * tamanho
        resultado = _validar(**{campo: texto})
        assert len(getattr(resultado, campo)) == tamanho


@pytest.mark.parametrize(
    ("campo", "limite", "mensagem"),
    [
        ("frente", 1000, "Use de 1 a 1.000 caracteres."),
        ("verso", 2000, "Use de 1 a 2.000 caracteres."),
        ("explicacao", 1000, "Use até 1.000 caracteres."),
    ],
)
@pytest.mark.parametrize("unidade", ["a", "🧬", "é"], ids=["ascii", "emoji", "combinante"])
def test_recusa_um_acima_do_maximo_com_a_mensagem_do_campo(
    campo: str, limite: int, mensagem: str, unidade: str
) -> None:
    with pytest.raises(TextoInvalido) as erro:
        _validar(**{campo: unidade * (limite + 1)})
    assert erro.value.campos == {campo: mensagem}


@pytest.mark.parametrize("campo", ["frente", "verso"])
@pytest.mark.parametrize("vazio", ["", " ", "   \n\t  ", "\r\n", "\x00", "​", "‮ ‬"])
def test_frente_e_verso_vazios_ou_invisiveis_sao_recusados(campo: str, vazio: str) -> None:
    """Só espaços (caso de borda) e texto sem nenhum caractere visível valem como vazio."""
    with pytest.raises(TextoInvalido) as erro:
        _validar(**{campo: vazio})
    assert list(erro.value.campos) == [campo]


@pytest.mark.parametrize("vazia", [None, "", "  ", "\n\n", "​"])
def test_explicacao_vazia_vira_none(vazia: str | None) -> None:
    assert validar_limites("f", "v", vazia, LIMITES).explicacao is None


def test_a_contagem_vem_depois_da_normalizacao() -> None:
    """Espaços nas pontas e CRLF não gastam o limite."""
    frente = "  " + "a\r\n" * 499 + "a" + "  \n"
    resultado = validar_limites(frente, "v", None, LIMITES)
    assert resultado.frente == "a\n" * 499 + "a"
    assert len(frente) > 1000 >= len(resultado.frente) == 999


def test_devolve_os_textos_normalizados() -> None:
    resultado = validar_limites("  é\r\nx  ", "\tv\n", " expl ", LIMITES)
    assert (resultado.frente, resultado.verso, resultado.explicacao) == ("é\nx", "v", "expl")


def test_varios_campos_invalidos_voltam_juntos_um_erro_por_campo() -> None:
    with pytest.raises(TextoInvalido) as erro:
        validar_limites("", "v" * 2001, "e" * 1001, LIMITES)
    assert erro.value.campos == {
        "frente": "Use de 1 a 1.000 caracteres.",
        "verso": "Use de 1 a 2.000 caracteres.",
        "explicacao": "Use até 1.000 caracteres.",
    }


def test_os_limites_vigentes_mandam_nao_os_padroes() -> None:
    pequenos = LimitesTexto(frente=5, verso=10, explicacao=3)
    assert validar_limites("12345", "1234567890", "123", pequenos).frente == "12345"
    with pytest.raises(TextoInvalido) as erro:
        validar_limites("123456", "x", "1234", pequenos)
    assert erro.value.campos == {
        "frente": "Use de 1 a 5 caracteres.",
        "explicacao": "Use até 3 caracteres.",
    }


@given(st.text(max_size=3000))
def test_texto_aceito_sempre_cabe_no_limite_e_nunca_e_vazio(texto: str) -> None:
    try:
        resultado = validar_limites(texto, texto, texto, LIMITES)
    except TextoInvalido:
        return
    assert 1 <= len(resultado.frente) <= 1000
    assert 1 <= len(resultado.verso) <= 2000
    assert resultado.explicacao is None or 1 <= len(resultado.explicacao) <= 1000


# --- Estado inicial (RF-003, DTEC 037) -----------------------------------------------------------


def test_estado_inicial_espelha_o_card_novo_da_biblioteca_fixada() -> None:
    card = Card()
    estado = estado_inicial(AGORA)
    assert card.state == State.Learning and card.step == 0, "a biblioteca mudou o cartão novo"
    assert estado.estado_fsrs is EstadoFsrs.APRENDIZADO
    assert estado.passo == card.step
    assert estado.estabilidade is card.stability is None
    assert estado.dificuldade is card.difficulty is None
    assert estado.ultima_revisao is card.last_review is None
    assert estado.vencimento == AGORA, "vence no instante da criação"


def test_todo_estado_da_biblioteca_tem_correspondente_no_enum() -> None:
    """Se uma versão nova da `fsrs` criar um estado, o mapeamento precisa ser revisto."""
    assert {estado.name for estado in State} == {
        "Learning",
        "Review",
        "Relearning",
    }
    assert {e.value for e in EstadoFsrs} == {"aprendizado", "revisao", "reaprendizado"}


def test_estado_inicial_exige_instante_com_fuso() -> None:
    with pytest.raises(ValueError, match="fuso"):
        estado_inicial(datetime(2026, 10, 20, 12, 0))  # noqa: DTZ001


def test_nada_de_agendamento_alem_do_card_e_calculado_aqui() -> None:
    """RN-26: o módulo não importa a biblioteca para revisar nem decide intervalos."""
    fonte = Path(dominio.__file__).read_text(encoding="utf-8")
    assert "Scheduler" not in fonte and "review_card" not in fonte


# --- Rótulos e derivados (RF-009, D-002) ---------------------------------------------------------


@pytest.mark.parametrize(
    ("origem", "rotulo", "selo"),
    [
        (OrigemCartao.GERADO_VERIFICADO, "Gerado e verificado", True),
        (OrigemCartao.EDITADO, "Editado por você", False),
        (OrigemCartao.CRIADO, "Criado por você", False),
    ],
)
def test_rotulo_e_selo_de_verificado_pela_origem(
    origem: OrigemCartao, rotulo: str, selo: bool
) -> None:
    assert rotulo_origem(origem) == rotulo
    assert verificado(origem) is selo


def test_so_gerado_verificado_tem_selo_de_verificado() -> None:
    """Princípio I: nunca em cartão criado ou editado pelo estudante."""
    assert [o for o in OrigemCartao if verificado(o)] == [OrigemCartao.GERADO_VERIFICADO]


@pytest.mark.parametrize(
    ("titulo", "fonte_id", "esperado"),
    [
        (None, None, False),  # sem referência
        ("Citologia", 7, False),  # fonte ainda existe
        ("Citologia", None, True),  # cópias presentes e fonte nula: "Fonte apagada"
        (None, 7, False),  # combinação que o CHECK do banco recusa
    ],
)
def test_fonte_apagada_deriva_das_copias_e_da_fonte_nula(
    titulo: str | None, fonte_id: int | None, esperado: bool
) -> None:
    assert fonte_apagada(titulo, fonte_id) is esperado


def test_rotulo_do_complemento_de_fonte_apagada() -> None:
    assert dominio.ROTULO_FONTE_APAGADA == "Fonte apagada"
