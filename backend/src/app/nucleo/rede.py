"""Endereço de rede do cliente, base dos limites por endereço (DTEC 020).

O `X-Forwarded-For` só é considerado quando a conexão vem de um proxy confiável
(`PROXIES_CONFIAVEIS`). Nesse caso, a lista é lida da direita para a esquerda e o primeiro
endereço que não é de proxy confiável é o do cliente: os da esquerda podem ter sido
forjados por ele e são ignorados.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Sequence

from starlette.types import Scope

from app.nucleo.configuracao import RedeConfiavel

EnderecoIP = ipaddress.IPv4Address | ipaddress.IPv6Address

ENDERECO_DESCONHECIDO: EnderecoIP = ipaddress.IPv4Address("0.0.0.0")  # noqa: S104


def _converter(valor: str) -> EnderecoIP | None:
    try:
        endereco = ipaddress.ip_address(valor.strip())
    except ValueError:
        return None
    if isinstance(endereco, ipaddress.IPv6Address) and endereco.ipv4_mapped:
        return endereco.ipv4_mapped
    return endereco


def _confiavel(endereco: EnderecoIP, proxies: Sequence[RedeConfiavel]) -> bool:
    return any(endereco.version == rede.version and endereco in rede for rede in proxies)


def _encaminhado_por(scope: Scope) -> list[str]:
    valores = [
        bytes(valor).decode("latin-1")
        for chave, valor in scope.get("headers", ())
        if chave == b"x-forwarded-for"
    ]
    return [parte for valor in valores for parte in valor.split(",")]


def endereco_cliente(scope: Scope, proxies: Sequence[RedeConfiavel]) -> EnderecoIP:
    cliente = scope.get("client")
    conexao = _converter(str(cliente[0])) if cliente else None
    if conexao is None:
        return ENDERECO_DESCONHECIDO
    if not _confiavel(conexao, proxies):
        return conexao
    for parte in reversed(_encaminhado_por(scope)):
        endereco = _converter(parte)
        if endereco is None:
            # Lista adulterada: não há como saber quem veio antes; fica o último salto válido.
            break
        if not _confiavel(endereco, proxies):
            return endereco
        conexao = endereco
    return conexao
