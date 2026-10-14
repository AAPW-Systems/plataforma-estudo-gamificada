"""A fábrica de arquivos fictícios gera o que promete (T010; CS-001 e CS-002 da spec 002).

Cada arquivo tem a propriedade esperada (páginas, senha, ausência de texto, tamanho, codificação).
Nada aqui é dado pessoal (regra 10) e nada é versionado: os arquivos são gerados.
"""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pymupdf
import pytest

from tests import fabricas_arquivos as fab

pytestmark = pytest.mark.unit

LIMITE = 2 * 1024 * 1024


@pytest.fixture(scope="module")
def validos() -> dict[str, fab.ArquivoGerado]:
    return {a.nome: a for a in fab.validos()}


@pytest.fixture(scope="module")
def invalidos() -> dict[str, fab.ArquivoGerado]:
    return {a.nome: a for a in fab.invalidos()}


@pytest.fixture(scope="module")
def adversariais() -> dict[str, fab.ArquivoGerado]:
    return {a.nome: a for a in fab.adversariais()}


def _abrir(arquivo: fab.ArquivoGerado) -> pymupdf.Document:
    return pymupdf.open(stream=arquivo.conteudo, filetype="pdf")


def test_ha_10_validos_e_10_invalidos(
    validos: dict[str, fab.ArquivoGerado], invalidos: dict[str, fab.ArquivoGerado]
) -> None:
    assert len(validos) == 10
    assert len(invalidos) == 10


def test_nomes_unicos_e_extensoes_aceitas_nos_validos(
    validos: dict[str, fab.ArquivoGerado],
) -> None:
    extensoes = {Path(nome).suffix for nome in validos}
    assert extensoes <= {".pdf", ".txt", ".md", ".markdown"}
    assert {".pdf", ".txt", ".md", ".markdown"} <= extensoes


def test_todo_valido_cabe_no_limite_e_nao_e_vazio(validos: dict[str, fab.ArquivoGerado]) -> None:
    for arquivo in validos.values():
        assert 0 < len(arquivo.conteudo) <= LIMITE, arquivo.nome


def test_pdfs_validos_tem_o_texto_conhecido_de_cada_pagina(
    validos: dict[str, fab.ArquivoGerado],
) -> None:
    pdfs = [a for a in validos.values() if a.nome.endswith(".pdf")]
    assert len(pdfs) >= 4
    for arquivo in pdfs:
        assert arquivo.paginas is not None
        documento = _abrir(arquivo)
        assert not documento.needs_pass
        assert documento.page_count == len(arquivo.paginas), arquivo.nome
        for pagina, esperado in zip(documento, arquivo.paginas, strict=True):
            assert pagina.get_text("text", sort=True).strip() == esperado.strip(), arquivo.nome


def test_pdf_com_paginas_em_branco_intercaladas(validos: dict[str, fab.ArquivoGerado]) -> None:
    arquivo = validos["pdf-paginas-em-branco.pdf"]
    assert arquivo.paginas is not None
    vazias = [i for i, texto in enumerate(arquivo.paginas, start=1) if not texto]
    com_texto = [i for i, texto in enumerate(arquivo.paginas, start=1) if texto]
    assert len(vazias) >= 2 and len(com_texto) >= 3
    # Intercaladas: há texto antes e depois de uma página em branco.
    assert min(com_texto) < min(vazias) < max(com_texto)


def test_pdf_de_quase_2_mb_para_medir_o_cs003(validos: dict[str, fab.ArquivoGerado]) -> None:
    tamanho = len(validos["pdf-2mb.pdf"].conteudo)
    assert 1_800_000 <= tamanho <= LIMITE


def test_pdf_de_cerca_de_1_mb(validos: dict[str, fab.ArquivoGerado]) -> None:
    assert 800_000 <= len(validos["biologia-citologia.pdf"].conteudo) <= 1_300_000


