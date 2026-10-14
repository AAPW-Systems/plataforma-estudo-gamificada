"""Funções executadas **dentro do subprocesso isolado** (DTEC 024 e 029).

Abrem o arquivo do estudante: PyMuPDF para PDF e decodificação UTF-8 para TXT e MD. Só stdlib e
PyMuPDF, para o filho nascer rápido (nada do núcleo, do FastAPI ou do SQLAlchemy). Recebem e
devolvem só dados simples e serializáveis; um defeito do arquivo vira um resultado nomeado, e a
mensagem da exceção (que pode trazer caminho ou conteúdo) nunca sai daqui.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pymupdf

TIPO_PDF = "application/pdf"


def verificar_pdf(caminho: str, max_paginas: int) -> dict[str, Any]:
    """Abre o PDF e confere senha e número de páginas (DTEC 028, passo 8).

    Resultados: `ok` (com `paginas`), `protegido`, `paginas_excedidas` e `corrompido`.
    """
    pymupdf.TOOLS.mupdf_display_errors(False)
    try:
        with pymupdf.open(caminho, filetype="pdf") as documento:
            if documento.needs_pass:
                return {"resultado": "protegido"}
            paginas = documento.page_count
            if paginas < 1:
                return {"resultado": "corrompido"}
            if paginas > max_paginas:
                return {"resultado": "paginas_excedidas", "paginas": paginas}
            documento.load_page(0)  # uma árvore de páginas quebrada só aparece ao carregar
            return {"resultado": "ok", "paginas": paginas}
    except Exception:  # qualquer defeito do arquivo vira "corrompido"
        return {"resultado": "corrompido"}


def extrair(caminho: str, tipo_midia: str, max_paginas: int) -> dict[str, Any]:
    """Texto bruto da fonte.

    PDF: `{"resultado": "ok", "paginas": [texto da página 1, texto da página 2, ...]}`.
    TXT e MD: `{"resultado": "ok", "texto": ...}`, sem o BOM. Falhas: `protegido`,
    `paginas_excedidas`, `corrompido` e `ilegivel`.
    """
    if tipo_midia == TIPO_PDF:
        return _extrair_pdf(caminho, max_paginas)
    return _extrair_texto(caminho)


def _extrair_pdf(caminho: str, max_paginas: int) -> dict[str, Any]:
    pymupdf.TOOLS.mupdf_display_errors(False)
    try:
        with pymupdf.open(caminho, filetype="pdf") as documento:
            if documento.needs_pass:
                return {"resultado": "protegido"}
            if documento.page_count > max_paginas:
                return {"resultado": "paginas_excedidas"}
            # A página é o número físico (índice + 1), igual ao contador de qualquer leitor.
            paginas = [
                pagina.get_text("text", sort=True, flags=pymupdf.TEXT_DEHYPHENATE)
                for pagina in documento
            ]
            return {"resultado": "ok", "paginas": paginas}
    except Exception:  # qualquer defeito do arquivo vira "corrompido"
        return {"resultado": "corrompido"}


def _extrair_texto(caminho: str) -> dict[str, Any]:
    try:
        bruto = Path(caminho).read_bytes()
    except OSError:
        return {"resultado": "ilegivel"}
    try:
        return {"resultado": "ok", "texto": bruto.decode("utf-8-sig")}
    except UnicodeDecodeError:
        return {"resultado": "ilegivel"}
