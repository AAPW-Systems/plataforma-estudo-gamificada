"""Único ponto de chamada ao provedor de IA (DTEC 040; plano da 004, "Dependências").

`ClienteIa.executar` confere o orçamento do dia de estudo, roda o agente com tempo limite e teto
de tokens, classifica as falhas e registra o consumo numa transação própria, com sucesso ou falha.
Nada do conteúdo (instruções, trechos, saída) vai para o banco nem para o log (RQ-003).
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

import structlog
from pydantic_ai import Agent
from pydantic_ai import exceptions as e
from pydantic_ai.models import Model
from pydantic_ai.usage import UsageLimits

from app.ia.configuracao import ConfiguracaoIa
from app.ia.excecoes import (
    ErroTransitorioIA,
    LimiteProvedor,
    OrcamentoEsgotado,
    ProvedorIndisponivel,
    RespostaInvalida,
)
from app.ia.modelos import ConsumoIa
from app.ia.orcamento import inicio_do_orcamento, restante
from app.ia.provedores import Finalidade, criar_modelo
from app.ia.repositorios import RepositorioConsumoIa
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.relogio import Relogio

logger = structlog.get_logger(__name__)

# Uma resposta e um pedido de correção da saída (`output_retries=1`, DTEC 043), com folga.
REQUISICOES_POR_EXECUCAO = 3

# Marcas de cota diária nos 429 do Gemini (`...PerDay...`) e do Groq (`per day`, TPD, RPD).
_MARCAS_DE_COTA_DIARIA = ("perday", "per day", "daily", "(tpd)", "(rpd)")


@dataclass(frozen=True, slots=True)
class ContextoChamada:
    usuario_id: int
    usuario_public_id: UUID
    fuso: str
    operacao: str
    versao_instrucoes: str
    geracao_id: int | None = None
    geracao_public_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ResultadoIa[Saida]:
    saida: Saida
    tokens_entrada: int | None
    tokens_saida: int | None


def _cota_diaria(corpo: object) -> bool:
    texto = corpo if isinstance(corpo, str) else json.dumps(corpo, default=str)
    texto = texto.lower()
    return any(marca in texto for marca in _MARCAS_DE_COTA_DIARIA)


def classificar_erro(erro: BaseException) -> BaseException:
    """A falha do provedor na hierarquia de `ia/excecoes.py`; outro erro volta como veio.

    Transitórios: timeout, conexão, 5xx e 429 por minuto. Cota diária: `LimiteProvedor`.
    Saída fora do esquema: `RespostaInvalida`. Teto de tokens: `OrcamentoEsgotado`.
    """
    if isinstance(erro, e.ModelQuotaExceededError):
        return LimiteProvedor()
    if isinstance(erro, e.ModelRateLimitError):
        return LimiteProvedor() if _cota_diaria(erro.body) else ErroTransitorioIA()
    if isinstance(erro, e.ModelHTTPError):
        if erro.status_code == 429:
            return LimiteProvedor() if _cota_diaria(erro.body) else ErroTransitorioIA()
        if erro.status_code >= 500:
            return ErroTransitorioIA()
        return ProvedorIndisponivel()
    if isinstance(erro, e.ModelRequestRejectedError):
        return ProvedorIndisponivel()
    if isinstance(erro, TimeoutError | e.RunTimedOut | e.ModelAPIError):
        # ModelAPIError restante: conexão, timeout de transporte, 5xx sem status, sobrecarga.
        return ErroTransitorioIA()
    if isinstance(erro, e.UsageLimitExceeded):
        return OrcamentoEsgotado()
    if isinstance(erro, e.UnexpectedModelBehavior):
        return RespostaInvalida()
    return erro


class ClienteIa:
    def __init__(
        self,
        fabrica: FabricaSessoes,
        configuracao: ConfiguracaoIa,
        relogio: Relogio,
        *,
        modelos: Callable[[Finalidade], Model] | None = None,
    ) -> None:
        self._fabrica = fabrica
        self._configuracao = configuracao
        self._relogio = relogio
        self._modelos = modelos or (lambda finalidade: criar_modelo(configuracao, finalidade))

    def limites(self, restante_do_dia: int) -> UsageLimits:
        """Teto da execução: o que resta do orçamento do dia (DTEC 040)."""
        return UsageLimits(
            request_limit=REQUISICOES_POR_EXECUCAO, total_tokens_limit=restante_do_dia
        )

    async def executar[Saida](
        self,
        agente: Agent[None, Saida],
        entrada: str,
        contexto: ContextoChamada,
        *,
        finalidade: Finalidade = "geracao",
    ) -> ResultadoIa[Saida]:
        disponivel = await self._disponivel(contexto)
        if disponivel <= 0:
            raise OrcamentoEsgotado()
        modelo = self._modelos(finalidade)
        inicio = time.perf_counter()
        try:
            resultado = await agente.run(
                entrada,
                model=modelo,
                usage_limits=self.limites(disponivel),
                timeout=self._configuracao.ia_timeout_segundos,
            )
        except Exception as erro:
            classificado = classificar_erro(erro)
            await self._registrar(contexto, modelo, inicio, sucesso=False)
            if classificado is erro:
                raise
            raise classificado from None
        uso = resultado.usage
        await self._registrar(
            contexto,
            modelo,
            inicio,
            sucesso=True,
            tokens_entrada=uso.input_tokens,
            tokens_saida=uso.output_tokens,
        )
        return ResultadoIa(resultado.output, uso.input_tokens, uso.output_tokens)

    async def _disponivel(self, contexto: ContextoChamada) -> int:
        inicio = inicio_do_orcamento(self._relogio.agora(), contexto.fuso)
        async with unidade_de_trabalho(self._fabrica) as sessao:
            consumido = await RepositorioConsumoIa(sessao).tokens_desde(contexto.usuario_id, inicio)
        return restante(self._configuracao.ia_orcamento_tokens_dia, consumido)

    async def _registrar(
        self,
        contexto: ContextoChamada,
        modelo: Model,
        inicio: float,
        *,
        sucesso: bool,
        tokens_entrada: int | None = None,
        tokens_saida: int | None = None,
    ) -> None:
        latencia_ms = round((time.perf_counter() - inicio) * 1000)
        provedor = self._configuracao.ia_provedor
        async with unidade_de_trabalho(self._fabrica) as sessao:
            await RepositorioConsumoIa(sessao).registrar(
                ConsumoIa(
                    usuario_id=contexto.usuario_id,
                    geracao_id=contexto.geracao_id,
                    operacao=contexto.operacao,
                    provedor=provedor,
                    modelo=modelo.model_name,
                    versao_instrucoes=contexto.versao_instrucoes,
                    tokens_entrada=tokens_entrada,
                    tokens_saida=tokens_saida,
                    latencia_ms=latencia_ms,
                    sucesso=sucesso,
                    criado_em=self._relogio.agora(),
                )
            )
        logger.info(
            "chamada_ia",
            operacao=contexto.operacao,
            provedor=provedor,
            modelo=modelo.model_name,
            versao_instrucoes=contexto.versao_instrucoes,
            tokens_entrada=tokens_entrada,
            tokens_saida=tokens_saida,
            latencia_ms=latencia_ms,
            sucesso=sucesso,
            usuario_id=str(contexto.usuario_public_id),
            geracao_id=str(contexto.geracao_public_id) if contexto.geracao_public_id else None,
        )
