"""Conversão central de erros no corpo `Erro` (plano da 001, "Controle de exceções")."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI
from pydantic import Field
from structlog.testing import capture_logs

from app.nucleo.dtos import EntradaDTO
from app.nucleo.erros import (
    AcessoNegado,
    CodigoErro,
    Conflito,
    EntradaInvalida,
    ErroAplicacao,
    ErroCampo,
    LimiteExcedido,
    MiddlewareErrosInesperados,
    NaoAutenticado,
    RecursoNaoEncontrado,
    RequisicaoMalformada,
    registrar_handlers,
)

pytestmark = pytest.mark.unit


class Corpo(EntradaDTO):
    meta_diaria: int = Field(ge=1, le=200)
    nome: str = Field(min_length=1, max_length=5)


def _criar_app() -> FastAPI:
    app = FastAPI()
    registrar_handlers(app)
    app.add_middleware(MiddlewareErrosInesperados)

    @app.post("/validar")
    async def validar(corpo: Corpo) -> dict[str, int]:
        return {"ok": corpo.meta_diaria}

    @app.get("/erro/{tipo}")
    async def erro(tipo: str) -> None:
        excecoes: dict[str, ErroAplicacao] = {
            "400": RequisicaoMalformada(),
            "401": NaoAutenticado(),
            "403": AcessoNegado(),
            "404": RecursoNaoEncontrado(),
            "409": Conflito("Este e-mail já está em uso.", codigo=CodigoErro.EMAIL_EM_USO),
            "422": EntradaInvalida(campos=[ErroCampo("senha", "Senha comum.")]),
            "429": LimiteExcedido(899.2),
        }
        raise excecoes[tipo]

    @app.get("/inesperado")
    async def inesperado() -> None:
        raise RuntimeError("detalhe interno: senha=segredo123 em /var/lib")

    return app


@pytest.fixture
async def cliente() -> AsyncIterator[httpx.AsyncClient]:
    transporte = httpx.ASGITransport(app=_criar_app())
    async with httpx.AsyncClient(transport=transporte, base_url="http://teste") as cliente:
        yield cliente


def _valida_corpo_erro(corpo: dict[str, object]) -> None:
    assert set(corpo) <= {"codigo", "mensagem", "campos", "idRequisicao"}
    assert isinstance(corpo["mensagem"], str) and corpo["mensagem"]
    uuid.UUID(str(corpo["idRequisicao"]))


@pytest.mark.parametrize(
    ("tipo", "codigo"),
    [
        ("400", "requisicao_malformada"),
        ("401", "nao_autenticado"),
        ("403", "csrf_invalido"),
        ("404", "recurso_nao_encontrado"),
        ("409", "email_em_uso"),
        ("422", "dados_invalidos"),
        ("429", "muitas_tentativas"),
    ],
)
async def test_cada_subclasse_vira_erro_com_status_certo(
    cliente: httpx.AsyncClient, tipo: str, codigo: str
) -> None:
    resposta = await cliente.get(f"/erro/{tipo}")
    assert resposta.status_code == int(tipo)
    corpo = resposta.json()
    _valida_corpo_erro(corpo)
    assert corpo["codigo"] == codigo


async def test_erro_com_campos_lista_os_campos(cliente: httpx.AsyncClient) -> None:
    corpo = (await cliente.get("/erro/422")).json()
    assert corpo["campos"] == [{"campo": "senha", "mensagem": "Senha comum."}]


async def test_limite_excedido_envia_retry_after_arredondado_para_cima(
    cliente: httpx.AsyncClient,
) -> None:
    resposta = await cliente.get("/erro/429")
    assert resposta.headers["retry-after"] == "900"


async def test_validacao_vira_422_com_campos_em_camel_case_e_mensagens_em_portugues(
    cliente: httpx.AsyncClient,
) -> None:
    resposta = await cliente.post("/validar", json={"metaDiaria": 0, "nome": "123456"})
    assert resposta.status_code == 422
    corpo = resposta.json()
    _valida_corpo_erro(corpo)
    assert corpo["codigo"] == "dados_invalidos"
    assert corpo["campos"] == [
        {"campo": "metaDiaria", "mensagem": "Use um valor a partir de 1."},
        {"campo": "nome", "mensagem": "Use no máximo 5 caracteres."},
    ]


async def test_campo_obrigatorio_e_campo_extra(cliente: httpx.AsyncClient) -> None:
    resposta = await cliente.post("/validar", json={"metaDiaria": 3, "papel": "admin"})
    campos = {c["campo"]: c["mensagem"] for c in resposta.json()["campos"]}
    assert campos == {"nome": "Campo obrigatório.", "papel": "Campo não permitido."}


async def test_nome_em_snake_case_nao_e_aceito(cliente: httpx.AsyncClient) -> None:
    resposta = await cliente.post("/validar", json={"meta_diaria": 3, "nome": "a"})
    assert resposta.status_code == 422
    campos = {c["campo"] for c in resposta.json()["campos"]}
    assert campos == {"metaDiaria", "meta_diaria"}


@pytest.mark.parametrize("corpo", [b"{nao e json", b"", b"[1, 2]", b'"texto"'])
async def test_corpo_ilegivel_vira_400(cliente: httpx.AsyncClient, corpo: bytes) -> None:
    resposta = await cliente.post(
        "/validar", content=corpo, headers={"content-type": "application/json"}
    )
    assert resposta.status_code == 400
    assert resposta.json()["codigo"] == "requisicao_malformada"


async def test_rota_inexistente_vira_404_no_corpo_padrao(cliente: httpx.AsyncClient) -> None:
    resposta = await cliente.get("/nao-existe")
    assert resposta.status_code == 404
    assert resposta.json()["codigo"] == "recurso_nao_encontrado"


async def test_excecao_inesperada_vira_500_sem_detalhes_e_com_pilha_no_log(
    cliente: httpx.AsyncClient,
) -> None:
    with capture_logs() as registros:
        resposta = await cliente.get("/inesperado")
    assert resposta.status_code == 500
    corpo = resposta.json()
    _valida_corpo_erro(corpo)
    assert corpo["codigo"] == "erro_interno"
    assert "segredo123" not in resposta.text and "RuntimeError" not in resposta.text
    [registro] = [r for r in registros if r["event"] == "erro_inesperado"]
    assert registro["log_level"] == "error"
    assert registro["exc_info"] is True
