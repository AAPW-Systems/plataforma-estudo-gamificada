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


# Spec 002 (plano, "Dependências entre domínios"): `materias` não importa `fontes` (as contagens e
# a exclusão das fontes chegam pelo participante da DTEC 027). Os módulos puros de `fontes` não
# conhecem framework nem banco; `extracao` roda no subprocesso e também não importa o núcleo.
MODULOS_PUROS_FONTES = {"app.fontes.extracao", "app.fontes.divisao", "app.fontes.validacao"}
FRAMEWORKS = {"fastapi", "starlette", "sqlalchemy"}
# Spec 003 (plano, "Dependências entre domínios"): `cartoes` depende de `materias` e de `fontes`, e
# nunca o contrário. As regras puras dos cartões (a 004 as reutiliza) não conhecem framework.
DOMINIOS_QUE_NAO_CONHECEM_CARTOES = ("app.materias.", "app.fontes.", "app.identidade.", "app.ia.")
MODULOS_PUROS_CARTOES = {"app.cartoes.dominio", "app.cartoes.cursor"}
# Spec 004 (plano, "Dependências entre domínios"): `ia` é a única porta para o provedor e não
# conhece nenhum domínio de negócio; o PydanticAI só aparece em `ia/` e na definição dos agentes;
# as regras puras da geração não conhecem framework, banco nem o PydanticAI.
DOMINIOS_DE_NEGOCIO = (
    "app.identidade",
    "app.materias",
    "app.fontes",
    "app.cartoes",
    "app.revisao",
    "app.saude",
)
MODULOS_COM_PYDANTIC_AI = ("app.ia.", "app.cartoes.geracao.agentes")
MODULOS_PUROS_GERACAO = {"app.cartoes.geracao.dominio", "app.cartoes.geracao.validacao"}
# Nomes que só o domínio `ia` lê: as chaves e o provedor configurado.
LEITURAS_EXCLUSIVAS_DA_IA = (
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "gemini_api_key",
    "groq_api_key",
    "IA_PROVEDOR",
    "ia_provedor",
    "chave_api",
)


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
        if modulo.startswith("app.materias.") and importacao.startswith("app.fontes"):
            erros.append(importacao)
        if modulo in MODULOS_PUROS_FONTES and partes & FRAMEWORKS:
            erros.append(importacao)
        if modulo.startswith(DOMINIOS_QUE_NAO_CONHECEM_CARTOES) and importacao.startswith(
            "app.cartoes"
        ):
            erros.append(importacao)
        if modulo in MODULOS_PUROS_CARTOES and partes & FRAMEWORKS:
            erros.append(importacao)
        if modulo == "app.fontes.extracao" and importacao.startswith("app.nucleo"):
            erros.append(importacao)
        if modulo.startswith("app.ia.") and importacao.startswith(DOMINIOS_DE_NEGOCIO):
            erros.append(importacao)
        if modulo in MODULOS_PUROS_GERACAO and partes & (FRAMEWORKS | {"pydantic_ai"}):
            erros.append(importacao)
        if importacao.split(".")[0] == "pydantic_ai" and not modulo.startswith(
            MODULOS_COM_PYDANTIC_AI
        ):
            erros.append(importacao)
        # Modelos precisam dos tipos padrão e da Base compartilhada, sem comportamento.
        if camada == "modelos" and not (
            importacao.split(".")[0] in sys.stdlib_module_names | {"sqlalchemy"}
            or importacao == "app.nucleo.banco.Base"
        ):
            erros.append(importacao)
    return erros


def _modulos_de_app() -> list[tuple[str, Path]]:
    return [
        ("app." + ".".join(arquivo.relative_to(RAIZ).with_suffix("").parts), arquivo)
        for arquivo in RAIZ.rglob("*.py")
    ]


def test_pydantic_ai_so_em_ia_e_nos_agentes() -> None:
    """Spec 004: inclusive no núcleo e na composição, que o teste das camadas não percorre."""
    erros = [
        f"{modulo}: {importacao}"
        for modulo, arquivo in _modulos_de_app()
        for importacao in importacoes(arquivo.read_text(encoding="utf-8"), modulo)
        if importacao.split(".")[0] == "pydantic_ai"
        and not modulo.startswith(MODULOS_COM_PYDANTIC_AI)
    ]
    assert not erros, "\n".join(erros)


