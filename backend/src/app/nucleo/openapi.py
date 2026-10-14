"""Ajustes do OpenAPI gerado, para que bata com os contratos de projeto (RQ-005, DTEC 018)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

SUFIXO_DTO = "DTO"
_PREFIXO_REFERENCIA = "#/components/schemas/"


def _sem_sufixo(nome: str) -> str:
    if nome.endswith(SUFIXO_DTO) and nome != SUFIXO_DTO:
        return nome.removesuffix(SUFIXO_DTO)
    return nome


def _referencia_renomeada(chave: str, valor: Any) -> bool:
    return chave == "$ref" and isinstance(valor, str) and valor.startswith(_PREFIXO_REFERENCIA)


def _reescrever_referencias(no: Any) -> Any:
    if isinstance(no, dict):
        reescrito: dict[str, Any] = {}
        for chave, valor in no.items():
            if _referencia_renomeada(chave, valor):
                nome = valor.removeprefix(_PREFIXO_REFERENCIA)
                reescrito[chave] = _PREFIXO_REFERENCIA + _sem_sufixo(nome)
            else:
                reescrito[chave] = _reescrever_referencias(valor)
        return reescrito
    if isinstance(no, list):
        return [_reescrever_referencias(item) for item in no]
    return no


def remover_sufixo_dto(esquema: dict[str, Any]) -> dict[str, Any]:
    """`PerfilDTO` vira `Perfil` nos componentes e em todas as referências.

    O sufixo é uma convenção do código (DTEC 018); o contrato público não o usa.
    """
    esquema = _reescrever_referencias(esquema)
    componentes = esquema.get("components", {}).get("schemas", {})
    renomeados = {_sem_sufixo(nome): corpo for nome, corpo in componentes.items()}
    if len(renomeados) != len(componentes):
        raise ValueError("dois esquemas teriam o mesmo nome sem o sufixo DTO")
    if componentes:
        esquema["components"]["schemas"] = renomeados
    return esquema


def instalar_openapi(app: FastAPI) -> None:
    """Substitui `app.openapi()` por uma versão com os nomes do contrato (guarda em cache)."""

    def openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            gerado = get_openapi(
                title=app.title,
                version=app.version,
                routes=app.routes,
                description=app.description,
            )
            app.openapi_schema = remover_sufixo_dto(gerado)
        return app.openapi_schema

    app.openapi = openapi  # type: ignore[method-assign]
