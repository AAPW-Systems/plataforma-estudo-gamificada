"""Tarefas assíncronas das fontes (spec 002; DTEC 025 e 030).

- `processar_fonte(fonte_id)`: enfileirada na transação do envio (e da nova tentativa), com
  `queueing_lock` e `lock` por fonte. Termina **sem efeito** se a fonte sumiu ou já está num
  estado final; nenhuma trava de banco fica aberta durante a leitura nem a extração.
- `reconciliar_objetos`: diária (3h30 UTC); apaga objetos sem linha criados há mais de
  `RECONCILIACAO_MARGEM_MIN` minutos (a queda do processo entre a gravação e a confirmação).

A lógica fica em `executar_*`, testável sem a fila; as tarefas só ligam as dependências.
"""

from __future__ import annotations

import asyncio
import re
import shutil
import tempfile
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path

import psycopg
import structlog
from procrastinate import JobContext, RetryStrategy
from sqlalchemy import select
from sqlalchemy.exc import InterfaceError, OperationalError

from app.fontes.divisao import Parametros
from app.fontes.dominio import CodigoFalha, EstadoFonte, estado_final
from app.fontes.modelos import Fonte
from app.fontes.processamento import (
    ArquivoProcessado,
    FalhaDeProcessamento,
    LimitesExtracao,
    processar_arquivo,
)
from app.fontes.repositorios import RepositorioFontes
from app.identidade.modelos import Usuario
from app.nucleo.armazenamento import Armazenamento, ObjetoInexistente, criar_armazenamento
from app.nucleo.banco import FabricaSessoes, criar_engine, criar_fabrica, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao, obter_configuracao
from app.nucleo.fila import ErroTransitorio, app_fila
from app.nucleo.isolamento import ExecutorIsolado, executar_isolado

logger = structlog.get_logger(__name__)

# `RetryStrategy(max_attempts=2)`: até 2 novas tentativas (3 execuções); a terceira é a última.
NOVAS_TENTATIVAS = 2
_CHAVE_DE_FONTE = re.compile(r"usuarios/[^/]+/fontes/[^/]+")
_LOTE_DA_RECONCILIACAO = 500
_ERROS_TRANSITORIOS = (OSError, OperationalError, InterfaceError, psycopg.OperationalError)


class ResultadoProcessamento(StrEnum):
    CONCLUIDA = "concluida"
    FALHOU = "falhou"
    SEM_EFEITO = "sem_efeito"


@dataclass(frozen=True, slots=True)
class DependenciasTarefas:
    """O que as tarefas usam; os testes trocam por versões ligadas ao banco de teste."""

    fabrica: FabricaSessoes
    armazenamento: Armazenamento
    configuracao: Configuracao
    semaforo: asyncio.Semaphore | None = None


_instaladas: DependenciasTarefas | None = None
_padrao: DependenciasTarefas | None = None


def usar_dependencias(dependencias: DependenciasTarefas) -> None:
    global _instaladas
    _instaladas = dependencias


def restaurar_dependencias() -> None:
    global _instaladas
    _instaladas = None


def obter_dependencias() -> DependenciasTarefas:
    """As dependências instaladas pelos testes ou, no worker, as da configuração do ambiente."""
    global _padrao
    if _instaladas is not None:
        return _instaladas
    if _padrao is None:
        configuracao = obter_configuracao()
        _padrao = DependenciasTarefas(
            fabrica=criar_fabrica(criar_engine(configuracao)),
            armazenamento=criar_armazenamento(configuracao),
            configuracao=configuracao,
        )
    return _padrao


# --- processar_fonte -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Partida:
    """O que a transação A deixa para as etapas seguintes (valores, não a entidade)."""

    chave: str
    tipo_midia: str
    fonte_public_id: str
    usuario_public_id: str


async def executar_processar_fonte(
    fonte_id: int,
    deps: DependenciasTarefas,
    *,
    ultima_tentativa: bool,
    executor: ExecutorIsolado = executar_isolado,
) -> ResultadoProcessamento:
    """Transação A, leitura, extração e transação B (DTEC 030)."""
    try:
        return await _processar(fonte_id, deps, executor)
    except ErroTransitorio:
        if not ultima_tentativa:
            raise  # a fila tenta de novo, com espera crescente; a fonte segue `processando`
        await _gravar_falha(fonte_id, deps, CodigoFalha.FALHA_TECNICA)
        return ResultadoProcessamento.FALHOU
    except Exception:
        # Defeito inesperado: não deixar a fonte presa em `processando`; o job aparece como
        # falho para quem opera, e o estudante pode tentar de novo.
        logger.exception("processamento_falhou", codigo=str(CodigoFalha.FALHA_TECNICA))
        await _gravar_falha(fonte_id, deps, CodigoFalha.FALHA_TECNICA)
        raise


