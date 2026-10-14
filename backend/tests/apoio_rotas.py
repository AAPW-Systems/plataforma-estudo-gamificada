"""Enumeração das rotas de uma aplicação FastAPI, inclusive as de `include_router`.

Desde o FastAPI 0.14x, `app.routes` traz um `_IncludedRouter` por roteador incluído, e as rotas
de verdade ficam em `effective_candidates()`. O percurso abaixo é por *duck typing* (não importa
a classe privada) e inclui as rotas fora do esquema OpenAPI, que são as que mais importam para
a segurança. Os testes que o usam conferem a lista contra o OpenAPI (`test_a_enumeracao...`),
de modo que uma mudança futura da biblioteca nunca resulte numa lista vazia em silêncio.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from typing import Any

from fastapi import FastAPI

METODOS_DE_LEITURA = frozenset({"GET", "HEAD", "OPTIONS"})
PARAMETRO = re.compile(r"\{[^}]+\}")


def _percorrer(itens: Iterable[Any]) -> Iterator[tuple[str, str]]:
    for item in itens:
        if hasattr(item, "effective_candidates"):  # roteador incluído: desce um nível
            yield from _percorrer(item.effective_candidates())
            continue
        caminho = getattr(item, "path", None)
        metodos = getattr(item, "methods", None)
        if caminho and metodos:
            for metodo in metodos:
                yield metodo, caminho


def rotas_da_aplicacao(app: FastAPI) -> list[tuple[str, str]]:
    """Todos os pares (método, caminho), sem HEAD e OPTIONS, em ordem estável."""
    return sorted(
        {
            (metodo, caminho)
            for metodo, caminho in _percorrer(app.routes)
            if metodo not in {"HEAD", "OPTIONS"}
        }
    )


def rotas_do_openapi(app: FastAPI) -> set[tuple[str, str]]:
    esquema = app.openapi()
    return {
        (metodo.upper(), caminho)
        for caminho, item in esquema["paths"].items()
        for metodo in item
        if metodo in {"get", "post", "put", "patch", "delete"}
    }


def rotas_que_alteram_estado(app: FastAPI) -> list[tuple[str, str]]:
    return [rota for rota in rotas_da_aplicacao(app) if rota[0] not in METODOS_DE_LEITURA]
