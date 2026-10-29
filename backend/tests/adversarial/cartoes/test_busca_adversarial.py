"""Entradas maliciosas ou inesperadas na busca e nos filtros da lista (T036; DTEC 033 e 034)."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from tests.apoio_acervo import criar_conta, criar_materia
from tests.apoio_cartoes import criar_cartao

pytestmark = pytest.mark.adversarial

FRENTES = [
    "Taxa de 100% de acerto",
    "Meta_final da unidade",
    "Caminho C:\\dados",
    "Aspas 'simples' e \"duplas\"",
    "Pergunta comum",
]


@pytest.fixture
async def estudante(acervo: FastAPI, cliente_real: httpx.AsyncClient) -> httpx.AsyncClient:
    await criar_conta(cliente_real)
    return cliente_real


@pytest.fixture
async def materia(estudante: httpx.AsyncClient) -> dict[str, Any]:
    criada = await criar_materia(estudante, "Biologia")
    for frente in FRENTES:
        assert (await criar_cartao(estudante, criada["id"], frente=frente)).status_code == 201
    return criada


async def _listar(cliente: httpx.AsyncClient, materia_id: str, **params: Any) -> httpx.Response:
    return await cliente.get(f"/api/v1/materias/{materia_id}/cartoes", params=params)


def _frentes(resposta: httpx.Response) -> list[str]:
    return sorted(c["frente"] for c in resposta.json()["itens"])


async def test_busca_com_101_caracteres_e_422_e_com_100_e_aceita(
    estudante: httpx.AsyncClient, materia: dict[str, Any]
) -> None:
    acima = await _listar(estudante, materia["id"], busca="a" * 101)
    assert acima.status_code == 422
    assert acima.json()["codigo"] == "dados_invalidos"
    no_limite = await _listar(estudante, materia["id"], busca="a" * 100)
    assert no_limite.status_code == 200
    assert no_limite.json()["total"] == 0
    # O teto conta caracteres, não bytes: 100 emojis fora do plano básico também cabem.
    assert (await _listar(estudante, materia["id"], busca="🧬" * 100)).status_code == 200


@pytest.mark.parametrize(
    ("termo", "esperadas"),
    [
        ("%", ["Taxa de 100% de acerto"]),
        ("%%%", []),
        ("_", ["Meta_final da unidade"]),
        ("%_%", []),
        ("\\", ["Caminho C:\\dados"]),
        ("\\\\", []),
        ("'", ["Aspas 'simples' e \"duplas\""]),
        ('"', ["Aspas 'simples' e \"duplas\""]),
        ("' OR '1'='1", []),
        ("'; DELETE FROM cartoes; --", []),
        ("\\'", []),
        ("$1", []),
        ("%' ESCAPE '", []),
    ],
)
async def test_curingas_aspas_e_trechos_de_sql_sao_texto(
    estudante: httpx.AsyncClient, materia: dict[str, Any], termo: str, esperadas: list[str]
) -> None:
    resposta = await _listar(estudante, materia["id"], busca=termo)
    assert resposta.status_code == 200, resposta.text
    assert _frentes(resposta) == sorted(esperadas)
    assert resposta.json()["total"] == len(esperadas)
    # Nada foi apagado nem alterado pela busca.
    assert (await _listar(estudante, materia["id"])).json()["total"] == len(FRENTES)


@pytest.mark.parametrize("termo", ["\x00", "\x00celula", "a\x07b", "\u200b"])
async def test_controles_e_invisiveis_no_termo_nao_viram_500(
    estudante: httpx.AsyncClient, materia: dict[str, Any], termo: str
) -> None:
    resposta = await _listar(estudante, materia["id"], busca=termo)
    assert resposta.status_code in {200, 422}, resposta.text
    if resposta.status_code == 422:
        assert resposta.json()["codigo"] == "dados_invalidos"


@pytest.mark.parametrize(
    ("parametro", "valor"),
    [
        ("situacao", "recusado"),
        ("situacao", "aguardando_revisao"),
        ("situacao", "ATIVO"),
        ("situacao", "ativo' OR '1'='1"),
        ("situacao", ""),
        ("origem", "verificado"),
        ("origem", "CRIADO"),
        ("origem", "gerado"),
        ("origem", ""),
    ],
)
async def test_valores_fora_dos_enums_de_situacao_e_origem_sao_422(
    estudante: httpx.AsyncClient, materia: dict[str, Any], parametro: str, valor: str
) -> None:
    resposta = await _listar(estudante, materia["id"], **{parametro: valor})
    assert resposta.status_code == 422, resposta.text
    corpo = resposta.json()
    assert corpo["codigo"] == "dados_invalidos"
    assert [c["campo"] for c in corpo["campos"]] == [parametro]


async def test_parametros_repetidos_nao_somam_filtros_nem_viram_500(
    estudante: httpx.AsyncClient, materia: dict[str, Any]
) -> None:
    resposta = await estudante.get(
        f"/api/v1/materias/{materia['id']}/cartoes?situacao=ativo&situacao=suspenso&busca=a&busca=b"
    )
    assert resposta.status_code in {200, 422}, resposta.text


async def test_cursor_de_uma_busca_nao_serve_para_a_mesma_busca_com_outro_curinga(
    estudante: httpx.AsyncClient, materia: dict[str, Any]
) -> None:
    primeira = (await _listar(estudante, materia["id"], busca="a", limite=1)).json()
    assert primeira["proximoCursor"]
    resposta = await _listar(
        estudante, materia["id"], busca="a%", limite=1, cursor=primeira["proximoCursor"]
    )
    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "cursor_invalido"
