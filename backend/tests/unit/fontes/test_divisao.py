"""Normalização e divisão em trechos (DTEC 029, RF-006, RF-016; T017).

Os invariantes valem para qualquer texto (Hypothesis, com os parâmetros padrão e com parâmetros
minúsculos que forçam todos os caminhos); os casos fixos documentam as regras por exemplo.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.fontes.divisao import (
    Parametros,
    TextoDividido,
    dividir_pdf,
    dividir_texto,
    normalizar_texto,
    tem_texto,
    versao_extracao,
)

pytestmark = pytest.mark.unit

PADRAO = Parametros()
MINUSCULOS = Parametros(alvo=60, maximo=90, sobreposicao=12)


# --- Parâmetros e versão ----------------------------------------------------------------------


def test_parametros_padrao_sao_os_da_dtec_029() -> None:
    assert (PADRAO.alvo, PADRAO.maximo, PADRAO.sobreposicao) == (1200, 2000, 150)


@pytest.mark.parametrize(
    ("alvo", "maximo", "sobreposicao"),
    [(100, 200, 100), (100, 200, 101), (300, 200, 10), (0, 200, 0), (100, 200, -1)],
)
def test_parametros_incoerentes_sao_recusados(alvo: int, maximo: int, sobreposicao: int) -> None:
    with pytest.raises(ValueError, match="parâmetros"):
        Parametros(alvo=alvo, maximo=maximo, sobreposicao=sobreposicao)


def test_versao_da_extracao_reflete_os_parametros() -> None:
    assert versao_extracao(PADRAO) == "v2-a1200-m2000-s150"
    assert versao_extracao(MINUSCULOS) == "v2-a60-m90-s12"
    assert versao_extracao(Parametros(alvo=500, maximo=800, sobreposicao=0)) == "v2-a500-m800-s0"


# --- Normalização -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("bruto", "esperado"),
    [
        ("a\r\nb\rc\nd", "a\nb\nc\nd"),
        ("a\x00b\x07c\x1bd\x7fe\x85f", "abcdef"),
        ("a   b\t\tc \t d", "a b c d"),
        ("a\n\n\n\nb", "a\n\nb"),
        ("a\n\n\n\n\n\nb", "a\n\nb"),
        ("linha   \nseguinte\t\n", "linha\nseguinte"),
        ("  começo e fim  \n\n", "começo e fim"),
        ("é", "é"),
        ("tab\taqui", "tab aqui"),
    ],
)
def test_normalizacao_segue_a_dtec(bruto: str, esperado: str) -> None:
    assert normalizar_texto(bruto) == esperado


def test_normalizacao_e_idempotente_em_exemplos() -> None:
    texto = "A  b\r\n\r\n\r\nc \x00 d\t\te\n"
    assert normalizar_texto(normalizar_texto(texto)) == normalizar_texto(texto)


@given(st.text(max_size=300))
def test_normalizacao_e_idempotente(texto: str) -> None:
    uma_vez = normalizar_texto(texto)
    assert normalizar_texto(uma_vez) == uma_vez
    assert "\r" not in uma_vez
    assert "\n\n\n" not in uma_vez
    assert "  " not in uma_vez
    assert not any(ord(c) < 32 and c not in "\n" for c in uma_vez)


def test_tem_texto_exige_caractere_alfanumerico() -> None:
    assert tem_texto("a")
    assert tem_texto("123")
    assert not tem_texto("")
    assert not tem_texto("  \n\n --- *** !!! ")
    assert not tem_texto("• □ →")


# --- Invariantes (DTEC 029) -------------------------------------------------------------------


def _conferir_invariantes(
    resultado: TextoDividido, p: Parametros, *, com_pagina: bool, paginas_validas: set[int]
) -> None:
    texto = resultado.texto_completo
    trechos = resultado.trechos
    anterior_inicio = -1
    for esperado, trecho in enumerate(trechos):
        # 1. Os deslocamentos conferem com o texto.
        assert texto[trecho.inicio : trecho.fim] == trecho.texto
        assert trecho.fim - trecho.inicio == len(trecho.texto) >= 1
        # 2. Ordem contígua a partir de 0, com inícios que não diminuem.
        assert trecho.ordem == esperado
        assert trecho.inicio >= anterior_inicio
        anterior_inicio = trecho.inicio
        # 3. Nenhum trecho passa do máximo.
        assert len(trecho.texto) <= p.maximo
        # 4. Começa e termina em caractere visível.
        assert not trecho.texto[0].isspace() and not trecho.texto[-1].isspace()
        # 5. Página só em PDF, e sempre em PDF.
        if com_pagina:
            assert trecho.pagina in paginas_validas
        else:
            assert trecho.pagina is None
    # 6. Todo caractere visível do texto pertence a pelo menos um trecho.
    cobertos = bytearray(len(texto))
    for trecho in trechos:
        cobertos[trecho.inicio : trecho.fim] = b"\x01" * (trecho.fim - trecho.inicio)
    for posicao, caractere in enumerate(texto):
        if not caractere.isspace():
            assert cobertos[posicao], f"o caractere {posicao} ({caractere!r}) não foi coberto"


ALFABETO = "abcdefg hij.k!l?m…\n\n  #`~ç\t-"


@settings(max_examples=300, deadline=None)
@given(st.text(alphabet=ALFABETO, max_size=1500), st.booleans())
def test_invariantes_em_texto_com_parametros_minusculos(texto: str, markdown: bool) -> None:
    resultado = dividir_texto(normalizar_texto(texto), markdown=markdown, p=MINUSCULOS)
    _conferir_invariantes(resultado, MINUSCULOS, com_pagina=False, paginas_validas=set())


@settings(max_examples=60, deadline=None)
@given(st.text(alphabet=ALFABETO + "palavra frase longa. ", max_size=9000), st.booleans())
def test_invariantes_em_texto_com_parametros_padrao(texto: str, markdown: bool) -> None:
    resultado = dividir_texto(normalizar_texto(texto), markdown=markdown, p=PADRAO)
    _conferir_invariantes(resultado, PADRAO, com_pagina=False, paginas_validas=set())


@settings(max_examples=200, deadline=None)
@given(st.lists(st.text(alphabet=ALFABETO, max_size=400), min_size=0, max_size=8))
def test_invariantes_em_pdf_nenhum_trecho_atravessa_paginas(paginas: list[str]) -> None:
    resultado = dividir_pdf(paginas, p=MINUSCULOS)
    com_texto = {n for n, bruto in enumerate(paginas, start=1) if normalizar_texto(bruto)}
    _conferir_invariantes(resultado, MINUSCULOS, com_pagina=True, paginas_validas=com_texto)
    # Cada trecho está inteiro na sua página: o texto da página o contém.
    for trecho in resultado.trechos:
        assert trecho.pagina is not None
        pagina = normalizar_texto(paginas[trecho.pagina - 1])
        assert trecho.texto in pagina


@settings(max_examples=100, deadline=None)
@given(st.text(alphabet=ALFABETO, max_size=1200), st.booleans())
def test_divisao_e_deterministica(texto: str, markdown: bool) -> None:
    normalizado = normalizar_texto(texto)
    primeira = dividir_texto(normalizado, markdown=markdown, p=MINUSCULOS)
    segunda = dividir_texto(normalizado, markdown=markdown, p=MINUSCULOS)
    assert primeira == segunda


# --- Casos fixos: TXT -------------------------------------------------------------------------


def test_texto_vazio_nao_gera_trechos() -> None:
    assert dividir_texto("", markdown=False, p=PADRAO).trechos == []


def test_um_paragrafo_curto_e_um_so_trecho_sem_pagina() -> None:
    resultado = dividir_texto("A célula é a unidade básica da vida.", markdown=False, p=PADRAO)
    assert len(resultado.trechos) == 1
    trecho = resultado.trechos[0]
    assert (trecho.ordem, trecho.pagina, trecho.inicio) == (0, None, 0)
    assert trecho.texto == "A célula é a unidade básica da vida."


def test_paragrafos_sao_acumulados_ate_o_tamanho_alvo() -> None:
    paragrafo = "Palavra " * 20  # 160 caracteres
    texto = normalizar_texto("\n\n".join([paragrafo] * 6))
    resultado = dividir_texto(
        texto, markdown=False, p=Parametros(alvo=400, maximo=600, sobreposicao=40)
    )
    # Cada trecho cabe no alvo (400) e há mais de um.
    assert len(resultado.trechos) >= 2
    assert all(len(t.texto) <= 600 for t in resultado.trechos)
    _conferir_invariantes(
        resultado,
        Parametros(alvo=400, maximo=600, sobreposicao=40),
        com_pagina=False,
        paginas_validas=set(),
    )


def test_sobreposicao_comeca_no_inicio_de_uma_palavra_e_repete_o_fim_do_trecho_anterior() -> None:
    p = Parametros(alvo=120, maximo=200, sobreposicao=30)
    paragrafos = [
        f"Primeiro bloco numero {n} com palavras suficientes para encher" for n in range(8)
    ]
    texto = normalizar_texto("\n\n".join(paragrafos))
    resultado = dividir_texto(texto, markdown=False, p=p)
    assert len(resultado.trechos) >= 3
    for anterior, atual in zip(resultado.trechos, resultado.trechos[1:], strict=False):
        assert atual.inicio < anterior.fim, "o trecho seguinte deve começar dentro do anterior"
        assert anterior.fim - atual.inicio <= p.sobreposicao
        assert resultado.texto_completo[atual.inicio - 1].isspace()  # início de palavra
        assert atual.inicio > anterior.inicio


def test_sem_sobreposicao_os_trechos_se_encostam_sem_repetir() -> None:
    p = Parametros(alvo=100, maximo=150, sobreposicao=0)
    texto = normalizar_texto("\n\n".join(f"Parágrafo {n} " + "x" * 60 for n in range(6)))
    resultado = dividir_texto(texto, markdown=False, p=p)
    for anterior, atual in zip(resultado.trechos, resultado.trechos[1:], strict=False):
        assert atual.inicio >= anterior.fim


def test_frase_maior_que_o_maximo_e_cortada_no_ultimo_espaco_antes_do_limite() -> None:
    p = Parametros(alvo=50, maximo=80, sobreposicao=10)
    frase = " ".join(["palavra"] * 40)  # uma única "frase" de ~319 caracteres, sem ponto
    resultado = dividir_texto(frase, markdown=False, p=p)
    assert len(resultado.trechos) > 3
    for trecho in resultado.trechos:
        assert len(trecho.texto) <= 80
        assert trecho.texto.startswith("palavra") and trecho.texto.endswith("palavra")


def test_paragrafo_maior_que_o_maximo_e_cortado_em_fim_de_frase() -> None:
    p = Parametros(alvo=100, maximo=160, sobreposicao=20)
    paragrafo = " ".join(f"Esta é a frase número {n} do parágrafo." for n in range(30))
    resultado = dividir_texto(paragrafo, markdown=False, p=p)
    assert len(resultado.trechos) > 3
    # Todo trecho que não é o último termina em fim de frase.
    for trecho in resultado.trechos[:-1]:
        assert trecho.texto.endswith(".")
        assert len(trecho.texto) <= 160


def test_palavra_maior_que_o_maximo_e_cortada_no_proprio_limite() -> None:
    p = Parametros(alvo=50, maximo=80, sobreposicao=10)
    palavra = "a" * 300
    resultado = dividir_texto(palavra, markdown=False, p=p)
    assert "".join(t.texto for t in resultado.trechos).count("a") >= 300
    assert all(len(t.texto) <= 80 for t in resultado.trechos)
    _conferir_invariantes(resultado, p, com_pagina=False, paginas_validas=set())


def test_sobra_final_pequena_e_unida_ao_trecho_anterior_se_couber() -> None:
    p = Parametros(alvo=300, maximo=600, sobreposicao=0)
    grande = "x" * 280
    pequena = "fim curto"
    texto = f"{grande}\n\n{pequena}"
    # Sem a regra seriam dois trechos; com ela, um só (280 + 2 + 9 = 291 cabe no máximo).
    resultado = dividir_texto(
        texto, markdown=False, p=Parametros(alvo=285, maximo=600, sobreposicao=0)
    )
    assert len(resultado.trechos) == 1
    assert resultado.trechos[0].texto == texto
    assert p.maximo == 600


def test_sobra_final_pequena_nao_e_unida_se_estouraria_o_maximo() -> None:
    # Dois segmentos não cabem no alvo (295 + 2 + 3 = 300 > 296); a união também passaria do máximo.
    p = Parametros(alvo=296, maximo=299, sobreposicao=0)
    texto = f"{'x' * 295}\n\nfim"
    resultado = dividir_texto(texto, markdown=False, p=p)
    assert [t.texto for t in resultado.trechos] == ["x" * 295, "fim"]


def test_sobreposicao_e_encurtada_quando_nao_cabe_com_o_paragrafo_novo_no_maximo() -> None:
    """Parágrafo de 85 caracteres (cabe no máximo de 90, mas não com 12 de sobreposição)."""
    p = Parametros(alvo=60, maximo=90, sobreposicao=12)
    curto = " ".join(["alfa"] * 10)  # 49 caracteres
    longo = " ".join(["beta"] * 17)  # 84 caracteres
    texto = f"{curto}\n\n{longo}"
    resultado = dividir_texto(texto, markdown=False, p=p)
    assert len(resultado.trechos) == 2
    segundo = resultado.trechos[1]
    assert len(segundo.texto) <= 90
    assert segundo.texto.endswith(longo)
    assert segundo.inicio >= len(curto) + 2 - 12
    _conferir_invariantes(resultado, p, com_pagina=False, paginas_validas=set())


@settings(max_examples=200, deadline=None)
@given(st.lists(st.text(alphabet="abc de", min_size=60, max_size=95), min_size=1, max_size=6))
def test_paragrafos_proximos_do_maximo_respeitam_o_maximo(paragrafos: list[str]) -> None:
    texto = normalizar_texto("\n\n".join(paragrafos))
    resultado = dividir_texto(texto, markdown=False, p=MINUSCULOS)
    _conferir_invariantes(resultado, MINUSCULOS, com_pagina=False, paginas_validas=set())


def test_texto_curto_pouco_conteudo_gera_pelo_menos_um_trecho() -> None:
    """RF-016, D-006: não há quantidade mínima de texto."""
    resultado = dividir_texto("Oi.", markdown=False, p=PADRAO)
    assert [t.texto for t in resultado.trechos] == ["Oi."]


# --- Casos fixos: Markdown --------------------------------------------------------------------


def test_markdown_divide_por_secao_de_titulo_e_nenhum_trecho_atravessa_secoes() -> None:
    p = Parametros(alvo=500, maximo=800, sobreposicao=20)
    texto = normalizar_texto(
        "Introdução solta antes do primeiro título.\n\n"
        "# Citologia\n\nA célula é a unidade básica.\n\n"
        "## Organelas\n\nMitocôndrias produzem energia.\n\n"
        "### Detalhes\n\nMais um parágrafo."
    )
    resultado = dividir_texto(texto, markdown=True, p=p)
    textos = [t.texto for t in resultado.trechos]
    assert textos == [
        "Introdução solta antes do primeiro título.",
        "# Citologia\n\nA célula é a unidade básica.",
        "## Organelas\n\nMitocôndrias produzem energia.",
        "### Detalhes\n\nMais um parágrafo.",
    ]
    assert all(t.pagina is None for t in resultado.trechos)


def test_titulo_dentro_de_bloco_de_codigo_nao_abre_secao() -> None:
    p = Parametros(alvo=500, maximo=800, sobreposicao=20)
    texto = normalizar_texto(
        "# Código\n\nVeja:\n\n```python\n# comentário que não é título\nx = 1\n```\n\nFim da seção."
    )
    resultado = dividir_texto(texto, markdown=True, p=p)
    assert len(resultado.trechos) == 1
    assert "# comentário que não é título" in resultado.trechos[0].texto


def test_bloco_cercado_com_til_tambem_protege_titulos() -> None:
    p = Parametros(alvo=500, maximo=800, sobreposicao=20)
    texto = normalizar_texto("# A\n\ntexto\n\n~~~\n# nao titulo\n~~~\n\n# B\n\nmais")
    resultado = dividir_texto(texto, markdown=True, p=p)
    assert [t.texto.splitlines()[0] for t in resultado.trechos] == ["# A", "# B"]


def test_cerca_de_codigo_so_fecha_com_o_mesmo_tipo() -> None:
    p = Parametros(alvo=500, maximo=800, sobreposicao=20)
    texto = normalizar_texto("# A\n\n```\n~~~\n# ainda dentro\n```\n\n# B\n\nfim")
    resultado = dividir_texto(texto, markdown=True, p=p)
    assert [t.texto.splitlines()[0] for t in resultado.trechos] == ["# A", "# B"]


@pytest.mark.parametrize("linha", ["#sem-espaco", "####### sete", "texto # no meio", "#"])
def test_so_titulo_atx_de_1_a_6_com_espaco_abre_secao(linha: str) -> None:
    p = Parametros(alvo=500, maximo=800, sobreposicao=20)
    texto = normalizar_texto(f"# Real\n\n{linha}\n\nresto")
    resultado = dividir_texto(texto, markdown=True, p=p)
    assert len(resultado.trechos) == 1


def test_txt_nao_divide_por_titulo() -> None:
    p = Parametros(alvo=500, maximo=800, sobreposicao=20)
    texto = normalizar_texto("# parece título\n\ncorpo\n\n# outro\n\nmais")
    assert len(dividir_texto(texto, markdown=False, p=p).trechos) == 1


# --- Casos fixos: PDF -------------------------------------------------------------------------


def test_pdf_um_trecho_por_pagina_com_a_pagina_fisica() -> None:
    resultado = dividir_pdf(["Primeira página.", "Segunda página.", "Terceira página."], p=PADRAO)
    assert [(t.pagina, t.texto) for t in resultado.trechos] == [
        (1, "Primeira página."),
        (2, "Segunda página."),
        (3, "Terceira página."),
    ]
    assert resultado.texto_completo == "Primeira página.\n\nSegunda página.\n\nTerceira página."


def test_paginas_em_branco_nao_geram_trecho_e_a_numeracao_continua_fisica() -> None:
    resultado = dividir_pdf(["Um.", "", "  \n ", "Quatro.", "", "Seis."], p=PADRAO)
    assert [(t.pagina, t.texto) for t in resultado.trechos] == [
        (1, "Um."),
        (4, "Quatro."),
        (6, "Seis."),
    ]


def test_deslocamentos_do_pdf_sao_relativos_ao_texto_das_paginas_unidas() -> None:
    resultado = dividir_pdf(["abc", "def"], p=PADRAO)
    assert [(t.inicio, t.fim) for t in resultado.trechos] == [(0, 3), (5, 8)]
    assert resultado.texto_completo[5:8] == "def"


def test_pagina_longa_vira_varios_trechos_todos_com_a_mesma_pagina() -> None:
    p = Parametros(alvo=80, maximo=120, sobreposicao=10)
    pagina = "\n\n".join(f"Parágrafo {n} da página com algum texto" for n in range(10))
    resultado = dividir_pdf(["curta", pagina, "final"], p=p)
    paginas = [t.pagina for t in resultado.trechos]
    assert paginas[0] == 1 and paginas[-1] == 3
    assert paginas.count(2) >= 3
    numeros = [n for n in paginas if n is not None]
    assert numeros == sorted(numeros)


def test_pdf_sem_paginas_ou_so_com_paginas_vazias_nao_gera_trechos() -> None:
    assert dividir_pdf([], p=PADRAO).trechos == []
    assert dividir_pdf(["", "  "], p=PADRAO).trechos == []


def test_markdown_em_pdf_nao_e_interpretado() -> None:
    resultado = dividir_pdf(["# não é título\n\ncorpo"], p=PADRAO)
    assert len(resultado.trechos) == 1
