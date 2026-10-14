"""Isolamento entre estudantes, verificado rota a rota (T041; DTEC 019, RF-007, CS-002).

A integração contínua falha quando uma rota nova:
- recebe um identificador no caminho e não entra em `CASOS_DE_ISOLAMENTO` (com o teste de duas
  contas que a cobre); ou
- é protegida e não responde `401` sem sessão (toda rota é protegida, salvo as de
  `ROTAS_PUBLICAS`, que são listadas de propósito e uma a uma).

As specs 002 a 007 acrescentam as suas rotas a essas tabelas. Nenhuma rota da 001 recebe
identificador de recurso (todas operam sobre o usuário da sessão); por isso a tabela de
casos começa vazia, e o mecanismo é provado com uma rota que só existe neste teste.

Cobertura incremental (divergência registrada no `tasks.md`): `PATCH /perfil` (T049) e
`POST /perfil/senha` e `/perfil/exclusao` (T056) só chegam depois do S1. Elas estão em
`ROTAS_PENDENTES`, não contam como cobertas, e o teste `test_pendentes_ainda_nao_existem`
obriga a movê-las para os casos de duas contas quando passarem a existir.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import String, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.identidade.dependencias import UsuarioAtual
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.dono import buscar_do_dono
from app.principal import criar_aplicacao
from tests.apoio_http import (
    abrir_cliente,
    cadastrar,
    definir_cookie,
    obter_csrf,
    sem_id_requisicao,
)
from tests.apoio_rotas import PARAMETRO, rotas_da_aplicacao, rotas_do_openapi
from tests.fabricas import dados_conta

pytestmark = pytest.mark.security

METODOS_LEITURA = frozenset({"GET", "HEAD", "OPTIONS"})

# Rotas que não exigem sessão, uma a uma e por motivo. Qualquer outra rota é protegida.
ROTAS_PUBLICAS: dict[tuple[str, str], str] = {
    ("GET", "/health"): "verificação de saúde do processo",
    ("GET", "/health/ready"): "verificação de prontidão (banco e fila)",
    ("GET", "/api/v1/auth/csrf"): "emite o token anti-CSRF antes de existir sessão",
    ("POST", "/api/v1/auth/cadastro"): "cria a conta",
    ("POST", "/api/v1/auth/entrada"): "inicia a sessão",
    ("POST", "/api/v1/auth/saida"): "idempotente: sem sessão válida, só apaga os cookies",
}

# Rotas com identificador de recurso no caminho -> teste de duas contas que as cobre.
CASOS_DE_ISOLAMENTO: dict[tuple[str, str], str] = {}

# Rotas do contrato que ainda não existem -> tarefa que as entrega.
ROTAS_PENDENTES: dict[tuple[str, str], str] = {
    ("POST", "/api/v1/perfil/senha"): "T056",
    ("POST", "/api/v1/perfil/exclusao"): "T056",
}


def rotas_com_identificador_sem_caso(
    app: FastAPI, casos: dict[tuple[str, str], str]
) -> list[tuple[str, str]]:
    return [
        (metodo, caminho)
        for metodo, caminho in rotas_da_aplicacao(app)
        if PARAMETRO.search(caminho) and (metodo, caminho) not in casos
    ]


def rotas_protegidas(app: FastAPI) -> list[tuple[str, str]]:
    return [rota for rota in rotas_da_aplicacao(app) if rota not in ROTAS_PUBLICAS]


def _url(caminho: str) -> str:
    return PARAMETRO.sub(lambda _: str(uuid.uuid4()), caminho)


# --- A tabela de casos (DTEC 019) ---------------------------------------------------------


def test_toda_rota_com_identificador_no_caminho_tem_caso_de_isolamento(
    aplicacao: FastAPI,
) -> None:
    faltando = rotas_com_identificador_sem_caso(aplicacao, CASOS_DE_ISOLAMENTO)
    assert not faltando, (
        f"rotas com identificador sem caso em CASOS_DE_ISOLAMENTO (DTEC 019): {faltando}. "
        "Acrescente o teste de duas contas e registre a rota na tabela."
    )


def test_o_detector_acusa_rota_nova_com_identificador_sem_caso(aplicacao: FastAPI) -> None:
    """Prova que a verificação acima falha de verdade quando alguém esquece o caso."""

    @aplicacao.get("/api/v1/materias/{materia_id}")
    async def ler_materia(materia_id: uuid.UUID) -> dict[str, str]:
        return {"id": str(materia_id)}

    assert rotas_com_identificador_sem_caso(aplicacao, CASOS_DE_ISOLAMENTO) == [
        ("GET", "/api/v1/materias/{materia_id}")
    ]
    assert not rotas_com_identificador_sem_caso(
        aplicacao, {("GET", "/api/v1/materias/{materia_id}"): "teste de duas contas"}
    )


def test_a_enumeracao_de_rotas_cobre_tudo_o_que_o_openapi_publica(aplicacao: FastAPI) -> None:
    """Sanidade: a lista de rotas nunca fica vazia nem perde rota se o FastAPI mudar por dentro."""
    enumeradas = set(rotas_da_aplicacao(aplicacao))
    assert enumeradas, "nenhuma rota enumerada"
    assert rotas_do_openapi(aplicacao) <= enumeradas
    assert ("GET", "/api/v1/perfil") in enumeradas


def test_a_tabela_de_casos_nao_guarda_rota_que_deixou_de_existir(aplicacao: FastAPI) -> None:
    existentes = set(rotas_da_aplicacao(aplicacao))
    assert set(CASOS_DE_ISOLAMENTO) <= existentes
    assert set(ROTAS_PUBLICAS) <= existentes, "ROTAS_PUBLICAS cita rota inexistente"


def test_pendentes_ainda_nao_existem(aplicacao: FastAPI) -> None:
    existentes = set(rotas_da_aplicacao(aplicacao))
    implementadas = sorted(set(ROTAS_PENDENTES) & existentes)
    assert not implementadas, (
        f"{implementadas} agora existem: tire-as de ROTAS_PENDENTES e acrescente-as aos "
        "testes de duas contas e de 401 desta suíte."
    )


# --- 401 sem dados em toda rota protegida (cenário 2) -------------------------------------


async def test_a_lista_de_rotas_protegidas_nao_e_vazia(aplicacao: FastAPI) -> None:
    assert ("GET", "/api/v1/perfil") in rotas_protegidas(aplicacao)


async def rotas_que_nao_respondem_401(app: FastAPI, cliente: httpx.AsyncClient) -> list[str]:
    """Rotas protegidas que, sem sessão, não respondem `401` sem dados do recurso."""
    problemas: list[str] = []
    for metodo, caminho in rotas_protegidas(app):
        # O token pré-sessão passa pelo CSRF; quem barra é a autenticação. A resposta 401 apaga
        # os cookies, então o token é pedido de novo antes de cada requisição (como faz o SPA).
        await obter_csrf(cliente)
        resposta = await cliente.request(
            metodo, _url(caminho), json={} if metodo != "GET" else None
        )
        corpo = resposta.json() if resposta.content else {}
        if resposta.status_code != 401 or set(corpo) != {"codigo", "mensagem", "idRequisicao"}:
            problemas.append(f"{metodo} {caminho}: {resposta.status_code} {corpo}")
        elif corpo["codigo"] != "nao_autenticado":
            problemas.append(f"{metodo} {caminho}: código {corpo['codigo']}")
    return problemas


async def test_toda_rota_protegida_responde_401_sem_dados_sem_sessao(
    aplicacao: FastAPI, cliente: httpx.AsyncClient
) -> None:
    assert await rotas_que_nao_respondem_401(aplicacao, cliente) == []


async def test_a_verificacao_de_401_acusa_uma_rota_esquecida_sem_autenticacao(
    aplicacao: FastAPI, cliente: httpx.AsyncClient
) -> None:
    """Prova que o teste acima falha de verdade quando uma rota nova esquece a sessão."""

    @aplicacao.get("/api/v1/materias")
    async def listar_sem_autenticar() -> list[dict[str, str]]:
        return [{"nome": "dado de estudante"}]

    problemas = await rotas_que_nao_respondem_401(aplicacao, cliente)
    assert [p for p in problemas if p.startswith("GET /api/v1/materias:")], problemas
    assert len(problemas) == 1


async def test_sessao_inexistente_ou_malformada_tambem_e_401_em_toda_rota_protegida(
    aplicacao: FastAPI, cliente: httpx.AsyncClient
) -> None:
    await obter_csrf(cliente)
    for token in ("lixo", "A" * 43, "A" * 400, ""):
        definir_cookie(cliente, "__Host-sessao", token)
        for metodo, caminho in rotas_protegidas(aplicacao):
            resposta = await cliente.request(
                metodo, _url(caminho), json={} if metodo != "GET" else None
            )
            # Com cookie de sessão malformado, o token anti-CSRF pré-sessão deixa de valer (403);
            # com cookie bem formado e desconhecido, a autenticação responde 401.
            assert resposta.status_code in {401, 403}, f"{metodo} {caminho} {token[:5]}"
            assert "usuario" not in resposta.text.lower()


# --- Duas contas (cenário 1) ---------------------------------------------------------------


async def test_perfil_e_saida_de_uma_conta_nao_afetam_a_outra(
    aplicacao: FastAPI, cliente: httpx.AsyncClient
) -> None:
    ana, bia = dados_conta(nome="Ana A"), dados_conta(nome="Bia B")
    async with abrir_cliente(aplicacao, ip="198.51.100.31") as cliente_bia:
        assert (await cadastrar(cliente, ana)).status_code == 201
        assert (await cadastrar(cliente_bia, bia)).status_code == 201

        perfil_ana = (await cliente.get("/api/v1/perfil")).json()
        perfil_bia = (await cliente_bia.get("/api/v1/perfil")).json()
        assert perfil_ana["email"] == ana.email and perfil_bia["email"] == bia.email
        assert ana.email not in str(perfil_bia) and bia.email not in str(perfil_ana)

        # Bia sai: só a sessão dela termina.
        assert (await cliente_bia.post("/api/v1/auth/saida")).status_code == 204
        assert (await cliente_bia.get("/api/v1/perfil")).status_code == 401
        assert (await cliente.get("/api/v1/perfil")).json() == perfil_ana


async def test_alteracao_do_perfil_de_uma_conta_nao_afeta_a_outra(
    aplicacao: FastAPI, cliente: httpx.AsyncClient
) -> None:
    """`PATCH /perfil` (T049) entrou na tabela de duas contas, fora de `ROTAS_PENDENTES`."""
    ana, bia = dados_conta(), dados_conta()
    async with abrir_cliente(aplicacao, ip="198.51.100.34") as cliente_bia:
        await cadastrar(cliente, ana)
        await cadastrar(cliente_bia, bia)
        antes_ana = (await cliente.get("/api/v1/perfil")).json()
        resposta = await cliente_bia.patch(
            "/api/v1/perfil",
            json={"nome": "Bia Alterada", "metaDiaria": 3, "retencaoDesejada": 0.71},
        )
        assert resposta.status_code == 200 and resposta.json()["email"] == bia.email
        assert (await cliente.get("/api/v1/perfil")).json() == antes_ana


async def test_a_sessao_de_uma_conta_nunca_devolve_dados_de_outra(
    aplicacao: FastAPI, cliente: httpx.AsyncClient
) -> None:
    """Mesmo com o cookie de A num cliente de B, o perfil é sempre o do dono do cookie."""
    ana, bia = dados_conta(), dados_conta()
    async with abrir_cliente(aplicacao, ip="198.51.100.32") as cliente_bia:
        await cadastrar(cliente, ana)
        await cadastrar(cliente_bia, bia)
        assert (await cliente_bia.get("/api/v1/perfil")).json()["email"] == bia.email
        assert (await cliente.get("/api/v1/perfil")).json()["email"] == ana.email


# --- Mecanismo para recursos com identificador (cenário 1, specs 002 em diante) -----------


class BaseDeTeste(DeclarativeBase):
    """Fora do `Base` da aplicação: a tabela só existe dentro da transação do teste."""


class RecursoDeTeste(BaseDeTeste):
    __tablename__ = "recursos_de_teste"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        unique=True, server_default=text("gen_random_uuid()")
    )
    usuario_id: Mapped[int] = mapped_column()
    titulo: Mapped[str] = mapped_column(String(50))


@pytest.fixture
async def aplicacao_com_recurso(
    aplicacao: FastAPI, conexao: AsyncConnection, fabrica_sessoes: FabricaSessoes
) -> AsyncIterator[FastAPI]:
    """A aplicação com rotas de um recurso fictício, que só existem neste arquivo."""
    await conexao.run_sync(BaseDeTeste.metadata.create_all)

    @aplicacao.get("/api/v1/_teste/recursos/{recurso_id}")
    async def ler(recurso_id: uuid.UUID, atual: UsuarioAtual) -> dict[str, str]:
        async with unidade_de_trabalho(fabrica_sessoes) as sessao:
            recurso = await buscar_do_dono(sessao, RecursoDeTeste, recurso_id, atual.usuario.id)
            return {"titulo": recurso.titulo}

    @aplicacao.patch("/api/v1/_teste/recursos/{recurso_id}")
    async def alterar(recurso_id: uuid.UUID, atual: UsuarioAtual) -> dict[str, str]:
        async with unidade_de_trabalho(fabrica_sessoes) as sessao:
            recurso = await buscar_do_dono(
                sessao, RecursoDeTeste, recurso_id, atual.usuario.id, para_atualizar=True
            )
            recurso.titulo = "alterado"
            return {"titulo": recurso.titulo}

    @aplicacao.delete("/api/v1/_teste/recursos/{recurso_id}", status_code=204)
    async def excluir(recurso_id: uuid.UUID, atual: UsuarioAtual) -> None:
        async with unidade_de_trabalho(fabrica_sessoes) as sessao:
            recurso = await buscar_do_dono(sessao, RecursoDeTeste, recurso_id, atual.usuario.id)
            await sessao.delete(recurso)

    yield aplicacao


async def _criar_recurso(sessao: AsyncSession, usuario_id: int, titulo: str) -> uuid.UUID:
    recurso = RecursoDeTeste(usuario_id=usuario_id, titulo=titulo)
    sessao.add(recurso)
    await sessao.flush()
    return recurso.public_id


async def test_recurso_de_outro_dono_responde_404_identico_ao_inexistente(
    aplicacao_com_recurso: FastAPI, cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    ana, bia = dados_conta(), dados_conta()
    async with abrir_cliente(aplicacao_com_recurso, ip="198.51.100.33") as cliente_bia:
        await cadastrar(cliente, ana)
        await cadastrar(cliente_bia, bia)
        async with unidade_de_trabalho(fabrica_sessoes) as sessao:
            id_ana = (
                await sessao.execute(
                    text("select id from usuarios where email = :e"), {"e": ana.email}
                )
            ).scalar_one()
            recurso_de_ana = await _criar_recurso(sessao, id_ana, "caderno da Ana")

        assert (await cliente.get(f"/api/v1/_teste/recursos/{recurso_de_ana}")).json() == {
            "titulo": "caderno da Ana"
        }

        inexistente = uuid.uuid4()
        for metodo in ("GET", "PATCH", "DELETE"):
            de_outro = await cliente_bia.request(
                metodo, f"/api/v1/_teste/recursos/{recurso_de_ana}"
            )
            sumido = await cliente_bia.request(metodo, f"/api/v1/_teste/recursos/{inexistente}")
            assert de_outro.status_code == sumido.status_code == 404, metodo
            assert sem_id_requisicao(de_outro.json()) == sem_id_requisicao(sumido.json())
            assert de_outro.json()["codigo"] == "recurso_nao_encontrado"
            assert {
                k: v for k, v in de_outro.headers.items() if k not in {"x-request-id", "date"}
            } == {k: v for k, v in sumido.headers.items() if k not in {"x-request-id", "date"}}
            assert str(recurso_de_ana) not in de_outro.text and "Ana" not in de_outro.text

        # Nada mudou: o recurso segue intacto e o dono ainda o acessa.
        assert (await cliente.get(f"/api/v1/_teste/recursos/{recurso_de_ana}")).json() == {
            "titulo": "caderno da Ana"
        }


async def test_dono_consegue_alterar_e_excluir_o_proprio_recurso(
    aplicacao_com_recurso: FastAPI, cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    ana = dados_conta()
    await cadastrar(cliente, ana)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        id_ana = (
            await sessao.execute(text("select id from usuarios where email = :e"), {"e": ana.email})
        ).scalar_one()
        recurso = await _criar_recurso(sessao, id_ana, "original")
    assert (await cliente.patch(f"/api/v1/_teste/recursos/{recurso}")).json() == {
        "titulo": "alterado"
    }
    assert (await cliente.delete(f"/api/v1/_teste/recursos/{recurso}")).status_code == 204
    assert (await cliente.get(f"/api/v1/_teste/recursos/{recurso}")).status_code == 404


async def test_a_rota_de_teste_com_identificador_exige_caso_de_isolamento(
    aplicacao_com_recurso: FastAPI,
) -> None:
    """A tabela de casos também pegaria a rota de teste, se ela fosse da aplicação."""
    sem_caso = rotas_com_identificador_sem_caso(aplicacao_com_recurso, CASOS_DE_ISOLAMENTO)
    assert ("GET", "/api/v1/_teste/recursos/{recurso_id}") in sem_caso


async def test_a_aplicacao_real_nao_tem_a_rota_de_teste() -> None:
    from app.nucleo.configuracao import obter_configuracao

    caminhos = {caminho for _, caminho in rotas_da_aplicacao(criar_aplicacao(obter_configuracao()))}
    assert not any("_teste" in caminho for caminho in caminhos)
