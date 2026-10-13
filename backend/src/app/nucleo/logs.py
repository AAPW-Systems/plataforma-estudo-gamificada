"""Logs JSON com structlog, correlação por requisição e mascaramento (RQ-002, DTEC 011).

Nenhum log carrega senha, cookie, token anti-CSRF, e-mail ou corpo de requisição: o
processador `mascarar_dados_sensiveis` substitui esses valores, em qualquer nível de
aninhamento, antes da renderização. Os logs do uvicorn passam pelo mesmo pipeline.
"""

from __future__ import annotations

import logging
import logging.config
import re
from collections.abc import Mapping, MutableMapping
from typing import Any

import structlog
from structlog.types import EventDict, Processor, WrappedLogger

REMOVIDO = "[REMOVIDO]"

# Comparação por nome normalizado (minúsculas, sem "-" nem "_").
_CHAVES_SENSIVEIS = frozenset(
    {
        "senha",
        "senhaatual",
        "novasenha",
        "password",
        "cookie",
        "cookies",
        "setcookie",
        "xcsrftoken",
        "csrf",
        "token",
        "authorization",
        "email",
        "corpo",
        "body",
        "sessao",
    }
)
_SEPARADORES = re.compile(r"[-_]")


def _sensivel(chave: object) -> bool:
    return isinstance(chave, str) and _SEPARADORES.sub("", chave.lower()) in _CHAVES_SENSIVEIS


def _mascarar(valor: Any) -> Any:
    if isinstance(valor, Mapping):
        return {k: (REMOVIDO if _sensivel(k) else _mascarar(v)) for k, v in valor.items()}
    if isinstance(valor, list | tuple):
        return type(valor)(_mascarar(item) for item in valor)
    return valor


def mascarar_dados_sensiveis(_logger: WrappedLogger, _metodo: str, evento: EventDict) -> EventDict:
    for chave in list(evento):
        if _sensivel(chave):
            evento[chave] = REMOVIDO
        else:
            evento[chave] = _mascarar(evento[chave])
    return evento


def _processadores_compartilhados() -> list[Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        mascarar_dados_sensiveis,
    ]


def configurar_logs(nivel: str = "INFO") -> None:
    """Configura structlog e o logging da biblioteca padrão para emitir JSON numa linha."""
    compartilhados = _processadores_compartilhados()
    structlog.configure(
        processors=[
            *compartilhados,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        # Sem cache: mantém os loggers reconfiguráveis (capture_logs nos testes).
        cache_logger_on_first_use=False,
    )
    configuracao: MutableMapping[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "foreign_pre_chain": compartilhados,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.dict_tracebacks,
                    structlog.processors.JSONRenderer(ensure_ascii=False),
                ],
            }
        },
        "handlers": {
            "saida": {"class": "logging.StreamHandler", "formatter": "json"},
        },
        "root": {"handlers": ["saida"], "level": nivel},
        "loggers": {
            # O log de acesso do uvicorn traz a URL com parâmetros; a correlação registra
            # a rota pelo modelo, sem valores (plano da 001, "Observabilidade").
            "uvicorn.access": {"handlers": [], "propagate": False},
            "uvicorn.error": {"handlers": [], "propagate": True},
        },
    }
    logging.config.dictConfig(dict(configuracao))
