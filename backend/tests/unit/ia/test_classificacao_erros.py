"""T008 (spec 004, DTEC 040 e 043): classificação dos erros do provedor.

Transitórios (nova tentativa da fila): timeout, conexão, 5xx e 429 por minuto. Cota diária do
provedor esgotada vira `limite_provedor`; saída fora do esquema, `resposta_invalida`.
"""

from __future__ import annotations

import pytest
from pydantic_ai import exceptions as e

from app.ia.cliente import classificar_erro
from app.ia.excecoes import (
    ErroIA,
    ErroTransitorioIA,
    LimiteProvedor,
    OrcamentoEsgotado,
    ProvedorIndisponivel,
    RespostaInvalida,
)

pytestmark = pytest.mark.unit

MODELO = "modelo-ficticio"


@pytest.mark.parametrize(
    "erro",
    [
        TimeoutError(),
        e.RunTimedOut("tempo esgotado"),
        e.ModelTimeoutError(MODELO, "timeout"),
        e.ModelRequestTimeout(MODELO, 60.0),
        e.ModelConnectionError(MODELO, "conexão recusada"),
        e.ModelServerError(MODELO, "erro interno"),
        e.ModelUnavailableError(MODELO, "indisponível"),
        e.ModelOverloadedError(MODELO, "sobrecarregado"),
        e.ModelHTTPError(500, MODELO),
        e.ModelHTTPError(503, MODELO, {"error": "unavailable"}),
        e.ModelRateLimitError(MODELO, "rate limit", body={"error": "requests per minute"}),
        e.ModelHTTPError(429, MODELO, {"error": {"message": "Resource exhausted, retry later"}}),
    ],
)
def test_transitorios(erro: Exception) -> None:
    classificado = classificar_erro(erro)
    assert isinstance(classificado, ErroTransitorioIA)
    assert classificado.codigo == "provedor_indisponivel"


@pytest.mark.parametrize(
    "erro",
    [
        e.ModelQuotaExceededError(MODELO, "quota"),
        e.ModelRateLimitError(
            MODELO, "rate limit", body={"error": "Rate limit reached for tokens per day (TPD)"}
        ),
        e.ModelHTTPError(
            429,
            MODELO,
            {"error": {"details": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel"}]}},
        ),
        e.ModelHTTPError(429, MODELO, "You exceeded your daily quota."),
    ],
)
def test_cota_diaria_vira_limite_do_provedor(erro: Exception) -> None:
    classificado = classificar_erro(erro)
    assert isinstance(classificado, LimiteProvedor)
    assert not isinstance(classificado, ErroTransitorioIA)
    assert classificado.codigo == "limite_provedor"


@pytest.mark.parametrize(
    "erro",
    [
        e.UnexpectedModelBehavior("Exceeded maximum output retries"),
        e.ContentFilterError("conteúdo filtrado"),
    ],
)
def test_saida_fora_do_esquema_vira_resposta_invalida(erro: Exception) -> None:
    classificado = classificar_erro(erro)
    assert isinstance(classificado, RespostaInvalida)
    assert classificado.codigo == "resposta_invalida"


def test_teto_da_execucao_vira_orcamento_esgotado() -> None:
    """O teto de tokens da execução é o que resta do orçamento do dia (DTEC 040)."""
    classificado = classificar_erro(e.UsageLimitExceeded("total_tokens_limit"))
    assert isinstance(classificado, OrcamentoEsgotado)
    assert classificado.codigo == "orcamento_esgotado"


@pytest.mark.parametrize(
    "erro",
    [
        e.ModelAuthenticationError(MODELO, "chave inválida"),
        e.ModelNotFoundError(MODELO, "modelo inexistente"),
        e.ModelHTTPError(400, MODELO),
        e.ModelHTTPError(403, MODELO),
    ],
)
def test_recusa_definitiva_nao_e_transitoria(erro: Exception) -> None:
    """Repetir o mesmo pedido não resolve: falha sem nova tentativa, como provedor indisponível."""
    classificado = classificar_erro(erro)
    assert isinstance(classificado, ProvedorIndisponivel)
    assert not isinstance(classificado, ErroTransitorioIA)


def test_mensagem_classificada_nao_carrega_o_corpo_do_provedor() -> None:
    """RQ-005: nenhum detalhe do provedor chega à mensagem nem ao log."""
    erro = e.ModelHTTPError(500, MODELO, {"error": "trecho secreto da fonte"})
    classificado = classificar_erro(erro)
    assert "secreto" not in str(classificado)
    assert isinstance(classificado, ErroIA)


def test_erro_desconhecido_nao_e_classificado() -> None:
    """Defeito de programação continua visível: não vira falha do provedor."""
    with pytest.raises(KeyError):
        raise classificar_erro(KeyError("defeito"))
