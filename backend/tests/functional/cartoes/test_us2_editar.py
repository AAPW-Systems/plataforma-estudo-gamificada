"""US2: editar um cartão, cenários 1 a 3 (T022; RF-005, RF-006, CS-002).

O cartão "Gerado e verificado" vem da fábrica (a 004 é quem os cria); a evidência mantida depois
da edição é reverificada pela 004, dona de `evidencias_cartoes`.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from app.cartoes.modelos import EstadoFsrs, OrigemCartao, SituacaoCartao
from app.nucleo.banco import FabricaSessoes
from app.nucleo.relogio import RelogioControlavel
from tests import fabricas_cartoes as fab
from tests.apoio_acervo import criar_conta, criar_materia, enviar
from tests.apoio_cartoes import criar_cartao, estado_fsrs, semear_na_materia
from tests.fabricas_arquivos import validos

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


async def _editar(cliente: httpx.AsyncClient, cartao_id: str, **corpo: Any) -> httpx.Response:
    return await cliente.patch(f"/api/v1/cartoes/{cartao_id}", json=corpo)


# --- Consulta --------------------------------------------------------------------------------


async def test_consultar_um_cartao_devolve_o_mesmo_corpo_da_lista(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    criado = (await criar_cartao(estudante, biologia["id"], explicacao="Linha 1\nLinha 2")).json()

    resposta = await estudante.get(f"/api/v1/cartoes/{criado['id']}")

    assert resposta.status_code == 200
    assert resposta.json() == criado
    assert resposta.headers["Cache-Control"] == "no-store"


# --- Cenário 1: editar um cartão "Criado por você" -------------------------------------------


async def test_editar_a_frente_muda_o_texto_e_nao_o_agendamento(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    biologia: dict[str, Any],
    relogio: RelogioControlavel,
) -> None:
    """US2-1 e RF-005: o novo texto aparece; vencimento e estabilidade ficam como estavam."""
    criado = (await criar_cartao(estudante, biologia["id"])).json()
    antes = await estado_fsrs(_fabrica(acervo), criado["id"])
    relogio.avancar(minutes=10)

    resposta = await _editar(estudante, criado["id"], frente="Que organela produz ATP?")

    assert resposta.status_code == 200
    editado = resposta.json()
    assert editado["frente"] == "Que organela produz ATP?"
    assert editado["verso"] == criado["verso"]
    assert (editado["origem"], editado["verificado"]) == ("criado", False)
    assert editado["atualizadoEm"] > criado["atualizadoEm"]
    assert editado["criadoEm"] == criado["criadoEm"]
    assert await estado_fsrs(_fabrica(acervo), criado["id"]) == antes
    lista = (await estudante.get(f"/api/v1/materias/{biologia['id']}/cartoes")).json()
    assert lista["itens"][0]["frente"] == "Que organela produz ATP?"


async def test_edicao_parcial_e_remocao_da_explicacao_com_nulo(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    criado = (await criar_cartao(estudante, biologia["id"], explicacao="Para lembrar")).json()

    so_verso = (await _editar(estudante, criado["id"], verso="Mitocôndria")).json()
    assert (so_verso["frente"], so_verso["verso"], so_verso["explicacao"]) == (
        criado["frente"],
        "Mitocôndria",
        "Para lembrar",
    )
    sem_explicacao = (await _editar(estudante, criado["id"], explicacao=None)).json()
    assert sem_explicacao["explicacao"] is None
    com_vazia = (await _editar(estudante, criado["id"], explicacao="   ")).json()
    assert com_vazia["explicacao"] is None
    nova = (await _editar(estudante, criado["id"], explicacao="Linha 1\r\nLinha 2")).json()
    assert nova["explicacao"] == "Linha 1\nLinha 2"


async def test_edicao_mantem_a_referencia_copiada(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    """A referência é definida só na criação (DTEC 035) e a edição não a toca."""
    resumo = {a.nome: a for a in validos()}["resumo.txt"]
    fonte = (await enviar(estudante, biologia["id"], resumo, titulo="Citologia")).json()
    criado = (await criar_cartao(estudante, biologia["id"], fonteId=fonte["id"])).json()

    editado = (await _editar(estudante, criado["id"], frente="Outra")).json()

    assert editado["referencia"] == criado["referencia"]
    assert editado["origem"] == "criado"


# --- Cenário 2: editar um cartão "Gerado e verificado" ---------------------------------------


@pytest.mark.parametrize("campo", ["frente", "verso", "explicacao"])
async def test_editar_um_gerado_e_verificado_vira_editado_por_voce(
    acervo: FastAPI, estudante: httpx.AsyncClient, biologia: dict[str, Any], campo: str
) -> None:
    """US2-2 e RF-006: a origem muda, o selo sai e o agendamento fica (CS-002)."""
    # Um cartão gerado já revisado, como os que a 004 publica e a 005 agenda.
    gerado = replace(
        next(c for c in fab.gerar(12) if c.origem is OrigemCartao.GERADO_VERIFICADO),
        situacao=SituacaoCartao.ATIVO,
        explicacao="Explicação gerada",
    )
    (cartao_id,) = await semear_na_materia(_fabrica(acervo), biologia["id"], [gerado])
    antes = (await estudante.get(f"/api/v1/cartoes/{cartao_id}")).json()
    fsrs_antes = await estado_fsrs(_fabrica(acervo), cartao_id)
    assert (antes["origem"], antes["verificado"]) == ("gerado_verificado", True)

    editado = (
        await _editar(estudante, cartao_id, **{campo: "Texto revisto pelo estudante"})
    ).json()

    assert (editado["origem"], editado["verificado"]) == ("editado", False)
    assert editado[campo] == "Texto revisto pelo estudante"
    assert await estado_fsrs(_fabrica(acervo), cartao_id) == fsrs_antes
    lista = (await estudante.get(f"/api/v1/materias/{biologia['id']}/cartoes")).json()
    assert lista["itens"][0]["origem"] == "editado"


async def test_editar_de_novo_um_editado_continua_editado(
    acervo: FastAPI, estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    item = replace(fab.cartao_ficticio(), origem=OrigemCartao.EDITADO)
    (cartao_id,) = await semear_na_materia(_fabrica(acervo), biologia["id"], [item])
    editado = (await _editar(estudante, cartao_id, verso="Outra vez")).json()
    assert (editado["origem"], editado["verificado"]) == ("editado", False)


# --- Cenário 3: edição sem mudança ----------------------------------------------------------


@pytest.mark.parametrize(
    "origem", [OrigemCartao.GERADO_VERIFICADO, OrigemCartao.EDITADO, OrigemCartao.CRIADO]
)
async def test_edicao_sem_mudanca_nao_muda_a_origem_nem_a_data(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    biologia: dict[str, Any],
    relogio: RelogioControlavel,
    origem: OrigemCartao,
) -> None:
    """US2-3: salvar o mesmo texto (até com espaços nas pontas e CRLF) não muda nada."""
    item = fab.cartao_ficticio(origem=origem, explicacao="Linha 1\nLinha 2")
    (cartao_id,) = await semear_na_materia(_fabrica(acervo), biologia["id"], [item])
    antes = (await estudante.get(f"/api/v1/cartoes/{cartao_id}")).json()
    relogio.avancar(hours=1)

    resposta = await _editar(
        estudante,
        cartao_id,
        frente=f"  {antes['frente']}  ",
        verso=antes["verso"],
        explicacao="Linha 1\r\nLinha 2\n",
    )

    assert resposta.status_code == 200
    assert resposta.json() == antes


# --- Validação --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("corpo", "campos"),
    [
        ({"frente": "   "}, {"frente": "Use de 1 a 1.000 caracteres."}),
        ({"verso": ""}, {"verso": "Use de 1 a 2.000 caracteres."}),
        ({"explicacao": "e" * 1001}, {"explicacao": "Use até 1.000 caracteres."}),
        (
            {"frente": "x" * 1001, "verso": "\n"},
            {"frente": "Use de 1 a 1.000 caracteres.", "verso": "Use de 1 a 2.000 caracteres."},
        ),
    ],
    ids=["frente-so-espacos", "verso-vazio", "explicacao-acima", "dois-campos"],
)
async def test_texto_invalido_na_edicao_e_422_por_campo_e_nada_muda(
    estudante: httpx.AsyncClient,
    biologia: dict[str, Any],
    corpo: dict[str, Any],
    campos: dict[str, str],
) -> None:
    criado = (await criar_cartao(estudante, biologia["id"])).json()
    resposta = await _editar(estudante, criado["id"], **corpo)
    assert resposta.status_code == 422
    assert {c["campo"]: c["mensagem"] for c in resposta.json()["campos"]} == campos
    assert (await estudante.get(f"/api/v1/cartoes/{criado['id']}")).json() == criado


# --- CS-002: 20 edições em estados diferentes do FSRS ------------------------------------------


async def test_cs002_vinte_edicoes_nao_mudam_vencimento_nem_estabilidade(
    acervo: FastAPI, estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    itens = [replace(c, com_referencia=False) for c in fab.gerar(20)]
    assert {c.estado_fsrs for c in itens} == set(EstadoFsrs)
    ids = await semear_na_materia(_fabrica(acervo), biologia["id"], itens)
    antes = {cartao_id: await estado_fsrs(_fabrica(acervo), cartao_id) for cartao_id in ids}
    variacoes: list[dict[str, Any]] = [
        {"frente": "Frente editada"},
        {"verso": "Verso editado"},
        {"explicacao": "Explicação nova"},
        {"explicacao": None},
        {"frente": "F", "verso": "V", "explicacao": "E"},
    ]

    for numero, cartao_id in enumerate(ids):
        resposta = await _editar(estudante, cartao_id, **variacoes[numero % len(variacoes)])
        assert resposta.status_code == 200, resposta.text

    for cartao_id in ids:
        assert await estado_fsrs(_fabrica(acervo), cartao_id) == antes[cartao_id], cartao_id
