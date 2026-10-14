"""Leitura do contrato de projeto (`docs/specs/NNN/contracts/openapi.yaml`) e comparações.

O contrato de projeto é a referência (RQ-005); o OpenAPI gerado pela aplicação tem de
contê-lo. As comparações aqui são deliberadamente estruturais: caminhos, métodos, códigos de
resposta, esquemas, campos obrigatórios, tipos, formatos e limites declarados.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from functools import cache
from pathlib import Path
from typing import Any

import yaml

RAIZ = Path(__file__).parents[2]
CONTRATO_001 = RAIZ / "docs" / "specs" / "001-conta-acesso" / "contracts" / "openapi.yaml"
CONTRATO_002 = RAIZ / "docs" / "specs" / "002-materias-fontes" / "contracts" / "openapi.yaml"
# O enum `Erro.codigo` é cumulativo: o da última spec contém os códigos de todas as anteriores.
CONTRATOS = (CONTRATO_001, CONTRATO_002)

RESTRICOES = (
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "multipleOf",
    "format",
    "writeOnly",
    "additionalProperties",
    "minProperties",
)


@cache
def carregar_contrato(caminho: Path = CONTRATO_001) -> dict[str, Any]:
    conteudo = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    assert isinstance(conteudo, dict)
    return conteudo


def resolver(documento: Mapping[str, Any], no: Any) -> Any:
    """Segue `$ref` locais até um nó sem referência."""
    while isinstance(no, Mapping) and "$ref" in no:
        destino: Any = documento
        for parte in str(no["$ref"]).removeprefix("#/").split("/"):
            destino = destino[parte]
        no = destino
    return no


def nome_da_referencia(no: Any) -> str | None:
    if isinstance(no, Mapping) and "$ref" in no:
        return str(no["$ref"]).rsplit("/", 1)[-1]
    return None


def resumo_do_esquema(documento: Mapping[str, Any], no: Any) -> dict[str, Any]:
    """Forma comparável de um esquema: tipos, enum e restrições, com `anyOf` achatado."""
    no = resolver(documento, no)
    tipos: set[str] = set()
    restricoes: dict[str, Any] = {}
    enum: set[Any] = set()

    def absorver(parte: Any) -> None:
        parte = resolver(documento, parte)
        for ramo in parte.get("anyOf", []) + parte.get("oneOf", []):
            absorver(ramo)
        declarado = parte.get("type")
        if isinstance(declarado, str):
            tipos.add(declarado)
        elif isinstance(declarado, list):
            tipos.update(declarado)
        enum.update(parte.get("enum", []))
        for chave in RESTRICOES:
            if chave in parte:
                restricoes[chave] = parte[chave]

    absorver(no)
    return {"tipos": tipos, "enum": enum, "restricoes": restricoes}


def validar_corpo_erro(corpo: Any, contrato: Mapping[str, Any] | None = None) -> None:
    """Valida `corpo` contra o esquema `Erro` do contrato (campos, tipos e códigos)."""
    contrato = contrato or carregar_contrato(CONTRATOS[-1])
    esquema = contrato["components"]["schemas"]["Erro"]
    assert isinstance(corpo, dict), f"o corpo de erro não é um objeto: {corpo!r}"
    faltando = set(esquema["required"]) - set(corpo)
    assert not faltando, f"campos obrigatórios ausentes no corpo de erro: {sorted(faltando)}"
    extras = set(corpo) - set(esquema["properties"])
    assert not extras, f"campos fora do contrato no corpo de erro: {sorted(extras)}"
    assert corpo["codigo"] in esquema["properties"]["codigo"]["enum"], (
        f"código fora do enum do contrato: {corpo['codigo']!r}"
    )
    assert isinstance(corpo["mensagem"], str) and corpo["mensagem"]
    uuid.UUID(corpo["idRequisicao"])
    for campo in corpo.get("campos", []):
        assert set(campo) == {"campo", "mensagem"}, campo
        assert isinstance(campo["campo"], str) and isinstance(campo["mensagem"], str)
