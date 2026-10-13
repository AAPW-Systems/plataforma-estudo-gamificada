"""Endereço de rede com proxies confiáveis (DTEC 020; T032, `X-Forwarded-For` forjado)."""

from __future__ import annotations

import ipaddress

import pytest

from app.nucleo.configuracao import RedeConfiavel
from app.nucleo.rede import ENDERECO_DESCONHECIDO, endereco_cliente

pytestmark = pytest.mark.unit

PROXY = "172.28.0.10"
PROXIES: list[RedeConfiavel] = [ipaddress.ip_network(PROXY), ipaddress.ip_network("10.0.0.0/8")]


def _escopo(cliente: str | None, *encaminhados: str) -> dict[str, object]:
    return {
        "type": "http",
        "client": (cliente, 5000) if cliente else None,
        "headers": [(b"x-forwarded-for", valor.encode()) for valor in encaminhados],
    }


def test_sem_proxy_usa_o_endereco_da_conexao() -> None:
    assert str(endereco_cliente(_escopo("203.0.113.7"), PROXIES)) == "203.0.113.7"


def test_x_forwarded_for_de_cliente_nao_confiavel_e_ignorado() -> None:
    escopo = _escopo("203.0.113.7", "198.51.100.1")
    assert str(endereco_cliente(escopo, PROXIES)) == "203.0.113.7"


def test_x_forwarded_for_de_proxy_confiavel_e_aceito() -> None:
    escopo = _escopo(PROXY, "198.51.100.1")
    assert str(endereco_cliente(escopo, PROXIES)) == "198.51.100.1"


def test_valor_forjado_a_esquerda_e_ignorado() -> None:
    # O cliente enviou "1.2.3.4"; o proxy acrescentou o endereço real à direita.
    escopo = _escopo(PROXY, "1.2.3.4, 198.51.100.1")
    assert str(endereco_cliente(escopo, PROXIES)) == "198.51.100.1"


def test_cadeia_de_proxies_confiaveis_e_percorrida() -> None:
    escopo = _escopo(PROXY, "198.51.100.1, 10.1.2.3")
    assert str(endereco_cliente(escopo, PROXIES)) == "198.51.100.1"


def test_varios_cabecalhos_sao_concatenados_na_ordem() -> None:
    escopo = _escopo(PROXY, "1.2.3.4", "198.51.100.1")
    assert str(endereco_cliente(escopo, PROXIES)) == "198.51.100.1"


@pytest.mark.parametrize("valor", ["lixo", "198.51.100.1, nao-ip", "", "999.1.1.1"])
def test_x_forwarded_for_adulterado_nao_derruba_e_nao_e_aceito(valor: str) -> None:
    resultado = endereco_cliente(_escopo(PROXY, valor), PROXIES)
    assert str(resultado) == PROXY


def test_ipv4_mapeado_em_ipv6_e_normalizado() -> None:
    assert str(endereco_cliente(_escopo("::ffff:203.0.113.7"), PROXIES)) == "203.0.113.7"


def test_sem_conexao_retorna_endereco_desconhecido() -> None:
    assert endereco_cliente(_escopo(None), PROXIES) == ENDERECO_DESCONHECIDO


def test_sem_proxies_configurados_nunca_aceita_o_cabecalho() -> None:
    assert str(endereco_cliente(_escopo(PROXY, "198.51.100.1"), [])) == PROXY
