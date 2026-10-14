"""Autenticação sob entradas hostis e concorrência (T032; RF-001, RF-005, RF-012, RQ-003).

Os testes de concorrência usam `fabrica_real` (conexões e transações reais), pois savepoints
em uma única conexão não exercitam a corrida pelo índice único nem as travas por chave.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select

from app.identidade.modelos import Sessao, TentativaAcesso, Usuario
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from tests.apoio_http import (
    COOKIE_SESSAO,
    abrir_cliente,
    cadastrar,
    entrar,
    obter_csrf,
    sair,
)
from tests.fabricas import dados_conta

pytestmark = pytest.mark.adversarial


async def _contar(fabrica: FabricaSessoes, entidade: type) -> int:
    async with unidade_de_trabalho(fabrica) as sessao:
        return (await sessao.execute(select(func.count()).select_from(entidade))).scalar_one()


# --- Concorrência ------------------------------------------------------------------------


@asynccontextmanager
async def _clientes_prontos(app: FastAPI, ips: list[str]) -> AsyncIterator[list[httpx.AsyncClient]]:
    """Um cliente por endereço, já com o token anti-CSRF: os POSTs saem juntos, de verdade.

    Sem esse preparo, criar o cliente e pedir o token escalonam as requisições e a rajada
    deixa de ser simultânea (a falta da trava passaria despercebida).
    """
    async with AsyncExitStack() as pilha:
        clientes = [await pilha.enter_async_context(abrir_cliente(app, ip=ip)) for ip in ips]
        await asyncio.gather(*(obter_csrf(cliente) for cliente in clientes))
        yield clientes


async def test_dois_cadastros_simultaneos_com_o_mesmo_email_criam_uma_conta(
    aplicacao_real: FastAPI, fabrica_real: FabricaSessoes
) -> None:
    ips = [f"198.51.100.{i + 1}" for i in range(6)]
    async with _clientes_prontos(aplicacao_real, ips) as clientes:
        corpos = [
            dados_conta(
                email="corrida.cadastro@exemplo.com" if i % 2 else "CORRIDA.cadastro@exemplo.com"
            )
            for i in range(6)
        ]
        respostas = await asyncio.gather(
            *(
                cliente.post("/api/v1/auth/cadastro", json=conta.cadastro())
                for cliente, conta in zip(clientes, corpos, strict=True)
            )
        )

    status = sorted(r.status_code for r in respostas)
    assert status == [201, 409, 409, 409, 409, 409], status
    assert await _contar(fabrica_real, Usuario) == 1
    assert await _contar(fabrica_real, Sessao) == 1, "só o cadastro vencedor abre sessão"


async def test_cadastros_simultaneos_do_mesmo_endereco_respeitam_o_limite_por_hora(
    aplicacao_real: FastAPI, fabrica_real: FabricaSessoes
) -> None:
    async with _clientes_prontos(aplicacao_real, ["203.0.113.50"] * 25) as clientes:
        respostas = await asyncio.gather(
            *(c.post("/api/v1/auth/cadastro", json=dados_conta().cadastro()) for c in clientes)
        )

    status = [r.status_code for r in respostas]
    assert status.count(201) == 10, status
    assert status.count(429) == 15, status
    assert await _contar(fabrica_real, Usuario) == 10


async def test_rajada_paralela_de_entradas_erradas_respeita_o_limite_da_conta(
    aplicacao_real: FastAPI, fabrica_real: FabricaSessoes
) -> None:
    async with abrir_cliente(aplicacao_real, ip="198.51.100.200") as preparo:
        conta = dados_conta()
        assert (await cadastrar(preparo, conta)).status_code == 201

    ips = [f"203.0.113.{i + 1}" for i in range(30)]
    async with _clientes_prontos(aplicacao_real, ips) as clientes:
        respostas = await asyncio.gather(
            *(
                c.post(
                    "/api/v1/auth/entrada", json={"email": conta.email, "senha": "errada-errada-1"}
                )
                for c in clientes
            )
        )

    status = [r.status_code for r in respostas]
    assert status.count(401) == 5, status
    assert status.count(429) == 25, status
    assert await _contar(fabrica_real, TentativaAcesso) == 5 + 1, "5 falhas e 1 cadastro, nada além"


async def test_rajada_com_a_senha_certa_no_meio_nao_burla_o_bloqueio(
    aplicacao_real: FastAPI, fabrica_real: FabricaSessoes
) -> None:
    """As cinco primeiras tentativas a chegar decidem: cinco erradas bloqueiam, a certa que
    vem depois também é recusada; e, se a certa chegar antes, ela zera as falhas."""
    async with abrir_cliente(aplicacao_real, ip="198.51.100.201") as preparo:
        conta = dados_conta()
        assert (await cadastrar(preparo, conta)).status_code == 201

    ips = [f"203.0.113.{i + 1}" for i in range(24)]
    async with _clientes_prontos(aplicacao_real, ips) as clientes:
        respostas = await asyncio.gather(
            *(
                c.post(
                    "/api/v1/auth/entrada",
                    json=conta.entrada()
                    if i == 20
                    else {"email": conta.email, "senha": "errada-errada-1"},
                )
                for i, c in enumerate(clientes)
            )
        )

    status = [r.status_code for r in respostas]
    assert set(status) <= {200, 401, 429}, status
    # Cada tentativa é serializada pela trava: nunca há mais de 5 erradas seguidas sem bloqueio.
    assert status.count(401) <= 5 + 5, status
    async with unidade_de_trabalho(fabrica_real) as sessao:
        falhas = (
            await sessao.execute(
                select(func.count())
                .select_from(TentativaAcesso)
                .where(TentativaAcesso.tipo == "falha_entrada")
            )
        ).scalar_one()
    assert falhas <= 5 or status[20] == 200, "sem uma entrada certa no meio, só 5 falhas cabem"


async def test_rajada_de_limite_por_endereco_nao_ultrapassa_20_falhas(
    aplicacao_real: FastAPI,
) -> None:
    async with _clientes_prontos(aplicacao_real, ["203.0.113.99"] * 40) as clientes:
        respostas = await asyncio.gather(
            *(
                c.post(
                    "/api/v1/auth/entrada",
                    json={"email": f"alvo.{i}@exemplo.com", "senha": "errada-errada-1"},
                )
                for i, c in enumerate(clientes)
            )
        )

    status = [r.status_code for r in respostas]
    assert status.count(401) == 20, status
    assert status.count(429) == 20, status


async def test_entradas_simultaneas_corretas_abrem_sessoes_distintas(
    aplicacao_real: FastAPI,
) -> None:
    async with abrir_cliente(aplicacao_real, ip="198.51.100.202") as preparo:
        conta = dados_conta()
        assert (await cadastrar(preparo, conta)).status_code == 201

    ips = [f"203.0.113.{i + 1}" for i in range(5)]
    async with _clientes_prontos(aplicacao_real, ips) as clientes:
        respostas = await asyncio.gather(
            *(c.post("/api/v1/auth/entrada", json=conta.entrada()) for c in clientes)
        )
        assert {r.status_code for r in respostas} == {200}
        tokens = {c.cookies[COOKIE_SESSAO] for c in clientes}
    assert len(tokens) == 5


# --- Reenvio -----------------------------------------------------------------------------


async def test_cadastro_reenviado_depois_do_sucesso_responde_409(
    cliente: httpx.AsyncClient,
) -> None:
    conta = dados_conta()
    assert (await cadastrar(cliente, conta)).status_code == 201
    repetido = await cadastrar(cliente, conta)
    assert repetido.status_code == 409
    assert repetido.json()["codigo"] == "email_em_uso"


# --- Corpo e entradas extremas -----------------------------------------------------------


async def test_corpo_acima_de_64_kib_e_recusado_com_413(cliente: httpx.AsyncClient) -> None:
    await obter_csrf(cliente)
    corpo = json.dumps({**dados_conta().cadastro(), "nome": "a" * (65 * 1024)})
    resposta = await cliente.post(
        "/api/v1/auth/cadastro", content=corpo, headers={"Content-Type": "application/json"}
    )
    assert resposta.status_code == 413
    assert resposta.json()["codigo"] == "requisicao_malformada"


async def test_corpo_grande_em_blocos_sem_content_length_tambem_e_recusado(
    cliente: httpx.AsyncClient,
) -> None:
    await obter_csrf(cliente)

    async def blocos() -> AsyncIterator[bytes]:
        yield b'{"email": "'
        for _ in range(80):
            yield b"a" * 1024
        yield b'", "senha": "x"}'

    resposta = await cliente.post(
        "/api/v1/auth/entrada", content=blocos(), headers={"Content-Type": "application/json"}
    )
    assert resposta.status_code == 413


@pytest.mark.parametrize(
    "corpo",
    [
        b"",
        b"{",
        b"[]",
        b"null",
        b'"texto"',
        b"\xff\xfe\x00",
        b'{"email": 1, "senha": 2}',
        b"{" * 5000,
    ],
)
async def test_corpos_malformados_na_entrada_sao_recusados_sem_erro_500(
    cliente: httpx.AsyncClient, corpo: bytes
) -> None:
    await obter_csrf(cliente)
    resposta = await cliente.post(
        "/api/v1/auth/entrada", content=corpo, headers={"Content-Type": "application/json"}
    )
    assert resposta.status_code in {400, 422}
    assert resposta.json()["codigo"] in {"requisicao_malformada", "dados_invalidos"}


@pytest.mark.parametrize(
    "nome",
    [
        "Ana‮evil",  # sobreposição de direção (RTL)
        "Ana⁧isolado",
        "Ana\x00",
        "Ana\r\nSet-Cookie: x=1",
        "\ud800lone",  # substituto isolado: não codifica em UTF-8
    ],
)
async def test_nome_com_unicode_malicioso_e_recusado(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes, nome: str
) -> None:
    await obter_csrf(cliente)
    corpo = json.dumps({**dados_conta().cadastro(), "nome": nome})  # ensure_ascii escapa \ud800
    resposta = await cliente.post(
        "/api/v1/auth/cadastro", content=corpo, headers={"Content-Type": "application/json"}
    )
    assert resposta.status_code == 422, resposta.text
    assert "nome" in {c["campo"] for c in resposta.json()["campos"]}
    assert await _contar(fabrica_sessoes, Usuario) == 0


async def test_nome_com_caracteres_de_combinacao_dentro_do_limite_e_aceito_normalizado(
    cliente: httpx.AsyncClient,
) -> None:
    decomposto = "Amélia" + "̣" * 3  # letra + acentos combinantes
    resposta = await cadastrar(cliente, {**dados_conta().cadastro(), "nome": decomposto})
    assert resposta.status_code == 201
    assert len(resposta.json()["nome"]) <= 100


async def test_senha_com_substituto_isolado_e_recusada_no_cadastro_sem_erro_500(
    cliente: httpx.AsyncClient,
) -> None:
    await obter_csrf(cliente)
    corpo = json.dumps({**dados_conta().cadastro(), "senha": "abcdefgh\ud800ijk"})
    resposta = await cliente.post(
        "/api/v1/auth/cadastro", content=corpo, headers={"Content-Type": "application/json"}
    )
    assert resposta.status_code == 422
    assert [c["campo"] for c in resposta.json()["campos"]] == ["senha"]


@pytest.mark.parametrize(
    "email",
    ["  ANA.Caixa@Exemplo.COM  ", "ana.caixa@exemplo.com", "Ana.Caixa@EXEMPLO.com"],
)
async def test_email_com_espacos_e_caixa_mista_e_o_mesmo_email(
    cliente: httpx.AsyncClient, email: str
) -> None:
    primeira = dados_conta(email="ana.caixa@exemplo.com")
    assert (await cadastrar(cliente, primeira)).status_code == 201
    await sair(cliente)
    repetida = await cadastrar(cliente, {**dados_conta().cadastro(), "email": email})
    assert repetida.status_code == 409
    await sair(cliente)
    assert (await entrar(cliente, {"email": email, "senha": primeira.senha})).status_code == 200


@pytest.mark.parametrize(
    "email",
    [
        "a@b",
        "ana@exemplo.com\r\nBcc: alvo@exemplo.com",
        "ana@exemplo.com\x00.evil",
        "<ana@exemplo.com>",
        '"ana"@exemplo.com',
        "ana@[127.0.0.1]",
        "ana@exemplo..com",
        "a" * 300 + "@exemplo.com",
    ],
)
async def test_emails_hostis_sao_recusados_no_cadastro(
    cliente: httpx.AsyncClient, email: str
) -> None:
    resposta = await cadastrar(cliente, {**dados_conta().cadastro(), "email": email})
    assert resposta.status_code == 422
    assert "email" in {c["campo"] for c in resposta.json()["campos"]}


async def test_nome_de_100_caracteres_aceito_e_de_101_recusado(cliente: httpx.AsyncClient) -> None:
    assert (
        await cadastrar(cliente, {**dados_conta().cadastro(), "nome": "n" * 100})
    ).status_code == 201
    assert (
        await cadastrar(cliente, {**dados_conta().cadastro(), "nome": "n" * 101})
    ).status_code == 422


# --- Cabeçalho X-Forwarded-For forjado ---------------------------------------------------


async def test_x_forwarded_for_forjado_nao_contorna_o_limite_por_endereco(
    aplicacao: FastAPI, cliente: httpx.AsyncClient
) -> None:
    """A conexão vem de um endereço que não é proxy confiável: o cabeçalho é ignorado."""
    conta = dados_conta()
    assert (await cadastrar(cliente, conta)).status_code == 201
    await sair(cliente)
    for i in range(20):
        await obter_csrf(cliente)
        resposta = await cliente.post(
            "/api/v1/auth/entrada",
            json={"email": f"alvo.{i}@exemplo.com", "senha": "errada-errada-1"},
            headers={"X-Forwarded-For": f"192.0.2.{i + 1}"},
        )
        assert resposta.status_code == 401
    await obter_csrf(cliente)
    bloqueada = await cliente.post(
        "/api/v1/auth/entrada", json=conta.entrada(), headers={"X-Forwarded-For": "192.0.2.250"}
    )
    assert bloqueada.status_code == 429


async def test_x_forwarded_for_so_vale_quando_vem_de_proxy_confiavel(
    aplicacao: FastAPI,
) -> None:
    """O proxy confiável diz quem é o cliente; endereços distintos têm limites distintos."""
    proxy = str(aplicacao.state.configuracao.proxies_confiaveis[0].network_address)
    conta = dados_conta()
    async with abrir_cliente(aplicacao, ip=proxy) as cliente:
        await cadastrar(cliente, conta)
        await sair(cliente)
        for i in range(20):
            await obter_csrf(cliente)
            resposta = await cliente.post(
                "/api/v1/auth/entrada",
                json={"email": f"alvo.{i}@exemplo.com", "senha": "errada-errada-1"},
                headers={"X-Forwarded-For": "192.0.2.10"},
            )
            assert resposta.status_code == 401
        await obter_csrf(cliente)
        bloqueado = await cliente.post(
            "/api/v1/auth/entrada", json=conta.entrada(), headers={"X-Forwarded-For": "192.0.2.10"}
        )
        assert bloqueado.status_code == 429
        await obter_csrf(cliente)
        outro_cliente = await cliente.post(
            "/api/v1/auth/entrada", json=conta.entrada(), headers={"X-Forwarded-For": "192.0.2.11"}
        )
        assert outro_cliente.status_code == 200, "outro cliente atrás do mesmo proxy não é afetado"
