"""Tarefas assíncronas da identidade (T056; DTEC 021 e 020).

- `apagar_objetos_usuario`: enfileirada na mesma transação da exclusão da conta; remove tudo
  sob `usuarios/{public_id}/` no armazenamento. Idempotente, com novas tentativas e espera
  crescente.
- `limpar_registros_expirados`: diária, às 3h UTC; apaga tentativas de acesso com mais de 24
  horas e sessões inválidas há mais de 30 dias.

A lógica fica em `executar_*`, testável sem a fila; as tarefas só ligam a configuração.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from procrastinate import RetryStrategy

from app.identidade.repositorios import RepositorioSessoes, RepositorioTentativas
from app.nucleo.armazenamento import Armazenamento, criar_armazenamento, prefixo_usuario
from app.nucleo.banco import FabricaSessoes, criar_engine, criar_fabrica, unidade_de_trabalho
from app.nucleo.configuracao import obter_configuracao
from app.nucleo.fila import app_fila

logger = structlog.get_logger(__name__)

RETENCAO_TENTATIVAS = timedelta(hours=24)
RETENCAO_SESSOES = timedelta(days=30)


@dataclass(frozen=True, slots=True)
class ResultadoLimpeza:
    tentativas: int
    sessoes: int


def criar_armazenamento_padrao() -> Armazenamento:
    return criar_armazenamento(obter_configuracao())


async def executar_apagar_objetos(armazenamento: Armazenamento, public_id: str) -> int:
    """Apaga os objetos do estudante e devolve quantos foram; repetir não tem efeito.

    O identificador tem de ser um UUID: nada que escape de `usuarios/{uuid}/` chega ao adaptador.
    """
    identificador = str(UUID(public_id))
    return await armazenamento.apagar_prefixo(prefixo_usuario(identificador))


async def executar_limpeza(
    fabrica: FabricaSessoes, agora: datetime, *, dias_inatividade: int
) -> ResultadoLimpeza:
    async with unidade_de_trabalho(fabrica) as sessao:
        tentativas = await RepositorioTentativas(sessao).apagar_anteriores_a(
            agora - RETENCAO_TENTATIVAS
        )
        sessoes = await RepositorioSessoes(sessao).apagar_invalidas_antes_de(
            agora - RETENCAO_SESSOES, dias_inatividade
        )
    return ResultadoLimpeza(tentativas=tentativas, sessoes=sessoes)


@app_fila.task(
    name="identidade.apagar_objetos_usuario",
    pass_context=False,
    retry=RetryStrategy(max_attempts=5, exponential_wait=10),
)
async def apagar_objetos_usuario(public_id: str) -> int:
    apagados = await executar_apagar_objetos(criar_armazenamento_padrao(), public_id)
    logger.info("objetos_do_usuario_apagados", usuario_public_id=public_id, quantidade=apagados)
    return apagados


@app_fila.periodic(cron="0 3 * * *")
@app_fila.task(name="identidade.limpar_registros_expirados", pass_context=False)
async def limpar_registros_expirados(timestamp: int) -> None:
    configuracao = obter_configuracao()
    engine = criar_engine(configuracao)
    try:
        resultado = await executar_limpeza(
            criar_fabrica(engine),
            datetime.now(UTC),
            dias_inatividade=configuracao.sessao_dias_inatividade,
        )
    finally:
        await engine.dispose()
    logger.info(
        "registros_expirados_apagados",
        tentativas=resultado.tentativas,
        sessoes=resultado.sessoes,
    )
