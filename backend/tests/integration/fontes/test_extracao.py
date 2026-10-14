"""Extração e divisão com o PyMuPDF real no subprocesso isolado (DTEC 024 e 029; T018).

Cobre CS-001 (páginas físicas conferem com a fábrica), CB-23 (PDF sem texto) e as falhas de
conteúdo ilegível. Os limites de tempo e memória são reais (`spawn` + `RLIMIT_AS`).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from app.fontes.divisao import Parametros, normalizar_texto, versao_extracao
from app.fontes.dominio import CodigoFalha
from app.fontes.processamento import (
    ArquivoProcessado,
    FalhaDeProcessamento,
    LimitesExtracao,
    processar_arquivo,
)
from tests import fabricas_arquivos as fab

pytestmark = pytest.mark.integration

LIMITES = LimitesExtracao(tempo_s=60, memoria_mb=512, max_paginas=500)
PARAMETROS = Parametros()


@pytest.fixture(scope="module")
def validos() -> dict[str, fab.ArquivoGerado]:
    return {a.nome: a for a in fab.validos()}


@pytest.fixture(scope="module")
def invalidos() -> dict[str, fab.ArquivoGerado]:
    return {a.nome: a for a in fab.invalidos()}


def _gravar(tmp_path: Path, arquivo: fab.ArquivoGerado) -> Path:
    caminho = tmp_path / "objeto"
    caminho.write_bytes(arquivo.conteudo)
    return caminho


def _tipo(nome: str) -> str:
    return {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".markdown": "text/markdown",
    }[Path(nome).suffix]


async def _processar(
    tmp_path: Path, arquivo: fab.ArquivoGerado, limites: LimitesExtracao = LIMITES
) -> ArquivoProcessado | FalhaDeProcessamento:
    return await processar_arquivo(
        _gravar(tmp_path, arquivo), _tipo(arquivo.nome), limites=limites, parametros=PARAMETROS
    )


def _processado(resultado: ArquivoProcessado | FalhaDeProcessamento) -> ArquivoProcessado:
    assert isinstance(resultado, ArquivoProcessado), resultado
    return resultado


# --- PDF: páginas físicas (CS-001, RF-006) -------------------------------------------------------


@pytest.mark.parametrize(
    "nome", ["pdf-uma-pagina.pdf", "pdf-paginas-em-branco.pdf", "biologia-citologia.pdf"]
)
async def test_paginas_fisicas_dos_trechos_conferem_com_a_fabrica(
    tmp_path: Path, validos: dict[str, fab.ArquivoGerado], nome: str
) -> None:
    arquivo = validos[nome]
    assert arquivo.paginas is not None
    processado = _processado(await _processar(tmp_path, arquivo))

    assert processado.total_paginas == len(arquivo.paginas)
    paginas_com_texto = {n for n, texto in enumerate(arquivo.paginas, start=1) if texto}
    assert {t.pagina for t in processado.trechos} == paginas_com_texto
    for trecho in processado.trechos:
        assert trecho.pagina is not None
        # O trecho está inteiro na página indicada: nenhuma linha dele vem de outra página.
        esperado = arquivo.paginas[trecho.pagina - 1]
        assert trecho.texto in normalizar_texto(esperado)
    assert processado.versao_extracao == versao_extracao(PARAMETROS)


async def test_pdf_com_paginas_em_branco_intercaladas_mantem_a_numeracao_fisica(
    tmp_path: Path, validos: dict[str, fab.ArquivoGerado]
) -> None:
    arquivo = validos["pdf-paginas-em-branco.pdf"]
    processado = _processado(await _processar(tmp_path, arquivo))
    paginas = {t.pagina for t in processado.trechos if t.pagina is not None}
    assert sorted(paginas) == [1, 3, 4, 7, 8]
    assert processado.total_paginas == 9


async def test_texto_completo_dos_deslocamentos_confere_com_os_trechos(
    tmp_path: Path, validos: dict[str, fab.ArquivoGerado]
) -> None:
    processado = _processado(await _processar(tmp_path, validos["biologia-citologia.pdf"]))
    for trecho in processado.trechos:
        assert processado.texto_completo[trecho.inicio : trecho.fim] == trecho.texto


async def test_hifenizacao_do_pdf_e_preservada_como_extraida(tmp_path: Path) -> None:
    """Caracterização: o `TEXT_DEHYPHENATE` da DTEC 029 não junta a palavra quebrada.

    Na versão 1.28.2 do PyMuPDF, a extração devolve "uni-\\ndade" mesmo com a opção ligada
    (verificado com hífen comum, hífen suave e hífen Unicode). A DTEC previa que a hifenização
    fosse desfeita; fazê-lo por regra própria muda o texto citado nos cartões e fica como
    decisão pendente (registro da sessão). Se isto mudar, este teste deve ser revisto.
    """
    arquivo = fab.pdf_com_hifenizacao()
    processado = _processado(
        await processar_arquivo(
            _gravar(tmp_path, arquivo),
            "application/pdf",
            limites=LIMITES,
            parametros=PARAMETROS,
        )
    )
    assert "uni-\ndade" in processado.texto_completo


async def test_pdf_sem_camada_de_texto_devolve_sem_texto(
    tmp_path: Path, invalidos: dict[str, fab.ArquivoGerado]
) -> None:
    """CB-23: PDF digitalizado abre, mas não tem texto extraível; sem nova tentativa."""
    resultado = await _processar(tmp_path, invalidos["digitalizado.pdf"])
    assert resultado == FalhaDeProcessamento(CodigoFalha.SEM_TEXTO)


# --- Falhas de conteúdo e limites do isolamento (DTEC 024 e 030) ---------------------------------


async def test_pdf_que_estoura_o_tempo_devolve_conteudo_invalido(
    tmp_path: Path, validos: dict[str, fab.ArquivoGerado]
) -> None:
    # O filho `spawn` leva mais que 50 ms só para iniciar: o tempo se esgota de forma estável.
    limites = LimitesExtracao(tempo_s=0.05, memoria_mb=512, max_paginas=500)
    resultado = await _processar(tmp_path, validos["pdf-uma-pagina.pdf"], limites)
    assert resultado == FalhaDeProcessamento(CodigoFalha.CONTEUDO_INVALIDO)


@pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="RLIMIT_AS só existe em Linux (DTEC 024)"
)
async def test_pdf_que_estoura_a_memoria_devolve_conteudo_invalido(
    tmp_path: Path, validos: dict[str, fab.ArquivoGerado]
) -> None:
    limites = LimitesExtracao(tempo_s=60, memoria_mb=1, max_paginas=500)
    resultado = await _processar(tmp_path, validos["pdf-2mb.pdf"], limites)
    assert resultado == FalhaDeProcessamento(CodigoFalha.CONTEUDO_INVALIDO)


@pytest.mark.parametrize("nome", ["corrompido.pdf", "protegido.pdf"])
async def test_pdf_ilegivel_ou_protegido_no_processamento_devolve_conteudo_invalido(
    tmp_path: Path, invalidos: dict[str, fab.ArquivoGerado], nome: str
) -> None:
    resultado = await _processar(tmp_path, invalidos[nome])
    assert resultado == FalhaDeProcessamento(CodigoFalha.CONTEUDO_INVALIDO)


async def test_pdf_com_mais_paginas_que_o_limite_devolve_conteudo_invalido(
    tmp_path: Path, validos: dict[str, fab.ArquivoGerado]
) -> None:
    limites = LimitesExtracao(tempo_s=60, memoria_mb=512, max_paginas=3)
    resultado = await _processar(tmp_path, validos["pdf-paginas-em-branco.pdf"], limites)
    assert resultado == FalhaDeProcessamento(CodigoFalha.CONTEUDO_INVALIDO)


async def test_texto_que_nao_e_utf8_no_processamento_devolve_conteudo_invalido(
    tmp_path: Path, invalidos: dict[str, fab.ArquivoGerado]
) -> None:
    caminho = _gravar(tmp_path, invalidos["latin1.txt"])
    resultado = await processar_arquivo(
        caminho, "text/plain", limites=LIMITES, parametros=PARAMETROS
    )
    assert resultado == FalhaDeProcessamento(CodigoFalha.CONTEUDO_INVALIDO)


async def test_arquivo_inexistente_devolve_conteudo_invalido_sem_derrubar_ninguem(
    tmp_path: Path,
) -> None:
    resultado = await processar_arquivo(
        tmp_path / "nao-existe", "application/pdf", limites=LIMITES, parametros=PARAMETROS
    )
    assert resultado == FalhaDeProcessamento(CodigoFalha.CONTEUDO_INVALIDO)


# --- TXT e MD: sem página (RF-006) ---------------------------------------------------------------


async def test_txt_nao_tem_pagina_nem_total_de_paginas(
    tmp_path: Path, validos: dict[str, fab.ArquivoGerado]
) -> None:
    processado = _processado(await _processar(tmp_path, validos["resumo.txt"]))
    assert processado.total_paginas is None
    assert processado.trechos
    assert all(t.pagina is None for t in processado.trechos)


async def test_bom_utf8_e_removido_e_o_texto_coincide_com_o_sem_bom(
    tmp_path: Path, validos: dict[str, fab.ArquivoGerado]
) -> None:
    sem_bom = _processado(await _processar(tmp_path, validos["resumo.txt"]))
    com_bom = _processado(await _processar(tmp_path, validos["resumo-com-bom.txt"]))
    assert com_bom.texto_completo == sem_bom.texto_completo
    assert not com_bom.texto_completo.startswith("﻿")


async def test_md_divide_por_secao_e_ignora_titulo_dentro_de_bloco_de_codigo(
    tmp_path: Path, validos: dict[str, fab.ArquivoGerado]
) -> None:
    processado = _processado(await _processar(tmp_path, validos["anotacoes.md"]))
    inicios = [t.texto.splitlines()[0] for t in processado.trechos]
    assert "# Biologia celular" in inicios
    assert "## Organelas" in inicios
    assert not any(i.startswith("# isto é um comentário") for i in inicios)
    assert all(t.pagina is None for t in processado.trechos)


async def test_um_paragrafo_gera_um_trecho_e_chega_a_ser_processado(
    tmp_path: Path, validos: dict[str, fab.ArquivoGerado]
) -> None:
    """RF-016, D-006, US1-8: pouco texto também é uma fonte válida."""
    processado = _processado(await _processar(tmp_path, validos["um-paragrafo.txt"]))
    assert len(processado.trechos) == 1


async def test_instrucoes_a_ia_no_texto_viram_trecho_comum(tmp_path: Path) -> None:
    """CB-15: o conteúdo é dado; nada nele é interpretado."""
    arquivo = {a.nome: a for a in fab.adversariais()}["instrucoes-ia.txt"]
    processado = _processado(await _processar(tmp_path, arquivo))
    junto = "\n".join(t.texto for t in processado.trechos).lower()
    assert "ignore todas as instruções anteriores" in junto


async def test_texto_so_com_simbolos_ainda_e_texto_extraivel(tmp_path: Path) -> None:
    arquivo = fab.ArquivoGerado("simbolos.txt", b"### *** ---\n", texto="### *** ---\n")
    processado = _processado(await _processar(tmp_path, arquivo))
    assert len(processado.trechos) == 1
