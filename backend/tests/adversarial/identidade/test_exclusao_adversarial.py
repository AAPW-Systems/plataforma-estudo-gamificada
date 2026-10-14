"""Troca de senha e exclusão sob concorrência e abuso (T055; RF-014, RF-015, RQ-003)."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select, text

from app.identidade.modelos import Sessao, Usuario
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from tests.apoio_http import abrir_cliente, cadastrar, clientes_prontos, entrar
from tests.fabricas import dados_conta

pytestmark = pytest.mark.adversarial


async def _contar(fabrica: FabricaSessoes, entidade: type) -> int:
    async with unidade_de_trabalho(fabrica) as sessao:
        return (await sessao.execute(select(func.count()).select_from(entidade))).scalar_one()


async def test_exclusao_pedida_duas_vezes_em_paralelo_tem_um_unico_efeito(
    aplicacao_real: FastAPI, fabrica_real: FabricaSessoes
) -> None:
    conta = dados_conta()
    async with abrir_cliente(aplicacao_real, ip="198.51.100.80") as cliente:
        assert (await cadastrar(cliente, conta)).status_code == 201
        respostas = await asyncio.gather(
            *(
                cliente.post("/api/v1/perfil/exclusao", json={"senhaAtual": conta.senha})
                for _ in range(6)
            )
        )
    status = sorted(r.status_code for r in respostas)
    assert status == [204, 401, 401, 401, 401, 401], status
    assert await _contar(fabrica_real, Usuario) == 0
    async with unidade_de_trabalho(fabrica_real) as sessao:
        jobs = (
            await sessao.execute(
                text(
                    "select count(*) from procrastinate_jobs "
                    "where task_name = 'identidade.apagar_objetos_usuario'"
                )
            )
        ).scalar_one()
    assert jobs == 1, "uma única tarefa de remoção de objetos"


async def test_exclusao_pedida_de_duas_sessoes_da_mesma_conta_em_paralelo(
    aplicacao_real: FastAPI, fabrica_real: FabricaSessoes
) -> None:
    conta = dados_conta()
    async with abrir_cliente(aplicacao_real, ip="198.51.100.81") as primeira:
        assert (await cadastrar(primeira, conta)).status_code == 201
        async with clientes_prontos(aplicacao_real, ["198.51.100.82", "198.51.100.83"]) as outras:
            for cliente in outras:
                assert (await entrar(cliente, conta)).status_code == 200
            respostas = await asyncio.gather(
                primeira.post("/api/v1/perfil/exclusao", json={"senhaAtual": conta.senha}),
                *(
                    c.post("/api/v1/perfil/exclusao", json={"senhaAtual": conta.senha})
                    for c in outras
                ),
            )
    assert sorted(r.status_code for r in respostas) == [204, 401, 401]
    assert await _contar(fabrica_real, Usuario) == 0


async def test_trocas_de_senha_concorrentes_deixam_uma_unica_senha_valida(
    aplicacao_real: FastAPI, fabrica_real: FabricaSessoes
) -> None:
    conta = dados_conta()
    async with abrir_cliente(aplicacao_real, ip="198.51.100.84") as cliente:
        assert (await cadastrar(cliente, conta)).status_code == 201
        novas = [f"senha nova numero {i} bem longa" for i in range(4)]
        respostas = await asyncio.gather(
            *(
                cliente.post(
                    "/api/v1/perfil/senha", json={"senhaAtual": conta.senha, "novaSenha": nova}
                )
                for nova in novas
            )
        )
    status = [r.status_code for r in respostas]
    assert status.count(204) == 1, status
    assert set(status) <= {204, 422}, status
    vencedora = novas[status.index(204)]
    async with abrir_cliente(aplicacao_real, ip="198.51.100.85") as novo:
        # A vencedora entra (e zera as falhas); a antiga e as perdedoras não entram.
        assert (await entrar(novo, {"email": conta.email, "senha": vencedora})).status_code == 200
        assert (await entrar(novo, {"email": conta.email, "senha": conta.senha})).status_code == 401
        for nova in novas:
            if nova != vencedora:
                assert (
                    await entrar(novo, {"email": conta.email, "senha": nova})
                ).status_code == 401


async def test_troca_de_senha_revoga_as_outras_sessoes_mesmo_com_rajada(
    aplicacao_real: FastAPI, fabrica_real: FabricaSessoes
) -> None:
    conta = dados_conta()
    async with abrir_cliente(aplicacao_real, ip="198.51.100.86") as cliente:
        assert (await cadastrar(cliente, conta)).status_code == 201
        async with clientes_prontos(
            aplicacao_real, [f"198.51.100.{90 + i}" for i in range(5)]
        ) as outros:
            for outro in outros:
                assert (await entrar(outro, conta)).status_code == 200
            assert (
                await cliente.post(
                    "/api/v1/perfil/senha",
                    json={"senhaAtual": conta.senha, "novaSenha": "nova frase longa bem unica"},
                )
            ).status_code == 204
            respostas = await asyncio.gather(*(o.get("/api/v1/perfil") for o in outros))
    assert {r.status_code for r in respostas} == {401}
    async with unidade_de_trabalho(fabrica_real) as sessao:
        ativas = (
            await sessao.execute(
                select(func.count()).select_from(Sessao).where(Sessao.revogada_em.is_(None))
            )
        ).scalar_one()
    assert ativas == 1


async def test_exclusao_com_a_conta_bloqueada_responde_429_e_nao_apaga(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    conta = dados_conta()
    await cadastrar(cliente, conta)
    for _ in range(5):
        resposta = await cliente.post(
            "/api/v1/perfil/exclusao", json={"senhaAtual": "errada-errada-1"}
        )
        assert resposta.status_code == 422
    bloqueada = await cliente.post("/api/v1/perfil/exclusao", json={"senhaAtual": conta.senha})
    assert bloqueada.status_code == 429
    assert bloqueada.json()["codigo"] == "muitas_tentativas"
    assert await _contar(fabrica_sessoes, Usuario) == 1
    assert (await cliente.get("/api/v1/perfil")).status_code == 200


async def test_rajada_de_exclusoes_erradas_nao_ultrapassa_o_limite_da_conta(
    aplicacao_real: FastAPI, fabrica_real: FabricaSessoes
) -> None:
    conta = dados_conta()
    async with abrir_cliente(aplicacao_real, ip="198.51.100.87") as principal:
        assert (await cadastrar(principal, conta)).status_code == 201
        async with clientes_prontos(
            aplicacao_real, [f"198.51.100.{100 + i}" for i in range(15)]
        ) as outros:
            for outro in outros:
                assert (await entrar(outro, conta)).status_code == 200
            # `entrar` zera as falhas a cada sucesso; a rajada vem depois de todas as entradas.
            respostas = await asyncio.gather(
                *(
                    o.post("/api/v1/perfil/exclusao", json={"senhaAtual": "errada-errada-1"})
                    for o in outros
                )
            )
    status = [r.status_code for r in respostas]
    assert status.count(422) == 5 and status.count(429) == 10, status
    assert await _contar(fabrica_real, Usuario) == 1


@pytest.mark.parametrize(
    "corpo",
    [
        {},
        {"senhaAtual": ""},
        {"senhaAtual": None},
        {"senhaAtual": 12345678},
        {"senhaAtual": ["a"]},
        {"senhaAtual": "x" * 100_000},
        {"senhaAtual": "abc\ud800def"},
        {"senhaAtual": "ok", "extra": 1},
        {"senhaAtual": "ok", "confirmar": True},
    ],
)
async def test_corpos_hostis_na_exclusao_nunca_apagam_nada(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes, corpo: dict[str, object]
) -> None:
    await cadastrar(cliente, dados_conta())
    resposta = await cliente.post(
        "/api/v1/perfil/exclusao",
        content=json.dumps(corpo),
        headers={"Content-Type": "application/json"},
    )
    assert resposta.status_code in {400, 413, 422}
    assert await _contar(fabrica_sessoes, Usuario) == 1


@pytest.mark.parametrize(
    "corpo",
    [
        {},
        {"senhaAtual": "x"},
        {"novaSenha": "uma frase longa e incomum"},
        {"senhaAtual": 1, "novaSenha": 2},
        {"senhaAtual": "x", "novaSenha": "uma frase longa e incomum", "papel": "admin"},
        {"senhaAtual": "x", "novaSenha": "a\ud800bcdefgh"},
        {"senhaAtual": "x", "novaSenha": "n" * 129},
    ],
)
async def test_corpos_hostis_na_troca_de_senha_sao_recusados(
    cliente: httpx.AsyncClient, corpo: dict[str, object]
) -> None:
    conta = dados_conta()
    await cadastrar(cliente, conta)
    resposta = await cliente.post(
        "/api/v1/perfil/senha",
        content=json.dumps(corpo),
        headers={"Content-Type": "application/json"},
    )
    assert resposta.status_code in {400, 422}
    assert (await cliente.get("/api/v1/perfil")).status_code == 200


async def test_troca_de_senha_nao_permite_que_outra_conta_mude_a_senha_alheia(
    aplicacao: FastAPI, cliente: httpx.AsyncClient
) -> None:
    ana, bia = dados_conta(), dados_conta()
    await cadastrar(cliente, ana)
    async with abrir_cliente(aplicacao, ip="198.51.100.88") as cliente_bia:
        await cadastrar(cliente_bia, bia)
        # Bia usa a senha atual DELA; a senha da Ana não muda.
        assert (
            await cliente_bia.post(
                "/api/v1/perfil/senha",
                json={"senhaAtual": bia.senha, "novaSenha": "nova frase da Bia 123"},
            )
        ).status_code == 204
        # Bia tentando a senha da Ana como "atual" erra a dela.
        r = await cliente_bia.post(
            "/api/v1/perfil/senha",
            json={"senhaAtual": ana.senha, "novaSenha": "outra frase da Bia 456"},
        )
        assert r.status_code == 422
    assert (await cliente.get("/api/v1/perfil")).json()["email"] == ana.email
    async with abrir_cliente(aplicacao, ip="198.51.100.89") as novo:
        assert (await entrar(novo, ana)).status_code == 200
