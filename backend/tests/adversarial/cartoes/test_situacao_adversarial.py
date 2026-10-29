"""Concorrência e entradas inesperadas em suspender, reativar e excluir (T029; DTEC 037)."""

from __future__ import annotations

import asyncio
from collections.abc import MutableMapping
from typing import Any

import httpx
import psycopg
import pytest
from fastapi import FastAPI
from structlog.testing import capture_logs

from app.nucleo.configuracao import Configuracao
from tests.apoio_acervo import criar_conta, criar_materia
from tests.apoio_cartoes import criar_cartao
from tests.apoio_http import clientes_prontos

pytestmark = pytest.mark.adversarial

ABAS = ["198.51.100.61", "198.51.100.62", "198.51.100.63", "198.51.100.64"]


@pytest.fixture
async def estudante(acervo: FastAPI, cliente_real: httpx.AsyncClient) -> httpx.AsyncClient:
    await criar_conta(cliente_real)
    return cliente_real


@pytest.fixture
async def cartao(estudante: httpx.AsyncClient) -> dict[str, Any]:
    materia = await criar_materia(estudante, "Biologia")
    corpo: dict[str, Any] = (await criar_cartao(estudante, materia["id"])).json()
    return corpo


def _eventos(registros: list[MutableMapping[str, Any]], nome: str) -> int:
    return sum(r["event"] == nome for r in registros)


async def test_suspensao_repetida_em_paralelo_tem_um_unico_efeito(
    acervo: FastAPI, estudante: httpx.AsyncClient, cartao: dict[str, Any]
) -> None:
    """Quatro abas suspendem juntas: todas respondem `200` suspenso, e só uma escreve."""
    async with clientes_prontos(acervo, ABAS) as abas:
        for aba in abas:
            aba.cookies.update(estudante.cookies)
        for rodada in range(3):
            with capture_logs() as registros:
                respostas = await asyncio.gather(
                    *(aba.post(f"/api/v1/cartoes/{cartao['id']}/suspensao") for aba in abas)
                )
            assert [r.status_code for r in respostas] == [200] * len(abas), rodada
            assert {r.json()["situacao"] for r in respostas} == {"suspenso"}
            assert len({r.json()["atualizadoEm"] for r in respostas}) == 1, "uma única escrita"
            assert _eventos(registros, "cartao_suspenso") == 1, rodada
            assert _eventos(registros, "cartao_situacao_sem_mudanca") == len(abas) - 1

            with capture_logs() as registros:
                respostas = await asyncio.gather(
                    *(aba.post(f"/api/v1/cartoes/{cartao['id']}/reativacao") for aba in abas)
                )
            assert {r.json()["situacao"] for r in respostas} == {"ativo"}
            assert _eventos(registros, "cartao_reativado") == 1, rodada


async def test_suspender_e_reativar_ao_mesmo_tempo_termina_numa_situacao_coerente(
    acervo: FastAPI, estudante: httpx.AsyncClient, cartao: dict[str, Any]
) -> None:
    async with clientes_prontos(acervo, ABAS[:2]) as (a, b):
        a.cookies.update(estudante.cookies)
        b.cookies.update(estudante.cookies)
        for _ in range(5):
            suspensao, reativacao = await asyncio.gather(
                a.post(f"/api/v1/cartoes/{cartao['id']}/suspensao"),
                b.post(f"/api/v1/cartoes/{cartao['id']}/reativacao"),
            )
            assert (suspensao.status_code, reativacao.status_code) == (200, 200)
            final = (await estudante.get(f"/api/v1/cartoes/{cartao['id']}")).json()
            assert final["situacao"] in {"ativo", "suspenso"}
            assert final["frente"] == cartao["frente"]


async def test_exclusao_repetida_em_paralelo_da_um_204_e_o_resto_404(
    acervo: FastAPI, estudante: httpx.AsyncClient, cartao: dict[str, Any]
) -> None:
    async with clientes_prontos(acervo, ABAS) as abas:
        for aba in abas:
            aba.cookies.update(estudante.cookies)
        respostas = await asyncio.gather(
            *(aba.delete(f"/api/v1/cartoes/{cartao['id']}") for aba in abas)
        )
    assert sorted(r.status_code for r in respostas) == [204] + [404] * (len(abas) - 1)


async def test_suspensao_durante_a_exclusao_da_404_e_nunca_500(
    estudante: httpx.AsyncClient, cartao: dict[str, Any], configuracao: Configuracao
) -> None:
    """A exclusão (outra conexão) segura a linha; a suspensão espera e encontra o cartão sumido."""
    async with await psycopg.AsyncConnection.connect(configuracao.conninfo()) as exclusao:
        await exclusao.execute("DELETE FROM cartoes WHERE public_id = %s", (cartao["id"],))
        suspensao = asyncio.create_task(estudante.post(f"/api/v1/cartoes/{cartao['id']}/suspensao"))
        await asyncio.sleep(0.3)
        assert not suspensao.done(), "a suspensão espera a linha travada"
        await exclusao.commit()
    resposta = await suspensao
    assert resposta.status_code == 404, resposta.text
    assert resposta.json()["codigo"] == "recurso_nao_encontrado"


@pytest.mark.parametrize("sufixo", ["/suspensao", "/reativacao"])
async def test_corpo_enviado_nas_acoes_e_ignorado_e_nao_forja_nada(
    estudante: httpx.AsyncClient, cartao: dict[str, Any], sufixo: str
) -> None:
    """As ações não têm corpo: campos como `origem` ou `vencimento` não mudam nada."""
    resposta = await estudante.post(
        f"/api/v1/cartoes/{cartao['id']}{sufixo}",
        json={"situacao": "recusado", "origem": "gerado_verificado", "vencimento": "2030-01-01"},
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["origem"] == "criado" and corpo["verificado"] is False
    assert corpo["situacao"] == ("suspenso" if sufixo == "/suspensao" else "ativo")


@pytest.mark.parametrize("metodo", ["GET", "PUT", "PATCH", "DELETE"])
async def test_metodos_nao_previstos_nas_acoes_sao_405(
    estudante: httpx.AsyncClient, cartao: dict[str, Any], metodo: str
) -> None:
    resposta = await estudante.request(metodo, f"/api/v1/cartoes/{cartao['id']}/suspensao")
    assert resposta.status_code == 405
    assert (await estudante.get(f"/api/v1/cartoes/{cartao['id']}")).json() == cartao
