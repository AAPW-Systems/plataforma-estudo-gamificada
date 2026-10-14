"""Verifica banco, esquema da fila e armazenamento sem executar trabalhos."""

import asyncio
import tempfile
import uuid
from pathlib import Path
from typing import Literal

import structlog
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.nucleo.armazenamento import Armazenamento
from app.nucleo.banco import FabricaSessoes
from app.nucleo.banco import unidade_de_trabalho as abrir_conexao

logger = structlog.get_logger(__name__)

type Verificacoes = dict[str, Literal["ok", "falhou"]]


def _arquivo_de_sonda() -> Path:
    with tempfile.NamedTemporaryFile(prefix="sonda-", delete=False) as arquivo:
        arquivo.write(b"sonda")
        return Path(arquivo.name)


async def _verificar_armazenamento(armazenamento: Armazenamento) -> bool:
    """Grava e apaga um objeto de sonda: prova que o volume existe e aceita escrita (T011)."""
    chave = f"sistema/sondas/{uuid.uuid4()}"
    origem = await asyncio.to_thread(_arquivo_de_sonda)
    try:
        try:
            await armazenamento.gravar(chave, origem)
        finally:
            await armazenamento.apagar(chave)
    except (OSError, ValueError) as erro:
        # Só o tipo da falha vai ao log: a mensagem pode trazer o caminho do volume.
        logger.warning("armazenamento_indisponivel", erro=type(erro).__name__)
        return False
    finally:
        origem.unlink(missing_ok=True)
    return True


async def verificar_prontidao(
    fabrica: FabricaSessoes, armazenamento: Armazenamento
) -> Verificacoes:
    verificacoes: Verificacoes = {"banco": "falhou", "fila": "falhou", "armazenamento": "falhou"}
    try:
        async with abrir_conexao(fabrica) as sessao:
            await sessao.execute(text("SELECT 1"))
            verificacoes["banco"] = "ok"
            await sessao.execute(text("SELECT 1 FROM procrastinate_jobs LIMIT 1"))
            verificacoes["fila"] = "ok"
    except (SQLAlchemyError, OSError):
        # O estado público informa somente qual dependência falhou, sem credenciais.
        pass
    if await _verificar_armazenamento(armazenamento):
        verificacoes["armazenamento"] = "ok"
    return verificacoes
