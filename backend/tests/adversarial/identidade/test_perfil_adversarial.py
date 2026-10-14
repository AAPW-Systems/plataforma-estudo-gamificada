"""Alteração do perfil sob entradas hostis e concorrência (T048; RF-008, RF-010, RF-003)."""

from __future__ import annotations

import asyncio
import json
from decimal import Decimal

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select

from app.identidade.modelos import Usuario
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.revisao.modelos import ParametrosFsrs
from tests.apoio_http import abrir_cliente, cadastrar, obter_csrf
from tests.fabricas import dados_conta

pytestmark = pytest.mark.adversarial


async def _enviar(cliente: httpx.AsyncClient, corpo: bytes | str) -> httpx.Response:
    return await cliente.patch(
        "/api/v1/perfil",
        content=corpo if isinstance(corpo, bytes) else corpo.encode(),
        headers={"Content-Type": "application/json"},
    )


async def _perfil(cliente: httpx.AsyncClient) -> dict[str, object]:
    return (await cliente.get("/api/v1/perfil")).json()  # type: ignore[no-any-return]


async def test_trocas_de_retencao_concorrentes_geram_versoes_sem_lacuna_nem_duplicata(
    aplicacao_real: FastAPI, fabrica_real: FabricaSessoes
) -> None:
    async with abrir_cliente(aplicacao_real, ip="198.51.100.60") as cliente:
        assert (await cadastrar(cliente, dados_conta())).status_code == 201
        # Vários clientes da mesma conta (mesma sessão) mandando valores diferentes ao mesmo tempo.
        valores = [0.70 + i * 0.01 for i in range(1, 21)]
        respostas = await asyncio.gather(
            *(
                cliente.patch("/api/v1/perfil", json={"retencaoDesejada": round(v, 2)})
                for v in valores
            )
        )
    assert {r.status_code for r in respostas} == {200}, [
        r.text for r in respostas if r.status_code != 200
    ]
    async with unidade_de_trabalho(fabrica_real) as sessao:
        versoes = list(
            (
                await sessao.execute(select(ParametrosFsrs.versao).order_by(ParametrosFsrs.versao))
            ).scalars()
        )
    assert versoes == list(range(1, 22)), "1 inicial + 20 trocas, sem lacuna e sem repetição"


async def test_trocas_concorrentes_do_mesmo_valor_criam_uma_so_versao(
    aplicacao_real: FastAPI, fabrica_real: FabricaSessoes
) -> None:
    async with abrir_cliente(aplicacao_real, ip="198.51.100.61") as cliente:
        assert (await cadastrar(cliente, dados_conta())).status_code == 201
        respostas = await asyncio.gather(
            *(cliente.patch("/api/v1/perfil", json={"retencaoDesejada": 0.85}) for _ in range(15))
        )
    assert {r.status_code for r in respostas} == {200}
    async with unidade_de_trabalho(fabrica_real) as sessao:
        versoes = list((await sessao.execute(select(ParametrosFsrs.versao))).scalars())
    assert sorted(versoes) == [1, 2]


async def test_alteracoes_simultaneas_de_campos_diferentes_nao_se_perdem(
    aplicacao_real: FastAPI, fabrica_real: FabricaSessoes
) -> None:
    async with abrir_cliente(aplicacao_real, ip="198.51.100.62") as cliente:
        assert (await cadastrar(cliente, dados_conta())).status_code == 201
        respostas = await asyncio.gather(
            cliente.patch("/api/v1/perfil", json={"metaDiaria": 77}),
            cliente.patch("/api/v1/perfil", json={"tamanhoLicao": 17}),
            cliente.patch("/api/v1/perfil", json={"limiteNovosDia": 7}),
            cliente.patch("/api/v1/perfil", json={"nome": "Nome Concorrente"}),
        )
        assert {r.status_code for r in respostas} == {200}
        perfil = await _perfil(cliente)
    assert (
        perfil["metaDiaria"],
        perfil["tamanhoLicao"],
        perfil["limiteNovosDia"],
        perfil["nome"],
    ) == (
        77,
        17,
        7,
        "Nome Concorrente",
    )


@pytest.mark.parametrize(
    "fuso",
    [
        "../../etc/passwd",
        "/etc/passwd",
        "..",
        "America/../UTC",
        "A" * 65,
        "UTC\x00",
        "",
        "utc ",
        "‮UTC",
    ],
)
async def test_fuso_hostil_e_recusado_sem_alterar_nada(
    cliente: httpx.AsyncClient, fuso: str
) -> None:
    await cadastrar(cliente, dados_conta(fuso="America/Recife"))
    antes = await _perfil(cliente)
    resposta = await _enviar(cliente, json.dumps({"fuso": fuso}))
    assert resposta.status_code == 422, resposta.text
    assert "fuso" in {c["campo"] for c in resposta.json()["campos"]}
    assert await _perfil(cliente) == antes


