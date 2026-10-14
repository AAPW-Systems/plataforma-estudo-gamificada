"""Regras puras das fontes (RQ-001, RF-003, RF-007, RF-015; T015)."""

from __future__ import annotations

import unicodedata

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.fontes import dominio
from app.fontes.dominio import CodigoFalha, EstadoFonte
from app.nucleo.texto import ValorInvalido

pytestmark = pytest.mark.unit


# --- Nome exibido (RQ-001, DTEC 028) ------------------------------------------------------------


@pytest.mark.parametrize(
    ("enviado", "esperado"),
    [
        ("citologia.pdf", "citologia.pdf"),
        ("../../etc/passwd", "passwd"),
        ("/etc/shadow", "shadow"),
        ("C:\\Users\\Ana\\notas.txt", "notas.txt"),
        ("pasta\\sub/arquivo.md", "arquivo.md"),
        ("..\\..\\sistema.pdf", "sistema.pdf"),
        ("  relatório final.pdf  ", "relatório final.pdf"),
    ],
)
def test_nome_exibido_fica_so_com_o_ultimo_segmento_do_caminho(enviado: str, esperado: str) -> None:
    assert dominio.nome_exibido(enviado) == esperado


@pytest.mark.parametrize("enviado", ["", "/", "\\", "../", "..\\", "pasta/", "a/b/", "   ", "\x00"])
def test_nome_vazio_depois_da_sanitizacao_vira_arquivo(enviado: str) -> None:
    assert dominio.nome_exibido(enviado) == "arquivo"


@pytest.mark.parametrize(
    "enviado",
    ["a\x00b.pdf", "a\x1fb.pdf", "a\x7fb.pdf", "a\x85b.pdf", "a\x9fb.pdf", "a\nb.pdf", "a\tb.pdf"],
)
def test_controles_c0_e_c1_saem_do_nome(enviado: str) -> None:
    assert dominio.nome_exibido(enviado) == "ab.pdf"


@pytest.mark.parametrize(
    "enviado",
    ["a\u202eb.pdf", "a\u202ab.pdf", "a\u2066b.pdf", "a\u2069b.pdf", "fdp.\u202etxt"],
)
def test_controles_de_direcao_saem_do_nome(enviado: str) -> None:
    nome = dominio.nome_exibido(enviado)
    assert not any(c in nome for c in "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")


def test_substituto_isolado_e_uso_privado_saem_do_nome() -> None:
    assert dominio.nome_exibido("a\ud800b\ue000c.pdf") == "abc.pdf"


def test_nome_com_255_caracteres_e_mantido_e_com_256_e_truncado() -> None:
    assert len(dominio.nome_exibido("a" * 251 + ".pdf")) == 255
    assert len(dominio.nome_exibido("a" * 252 + ".pdf")) == 255
    assert dominio.nome_exibido("a" * 300) == "a" * 255


def test_nome_longo_demais_mantem_a_extensao_ao_ser_truncado() -> None:
    """Um nome de 300 caracteres continua terminando em `.txt` (a extensão decide o formato)."""
    nome = dominio.nome_exibido(("x" * 300) + ".txt")
    assert len(nome) == 255
    assert nome == "x" * 251 + ".txt"


def test_extensao_gigante_nao_e_preservada_e_o_nome_e_truncado_mesmo_assim() -> None:
    nome = dominio.nome_exibido("a." + "e" * 400)
    assert len(nome) == 255 and nome.startswith("a.eee")


def test_nome_exibido_e_normalizado_em_nfc() -> None:
    decomposto = unicodedata.normalize("NFD", "relatório.pdf")
    assert dominio.nome_exibido(decomposto) == "relatório.pdf"


def test_marcas_de_direcao_rtl_sao_preservadas() -> None:
    assert "\u200f" in dominio.nome_exibido("עברית\u200f.txt")