def test_txt_e_md_validos_sao_utf_8_com_e_sem_bom(validos: dict[str, fab.ArquivoGerado]) -> None:
    com_bom = [a for a in validos.values() if a.conteudo.startswith(b"\xef\xbb\xbf")]
    sem_bom = [
        a
        for a in validos.values()
        if not a.nome.endswith(".pdf") and not a.conteudo.startswith(b"\xef\xbb\xbf")
    ]
    assert {Path(a.nome).suffix for a in com_bom} >= {".txt", ".md"}
    assert sem_bom
    for arquivo in (*com_bom, *sem_bom):
        decodificado = arquivo.conteudo.decode("utf-8-sig")
        assert decodificado == arquivo.texto
        assert "\x00" not in decodificado


def test_md_tem_titulos_e_bloco_de_codigo_com_falso_titulo(
    validos: dict[str, fab.ArquivoGerado],
) -> None:
    texto = validos["anotacoes.md"].texto
    assert texto is not None
    assert texto.startswith("# ")
    assert "## " in texto
    assert "```" in texto
    bloco = texto.split("```")[1]
    assert any(linha.startswith("# ") for linha in bloco.splitlines())


def test_um_paragrafo_tem_pouco_texto(validos: dict[str, fab.ArquivoGerado]) -> None:
    texto = validos["um-paragrafo.txt"].texto
    assert texto is not None
    assert "\n\n" not in texto.strip()
    assert 100 <= len(texto) <= 1000


# --- Inválidos (CS-002) ----------------------------------------------------------------------


def test_cada_invalido_tem_um_motivo_de_recusa_ou_falha(
    invalidos: dict[str, fab.ArquivoGerado],
) -> None:
    for arquivo in invalidos.values():
        assert (arquivo.codigo_esperado is None) != (arquivo.falha_esperada is None), arquivo.nome
    esperados = {a.codigo_esperado for a in invalidos.values() if a.codigo_esperado}
    assert esperados == {
        "arquivo_muito_grande",
        "tipo_divergente",
        "arquivo_vazio",
        "arquivo_corrompido",
        "pdf_protegido",
        "codificacao_invalida",
    }
    assert [a.nome for a in invalidos.values() if a.falha_esperada] == ["digitalizado.pdf"]


def test_acima_do_tamanho(invalidos: dict[str, fab.ArquivoGerado]) -> None:
    assert len(invalidos["grande-3mb.pdf"].conteudo) > LIMITE
    assert invalidos["grande-3mb.pdf"].status_http == 413


def test_disfarces_de_tipo(invalidos: dict[str, fab.ArquivoGerado]) -> None:
    assert not invalidos["disfarcado.pdf"].conteudo.startswith(b"%PDF-")
    assert invalidos["pdf-como-txt.txt"].conteudo.startswith(b"%PDF-")
    assert invalidos["disfarcado.pdf"].codigo_esperado == "tipo_divergente"
    assert invalidos["pdf-como-txt.txt"].codigo_esperado == "tipo_divergente"


def test_vazio_e_so_espacos(invalidos: dict[str, fab.ArquivoGerado]) -> None:
    assert invalidos["vazio.txt"].conteudo == b""
    assert invalidos["so-espacos.txt"].conteudo.decode().strip() == ""
    assert invalidos["so-espacos.txt"].conteudo != b""


def test_pdf_corrompido_nao_abre(invalidos: dict[str, fab.ArquivoGerado]) -> None:
    arquivo = invalidos["corrompido.pdf"]
    assert arquivo.conteudo.startswith(b"%PDF-")
    with pytest.raises(pymupdf.FileDataError):
        _abrir(arquivo)


def test_pdf_protegido_exige_senha(invalidos: dict[str, fab.ArquivoGerado]) -> None:
    documento = _abrir(invalidos["protegido.pdf"])
    assert documento.needs_pass


