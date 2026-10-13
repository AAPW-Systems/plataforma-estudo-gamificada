"""Verifica banco e acesso ao esquema da fila sem executar trabalhos."""

from typing import Literal

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.nucleo.banco import FabricaSessoes
from app.nucleo.banco import unidade_de_trabalho as abrir_conexao


async def verificar_prontidao(fabrica: FabricaSessoes) -> dict[str, Literal["ok", "falhou"]]:
    verificacoes: dict[str, Literal["ok", "falhou"]] = {"banco": "falhou", "fila": "falhou"}
    try:
        async with abrir_conexao(fabrica) as sessao:
            await sessao.execute(text("SELECT 1"))
            verificacoes["banco"] = "ok"
            await sessao.execute(text("SELECT 1 FROM procrastinate_jobs LIMIT 1"))
            verificacoes["fila"] = "ok"
    except (SQLAlchemyError, OSError):
        # O estado público informa somente qual dependência falhou, sem credenciais.
        return verificacoes
    return verificacoes