@given(st.text(max_size=400))
def test_nome_exibido_nunca_tem_caminho_controle_nem_passa_de_255(texto: str) -> None:
    nome = dominio.nome_exibido(texto)
    assert 1 <= len(nome) <= 255
    assert "/" not in nome and "\\" not in nome
    assert not any(unicodedata.category(c) in {"Cc", "Cs", "Co"} for c in nome)
    assert unicodedata.is_normalized("NFC", nome)
    nome.encode("utf-8")
    assert dominio.nome_exibido(nome) == nome


# --- Título padrão e título digitado (RF-003, RF-015) ---------------------------------------------


@pytest.mark.parametrize(
    ("nome", "esperado"),
    [
        ("citologia.pdf", "citologia"),
        ("Aula 1.tar.gz", "Aula 1.tar"),
        ("anotacoes.MD", "anotacoes"),
        ("sem-extensao", "sem-extensao"),
        (".oculto", ".oculto"),
        ("final.", "final"),
    ],
)
def test_titulo_padrao_e_o_nome_sem_a_extensao(nome: str, esperado: str) -> None:
    assert dominio.titulo_padrao(nome) == esperado


def test_titulo_padrao_e_truncado_em_120_caracteres() -> None:
    assert dominio.titulo_padrao("a" * 200 + ".pdf") == "a" * 120
    assert len(dominio.titulo_padrao("b" * 119 + "ç.pdf")) == 120


def test_titulo_padrao_vazio_ou_invisivel_vira_fonte_sem_titulo() -> None:
    assert dominio.titulo_padrao("") == "Fonte sem título"
    assert dominio.titulo_padrao("   ") == "Fonte sem título"
    assert dominio.titulo_padrao("\u200b.pdf") == "Fonte sem título"


@pytest.mark.parametrize("tamanho", [1, 2, 119, 120])
def test_titulo_digitado_de_1_a_120_caracteres(tamanho: int) -> None:
    assert len(dominio.validar_titulo("t" * tamanho)) == tamanho


@pytest.mark.parametrize("titulo", ["", "   ", "\u200b"])
def test_titulo_vazio_e_recusado(titulo: str) -> None:
    with pytest.raises(ValorInvalido, match="Informe o título"):
        dominio.validar_titulo(titulo)


def test_titulo_com_121_caracteres_e_recusado() -> None:
    with pytest.raises(ValorInvalido, match="no máximo 120"):
        dominio.validar_titulo("t" * 121)


def test_titulo_com_controle_ou_direcao_e_recusado() -> None:
    for titulo in ("a\nb", "a\x00b", "a\u202eb"):
        with pytest.raises(ValorInvalido, match="caracteres que não podem"):
            dominio.validar_titulo(titulo)


def test_titulo_digitado_e_normalizado() -> None:
    assert dominio.validar_titulo("  " + unicodedata.normalize("NFD", "Física") + " ") == "Física"


# --- Estados e transições (DTEC 030, modelo de dados) -----------------------------------------


E = EstadoFonte
C = CodigoFalha


@pytest.mark.parametrize(
    ("de", "para"),
    [
        (E.PENDENTE, E.PROCESSANDO),
        (E.PROCESSANDO, E.PROCESSANDO),  # nova tentativa automática / job reenfileirado
        (E.PROCESSANDO, E.CONCLUIDO),
        (E.PROCESSANDO, E.FALHOU),
    ],
)
def test_transicoes_permitidas_do_worker(de: EstadoFonte, para: EstadoFonte) -> None:
    assert dominio.transicao_permitida(de, para)


def test_nova_tentativa_so_depois_de_falha_tecnica() -> None:
    assert dominio.transicao_permitida(E.FALHOU, E.PENDENTE, codigo_atual=C.FALHA_TECNICA)
    assert not dominio.transicao_permitida(E.FALHOU, E.PENDENTE, codigo_atual=C.SEM_TEXTO)
    assert not dominio.transicao_permitida(E.FALHOU, E.PENDENTE, codigo_atual=C.CONTEUDO_INVALIDO)
    assert not dominio.transicao_permitida(E.FALHOU, E.PENDENTE, codigo_atual=None)


