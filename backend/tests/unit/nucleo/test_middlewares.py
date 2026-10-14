"""Limite de corpo por rota (DTEC 028, T006): o envio de fonte aceita mais que as demais."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI, Request

from app.nucleo.erros import (
    ConteudoMuitoGrande,
    MiddlewareErrosInesperados,
    registrar_handlers,
)
from app.nucleo.middlewares import LIMITE_CORPO_PADRAO, LimiteRota, MiddlewareLimiteCorpo

pytestmark = pytest.mark.unit

LIMITE_ENVIO = 5_000


def _criar_app() -> FastAPI:
    app = FastAPI()
    registrar_handlers(app)
    app.add_middleware(MiddlewareErrosInesperados)
    app.add_middleware(
        MiddlewareLimiteCorpo,
        limites_por_rota=[
            LimiteRota(
                "POST",
                re.compile(r"^/api/v1/materias/[^/]+/fontes$"),
                LIMITE_ENVIO,
                lambda: ConteudoMuitoGrande("O arquivo é grande demais para este teste."),
            )
        ],
    )

    @app.post("/api/v1/materias/{materia}/fontes")
    async def envio(materia: str, request: Request) -> dict[str, int]:
        return {"bytes": len(await request.body())}

    @app.post("/api/v1/outra")
    async def outra(request: Request) -> dict[str, int]:
        return {"bytes": len(await request.body())}

    @app.get("/api/v1/materias/{materia}/fontes")
    async def listar(materia: str) -> dict[str, str]:
        return {"materia": materia}

    return app


@pytest.fixture
async def cliente() -> AsyncIterator[httpx.AsyncClient]:
    transporte = httpx.ASGITransport(app=_criar_app())
    async with httpx.AsyncClient(transport=transporte, base_url="http://teste") as cliente:
        yield cliente


async def _em_pedacos(total: int, pedaco: int = 1024) -> AsyncIterator[bytes]:
    restante = total
    while restante > 0:
        tamanho = min(pedaco, restante)
        restante -= tamanho
        yield b"x" * tamanho


async def test_rota_de_envio_aceita_ate_o_seu_limite(cliente: httpx.AsyncClient) -> None:
    resposta = await cliente.post("/api/v1/materias/m/fontes", content=b"x" * LIMITE_ENVIO)
    assert resposta.status_code == 200
    assert resposta.json() == {"bytes": LIMITE_ENVIO}


async def test_rota_de_envio_acima_do_limite_pelo_content_length_vira_413_arquivo_muito_grande(
    cliente: httpx.AsyncClient,
) -> None:
    resposta = await cliente.post("/api/v1/materias/m/fontes", content=b"x" * (LIMITE_ENVIO + 1))
    assert resposta.status_code == 413
    assert resposta.json()["codigo"] == "arquivo_muito_grande"
    assert resposta.json()["mensagem"] == "O arquivo é grande demais para este teste."
    assert "idRequisicao" in resposta.json()


async def test_rota_de_envio_acima_do_limite_sem_content_length_vira_413_na_leitura(
    cliente: httpx.AsyncClient,
) -> None:
    requisicao = cliente.build_request(
        "POST", "/api/v1/materias/m/fontes", content=_em_pedacos(LIMITE_ENVIO * 4)
    )
    assert "content-length" not in requisicao.headers
    resposta = await cliente.send(requisicao)
    assert resposta.status_code == 413
    assert resposta.json()["codigo"] == "arquivo_muito_grande"


async def test_rota_de_envio_sem_content_length_dentro_do_limite_passa(
    cliente: httpx.AsyncClient,
) -> None:
    requisicao = cliente.build_request(
        "POST", "/api/v1/materias/m/fontes", content=_em_pedacos(LIMITE_ENVIO)
    )
    resposta = await cliente.send(requisicao)
    assert resposta.status_code == 200
    assert resposta.json() == {"bytes": LIMITE_ENVIO}


async def test_as_demais_rotas_mantem_64_kib(cliente: httpx.AsyncClient) -> None:
    dentro = await cliente.post("/api/v1/outra", content=b"x" * LIMITE_CORPO_PADRAO)
    assert dentro.status_code == 200
    fora = await cliente.post("/api/v1/outra", content=b"x" * (LIMITE_CORPO_PADRAO + 1))
    assert fora.status_code == 413
    assert fora.json()["codigo"] == "requisicao_malformada"


async def test_o_limite_maior_so_vale_para_o_metodo_e_o_caminho_configurados(
    cliente: httpx.AsyncClient,
) -> None:
    # Caminho parecido (barra a mais) e outro método não ganham o limite da rota de envio.
    parecido = await cliente.post(
        "/api/v1/materias/m/fontes/", content=b"x" * (LIMITE_CORPO_PADRAO + 1)
    )
    assert parecido.status_code in {307, 404, 413}
    assert parecido.status_code != 200
    leitura = await cliente.get("/api/v1/materias/m/fontes")
    assert leitura.status_code == 200


async def test_content_length_invalido_continua_400(cliente: httpx.AsyncClient) -> None:
    resposta = await cliente.post(
        "/api/v1/materias/m/fontes", content=b"x", headers={"Content-Length": "abc"}
    )
    assert resposta.status_code == 400
