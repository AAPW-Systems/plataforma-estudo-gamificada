"""T022: saúde, documentação e composição da aplicação real."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast
from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI

from app.nucleo.configuracao import Configuracao
from app.principal import criar_aplicacao

pytestmark = pytest.mark.integration


async def test_saude(cliente: httpx.AsyncClient) -> None:
    """T022 e T011: processo, banco, esquema da fila e armazenamento acessíveis."""
    assert (await cliente.get("/health")).json() == {"estado": "ok"}
    resposta = await cliente.get("/health/ready")
    assert resposta.status_code == 200
    assert resposta.json() == {
        "estado": "ok",
        "verificacoes": {"banco": "ok", "fila": "ok", "armazenamento": "ok"},
    }


async def test_banco_indisponivel(cliente: httpx.AsyncClient) -> None:
    """T022: falha real de conexão retorna 503 sem detalhes internos."""

    @asynccontextmanager
    async def indisponivel(fabrica: object) -> AsyncIterator[None]:
        if fabrica is not None:
            raise OSError("detalhe interno")
        yield  # pragma: no cover

    with patch("app.saude.servicos.abrir_conexao", indisponivel):
        resposta = await cliente.get("/health/ready")
    assert resposta.status_code == 503
    assert resposta.json()["estado"] == "indisponivel"
    assert "detalhe interno" not in resposta.text
    assert (await cliente.get("/health")).status_code == 200


async def test_ordem_middlewares(aplicacao: FastAPI, cliente: httpx.AsyncClient) -> None:
    """T022: respostas curtas 403, 413 e 500 mantêm correlação e segurança."""
    assert [cast(type[object], m.cls).__name__ for m in aplicacao.user_middleware] == [
        "MiddlewareCorrelacao",
        "MiddlewareCabecalhosSeguranca",
        "MiddlewareLimiteCorpo",
        "MiddlewareProtecaoCsrf",
        "MiddlewareErrosInesperados",
    ]

    @aplicacao.get("/api/teste-falha")
    async def falhar() -> None:
        raise RuntimeError("detalhe secreto")

    respostas = [
        await cliente.get("/api/teste-falha"),
        await cliente.post("/api/teste", content=b"x" * 65537),
        await cliente.post("/api/teste", json={}),
    ]
    assert [r.status_code for r in respostas] == [500, 413, 403]
    for resposta in respostas:
        assert resposta.headers["x-request-id"] == resposta.json()["idRequisicao"]
        assert resposta.headers["x-frame-options"] == "DENY"
        assert resposta.headers["cache-control"] == "no-store"
        assert "detalhe secreto" not in resposta.text


@pytest.mark.parametrize(
    "ambiente,esperado", [("desenvolvimento", 200), ("teste", 404), ("producao", 404)]
)
async def test_swagger_so_em_desenvolvimento(
    configuracao: Configuracao, ambiente: str, esperado: int
) -> None:
    app = criar_aplicacao(configuracao.model_copy(update={"app_ambiente": ambiente}))
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://teste"
        ) as cliente,
    ):
        assert (await cliente.get("/api/docs")).status_code == esperado
        assert (await cliente.get("/api/openapi.json")).status_code == esperado


# --- Armazenamento (T011): /health/ready grava e apaga um objeto de sonda ---------------------


async def _aplicacao_com_disco(configuracao: Configuracao, raiz: Path) -> FastAPI:
    return criar_aplicacao(
        configuracao.model_copy(
            update={"armazenamento_adaptador": "local", "armazenamento_diretorio": raiz}
        )
    )


async def _prontidao(app: FastAPI) -> httpx.Response:
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://teste"
        ) as cliente_http,
    ):
        return await cliente_http.get("/health/ready")


async def test_armazenamento_gravavel_deixa_a_prontidao_em_200_sem_resíduo(
    configuracao: Configuracao, tmp_path: Path
) -> None:
    resposta = await _prontidao(await _aplicacao_com_disco(configuracao, tmp_path / "arquivos"))
    assert resposta.status_code == 200
    assert resposta.json()["verificacoes"]["armazenamento"] == "ok"
    # A sonda é apagada: nenhum objeto sobra no volume.
    assert [p for p in (tmp_path / "arquivos").rglob("*") if p.is_file()] == []


async def test_raiz_que_nao_e_diretorio_gera_503_sem_detalhes(
    configuracao: Configuracao, tmp_path: Path
) -> None:
    raiz = tmp_path / "arquivos"
    raiz.write_text("sou um arquivo, não um diretório")
    resposta = await _prontidao(await _aplicacao_com_disco(configuracao, raiz))
    assert resposta.status_code == 503
    assert resposta.json()["verificacoes"] == {
        "banco": "ok",
        "fila": "ok",
        "armazenamento": "falhou",
    }
    assert str(tmp_path) not in resposta.text


@pytest.mark.skipif(os.geteuid() == 0, reason="o superusuário ignora as permissões de escrita")
async def test_diretorio_sem_permissao_de_escrita_gera_503(
    configuracao: Configuracao, tmp_path: Path
) -> None:
    raiz = tmp_path / "arquivos"
    raiz.mkdir()
    raiz.chmod(0o500)
    try:
        resposta = await _prontidao(await _aplicacao_com_disco(configuracao, raiz))
    finally:
        raiz.chmod(0o700)
    assert resposta.status_code == 503
    assert resposta.json()["verificacoes"]["armazenamento"] == "falhou"


async def test_falha_ao_gravar_a_sonda_gera_503(
    configuracao: Configuracao, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.nucleo.armazenamento import ArmazenamentoDisco

    async def falhar(self: ArmazenamentoDisco, chave: str, origem: Path) -> None:
        raise OSError("disco cheio")

    monkeypatch.setattr(ArmazenamentoDisco, "gravar", falhar)
    resposta = await _prontidao(await _aplicacao_com_disco(configuracao, tmp_path / "arquivos"))
    assert resposta.status_code == 503
    assert "disco cheio" not in resposta.text
