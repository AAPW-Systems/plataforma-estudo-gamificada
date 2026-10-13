"""Token anti-CSRF: *double submit* assinado (OWASP; DTEC 023).

Token = `aleatorio.HMAC(segredo, vinculo + aleatorio)`, no cookie legível pelo JavaScript e
repetido no cabeçalho `X-CSRF-Token`. O vínculo amarra o token à sessão (ou, antes de
existir sessão, a um vínculo de pré-sessão), então o token de uma sessão não vale em outra.
O vínculo da sessão usa o SHA-256 do identificador, nunca o identificador em si.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from collections.abc import Mapping

from app.nucleo.seguranca.sessoes import hash_token, token_bem_formado

VINCULO_PRE_SESSAO = b"pre-sessao"

_PREFIXO_ASSINATURA = b"csrf-v1|"
_TAMANHO_ALEATORIO = 32
_TAMANHO_MAXIMO_TOKEN = 128


def vinculo_da_sessao(token_hash: bytes) -> bytes:
    return b"sessao:" + token_hash.hex().encode()


def vinculo_dos_cookies(cookies: Mapping[str, str], nome_cookie_sessao: str) -> bytes:
    """Vínculo da requisição, sem consultar o banco: o cookie de sessão bem formado, se houver."""
    token = cookies.get(nome_cookie_sessao)
    if token is not None and token_bem_formado(token):
        return vinculo_da_sessao(hash_token(token))
    return VINCULO_PRE_SESSAO


def _b64(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode()


def _assinar(segredo: bytes, vinculo: bytes, aleatorio: str) -> str:
    mensagem = _PREFIXO_ASSINATURA + vinculo + b"|" + aleatorio.encode("ascii")
    return _b64(hmac.new(segredo, mensagem, hashlib.sha256).digest())


def emitir_token(segredo: bytes, vinculo: bytes) -> str:
    aleatorio = _b64(secrets.token_bytes(_TAMANHO_ALEATORIO))
    return f"{aleatorio}.{_assinar(segredo, vinculo, aleatorio)}"


def verificar_token(
    segredo: bytes, vinculo: bytes, token_cookie: str | None, token_cabecalho: str | None
) -> bool:
    """Cookie e cabeçalho iguais e com assinatura válida para o vínculo da requisição."""
    if not token_cookie or not token_cabecalho:
        return False
    if len(token_cookie) > _TAMANHO_MAXIMO_TOKEN or len(token_cabecalho) > _TAMANHO_MAXIMO_TOKEN:
        return False
    if not hmac.compare_digest(token_cookie.encode(), token_cabecalho.encode()):
        return False
    aleatorio, separador, assinatura = token_cabecalho.partition(".")
    if not separador or not aleatorio or not assinatura.isascii() or not aleatorio.isascii():
        return False
    esperada = _assinar(segredo, vinculo, aleatorio)
    return hmac.compare_digest(assinatura.encode(), esperada.encode())
