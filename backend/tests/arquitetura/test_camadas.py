"""DTEC 018 / T023: fronteiras de importação verificadas por AST, inclusive relativas."""

import ast
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit
RAIZ = Path(__file__).parents[2] / "src" / "app"
PROIBIDOS = {
    "rotas": {"modelos", "repositorios", "sqlalchemy"},
    "dtos": {"modelos", "fastapi", "starlette"},
    "mapeadores": {"fastapi", "starlette", "banco", "sqlalchemy"},
    "servicos": {"fastapi", "starlette", "dtos"},
    "dominio": {"sqlalchemy", "fastapi", "starlette"},
    "repositorios": {"fastapi", "starlette", "dtos"},
}


def importacoes(codigo: str, modulo: str) -> list[str]:
    encontrados: list[str] = []
    for no in ast.walk(ast.parse(codigo)):
        if isinstance(no, ast.Import):
            encontrados.extend(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom):
            pacote = modulo.split(".")[: -no.level] if no.level else []
            base = ".".join([*pacote, no.module or ""]).strip(".")
            encontrados.extend(f"{base}.{alias.name}" for alias in no.names)
    return encontrados


def violacoes(codigo: str, modulo: str) -> list[str]:
    camada = modulo.split(".")[-1]
    erros = []
    for importacao in importacoes(codigo, modulo):
        partes = set(importacao.split("."))
        if partes & PROIBIDOS.get(camada, set()):
            erros.append(importacao)
        # Modelos precisam dos tipos padrão e da Base compartilhada, sem comportamento.
        if camada == "modelos" and not (
            importacao.split(".")[0] in sys.stdlib_module_names | {"sqlalchemy"}
            or importacao == "app.nucleo.banco.Base"
        ):
            erros.append(importacao)
    return erros


def test_camadas_respeitam_dtec018() -> None:
    erros: list[str] = []
    for arquivo in RAIZ.rglob("*.py"):
        relativo = arquivo.relative_to(RAIZ)
        if len(relativo.parts) < 2 or relativo.parts[0] == "nucleo":
            continue
        modulo = "app." + ".".join(relativo.with_suffix("").parts)
        erros.extend(
            f"{relativo}: {erro}" for erro in violacoes(arquivo.read_text(encoding="utf-8"), modulo)
        )
    assert not erros, "\n".join(erros)


@pytest.mark.parametrize(
    "modulo,codigo",
    [
        ("app.identidade.rotas", "from . import repositorios"),
        ("app.identidade.rotas", "from app.identidade import modelos"),
        ("app.identidade.dtos", "import fastapi"),
        ("app.identidade.servicos", "from .dtos import Entrada"),
        ("app.identidade.dominio", "from sqlalchemy import select"),
        ("app.identidade.mapeadores", "from app.nucleo.banco import FabricaSessoes"),
        ("app.identidade.repositorios", "import fastapi as web"),
        ("app.identidade.modelos", "from .dominio import normalizar"),
    ],
)
def test_detector_recusa_importacao_proibida(modulo: str, codigo: str) -> None:
    """DTEC 018: prova que uma violação futura realmente faz o detector falhar."""
    assert violacoes(codigo, modulo)