@pytest.mark.parametrize(
    ("de", "para"),
    [
        (E.PENDENTE, E.CONCLUIDO),
        (E.PENDENTE, E.FALHOU),
        (E.PENDENTE, E.PENDENTE),
        (E.CONCLUIDO, E.PENDENTE),
        (E.CONCLUIDO, E.PROCESSANDO),
        (E.CONCLUIDO, E.FALHOU),
        (E.CONCLUIDO, E.CONCLUIDO),
        (E.FALHOU, E.PROCESSANDO),
        (E.FALHOU, E.CONCLUIDO),
        (E.FALHOU, E.FALHOU),
        (E.PROCESSANDO, E.PENDENTE),
    ],
)
def test_transicoes_recusadas(de: EstadoFonte, para: EstadoFonte) -> None:
    assert not dominio.transicao_permitida(de, para, codigo_atual=C.FALHA_TECNICA)


def test_estados_finais_e_nao_finais() -> None:
    assert {e for e in E if dominio.estado_final(e)} == {E.CONCLUIDO, E.FALHOU}
    assert {e for e in E if not dominio.estado_final(e)} == {E.PENDENTE, E.PROCESSANDO}


# --- Catálogo de falhas (RF-007, DTEC 030) -----------------------------------------------------


def test_catalogo_falhas_tem_uma_mensagem_em_portugues_por_codigo() -> None:
    assert dominio.mensagem_falha(C.FALHA_TECNICA) == (
        "Não conseguimos processar esta fonte por um problema técnico. Tente novamente."
    )
    assert dominio.mensagem_falha(C.SEM_TEXTO) == (
        "Este PDF não tem texto selecionável. PDFs digitalizados (imagens de páginas) não são "
        "aceitos."
    )
    assert dominio.mensagem_falha(C.CONTEUDO_INVALIDO) == (
        "Não foi possível ler o conteúdo deste arquivo. Verifique se ele abre normalmente e "
        "envie de novo."
    )
    assert {c for c in C} == {C.FALHA_TECNICA, C.SEM_TEXTO, C.CONTEUDO_INVALIDO}


def test_catalogo_falhas_so_a_falha_tecnica_permite_nova_tentativa() -> None:
    assert dominio.pode_tentar_novamente(E.FALHOU, C.FALHA_TECNICA)
    assert not dominio.pode_tentar_novamente(E.FALHOU, C.SEM_TEXTO)
    assert not dominio.pode_tentar_novamente(E.FALHOU, C.CONTEUDO_INVALIDO)
    assert not dominio.pode_tentar_novamente(E.CONCLUIDO, None)
    assert not dominio.pode_tentar_novamente(E.PENDENTE, None)
    assert not dominio.pode_tentar_novamente(E.PROCESSANDO, None)


def test_mensagem_de_falha_so_existe_em_falhou() -> None:
    assert dominio.mensagem_do_estado(E.FALHOU, C.SEM_TEXTO) == dominio.mensagem_falha(C.SEM_TEXTO)
    for estado in (E.PENDENTE, E.PROCESSANDO, E.CONCLUIDO):
        assert dominio.mensagem_do_estado(estado, None) is None


# --- Mensagens das recusas do envio -------------------------------------------------------------


def test_mensagem_de_duplicata_cita_o_titulo_da_fonte_existente() -> None:
    assert (
        dominio.mensagem_duplicada("Citologia") == "Esta fonte já está nesta matéria: «Citologia»."
    )


def test_mensagem_de_arquivo_grande_cita_o_limite_em_mb() -> None:
    assert dominio.mensagem_arquivo_grande(2 * 1024 * 1024) == (
        "O arquivo tem mais de 2 MB. Envie um arquivo menor."
    )
    assert "1,5 MB" in dominio.mensagem_arquivo_grande(1_572_864)