def test_pdf_digitalizado_abre_mas_nao_tem_texto(invalidos: dict[str, fab.ArquivoGerado]) -> None:
    documento = _abrir(invalidos["digitalizado.pdf"])
    assert not documento.needs_pass
    assert documento.page_count >= 1
    assert all(not pagina.get_text("text").strip() for pagina in documento)
    assert invalidos["digitalizado.pdf"].falha_esperada == "sem_texto"


def test_latin1_nao_e_utf8_e_byte_nulo_nao_e_texto(
    invalidos: dict[str, fab.ArquivoGerado],
) -> None:
    with pytest.raises(UnicodeDecodeError):
        invalidos["latin1.txt"].conteudo.decode("utf-8")
    assert b"\x00" in invalidos["byte-nulo.txt"].conteudo


# --- Adversariais ----------------------------------------------------------------------------


def test_zip_com_extensao_md(adversariais: dict[str, fab.ArquivoGerado]) -> None:
    arquivo = adversariais["zip-como-md.md"]
    assert arquivo.conteudo.startswith(b"PK")
    assert arquivo.codigo_esperado == "tipo_divergente"
    from io import BytesIO

    with zipfile.ZipFile(BytesIO(arquivo.conteudo)) as pacote:
        assert pacote.namelist()


def test_pdf_com_501_paginas(adversariais: dict[str, fab.ArquivoGerado]) -> None:
    arquivo = adversariais["pdf-501-paginas.pdf"]
    assert _abrir(arquivo).page_count == 501
    assert len(arquivo.conteudo) <= LIMITE
    assert arquivo.codigo_esperado == "pdf_paginas_excedidas"


def test_texto_com_instrucoes_a_ia_e_um_texto_valido(
    adversariais: dict[str, fab.ArquivoGerado],
) -> None:
    arquivo = adversariais["instrucoes-ia.txt"]
    assert arquivo.codigo_esperado is None and arquivo.falha_esperada is None
    assert arquivo.texto is not None
    assert "ignore" in arquivo.texto.lower()


def test_pdf_com_hifenizacao_tem_a_palavra_quebrada_na_linha() -> None:
    arquivo = fab.pdf_com_hifenizacao()
    pagina = _abrir(arquivo)[0]
    assert "uni-\ndade" in pagina.get_text("text")


# --- Reprodutibilidade e linha de comando ---------------------------------------------------


def test_textos_sao_deterministicos() -> None:
    primeiro = {a.nome: a.conteudo for a in fab.validos() if not a.nome.endswith(".pdf")}
    segundo = {a.nome: a.conteudo for a in fab.validos() if not a.nome.endswith(".pdf")}
    assert primeiro == segundo


def test_nenhum_dado_pessoal_nos_textos(validos: dict[str, fab.ArquivoGerado]) -> None:
    for arquivo in validos.values():
        trechos = [arquivo.texto or "", *(arquivo.paginas or ())]
        for texto in trechos:
            assert "@" not in texto
            assert "http" not in texto


def test_linha_de_comando_grava_os_conjuntos_nas_pastas_do_quickstart(tmp_path: Path) -> None:
    saida = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "tests.fabricas_arquivos", str(tmp_path)],
        capture_output=True,
        text=True,
        check=True,
        timeout=240,
    )
    assert str(tmp_path) in saida.stdout
    esperados = [
        "validos/biologia-citologia.pdf",
        "validos/pdf-2mb.pdf",
        "validos/anotacoes.md",
        "validos/resumo.txt",
        "validos/um-paragrafo.txt",
        "invalidos/grande-3mb.pdf",
        "invalidos/disfarcado.pdf",
        "invalidos/corrompido.pdf",
        "invalidos/protegido.pdf",
        "invalidos/latin1.txt",
        "invalidos/vazio.txt",
        "processamento/digitalizado.pdf",
        "adversariais/zip-como-md.md",
        "adversariais/pdf-501-paginas.pdf",
        "adversariais/instrucoes-ia.txt",
    ]
    for relativo in esperados:
        assert (tmp_path / relativo).is_file(), relativo
    assert (tmp_path / "invalidos/vazio.txt").stat().st_size == 0
