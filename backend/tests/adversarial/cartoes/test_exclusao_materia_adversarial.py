"""A exclusão da matéria trava os cartões antes de contar (emenda de 15/10/2026 da DTEC 027).

Teste que falha sem a trava: durante a janela da contagem, outra transação não consegue pegar
as linhas dos cartões da matéria.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import psycopg
import pytest
from fastapi import FastAPI
from psycopg import errors

from app.nucleo.configuracao import Configuracao
from app.nucleo.participantes_acervo import registro_acervo
from tests.apoio_acervo import criar_conta, criar_materia, id_interno_da_materia
from tests.apoio_cartoes import criar_cartao
from tests.participantes_falsos import ParticipanteFalso

pytestmark = pytest.mark.adversarial


@pytest.fixture
def contagem_lenta() -> Any:
    """Participante falso, depois dos cartões (300), que alarga a janela da contagem."""
    participante = ParticipanteFalso(nome="lento", atraso_s=1.0)
    registro_acervo.registrar(350, "lento", participante)
    try:
        yield participante
    finally:
        registro_acervo.remover("lento")


async def test_cartoes_da_materia_ficam_travados_durante_a_contagem_da_exclusao(
    acervo: FastAPI,
    cliente_real: httpx.AsyncClient,
    configuracao: Configuracao,
    contagem_lenta: ParticipanteFalso,
) -> None:
    await criar_conta(cliente_real)
    materia = await criar_materia(cliente_real, "Biologia")
    for numero in range(3):
        await criar_cartao(cliente_real, materia["id"], frente=f"Pergunta {numero}")
    interno = await id_interno_da_materia(acervo.state.fabrica_sessoes, materia["id"])
    exibido = (await cliente_real.get(f"/api/v1/materias/{materia['id']}/impacto-exclusao")).json()
    assert exibido["contagens"]["cartoesAtivos"] == 3

    exclusao = asyncio.create_task(
        cliente_real.post(
            f"/api/v1/materias/{materia['id']}/exclusao",
            json={"nomeConfirmacao": "Biologia", "impactoConfirmado": exibido["contagens"]},
        )
    )
    travados = False
    prazo = time.monotonic() + 5
    async with await psycopg.AsyncConnection.connect(configuracao.conninfo()) as outra:
        while time.monotonic() < prazo and not exclusao.done():
            try:
                await outra.execute(
                    "SELECT id FROM cartoes WHERE materia_id = %s ORDER BY id FOR UPDATE NOWAIT",
                    (interno,),
                )
            except errors.LockNotAvailable:
                travados = True
                break
            finally:
                await outra.rollback()
            await asyncio.sleep(0.02)
    resposta = await exclusao

    assert travados, "a exclusão não travou os cartões da matéria antes de contar"
    assert resposta.status_code == 204, resposta.text


async def test_criar_cartao_durante_a_exclusao_da_materia_responde_404_e_nao_500(
    acervo: FastAPI,
    cliente_real: httpx.AsyncClient,
    contagem_lenta: ParticipanteFalso,
) -> None:
    """A criação espera a exclusão (a FK pede a linha da matéria) e então não encontra a matéria."""
    await criar_conta(cliente_real)
    materia = await criar_materia(cliente_real, "Biologia")
    exibido = (await cliente_real.get(f"/api/v1/materias/{materia['id']}/impacto-exclusao")).json()

    exclusao = asyncio.create_task(
        cliente_real.post(
            f"/api/v1/materias/{materia['id']}/exclusao",
            json={"nomeConfirmacao": "Biologia", "impactoConfirmado": exibido["contagens"]},
        )
    )
    await asyncio.sleep(0.3)  # a exclusão já travou a matéria e está na contagem lenta
    criacao = await criar_cartao(cliente_real, materia["id"], frente="Tarde demais")
    resposta_exclusao = await exclusao

    assert resposta_exclusao.status_code == 204
    assert criacao.status_code == 404, criacao.text
    assert criacao.json()["codigo"] == "recurso_nao_encontrado"
