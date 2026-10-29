"""US4: encontrar um cartão, cenários 1 a 3, com os 120 cartões da fábrica (T035; RF-010).

O esperado é calculado em Python sobre os mesmos textos (sem acentos e em minúsculas), e a API
tem de devolver exatamente esse conjunto, percorrendo todas as páginas.
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from dataclasses import replace
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from app.nucleo.banco import FabricaSessoes
from tests import fabricas_cartoes as fab
from tests.apoio_acervo import criar_conta, criar_materia
from tests.apoio_cartoes import semear_na_materia

pytestmark = pytest.mark.functional

ITENS = [replace(c, com_referencia=False) for c in fab.gerar(120)]


def _simples(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c)).lower()


def _esperado(
    termo: str | None = None, situacao: str | None = None, origem: str | None = None
) -> Counter[tuple[str, str]]:
    """Quantos cartões de cada texto devem voltar (a fábrica repete textos entre os 120)."""
    return Counter(
        (c.frente, c.verso)
        for c in ITENS
        if (
            termo is None
            or _simples(termo) in _simples(c.frente)
            or _simples(termo) in _simples(c.verso)
        )
        and (situacao is None or c.situacao.value == situacao)
        and (origem is None or c.origem.value == origem)
    )


@pytest.fixture
async def estudante(acervo: FastAPI, cliente_real: httpx.AsyncClient) -> httpx.AsyncClient:
    await criar_conta(cliente_real)
    return cliente_real


@pytest.fixture
async def biologia(acervo: FastAPI, estudante: httpx.AsyncClient) -> dict[str, Any]:
    materia = await criar_materia(estudante, "Biologia")
    fabrica: FabricaSessoes = acervo.state.fabrica_sessoes
    await semear_na_materia(fabrica, materia["id"], ITENS)
    return materia


async def _todas(
    cliente: httpx.AsyncClient, materia_id: str, **filtros: Any
) -> tuple[list[dict[str, Any]], list[int]]:
    """Todas as páginas da lista com os filtros; devolve os itens e o `total` de cada página."""
    itens: list[dict[str, Any]] = []
    totais: list[int] = []
    parametros = {k: v for k, v in filtros.items() if v is not None}
    while True:
        resposta = await cliente.get(f"/api/v1/materias/{materia_id}/cartoes", params=parametros)
        assert resposta.status_code == 200, resposta.text
        corpo = resposta.json()
        itens += corpo["itens"]
        totais.append(corpo["total"])
        if corpo["proximoCursor"] is None:
            return itens, totais
        parametros["cursor"] = corpo["proximoCursor"]


def _pares(itens: list[dict[str, Any]]) -> Counter[tuple[str, str]]:
    return Counter((c["frente"], c["verso"]) for c in itens)


# --- Cenário 1: busca por texto ------------------------------------------------------------------


@pytest.mark.parametrize("termo", ["celula", "CÉLULA", "Célula", "CELULA"])
async def test_busca_encontra_frente_ou_verso_sem_diferenciar_maiusculas_e_acentos(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], termo: str
) -> None:
    esperado = _esperado(termo)
    assert esperado.total() >= 10, "a fábrica tem cartões com variações de 'célula'"

    itens, totais = await _todas(estudante, biologia["id"], busca=termo)

    assert _pares(itens) == esperado
    assert len({c["id"] for c in itens}) == len(itens), "sem repetição"
    assert set(totais) == {esperado.total()}


async def test_busca_por_uma_palavra_que_so_aparece_no_verso(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    so_no_verso = next(
        palavra
        for c in ITENS
        for palavra in c.verso.split()
        if len(palavra) > 5
        and palavra.isalpha()
        and not any(_simples(palavra) in _simples(o.frente) for o in ITENS)
    )
    esperado = _esperado(so_no_verso)
    assert esperado

    itens, _ = await _todas(estudante, biologia["id"], busca=so_no_verso)

    assert _pares(itens) == esperado


# --- Cenário 2: filtros combináveis --------------------------------------------------------------


@pytest.mark.parametrize(
    "filtros",
    [
        {"situacao": "suspenso"},
        {"situacao": "ativo"},
        {"origem": "criado"},
        {"origem": "editado"},
        {"origem": "gerado_verificado"},
        {"busca": "celula", "situacao": "suspenso"},
        {"busca": "celula", "origem": "criado"},
        {"busca": "celula", "situacao": "ativo", "origem": "gerado_verificado"},
    ],
    ids=lambda f: "-".join(f"{k}={v}" for k, v in f.items()),
)
async def test_filtros_de_situacao_e_origem_combinam_com_a_busca(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], filtros: dict[str, str]
) -> None:
    esperado = _esperado(filtros.get("busca"), filtros.get("situacao"), filtros.get("origem"))

    itens, totais = await _todas(estudante, biologia["id"], **filtros)

    assert _pares(itens) == esperado
    assert set(totais) == {esperado.total()}
    for item in itens:
        if "situacao" in filtros:
            assert item["situacao"] == filtros["situacao"]
        if "origem" in filtros:
            assert item["origem"] == filtros["origem"]


async def test_suspenso_aparece_como_suspenso_na_lista_filtrada(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    """Remete à T028: o filtro por situação, que chegou com a US4 (RF-004)."""
    itens, _ = await _todas(estudante, biologia["id"], situacao="suspenso")
    assert itens and {c["situacao"] for c in itens} == {"suspenso"}
    sem_filtro, _ = await _todas(estudante, biologia["id"])
    assert {c["id"] for c in itens} < {c["id"] for c in sem_filtro}


# --- Cenário 3: nenhum resultado e total ---------------------------------------------------------


async def test_busca_sem_resultado_tem_total_zero_mas_a_materia_continua_com_cartoes(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    """A tela distingue "nenhum cartão corresponde" (total 0 com filtros) da matéria vazia."""
    filtrada = (
        await estudante.get(f"/api/v1/materias/{biologia['id']}/cartoes", params={"busca": "xyzw"})
    ).json()
    sem_filtro = (await estudante.get(f"/api/v1/materias/{biologia['id']}/cartoes")).json()
    vazia = await criar_materia(estudante, "Vazia")
    da_vazia = (await estudante.get(f"/api/v1/materias/{vazia['id']}/cartoes")).json()

    assert (filtrada["itens"], filtrada["total"], filtrada["proximoCursor"]) == ([], 0, None)
    assert sem_filtro["total"] == 120
    assert (da_vazia["itens"], da_vazia["total"]) == ([], 0)


@pytest.mark.parametrize("busca", ["", "   ", "\t \n"])
async def test_busca_vazia_ou_so_com_espacos_equivale_a_sem_busca(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], busca: str
) -> None:
    primeira = (
        await estudante.get(
            f"/api/v1/materias/{biologia['id']}/cartoes", params={"busca": busca, "limite": 10}
        )
    ).json()
    assert primeira["total"] == 120
    # Equivale também no cursor: o da lista sem busca serve na lista com busca vazia.
    sem_busca = (
        await estudante.get(f"/api/v1/materias/{biologia['id']}/cartoes", params={"limite": 10})
    ).json()
    seguinte = await estudante.get(
        f"/api/v1/materias/{biologia['id']}/cartoes",
        params={"busca": busca, "limite": 10, "cursor": sem_busca["proximoCursor"]},
    )
    assert seguinte.status_code == 200
    assert primeira["itens"] == sem_busca["itens"]


# --- Paginação com filtros -----------------------------------------------------------------------


async def test_paginacao_com_filtros_nao_repete_nem_pula(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    esperado = _esperado("a", situacao="ativo")
    assert esperado.total() > 7 * 3, "várias páginas"

    itens, totais = await _todas(estudante, biologia["id"], busca="a", situacao="ativo", limite=7)

    assert len(itens) == len({c["id"] for c in itens}) == esperado.total()
    assert _pares(itens) == esperado
    assert set(totais) == {esperado.total()}
    datas = [c["criadoEm"] for c in itens]
    assert datas == sorted(datas, reverse=True), "do mais recente ao mais antigo"


@pytest.mark.parametrize(
    "outros",
    [
        {"busca": "outra"},
        {"busca": "celula", "situacao": "ativo"},
        {"busca": "celula", "origem": "criado"},
        {},
    ],
    ids=["outra-busca", "mais-situacao", "mais-origem", "sem-filtros"],
)
async def test_cursor_reaproveitado_com_outros_filtros_e_422_cursor_invalido(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], outros: dict[str, str]
) -> None:
    primeira = (
        await estudante.get(
            f"/api/v1/materias/{biologia['id']}/cartoes", params={"busca": "celula", "limite": 2}
        )
    ).json()
    assert primeira["proximoCursor"]

    resposta = await estudante.get(
        f"/api/v1/materias/{biologia['id']}/cartoes",
        params={**outros, "limite": 2, "cursor": primeira["proximoCursor"]},
    )

    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "cursor_invalido"


async def test_termo_com_espacos_nas_pontas_e_a_mesma_lista_para_o_cursor(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    """O resumo do cursor guarda o termo normalizado (NFC, sem pontas)."""
    primeira = (
        await estudante.get(
            f"/api/v1/materias/{biologia['id']}/cartoes", params={"busca": " celula ", "limite": 2}
        )
    ).json()
    seguinte = await estudante.get(
        f"/api/v1/materias/{biologia['id']}/cartoes",
        params={"busca": "celula", "limite": 2, "cursor": primeira["proximoCursor"]},
    )
    assert seguinte.status_code == 200
