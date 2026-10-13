"""Identificador e validade da sessão (DTEC 003 e 023; RF-006).

O identificador tem 256 bits aleatórios e vai ao navegador em base64url. O banco guarda
só o SHA-256 dele: um vazamento do banco não entrega sessões utilizáveis (RQ-001).
"""

from __future__ import annotations

import base64
import hashlib
import re
import secrets
from datetime import datetime, timedelta

TAMANHO_TOKEN_BYTES = 32
INTERVALO_RENOVACAO = timedelta(seconds=60)

# 32 bytes em base64url sem preenchimento ocupam exatamente 43 caracteres.
_TOKEN = re.compile(r"^[A-Za-z0-9_-]{43}$")


def gerar_token() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(TAMANHO_TOKEN_BYTES)).rstrip(b"=").decode()


def token_bem_formado(valor: str | None) -> bool:
    """Recusa de imediato o que não pode ser um identificador, sem consultar o banco."""
    return valor is not None and _TOKEN.fullmatch(valor) is not None


def hash_token(token: str) -> bytes:
    return hashlib.sha256(token.encode("ascii")).digest()


def calcular_expiracao(criada_em: datetime, dias_maximo: int) -> datetime:
    return criada_em + timedelta(days=dias_maximo)


def sessao_valida(
    *,
    agora: datetime,
    expira_em: datetime,
    ultimo_uso_em: datetime,
    revogada_em: datetime | None,
    dias_inatividade: int,
) -> bool:
    """Válida quando não revogada, antes da expiração absoluta e dentro da inatividade."""
    if revogada_em is not None:
        return False
    if agora >= expira_em:
        return False
    return agora < ultimo_uso_em + timedelta(days=dias_inatividade)


def deve_renovar_uso(ultimo_uso_em: datetime, agora: datetime) -> bool:
    """`ultimo_uso_em` é gravado no máximo uma vez por minuto, não a cada requisição."""
    return agora - ultimo_uso_em >= INTERVALO_RENOVACAO
