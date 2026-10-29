"""T008 (spec 004, DTEC 040): `ia/cliente.py` é o único ponto de chamada ao provedor.

Uma linha de `consumo_ia` por chamada, com sucesso ou falha, sem conteúdo; o orçamento é
conferido antes de chamar; o teto da execução e o tempo limite valem em toda chamada.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai import exceptions as e
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models import Model
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage
from sqlalchemy import select, text
from structlog.testing import capture_logs

from app.ia.cliente import ClienteIa, ContextoChamada
from app.ia.configuracao import ConfiguracaoIa
from app.ia.excecoes import ErroTransitorioIA, OrcamentoEsgotado, RespostaInvalida
from app.ia.modelos import ConsumoIa
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.relogio import RelogioControlavel
from tests.apoio_cartoes import semear_estudante

pytestmark = pytest.mark.integration

SENTINELA = "MITOCONDRIA-SECRETA-123"
AGORA = datetime(2026, 10, 20, 15, 0, tzinfo=UTC)  # 12:00 em Recife


class Saida(BaseModel):
    resposta: str


def _agente() -> Agent[None, Saida]:
    return Agent(output_type=Saida, instructions=f"Instrução {SENTINELA}", retries={"output": 1})


def _responde(
    resposta: str = f"ok {SENTINELA}", entrada: int = 100, saida: int = 20
) -> Callable[[list[ModelMessage], AgentInfo], ModelResponse]:
    def funcao(mensagens: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert info.output_tools
        return ModelResponse(
            parts=[ToolCallPart(info.output_tools[0].name, {"resposta": resposta})],
            usage=RequestUsage(input_tokens=entrada, output_tokens=saida),
        )

    return funcao


class Contador:
    def __init__(self, funcao: Callable[[list[ModelMessage], AgentInfo], ModelResponse]) -> None:
        self.chamadas = 0
        self.funcao = funcao

    def __call__(self, mensagens: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        self.chamadas += 1
        return self.funcao(mensagens, info)


def _cliente(
    fabrica: FabricaSessoes,
    modelo: Model,
    *,
    orcamento: int = 300_000,
    timeout: int = 60,
) -> ClienteIa:
    config = ConfiguracaoIa(
        app_ambiente="teste",
        ia_provedor="teste",
        ia_orcamento_tokens_dia=orcamento,
        ia_timeout_segundos=timeout,
    )
    return ClienteIa(fabrica, config, RelogioControlavel(AGORA), modelos=lambda _: modelo)


async def _contexto(fabrica: FabricaSessoes) -> ContextoChamada:
    async with unidade_de_trabalho(fabrica) as sessao:
        usuario, _ = await semear_estudante(sessao)
    return ContextoChamada(
        usuario_id=usuario.id,
        usuario_public_id=usuario.public_id,
        fuso="America/Recife",
        operacao="gerar_cartoes",
        versao_instrucoes="gerador-v1+juiza-v1",
    )


async def _consumos(fabrica: FabricaSessoes, usuario_id: int) -> list[ConsumoIa]:
    async with unidade_de_trabalho(fabrica) as sessao:
        consulta = select(ConsumoIa).where(ConsumoIa.usuario_id == usuario_id)
        return list((await sessao.execute(consulta.order_by(ConsumoIa.id))).scalars())


async def test_chamada_com_sucesso_registra_uma_linha_de_consumo(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    contexto = await _contexto(fabrica_sessoes)
    cliente = _cliente(fabrica_sessoes, FunctionModel(_responde(), model_name="simulado-a"))

    resultado = await cliente.executar(_agente(), f"Trechos {SENTINELA}", contexto)

    assert resultado.saida == Saida(resposta=f"ok {SENTINELA}")
    assert (resultado.tokens_entrada, resultado.tokens_saida) == (100, 20)
    [consumo] = await _consumos(fabrica_sessoes, contexto.usuario_id)
    assert consumo.sucesso is True
    assert (consumo.operacao, consumo.provedor, consumo.modelo) == (
        "gerar_cartoes",
        "teste",
        "simulado-a",
    )
    assert consumo.versao_instrucoes == "gerador-v1+juiza-v1"
    assert (consumo.tokens_entrada, consumo.tokens_saida) == (100, 20)
    assert consumo.latencia_ms >= 0
    assert consumo.geracao_id is None
    assert consumo.criado_em == AGORA


async def test_chamada_com_falha_tambem_registra_consumo_sem_tokens(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    contexto = await _contexto(fabrica_sessoes)

    def falha(mensagens: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise e.ModelHTTPError(503, "simulado", {"error": SENTINELA})

    cliente = _cliente(fabrica_sessoes, FunctionModel(falha, model_name="simulado"))

    with pytest.raises(ErroTransitorioIA):
        await cliente.executar(_agente(), "Trechos", contexto)

    [consumo] = await _consumos(fabrica_sessoes, contexto.usuario_id)
    assert consumo.sucesso is False
    assert (consumo.tokens_entrada, consumo.tokens_saida) == (None, None)


async def test_resposta_malformada_pede_correcao_uma_vez_e_falha(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    """DTEC 043: `output_retries=1`; depois disso, `resposta_invalida`."""
    contexto = await _contexto(fabrica_sessoes)

    def malformada(mensagens: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[TextPart("não é JSON")])

    contador = Contador(malformada)
    cliente = _cliente(fabrica_sessoes, FunctionModel(contador, model_name="simulado"))

    with pytest.raises(RespostaInvalida):
        await cliente.executar(_agente(), "Trechos", contexto)

    assert contador.chamadas == 2
    [consumo] = await _consumos(fabrica_sessoes, contexto.usuario_id)
    assert consumo.sucesso is False


async def test_orcamento_esgotado_impede_a_chamada(fabrica_sessoes: FabricaSessoes) -> None:
    """DTEC 040: conferido antes de cada chamada; o modelo nem é chamado."""
    contexto = await _contexto(fabrica_sessoes)
    contador = Contador(_responde(entrada=600, saida=400))
    cliente = _cliente(fabrica_sessoes, FunctionModel(contador), orcamento=1000)

    await cliente.executar(_agente(), "Trechos", contexto)
    with pytest.raises(OrcamentoEsgotado):
        await cliente.executar(_agente(), "Trechos", contexto)

    assert contador.chamadas == 1
    assert len(await _consumos(fabrica_sessoes, contexto.usuario_id)) == 1


async def test_orcamento_conta_so_o_dia_de_estudo_e_o_proprio_estudante(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    contexto = await _contexto(fabrica_sessoes)
    outro = await _contexto(fabrica_sessoes)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        for usuario_id, criado_em in (
            # ontem, antes da virada das 4h em Recife (07:00 UTC): não conta
            (contexto.usuario_id, datetime(2026, 10, 20, 6, 59, tzinfo=UTC)),
            # de outro estudante, hoje: não conta
            (outro.usuario_id, AGORA - timedelta(hours=1)),
        ):
            sessao.add(
                ConsumoIa(
                    usuario_id=usuario_id,
                    operacao="gerar_cartoes",
                    provedor="teste",
                    modelo="simulado",
                    tokens_entrada=5000,
                    tokens_saida=5000,
                    latencia_ms=1,
                    sucesso=True,
                    criado_em=criado_em,
                )
            )
    contador = Contador(_responde(entrada=10, saida=10))
    cliente = _cliente(fabrica_sessoes, FunctionModel(contador), orcamento=1000)

    await cliente.executar(_agente(), "Trechos", contexto)

    assert contador.chamadas == 1


async def test_tokens_nao_informados_nao_anulam_a_soma_do_dia(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    """Uma chamada com só os tokens de saída informados ainda conta (soma com nulos)."""
    contexto = await _contexto(fabrica_sessoes)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        sessao.add(
            ConsumoIa(
                usuario_id=contexto.usuario_id,
                operacao="gerar_cartoes",
                provedor="teste",
                modelo="simulado",
                tokens_entrada=None,
                tokens_saida=900,
                latencia_ms=1,
                sucesso=True,
                criado_em=AGORA - timedelta(minutes=5),
            )
        )
    cliente = _cliente(
        fabrica_sessoes, FunctionModel(_responde(entrada=60, saida=60)), orcamento=1000
    )

    # restam 100 tokens: a chamada de 120 passa do teto e vira orçamento esgotado
    with pytest.raises(OrcamentoEsgotado):
        await cliente.executar(_agente(), "Trechos", contexto)


async def test_teto_da_execucao_e_o_que_resta_do_orcamento(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    """`UsageLimits`: uma chamada não passa do orçamento do dia em mais de uma resposta."""
    contexto = await _contexto(fabrica_sessoes)
    capturado: dict[str, Any] = {}
    cliente = _cliente(
        fabrica_sessoes, FunctionModel(_responde(entrada=10, saida=10)), orcamento=500
    )
    original = cliente.limites

    def espiar(restante: int) -> Any:
        capturado["limites"] = original(restante)
        return capturado["limites"]

    cliente.limites = espiar  # type: ignore[method-assign, assignment]
    await cliente.executar(_agente(), "Trechos", contexto)
    assert capturado["limites"].total_tokens_limit == 500
    assert capturado["limites"].request_limit == 3

    estouro = _cliente(
        fabrica_sessoes, FunctionModel(_responde(entrada=900, saida=900)), orcamento=500
    )
    with pytest.raises(OrcamentoEsgotado):
        await estouro.executar(_agente(), "Trechos", contexto)
    # a chamada estourada também é registrada, como falha
    consumos = await _consumos(fabrica_sessoes, contexto.usuario_id)
    assert [c.sucesso for c in consumos] == [True, False]


async def test_tempo_limite_da_chamada(fabrica_sessoes: FabricaSessoes) -> None:
    contexto = await _contexto(fabrica_sessoes)

    async def lenta(mensagens: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        await asyncio.sleep(5)
        return _responde()(mensagens, info)

    cliente = _cliente(fabrica_sessoes, FunctionModel(lenta), timeout=1)

    with pytest.raises(ErroTransitorioIA):
        await cliente.executar(_agente(), "Trechos", contexto)
    [consumo] = await _consumos(fabrica_sessoes, contexto.usuario_id)
    assert consumo.sucesso is False
    assert 900 <= consumo.latencia_ms < 4000


async def test_consumo_e_logs_sem_conteudo(fabrica_sessoes: FabricaSessoes) -> None:
    """RQ-003: nem a linha de consumo nem o log levam instruções, entrada ou saída."""
    contexto = await _contexto(fabrica_sessoes)
    geracao_public_id = uuid.uuid4()
    contexto = replace(contexto, geracao_public_id=geracao_public_id)
    cliente = _cliente(fabrica_sessoes, FunctionModel(_responde(), model_name="simulado"))

    with capture_logs() as registros:
        await cliente.executar(_agente(), f"Trechos {SENTINELA}", contexto)

    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        linha = (
            await sessao.execute(
                text("SELECT row_to_json(c)::text FROM consumo_ia c WHERE usuario_id = :u"),
                {"u": contexto.usuario_id},
            )
        ).scalar_one()
    assert SENTINELA not in linha
    [evento] = [r for r in registros if r["event"] == "chamada_ia"]
    assert SENTINELA not in repr(registros)
    assert evento["usuario_id"] == str(contexto.usuario_public_id)
    assert evento["geracao_id"] == str(geracao_public_id)
    assert evento["sucesso"] is True
    assert (evento["tokens_entrada"], evento["tokens_saida"]) == (100, 20)


async def test_geracao_do_consumo_e_gravada(fabrica_sessoes: FabricaSessoes) -> None:
    contexto = await _contexto(fabrica_sessoes)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        materia = (
            await sessao.execute(
                text("SELECT id FROM materias WHERE usuario_id = :u"), {"u": contexto.usuario_id}
            )
        ).scalar_one()
        geracao_id = (
            await sessao.execute(
                text(
                    "INSERT INTO geracoes (usuario_id, materia_id, chave_idempotencia) "
                    "VALUES (:u, :m, gen_random_uuid()) RETURNING id"
                ),
                {"u": contexto.usuario_id, "m": materia},
            )
        ).scalar_one()
    contexto = replace(contexto, geracao_id=geracao_id)
    await _cliente(fabrica_sessoes, FunctionModel(_responde())).executar(
        _agente(), "Trechos", contexto
    )
    [consumo] = await _consumos(fabrica_sessoes, contexto.usuario_id)
    assert consumo.geracao_id == geracao_id