@pytest.mark.parametrize("valor", ["0.925", "0.9001", "0.8999999", "9e-1", "0.699", "0.971"])
async def test_retencao_com_mais_de_duas_casas_ou_fora_do_intervalo_e_recusada(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes, valor: str
) -> None:
    await cadastrar(cliente, dados_conta())
    resposta = await _enviar(cliente, f'{{"retencaoDesejada": {valor}}}')  # número JSON cru
    if Decimal(valor).quantize(Decimal("0.01")) == Decimal(valor) and Decimal("0.70") <= Decimal(
        valor
    ) <= Decimal("0.97"):
        assert resposta.status_code == 200
    else:
        assert resposta.status_code == 422, resposta.text
        assert [c["campo"] for c in resposta.json()["campos"]] == ["retencaoDesejada"]
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        assert len(list((await sessao.execute(select(ParametrosFsrs.id))).scalars())) == 1


@pytest.mark.parametrize(
    "valor", ["NaN", "Infinity", "-Infinity", "1e999", "true", '"0.9"', "null", "[0.9]", '{"a": 1}']
)
async def test_retencao_com_tipos_e_valores_estranhos_e_recusada(
    cliente: httpx.AsyncClient, valor: str
) -> None:
    await cadastrar(cliente, dados_conta())
    resposta = await _enviar(cliente, f'{{"retencaoDesejada": {valor}}}')
    assert resposta.status_code in {400, 422}, resposta.text
    assert (await _perfil(cliente))["retencaoDesejada"] == 0.9


@pytest.mark.parametrize("corpo", ["{}", "[]", "null", "", "{", '"x"', "0"])
async def test_corpo_vazio_ou_malformado_e_recusado(cliente: httpx.AsyncClient, corpo: str) -> None:
    await cadastrar(cliente, dados_conta())
    resposta = await _enviar(cliente, corpo)
    assert resposta.status_code in {400, 422}
    assert resposta.json()["codigo"] in {"requisicao_malformada", "dados_invalidos"}


@pytest.mark.parametrize(
    "extra",
    [
        {"papel": "admin"},
        {"email": "outro@exemplo.com"},
        {"id": 1},
        {"publicId": "x"},
        {"senha": "outra senha longa 123"},
        {"criadoEm": "2020-01-01T00:00:00Z"},
        {"xpTotal": 9999},
    ],
)
async def test_campos_extras_sao_recusados_e_nada_muda(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes, extra: dict[str, object]
) -> None:
    await cadastrar(cliente, dados_conta())
    antes = await _perfil(cliente)
    resposta = await cliente.patch("/api/v1/perfil", json={"metaDiaria": 31, **extra})
    assert resposta.status_code == 422
    assert next(iter(extra)) in {c["campo"] for c in resposta.json()["campos"]}
    assert await _perfil(cliente) == antes, "nem o campo válido do mesmo corpo é aplicado"
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        assert (await sessao.execute(select(Usuario.papel))).scalar_one() == "estudante"


@pytest.mark.parametrize("valor", ["5", 5.5, True, None, [5], -0, 10**30, "٥"])
async def test_inteiros_com_tipos_estranhos_sao_recusados(
    cliente: httpx.AsyncClient, valor: object
) -> None:
    await cadastrar(cliente, dados_conta())
    antes = await _perfil(cliente)
    resposta = await cliente.patch("/api/v1/perfil", json={"tamanhoLicao": valor})
    # `-0` vale 0, abaixo do mínimo de 5; os demais não são inteiros.
    assert resposta.status_code == 422, resposta.text
    assert await _perfil(cliente) == antes


async def test_nome_com_unicode_malicioso_e_recusado(cliente: httpx.AsyncClient) -> None:
    await cadastrar(cliente, dados_conta())
    antes = await _perfil(cliente)
    for nome in ("Ana‮evil", "Ana\x00", "x" * 101, "   "):
        resposta = await cliente.patch("/api/v1/perfil", json={"nome": nome})
        assert resposta.status_code == 422
    assert await _perfil(cliente) == antes


async def test_conta_nao_altera_o_perfil_de_outra(
    aplicacao: FastAPI, cliente: httpx.AsyncClient
) -> None:
    await cadastrar(cliente, dados_conta())
    antes = await _perfil(cliente)
    async with abrir_cliente(aplicacao, ip="198.51.100.63") as outro:
        await cadastrar(outro, dados_conta())
        assert (
            await outro.patch(
                "/api/v1/perfil",
                json={"metaDiaria": 3, "retencaoDesejada": 0.71, "nome": "Invasora"},
            )
        ).status_code == 200
        assert (await _perfil(outro))["metaDiaria"] == 3
    assert await _perfil(cliente) == antes


async def test_alteracao_exige_csrf(cliente: httpx.AsyncClient) -> None:
    await cadastrar(cliente, dados_conta())
    await obter_csrf(cliente)
    resposta = await cliente.patch(
        "/api/v1/perfil", json={"metaDiaria": 3}, headers={"X-CSRF-Token": ""}
    )
    assert resposta.status_code == 403