async def _processar(
    fonte_id: int, deps: DependenciasTarefas, executor: ExecutorIsolado
) -> ResultadoProcessamento:
    inicio = time.monotonic()
    agora = datetime.now(UTC)
    # Transação A: trava, confere o estado e grava `processando`; a trava termina aqui.
    try:
        async with unidade_de_trabalho(deps.fabrica) as sessao:
            fonte = await RepositorioFontes(sessao).bloquear_por_id(fonte_id)
            if fonte is None or estado_final(EstadoFonte(fonte.estado)):
                return ResultadoProcessamento.SEM_EFEITO
            fonte.estado = EstadoFonte.PROCESSANDO.value
            fonte.atualizado_em = agora
            usuario_public_id = (
                await sessao.execute(
                    select(Usuario.public_id).where(Usuario.id == fonte.usuario_id)
                )
            ).scalar_one()
            partida = _Partida(
                fonte.chave_objeto, fonte.tipo_midia, str(fonte.public_id), str(usuario_public_id)
            )
    except _ERROS_TRANSITORIOS as erro:
        raise ErroTransitorio(type(erro).__name__) from erro
    logger.info(
        "processamento_iniciado",
        fonte_public_id=partida.fonte_public_id,
        usuario_public_id=partida.usuario_public_id,
    )

    diretorio = Path(await asyncio.to_thread(tempfile.mkdtemp))
    try:
        destino = diretorio / "objeto"
        try:
            await deps.armazenamento.ler_para_arquivo(partida.chave, destino)
        except ObjetoInexistente:
            # O objeto sumiu: se a fonte também, a exclusão venceu (CB-16); senão, falha técnica.
            if not await _fonte_existe(fonte_id, deps):
                return ResultadoProcessamento.SEM_EFEITO
            return await _gravar_falha(fonte_id, deps, CodigoFalha.FALHA_TECNICA, partida)
        except OSError as erro:
            raise ErroTransitorio(type(erro).__name__) from erro
        c = deps.configuracao
        processado = await processar_arquivo(
            destino,
            partida.tipo_midia,
            limites=LimitesExtracao(c.extracao_tempo_s, c.extracao_memoria_mb, c.pdf_max_paginas),
            parametros=Parametros(
                c.trecho_tamanho_alvo, c.trecho_tamanho_maximo, c.trecho_sobreposicao
            ),
            semaforo=deps.semaforo,
            executor=executor,
        )
    finally:
        await asyncio.to_thread(shutil.rmtree, diretorio, True)

    return await _concluir(fonte_id, deps, partida, processado, inicio)


async def _concluir(
    fonte_id: int,
    deps: DependenciasTarefas,
    partida: _Partida,
    processado: ArquivoProcessado | FalhaDeProcessamento,
    inicio: float,
) -> ResultadoProcessamento:
    """Transação B: trava de novo; fonte excluída no meio termina sem gravar nada (CB-16)."""
    agora = datetime.now(UTC)
    try:
        async with unidade_de_trabalho(deps.fabrica) as sessao:
            repositorio = RepositorioFontes(sessao)
            fonte = await repositorio.bloquear_por_id(fonte_id)
            if fonte is None or EstadoFonte(fonte.estado) is not EstadoFonte.PROCESSANDO:
                return ResultadoProcessamento.SEM_EFEITO
            # Sobras de uma execução anterior que não chegou ao fim (RF-008).
            await repositorio.apagar_trechos(fonte.id)
            fonte.atualizado_em = agora
            if isinstance(processado, FalhaDeProcessamento):
                fonte.estado = EstadoFonte.FALHOU.value
                fonte.codigo_falha = processado.codigo.value
            else:
                await repositorio.inserir_trechos(fonte.id, processado.trechos)
                fonte.estado = EstadoFonte.CONCLUIDO.value
                fonte.total_trechos = len(processado.trechos)
                fonte.total_paginas = processado.total_paginas
                fonte.versao_extracao = processado.versao_extracao
                fonte.processada_em = agora
    except _ERROS_TRANSITORIOS as erro:
        raise ErroTransitorio(type(erro).__name__) from erro
    duracao_ms = round((time.monotonic() - inicio) * 1000)
    if isinstance(processado, FalhaDeProcessamento):
        logger.info(
            "processamento_falhou",
            fonte_public_id=partida.fonte_public_id,
            usuario_public_id=partida.usuario_public_id,
            codigo=str(processado.codigo),
            duracao_ms=duracao_ms,
        )
        return ResultadoProcessamento.FALHOU
    logger.info(
        "processamento_concluido",
        fonte_public_id=partida.fonte_public_id,
        usuario_public_id=partida.usuario_public_id,
        duracao_ms=duracao_ms,
        paginas=processado.total_paginas,
        trechos=len(processado.trechos),
    )
    return ResultadoProcessamento.CONCLUIDA


