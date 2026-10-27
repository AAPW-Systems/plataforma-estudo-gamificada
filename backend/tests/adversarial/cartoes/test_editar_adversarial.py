"""Entradas maliciosas e concorrência na edição de cartões (T023; DTEC 036 e 037)."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import psycopg
import pytest
from fastapi import FastAPI

from app.nucleo.configuracao import Configuracao
from tests.apoio_acervo import criar_conta, criar_materia
from tests.apoio_cartoes import criar_cartao
from tests.apoio_http import clientes_prontos

pytestmark = pytest.mark.adversarial


@pytest.fixture
async def estudante(acervo: FastAPI, cliente_real: httpx.AsyncClient) -> httpx.AsyncClient:
    await criar_conta(cliente_real)
    return cliente_real


@pytest.fixture
async def cartao(estudante: httpx.AsyncClient) -> dict[str, Any]:
    materia = await criar_materia(estudante, "Biologia")
    corpo: dict[str, Any] = (await criar_cartao(estudante, materia["id"])).json()
    return corpo


async def _editar(cliente: httpx.AsyncClient, cartao_id: str, corpo: Any) -> httpx.Response:
    return await cliente.patch(f"/api/v1/cartoes/{cartao_id}", json=corpo)


# --- Corpo ------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "corpo",
    [
        {},
        {"frente": None},
        {"verso": None},
        {"frente": 1},
        {"verso": ["v"]},
        {"explicacao": {"a": 1}},
        {"frente": "a" * 4001},
        {"verso": "a" * 8001},
        {"explicacao": "a" * 4001},
        {"origem": "gerado_verificado"},
        {"verificado": True},
        {"situacao": "suspenso"},
        {"fonteId": None},
        {"materiaId": "11111111-1111-4111-8111-111111111111"},
        {"vencimento": "2030-01-01T00:00:00Z"},
        {"estabilidade": 100.0},
        {"frente": "ok", "origem": "editado"},
    ],
    ids=lambda c: (next(iter(c)) if isinstance(c, dict) and c else type(c).__name__) or "vazio",
)
async def test_corpo_invalido_ou_com_campos_extras_e_422_e_nada_muda(
    estudante: httpx.AsyncClient, cartao: dict[str, Any], corpo: Any
) -> None:
    """`minProperties: 1`, tipos, tetos e `extra="forbid"`: nem origem nem agendamento entram."""
    resposta = await _editar(estudante, cartao["id"], corpo)
    assert resposta.status_code == 422, resposta.text
    assert resposta.json()["codigo"] == "dados_invalidos"
    assert (await estudante.get(f"/api/v1/cartoes/{cartao['id']}")).json() == cartao


@pytest.mark.parametrize("bruto", [b"", b"{", b"[]", b'"frente"', b"null", b"\xff\xfe"])
async def test_corpo_que_nao_e_um_objeto_json_nao_edita_nada(
    estudante: httpx.AsyncClient, cartao: dict[str, Any], bruto: bytes
) -> None:
    """Mesma convenção da criação: `400` ou `422`, e o cartão fica como estava."""
    resposta = await estudante.patch(
        f"/api/v1/cartoes/{cartao['id']}",
        content=bruto,
        headers={"Content-Type": "application/json"},
    )
    assert resposta.status_code in {400, 422}
    assert resposta.json()["codigo"] in {"requisicao_malformada", "dados_invalidos"}
    assert (await estudante.get(f"/api/v1/cartoes/{cartao['id']}")).json() == cartao


async def test_corpo_acima_de_64_kib_na_edicao_vira_413(
    estudante: httpx.AsyncClient, cartao: dict[str, Any]
) -> None:
    resposta = await _editar(estudante, cartao["id"], {"explicacao": "e" * (64 * 1024 + 1)})
    assert resposta.status_code == 413
    assert (await estudante.get(f"/api/v1/cartoes/{cartao['id']}")).json() == cartao


async def test_marcacao_e_invisiveis_no_meio_voltam_literais_na_edicao(
    estudante: httpx.AsyncClient, cartao: dict[str, Any]
) -> None:
    texto = "<script>alert(1)</script> ‮abc‬ e​f"
    resposta = await _editar(estudante, cartao["id"], {"frente": texto, "verso": texto})
    assert resposta.status_code == 200
    assert resposta.json()["frente"] == resposta.json()["verso"] == texto


# --- Concorrência -------------------------------------------------------------------------------


async def test_duas_edicoes_simultaneas_a_ultima_vale_sem_erro(
    acervo: FastAPI, estudante: httpx.AsyncClient, cartao: dict[str, Any]
) -> None:
    """Caso de borda: duas abas. As duas gravam (sem erro) e a linha fica com uma delas inteira."""
    async with clientes_prontos(acervo, ["198.51.100.41"]) as (outra_aba,):
        outra_aba.cookies.update(estudante.cookies)
        for rodada in range(5):
            a, b = await asyncio.gather(
                _editar(estudante, cartao["id"], {"frente": f"Aba A {rodada}", "verso": "A"}),
                _editar(outra_aba, cartao["id"], {"frente": f"Aba B {rodada}", "verso": "B"}),
            )
            assert (a.status_code, b.status_code) == (200, 200), (a.text, b.text)
            final = (await estudante.get(f"/api/v1/cartoes/{cartao['id']}")).json()
            assert (final["frente"], final["verso"]) in {
                (f"Aba A {rodada}", "A"),
                (f"Aba B {rodada}", "B"),
            }, "nunca uma mistura das duas edições"


async def test_exclusao_durante_a_edicao_da_404_e_nunca_500(
    estudante: httpx.AsyncClient, cartao: dict[str, Any], configuracao: Configuracao
) -> None:
    """Outra transação apaga o cartão enquanto a edição espera a linha: a edição não acha nada."""
    async with await psycopg.AsyncConnection.connect(configuracao.conninfo()) as exclusao:
        await exclusao.execute("DELETE FROM cartoes WHERE public_id = %s", (cartao["id"],))
        edicao = asyncio.create_task(_editar(estudante, cartao["id"], {"frente": "Tarde demais"}))
        await asyncio.sleep(0.3)
        assert not edicao.done(), "a edição espera a linha travada"
        await exclusao.commit()
    resposta = await edicao
    assert resposta.status_code == 404, resposta.text
    assert resposta.json()["codigo"] == "recurso_nao_encontrado"


async def test_edicao_antes_da_exclusao_e_aplicada_e_depois_o_cartao_some(
    estudante: httpx.AsyncClient, cartao: dict[str, Any], configuracao: Configuracao
) -> None:
    assert (await _editar(estudante, cartao["id"], {"frente": "Editado"})).status_code == 200
    async with await psycopg.AsyncConnection.connect(configuracao.conninfo()) as exclusao:
        await exclusao.execute("DELETE FROM cartoes WHERE public_id = %s", (cartao["id"],))
        await exclusao.commit()
    assert (await estudante.get(f"/api/v1/cartoes/{cartao['id']}")).status_code == 404
    assert (await _editar(estudante, cartao["id"], {"frente": "Outra"})).status_code == 404
