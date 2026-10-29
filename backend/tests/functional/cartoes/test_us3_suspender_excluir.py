"""US3: suspender, reativar e excluir, cenários 1 a 3 (T028; RF-004, RF-007, RF-008).

A ausência do suspenso nas lições (CS-003) e as revisões e o XP preservados depois da exclusão
são reverificados pela 005 e pela 006, donas das lições, das revisões e do XP. O filtro da lista
pela situação chega com a US4 (T035); aqui, a lista sem filtro mostra o suspenso como suspenso.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select, update

from app.cartoes.modelos import Cartao, EstadoFsrs
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.relogio import RelogioControlavel
from tests import fabricas_cartoes as fab
from tests.apoio_acervo import criar_conta, criar_materia
from tests.apoio_cartoes import criar_cartao, estado_fsrs, semear_na_materia

pytestmark = pytest.mark.functional


@pytest.fixture
async def estudante(acervo: FastAPI, cliente_real: httpx.AsyncClient) -> httpx.AsyncClient:
    await criar_conta(cliente_real)
    return cliente_real


@pytest.fixture
async def biologia(estudante: httpx.AsyncClient) -> dict[str, Any]:
    return await criar_materia(estudante, "Biologia")


def _fabrica(app: FastAPI) -> FabricaSessoes:
    fabrica: FabricaSessoes = app.state.fabrica_sessoes
    return fabrica


async def _suspender(cliente: httpx.AsyncClient, cartao_id: str) -> httpx.Response:
    return await cliente.post(f"/api/v1/cartoes/{cartao_id}/suspensao")


async def _reativar(cliente: httpx.AsyncClient, cartao_id: str) -> httpx.Response:
    return await cliente.post(f"/api/v1/cartoes/{cartao_id}/reativacao")


async def _atualizado_em(fabrica: FabricaSessoes, cartao_id: str) -> Any:
    async with unidade_de_trabalho(fabrica) as sessao:
        return (
            await sessao.execute(select(Cartao.atualizado_em).where(Cartao.public_id == cartao_id))
        ).scalar_one()


async def _lista(cliente: httpx.AsyncClient, materia_id: str) -> dict[str, Any]:
    corpo: dict[str, Any] = (await cliente.get(f"/api/v1/materias/{materia_id}/cartoes")).json()
    return corpo


# --- Cenário 1: suspender --------------------------------------------------------------------


async def test_suspender_um_cartao_ativo_preserva_o_agendamento_e_aparece_como_suspenso(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    biologia: dict[str, Any],
    relogio: RelogioControlavel,
) -> None:
    """US3-1 e RF-007: situação suspensa na resposta e na lista; o FSRS fica como estava."""
    criado = (await criar_cartao(estudante, biologia["id"])).json()
    antes = await estado_fsrs(_fabrica(acervo), criado["id"])
    relogio.avancar(minutes=5)

    resposta = await _suspender(estudante, criado["id"])

    assert resposta.status_code == 200
    suspenso = resposta.json()
    assert suspenso["situacao"] == "suspenso"
    assert suspenso["atualizadoEm"] != criado["atualizadoEm"]
    assert {k: v for k, v in suspenso.items() if k not in {"situacao", "atualizadoEm"}} == {
        k: v for k, v in criado.items() if k not in {"situacao", "atualizadoEm"}
    }
    assert await estado_fsrs(_fabrica(acervo), criado["id"]) == antes
    lista = await _lista(estudante, biologia["id"])
    assert [(c["id"], c["situacao"]) for c in lista["itens"]] == [(criado["id"], "suspenso")]
    assert lista["total"] == 1, "o suspenso continua na lista (RF-004)"


async def test_suspender_tira_o_cartao_da_contagem_de_ativos_da_materia(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    primeiro = (await criar_cartao(estudante, biologia["id"])).json()
    await criar_cartao(estudante, biologia["id"], frente="Outra")
    await _suspender(estudante, primeiro["id"])

    materia = (await estudante.get(f"/api/v1/materias/{biologia['id']}")).json()

    assert materia["cartoesAtivos"] == 1


@pytest.mark.parametrize("estado", list(EstadoFsrs))
async def test_suspender_e_reativar_mantem_as_colunas_do_fsrs_em_qualquer_estado(
    acervo: FastAPI, estudante: httpx.AsyncClient, biologia: dict[str, Any], estado: EstadoFsrs
) -> None:
    """RF-007: cartões já revisados (da fábrica) voltam com o mesmo estado, passo e vencimento."""
    item = next(c for c in fab.gerar(30) if c.estado_fsrs is estado)
    (cartao_id,) = await semear_na_materia(
        _fabrica(acervo), biologia["id"], [replace(item, com_referencia=False)]
    )
    antes = await estado_fsrs(_fabrica(acervo), cartao_id)

    for _ in range(2):
        assert (await _suspender(estudante, cartao_id)).json()["situacao"] == "suspenso"
        assert await estado_fsrs(_fabrica(acervo), cartao_id) == antes
        assert (await _reativar(estudante, cartao_id)).json()["situacao"] == "ativo"
        assert await estado_fsrs(_fabrica(acervo), cartao_id) == antes


# --- Cenário 2: reativar ---------------------------------------------------------------------


async def test_reativar_devolve_o_cartao_com_o_vencimento_de_antes(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    biologia: dict[str, Any],
    relogio: RelogioControlavel,
) -> None:
    """US3-2: o vencimento passou durante a suspensão, e o cartão volta devido, sem recálculo."""
    criado = (await criar_cartao(estudante, biologia["id"])).json()
    vencido = relogio.agora() - timedelta(days=12)
    async with unidade_de_trabalho(_fabrica(acervo)) as sessao:
        await sessao.execute(
            update(Cartao).where(Cartao.public_id == criado["id"]).values(vencimento=vencido)
        )
    antes = await estado_fsrs(_fabrica(acervo), criado["id"])
    await _suspender(estudante, criado["id"])
    relogio.avancar(hours=20)

    resposta = await _reativar(estudante, criado["id"])

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "ativo"
    depois = await estado_fsrs(_fabrica(acervo), criado["id"])
    assert depois == antes
    assert depois[4] == vencido < relogio.agora(), "continua no passado: devido"
    materia = (await estudante.get(f"/api/v1/materias/{biologia['id']}")).json()
    assert materia["cartoesAtivos"] == 1


async def test_suspender_ou_reativar_de_novo_nao_escreve_nada(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    biologia: dict[str, Any],
    relogio: RelogioControlavel,
) -> None:
    """Idempotente: `200` com o mesmo corpo e `atualizado_em` igual (contrato)."""
    criado = (await criar_cartao(estudante, biologia["id"])).json()

    relogio.avancar(minutes=1)
    reativado = await _reativar(estudante, criado["id"])
    assert reativado.status_code == 200
    assert reativado.json() == criado, "já ativo: nada muda"

    suspenso = (await _suspender(estudante, criado["id"])).json()
    marca = await _atualizado_em(_fabrica(acervo), criado["id"])
    relogio.avancar(minutes=1)
    de_novo = await _suspender(estudante, criado["id"])

    assert de_novo.status_code == 200
    assert de_novo.json() == suspenso
    assert await _atualizado_em(_fabrica(acervo), criado["id"]) == marca


# --- Cenário 3: excluir ----------------------------------------------------------------------


async def test_excluir_remove_o_cartao_e_um_segundo_pedido_e_404(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    """US3-3 e RF-008: `204`; depois, consulta, nova exclusão, suspensão e edição dão `404`."""
    fica = (await criar_cartao(estudante, biologia["id"], frente="Fica")).json()
    sai = (await criar_cartao(estudante, biologia["id"], frente="Sai")).json()

    resposta = await estudante.delete(f"/api/v1/cartoes/{sai['id']}")

    assert resposta.status_code == 204
    assert resposta.content == b""
    for depois in (
        await estudante.get(f"/api/v1/cartoes/{sai['id']}"),
        await estudante.delete(f"/api/v1/cartoes/{sai['id']}"),
        await _suspender(estudante, sai["id"]),
        await _reativar(estudante, sai["id"]),
        await estudante.patch(f"/api/v1/cartoes/{sai['id']}", json={"frente": "x"}),
    ):
        assert depois.status_code == 404
        assert depois.json()["codigo"] == "recurso_nao_encontrado"
    lista = await _lista(estudante, biologia["id"])
    assert [c["id"] for c in lista["itens"]] == [fica["id"]]
    assert lista["total"] == 1
    materia = (await estudante.get(f"/api/v1/materias/{biologia['id']}")).json()
    assert materia["cartoesAtivos"] == 1


async def test_excluir_um_cartao_suspenso_tambem_funciona(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    criado = (await criar_cartao(estudante, biologia["id"])).json()
    await _suspender(estudante, criado["id"])

    assert (await estudante.delete(f"/api/v1/cartoes/{criado['id']}")).status_code == 204
    assert (await _lista(estudante, biologia["id"]))["total"] == 0


async def test_excluir_um_cartao_que_cita_uma_fonte_nao_mexe_na_fonte(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    from tests.apoio_acervo import enviar
    from tests.fabricas_arquivos import validos

    arquivo = next(a for a in validos() if a.nome == "resumo.txt")
    fonte = (await enviar(estudante, biologia["id"], arquivo)).json()
    criado = (await criar_cartao(estudante, biologia["id"], fonteId=fonte["id"])).json()

    assert (await estudante.delete(f"/api/v1/cartoes/{criado['id']}")).status_code == 204
    assert (await estudante.get(f"/api/v1/fontes/{fonte['id']}")).status_code == 200
    materia = (await estudante.get(f"/api/v1/materias/{biologia['id']}")).json()
    assert materia["totalFontes"] == 1