async def _fonte_existe(fonte_id: int, deps: DependenciasTarefas) -> bool:
    try:
        async with unidade_de_trabalho(deps.fabrica) as sessao:
            consulta = select(Fonte.id).where(Fonte.id == fonte_id)
            return (await sessao.execute(consulta)).scalar_one_or_none() is not None
    except _ERROS_TRANSITORIOS as erro:
        raise ErroTransitorio(type(erro).__name__) from erro


async def _gravar_falha(
    fonte_id: int,
    deps: DependenciasTarefas,
    codigo: CodigoFalha,
    partida: _Partida | None = None,
) -> ResultadoProcessamento:
    """Grava `falhou` com o código, se a fonte ainda existe e segue sem estado final."""
    async with unidade_de_trabalho(deps.fabrica) as sessao:
        fonte = await RepositorioFontes(sessao).bloquear_por_id(fonte_id)
        if fonte is None or estado_final(EstadoFonte(fonte.estado)):
            return ResultadoProcessamento.SEM_EFEITO
        await RepositorioFontes(sessao).apagar_trechos(fonte.id)
        fonte.estado = EstadoFonte.FALHOU.value
        fonte.codigo_falha = codigo.value
        fonte.atualizado_em = datetime.now(UTC)
        public_id = str(fonte.public_id)
    logger.info(
        "processamento_falhou",
        fonte_public_id=partida.fonte_public_id if partida else public_id,
        codigo=str(codigo),
    )
    return ResultadoProcessamento.FALHOU


@app_fila.task(
    name="fontes.processar_fonte",
    pass_context=True,
    retry=RetryStrategy(
        max_attempts=NOVAS_TENTATIVAS, exponential_wait=5, retry_exceptions={ErroTransitorio}
    ),
)
async def processar_fonte(contexto: JobContext, fonte_id: int) -> None:
    await executar_processar_fonte(
        fonte_id,
        obter_dependencias(),
        ultima_tentativa=contexto.job.attempts >= NOVAS_TENTATIVAS,
    )


# --- reconciliar_objetos -------------------------------------------------------------------------


async def executar_reconciliacao(deps: DependenciasTarefas, agora: datetime) -> int:
    """Apaga objetos de fonte sem linha, mais antigos que a margem (DTEC 025); devolve quantos."""
    margem = timedelta(minutes=deps.configuracao.reconciliacao_margem_min)
    objetos = await deps.armazenamento.listar_prefixo("usuarios/")
    candidatos = [
        o.chave
        for o in objetos
        if _CHAVE_DE_FONTE.fullmatch(o.chave) and agora - o.criado_em > margem
    ]
    apagados = 0
    for inicio in range(0, len(candidatos), _LOTE_DA_RECONCILIACAO):
        lote = candidatos[inicio : inicio + _LOTE_DA_RECONCILIACAO]
        async with unidade_de_trabalho(deps.fabrica) as sessao:
            consulta = select(Fonte.chave_objeto).where(Fonte.chave_objeto.in_(lote))
            com_linha = set((await sessao.execute(consulta)).scalars())
        for chave in lote:
            if chave not in com_linha and await deps.armazenamento.apagar(chave):
                apagados += 1
    if apagados:
        logger.warning("objetos_reconciliados", quantidade=apagados)
    return apagados


@app_fila.periodic(cron="30 3 * * *")
@app_fila.task(name="fontes.reconciliar_objetos", pass_context=False)
async def reconciliar_objetos(timestamp: int) -> None:
    await executar_reconciliacao(obter_dependencias(), datetime.now(UTC))
