"""Proteção contra falsificação de requisição em toda rota que altera estado (T042; RF-011).

Parametrizado por todas as rotas `POST`, `PUT`, `PATCH` e `DELETE` da aplicação: uma rota nova
entra aqui automaticamente. Cada rota é recusada com `403` sem token, com token de outra
sessão, com `Origin` fora da lista e com `Sec-Fetch-Site` diferente de `same-origin`.
"""

from __future__ import annotations

import uuid

import httpx
import pytest
from fastapi import FastAPI

from app.nucleo.configuracao import obter_configuracao
from app.principal import criar_aplicacao
from tests.apoio_http import (
    COOKIE_CSRF,
    COOKIE_SESSAO,
    abrir_cliente,
    cadastrar,
    definir_cookie,
    obter_csrf,
)
from tests.apoio_rotas import PARAMETRO, rotas_que_alteram_estado
from tests.fabricas import dados_conta

pytestmark = pytest.mark.security


ROTAS = rotas_que_alteram_estado(criar_aplicacao(obter_configuracao()))
IDS = [f"{metodo} {caminho}" for metodo, caminho in ROTAS]


def _url(caminho: str) -> str:
    return PARAMETRO.sub(lambda _: str(uuid.uuid4()), caminho)


def test_a_lista_de_rotas_que_alteram_estado_tem_as_rotas_conhecidas() -> None:
    assert ("POST", "/api/v1/auth/cadastro") in ROTAS
    assert ("POST", "/api/v1/auth/entrada") in ROTAS
    assert ("POST", "/api/v1/auth/saida") in ROTAS


async def _recusada(
    cliente: httpx.AsyncClient, metodo: str, caminho: str, codigo: str, **opcoes: object
) -> None:
    resposta = await cliente.request(metodo, _url(caminho), json={}, **opcoes)  # type: ignore[arg-type]
    assert resposta.status_code == 403, (
        f"{metodo} {caminho}: {resposta.status_code} {resposta.text}"
    )
    assert resposta.json()["codigo"] == codigo


@pytest.mark.parametrize("metodo,caminho", ROTAS, ids=IDS)
async def test_sem_token_a_requisicao_e_recusada_com_e_sem_sessao(
    cliente: httpx.AsyncClient, metodo: str, caminho: str
) -> None:
    await _recusada(cliente, metodo, caminho, "csrf_invalido")  # sem cookie nem cabeçalho
    await obter_csrf(cliente)
    await _recusada(cliente, metodo, caminho, "csrf_invalido", headers={"X-CSRF-Token": ""})

    assert (await cadastrar(cliente, dados_conta())).status_code == 201
    await _recusada(cliente, metodo, caminho, "csrf_invalido", headers={"X-CSRF-Token": ""})
    await _recusada(cliente, metodo, caminho, "csrf_invalido", headers={"X-CSRF-Token": "a.b"})
    # A conta e a sessão seguem intactas depois das recusas.
    assert (await cliente.get("/api/v1/perfil")).status_code == 200


@pytest.mark.parametrize("metodo,caminho", ROTAS, ids=IDS)
async def test_token_de_outra_sessao_e_recusado(
    aplicacao: FastAPI, cliente: httpx.AsyncClient, metodo: str, caminho: str
) -> None:
    async with abrir_cliente(aplicacao, ip="198.51.100.41") as cliente_bia:
        assert (await cadastrar(cliente, dados_conta())).status_code == 201
        assert (await cadastrar(cliente_bia, dados_conta())).status_code == 201
        token_da_bia = cliente_bia.cookies[COOKIE_CSRF]

        # Só o cabeçalho trocado: não bate com o cookie da própria sessão.
        await _recusada(
            cliente, metodo, caminho, "csrf_invalido", headers={"X-CSRF-Token": token_da_bia}
        )

        # Quem consegue plantar o cookie e o cabeçalho com o token de outra sessão também falha:
        # a assinatura está ligada à sessão.
        definir_cookie(cliente, COOKIE_CSRF, token_da_bia)
        await _recusada(
            cliente, metodo, caminho, "csrf_invalido", headers={"X-CSRF-Token": token_da_bia}
        )
        assert (await cliente_bia.get("/api/v1/perfil")).status_code == 200


@pytest.mark.parametrize("metodo,caminho", ROTAS, ids=IDS)
async def test_token_de_pre_sessao_nao_vale_com_sessao_aberta(
    aplicacao: FastAPI, cliente: httpx.AsyncClient, metodo: str, caminho: str
) -> None:
    async with abrir_cliente(aplicacao, ip="198.51.100.42") as anonimo:
        await obter_csrf(anonimo)
        token_pre_sessao = anonimo.cookies[COOKIE_CSRF]
    assert (await cadastrar(cliente, dados_conta())).status_code == 201
    assert COOKIE_SESSAO in cliente.cookies
    definir_cookie(cliente, COOKIE_CSRF, token_pre_sessao)
    await _recusada(
        cliente, metodo, caminho, "csrf_invalido", headers={"X-CSRF-Token": token_pre_sessao}
    )


@pytest.mark.parametrize("metodo,caminho", ROTAS, ids=IDS)
@pytest.mark.parametrize(
    "origem",
    [
        "https://atacante.example",
        "http://teste",  # esquema diferente
        "https://teste.atacante.example",
        "https://teste:8443",
        "null",
        "",
    ],
)
async def test_origin_fora_da_lista_e_recusada_mesmo_com_token_valido(
    cliente: httpx.AsyncClient, metodo: str, caminho: str, origem: str
) -> None:
    assert (await cadastrar(cliente, dados_conta())).status_code == 201
    await _recusada(cliente, metodo, caminho, "origem_nao_permitida", headers={"Origin": origem})
    assert (await cliente.get("/api/v1/perfil")).status_code == 200


@pytest.mark.parametrize("metodo,caminho", ROTAS, ids=IDS)
@pytest.mark.parametrize("site", ["cross-site", "same-site", "none", "Cross-Site", ""])
async def test_sec_fetch_site_diferente_de_same_origin_e_recusado(
    cliente: httpx.AsyncClient, metodo: str, caminho: str, site: str
) -> None:
    assert (await cadastrar(cliente, dados_conta())).status_code == 201
    await _recusada(
        cliente, metodo, caminho, "origem_nao_permitida", headers={"Sec-Fetch-Site": site}
    )
    assert (await cliente.get("/api/v1/perfil")).status_code == 200


@pytest.mark.parametrize("metodo,caminho", ROTAS, ids=IDS)
async def test_cabecalhos_de_origem_duplicados_sao_recusados(
    cliente: httpx.AsyncClient, metodo: str, caminho: str
) -> None:
    assert (await cadastrar(cliente, dados_conta())).status_code == 201
    pedido = cliente.build_request(
        metodo,
        _url(caminho),
        json={},
        headers=[("Origin", "https://teste"), ("Origin", "https://atacante.example")],
    )
    assert [v for k, v in pedido.headers.multi_items() if k.lower() == "origin"] == [
        "https://teste",
        "https://atacante.example",
    ], "o pedido de teste deveria carregar dois cabeçalhos Origin"
    resposta = await cliente.send(pedido)
    assert resposta.status_code == 403


async def test_leituras_nao_exigem_token_nem_sao_afetadas_pela_origem(
    cliente: httpx.AsyncClient,
) -> None:
    """A proteção vale para quem altera estado; `GET` segue seu curso (e sem sessão vira 401)."""
    resposta = await cliente.get("/api/v1/perfil", headers={"Origin": "https://atacante.example"})
    assert resposta.status_code == 401
