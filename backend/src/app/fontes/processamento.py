"""Do arquivo guardado aos trechos: extração isolada, normalização e divisão (DTEC 024, 029 e 030).

É o miolo da tarefa `processar_fonte`, separado dela para ser testado sem fila nem banco. A
extração roda sempre no subprocesso (`executar_isolado`); aqui só se traduz o resultado em
trechos ou na falha de conteúdo que a spec distingue: `sem_texto` (CB-23) e `conteudo_invalido`.
Estouro de tempo ou de memória, arquivo ilegível ou protegido valem `conteudo_invalido`.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

from app.fontes import extracao
from app.fontes.divisao import (
    Parametros,
    TrechoDividido,
    dividir_pdf,
    dividir_texto,
    normalizar_texto,
    tem_texto,
    versao_extracao,
)
from app.fontes.dominio import CodigoFalha
from app.nucleo.isolamento import ResultadoIsolado, StatusIsolado, executar_isolado

logger = structlog.get_logger(__name__)

TIPO_MARKDOWN = "text/markdown"

type Executor = Callable[..., Awaitable[ResultadoIsolado]]


@dataclass(frozen=True, slots=True)
class LimitesExtracao:
    tempo_s: float
    memoria_mb: int
    max_paginas: int


@dataclass(frozen=True, slots=True)
class ArquivoProcessado:
    texto_completo: str
    trechos: list[TrechoDividido]
    total_paginas: int | None
    versao_extracao: str


@dataclass(frozen=True, slots=True)
class FalhaDeProcessamento:
    codigo: CodigoFalha


async def processar_arquivo(
    caminho: Path,
    tipo_midia: str,
    *,
    limites: LimitesExtracao,
    parametros: Parametros,
    semaforo: asyncio.Semaphore | None = None,
    executor: Executor = executar_isolado,
) -> ArquivoProcessado | FalhaDeProcessamento:
    resultado = await executor(
        extracao.extrair,
        (str(caminho), tipo_midia, limites.max_paginas),
        tempo_limite_s=limites.tempo_s,
        memoria_max_mb=limites.memoria_mb,
        semaforo=semaforo,
    )
    if resultado.status is not StatusIsolado.OK:
        # Só o status vai ao log: nada do arquivo (RQ-002).
        logger.warning("isolamento_esgotado", status=str(resultado.status))
        return FalhaDeProcessamento(CodigoFalha.CONTEUDO_INVALIDO)
    valor: dict[str, Any] = resultado.valor
    if valor.get("resultado") != "ok":
        return FalhaDeProcessamento(CodigoFalha.CONTEUDO_INVALIDO)

    if tipo_midia == extracao.TIPO_PDF:
        paginas: list[str] = valor["paginas"]
        dividido = dividir_pdf(paginas, parametros)
        if not tem_texto(dividido.texto_completo):
            return FalhaDeProcessamento(CodigoFalha.SEM_TEXTO)
        total_paginas: int | None = len(paginas)
    else:
        texto = normalizar_texto(valor["texto"])
        dividido = dividir_texto(texto, markdown=tipo_midia == TIPO_MARKDOWN, p=parametros)
        if not dividido.trechos:
            return FalhaDeProcessamento(CodigoFalha.CONTEUDO_INVALIDO)
        total_paginas = None
    return ArquivoProcessado(
        dividido.texto_completo, dividido.trechos, total_paginas, versao_extracao(parametros)
    )