def leituras_da_ia_fora_dela(codigo: str, modulo: str) -> list[str]:
    if modulo.startswith("app.ia."):
        return []
    return [nome for nome in LEITURAS_EXCLUSIVAS_DA_IA if nome in codigo]


def test_chaves_e_provedor_so_sao_lidos_em_ia() -> None:
    """Spec 004 (RQ-001): trocar de provedor muda só `IA_PROVEDOR` e as chaves."""
    erros = [
        f"{modulo}: {nome}"
        for modulo, arquivo in _modulos_de_app()
        for nome in leituras_da_ia_fora_dela(arquivo.read_text(encoding="utf-8"), modulo)
    ]
    assert not erros, "\n".join(erros)


@pytest.mark.parametrize(
    "modulo,codigo",
    [
        ("app.cartoes.geracao.servicos", "x = configuracao.gemini_api_key"),
        ("app.principal", "os.environ['GROQ_API_KEY']"),
        ("app.cartoes.geracao.tarefas", "if configuracao_ia.ia_provedor == 'teste': pass"),
        ("app.nucleo.logs", "chave = cfg.chave_api"),
    ],
)
def test_detector_recusa_leitura_das_chaves_fora_de_ia(modulo: str, codigo: str) -> None:
    assert leituras_da_ia_fora_dela(codigo, modulo)


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
        ("app.materias.servicos", "from app.fontes.repositorios import RepositorioFontes"),
        ("app.materias.dominio", "from app.fontes import dominio"),
        ("app.fontes.extracao", "import fastapi"),
        ("app.fontes.extracao", "from sqlalchemy import text"),
        ("app.fontes.extracao", "from app.nucleo.erros import ErroAplicacao"),
        ("app.fontes.divisao", "from starlette.responses import Response"),
        ("app.fontes.validacao", "from sqlalchemy.ext.asyncio import AsyncSession"),
        # Spec 003: o acervo e a identidade não conhecem os cartões (DTEC 027 e 038).
        ("app.materias.servicos", "from app.cartoes.repositorios import RepositorioCartoes"),
        ("app.materias.dominio", "import app.cartoes.dominio"),
        ("app.fontes.registros", "from app.cartoes import modelos"),
        ("app.fontes.servicos", "from app.cartoes.registros import participante_cartoes"),
        ("app.identidade.servicos", "from app.cartoes.servicos import ServicoCartoes"),
        # O domínio e o cursor dos cartões são puros, sem framework nem banco.
        ("app.cartoes.dominio", "import fastapi"),
        ("app.cartoes.dominio", "from sqlalchemy import select"),
        ("app.cartoes.cursor", "import fastapi"),
        ("app.cartoes.cursor", "from sqlalchemy.ext.asyncio import AsyncSession"),
        ("app.cartoes.cursor", "from starlette.responses import Response"),
        # Spec 004: `ia` não conhece domínios de negócio, e ninguém do acervo conhece cartões.
        ("app.ia.cliente", "from app.cartoes.geracao.modelos import Geracao"),
        ("app.ia.servicos", "from app.fontes.consultas import fonte_do_dono"),
        ("app.ia.repositorios", "from app.identidade.modelos import Usuario"),
        ("app.ia.registros", "import app.materias.registros"),
        ("app.ia.aviso", "from app.revisao import dominio"),
        ("app.fontes.consultas", "from app.cartoes.geracao import dominio"),
        ("app.materias.registros", "from app.cartoes.geracao.registros import participante"),
        # O PydanticAI fica no `ia` e na definição dos agentes.
        ("app.cartoes.geracao.servicos", "from pydantic_ai import Agent"),
        ("app.cartoes.geracao.tarefas", "import pydantic_ai.models"),
        ("app.fontes.servicos", "from pydantic_ai.models.test import TestModel"),
        # As regras puras da geração não conhecem framework, banco nem o PydanticAI.
        ("app.cartoes.geracao.dominio", "from sqlalchemy import select"),
        ("app.cartoes.geracao.dominio", "import fastapi"),
        ("app.cartoes.geracao.validacao", "from pydantic_ai import Agent"),
        ("app.cartoes.geracao.validacao", "from starlette.responses import Response"),
    ],
)
def test_detector_recusa_importacao_proibida(modulo: str, codigo: str) -> None:
    """DTEC 018: prova que uma violação futura realmente faz o detector falhar."""
    assert violacoes(codigo, modulo)
