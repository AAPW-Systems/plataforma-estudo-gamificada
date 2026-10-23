"""US1: criar um cartão manual, cenários 1 a 3 (T010; RF-001 a RF-004, RF-009, RF-011, RQ-001).

API e worker rodam em processo sobre o mesmo banco real. O estado gravado do cartão novo é
conferido no banco; a entrada numa lição real é reverificada pela 005.
"""

from __future__ import annotations

import uuid
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from procrastinate import App
from sqlalchemy import text

from app.cartoes.modelos import EstadoFsrs, OrigemCartao, SituacaoCartao
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.relogio import RelogioControlavel
from tests import fabricas_arquivos as fab
from tests.apoio_acervo import (
    consultar_fonte,
    criar_conta,
    criar_materia,
    enviar,
    id_interno_da_materia,
)
from tests.apoio_cartoes import ajustar_limites_cartoes, cartoes_da_materia, criar_cartao
from tests.conftest import executar_jobs
from tests.fabricas_arquivos import ArquivoGerado

pytestmark = pytest.mark.functional


@pytest.fixture(scope="module")
def validos() -> dict[str, ArquivoGerado]:
    return {a.nome: a for a in fab.validos()}


@pytest.fixture(scope="module")
def invalidos() -> dict[str, ArquivoGerado]:
    return {a.nome: a for a in fab.invalidos()}


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


async def _listar(cliente: httpx.AsyncClient, materia_id: str, **parametros: Any) -> dict[str, Any]:
    resposta = await cliente.get(f"/api/v1/materias/{materia_id}/cartoes", params=parametros)
    assert resposta.status_code == 200, resposta.text
    corpo: dict[str, Any] = resposta.json()
    return corpo


# --- Limites vigentes (RF-001, D-004) ------------------------------------------------------------


async def test_limites_vigentes_vem_da_configuracao_e_nao_do_cache(
    acervo: FastAPI, estudante: httpx.AsyncClient
) -> None:
    resposta = await estudante.get("/api/v1/cartoes/limites")
    assert resposta.status_code == 200
    assert resposta.json() == {
        "frenteMax": 1000,
        "versoMax": 2000,
        "explicacaoMax": 1000,
        "buscaMax": 100,
    }
    assert resposta.headers["Cache-Control"] == "no-store"

    ajustar_limites_cartoes(
        acervo, cartao_frente_max=50, cartao_verso_max=60, cartao_explicacao_max=7
    )
    assert (await estudante.get("/api/v1/cartoes/limites")).json() == {
        "frenteMax": 50,
        "versoMax": 60,
        "explicacaoMax": 7,
        "buscaMax": 100,
    }


async def test_limite_configurado_vale_na_criacao(
    acervo: FastAPI, estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    ajustar_limites_cartoes(acervo, cartao_frente_max=5)
    assert (await criar_cartao(estudante, biologia["id"], frente="12345")).status_code == 201
    recusado = await criar_cartao(estudante, biologia["id"], frente="123456")
    assert recusado.status_code == 422
    assert recusado.json()["campos"] == [
        {"campo": "frente", "mensagem": "Use de 1 a 5 caracteres."}
    ]


# --- Cenário 1: criar e ver na lista -------------------------------------------------------------


async def test_cria_cartao_ativo_criado_por_voce_e_ele_aparece_na_lista(
    acervo: FastAPI, estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    """US1-1 e RF-004: ativo, "Criado por você", sem selo de verificado."""
    resposta = await criar_cartao(
        estudante,
        biologia["id"],
        frente="Qual organela produz ATP?",
        verso="A mitocôndria.",
        explicacao="Linha 1\nLinha 2",
    )

    assert resposta.status_code == 201
    cartao = resposta.json()
    assert resposta.headers["Location"] == f"/api/v1/cartoes/{cartao['id']}"
    assert uuid.UUID(cartao["id"]) and cartao["materiaId"] == biologia["id"]
    assert cartao["frente"] == "Qual organela produz ATP?"
    assert cartao["verso"] == "A mitocôndria."
    assert cartao["explicacao"] == "Linha 1\nLinha 2", "a quebra de linha é preservada (RF-011)"
    assert (cartao["origem"], cartao["situacao"]) == ("criado", "ativo")
    assert cartao["verificado"] is False
    assert cartao["referencia"] is None
    assert cartao["criadoEm"] == cartao["atualizadoEm"]
    assert set(cartao) == {
        "id", "materiaId", "frente", "verso", "explicacao", "origem", "verificado", "situacao",
        "referencia", "criadoEm", "atualizadoEm",
    }, "nenhum campo do FSRS nem id interno sai pela API"  # fmt: skip

    lista = await _listar(estudante, biologia["id"])
    assert lista["total"] == 1 and lista["proximoCursor"] is None
    assert lista["itens"] == [cartao]


async def test_cartao_novo_tem_o_estado_gravado_de_cartao_novo_na_ordem_de_criacao(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    biologia: dict[str, Any],
    relogio: RelogioControlavel,
) -> None:
    """RF-003 e o teste independente: estado do `fsrs.Card()` e `entrada_estudo_em` crescente."""
    for pergunta in ("Primeiro", "Segundo", "Terceiro"):
        assert (await criar_cartao(estudante, biologia["id"], frente=pergunta)).status_code == 201
        relogio.avancar(seconds=30)

    interno = await id_interno_da_materia(_fabrica(acervo), biologia["id"])
    cartoes = await cartoes_da_materia(_fabrica(acervo), interno)

    assert [c.frente for c in cartoes] == ["Primeiro", "Segundo", "Terceiro"]
    for c in cartoes:
        assert (c.origem, c.situacao) == (OrigemCartao.CRIADO, SituacaoCartao.ATIVO)
        assert c.estado_fsrs is EstadoFsrs.APRENDIZADO and c.passo == 0
        assert (c.estabilidade, c.dificuldade, c.ultima_revisao) == (None, None, None)
        assert c.vencimento == c.entrada_estudo_em == c.criado_em
    entradas = [c.entrada_estudo_em for c in cartoes if c.entrada_estudo_em is not None]
    assert entradas == sorted(entradas) and len(set(entradas)) == 3


async def test_matéria_sem_cartoes_devolve_lista_vazia_com_total_zero(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    resposta = await estudante.get(f"/api/v1/materias/{biologia['id']}/cartoes")
    assert resposta.status_code == 200
    assert resposta.json() == {"itens": [], "proximoCursor": None, "total": 0}
    assert resposta.headers["Cache-Control"] == "no-store"


async def test_lista_do_mais_recente_ao_mais_antigo_com_cursor_e_total(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    biologia: dict[str, Any],
    relogio: RelogioControlavel,
) -> None:
    for numero in range(1, 8):
        await criar_cartao(estudante, biologia["id"], frente=f"Pergunta {numero}")
        relogio.avancar(seconds=1)

    pagina = await _listar(estudante, biologia["id"], limite=3)
    assert [c["frente"] for c in pagina["itens"]] == ["Pergunta 7", "Pergunta 6", "Pergunta 5"]
    assert pagina["total"] == 7 and pagina["proximoCursor"]

    vistos = [c["frente"] for c in pagina["itens"]]
    while pagina["proximoCursor"]:
        pagina = await _listar(estudante, biologia["id"], limite=3, cursor=pagina["proximoCursor"])
        assert pagina["total"] == 7
        vistos += [c["frente"] for c in pagina["itens"]]
    assert vistos == [f"Pergunta {n}" for n in range(7, 0, -1)]


async def test_cartoes_de_uma_materia_nao_aparecem_na_outra(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    quimica = await criar_materia(estudante, "Química")
    await criar_cartao(estudante, biologia["id"], frente="De biologia")
    await criar_cartao(estudante, quimica["id"], frente="De química")
    assert [c["frente"] for c in (await _listar(estudante, quimica["id"]))["itens"]] == [
        "De química"
    ]


# --- Cenário 2: texto inválido -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("corpo", "campos"),
    [
        ({"frente": "", "verso": "v"}, {"frente": "Use de 1 a 1.000 caracteres."}),
        ({"frente": "f", "verso": ""}, {"verso": "Use de 1 a 2.000 caracteres."}),
        ({"frente": "   \n\t ", "verso": "v"}, {"frente": "Use de 1 a 1.000 caracteres."}),
        ({"frente": "f", "verso": " \r\n "}, {"verso": "Use de 1 a 2.000 caracteres."}),
        ({"frente": "x" * 1001, "verso": "v"}, {"frente": "Use de 1 a 1.000 caracteres."}),
        ({"frente": "f", "verso": "x" * 2001}, {"verso": "Use de 1 a 2.000 caracteres."}),
        (
            {"frente": "f", "verso": "v", "explicacao": "x" * 1001},
            {"explicacao": "Use até 1.000 caracteres."},
        ),
        (
            {"frente": " ", "verso": "x" * 2001, "explicacao": "x" * 1001},
            {
                "frente": "Use de 1 a 1.000 caracteres.",
                "verso": "Use de 1 a 2.000 caracteres.",
                "explicacao": "Use até 1.000 caracteres.",
            },
        ),
    ],
    ids=[
        "frente-vazia",
        "verso-vazio",
        "frente-so-espacos",
        "verso-so-quebras",
        "frente-acima",
        "verso-acima",
        "explicacao-acima",
        "tres-campos",
    ],  # fmt: skip
)
async def test_texto_vazio_ou_acima_do_limite_nao_cria_nada_e_aponta_o_campo(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    biologia: dict[str, Any],
    corpo: dict[str, Any],
    campos: dict[str, str],
) -> None:
    """US1-2 e o caso de borda "só com espaços": 422 por campo, nada é criado."""
    resposta = await estudante.post(f"/api/v1/materias/{biologia['id']}/cartoes", json=corpo)

    assert resposta.status_code == 422
    erro = resposta.json()
    assert erro["codigo"] == "dados_invalidos"
    assert {c["campo"]: c["mensagem"] for c in erro["campos"]} == campos
    assert (await _listar(estudante, biologia["id"]))["total"] == 0
    interno = await id_interno_da_materia(_fabrica(acervo), biologia["id"])
    assert await cartoes_da_materia(_fabrica(acervo), interno) == []


async def test_textos_nos_limites_exatos_sao_aceitos(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    resposta = await criar_cartao(
        estudante, biologia["id"], frente="f" * 1000, verso="v" * 2000, explicacao="e" * 1000
    )
    assert resposta.status_code == 201
    cartao = resposta.json()
    assert (len(cartao["frente"]), len(cartao["verso"]), len(cartao["explicacao"])) == (
        1000,
        2000,
        1000,
    )


async def test_o_limite_conta_code_points_nao_bytes_nem_unidades_utf16(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    """1.000 emoji ocupam 4.000 bytes e 2.000 unidades UTF-16, e valem 1.000 caracteres."""
    assert (await criar_cartao(estudante, biologia["id"], frente="🧬" * 1000)).status_code == 201
    assert (await criar_cartao(estudante, biologia["id"], frente="🧬" * 1001)).status_code == 422
    combinado = "é" * 1000  # vira 1.000 "é" depois do NFC
    resposta = await criar_cartao(estudante, biologia["id"], frente=combinado)
    assert resposta.status_code == 201 and resposta.json()["frente"] == "é" * 1000


# --- Normalização e texto puro (RF-011, RQ-001) --------------------------------------------------


async def test_texto_e_normalizado_e_a_explicacao_vazia_vira_nula(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    resposta = await criar_cartao(
        estudante, biologia["id"], frente="  época\r\ncom quebra  ", verso="\tv\n", explicacao="  "
    )
    cartao = resposta.json()
    assert (cartao["frente"], cartao["verso"], cartao["explicacao"]) == (
        "época\ncom quebra",
        "v",
        None,
    )


@pytest.mark.parametrize(
    "texto",
    [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "**negrito** [link](javascript:alert(1))",
        "Tom & Jerry &amp; &lt;b&gt;",
        "50% _ \\ literal",
        "‮abc‬ e​ largura zero",
    ],
)
async def test_marcacao_e_script_voltam_literalmente_como_texto(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], texto: str
) -> None:
    """RQ-001: o servidor guarda e devolve o texto como foi digitado, em JSON."""
    resposta = await criar_cartao(estudante, biologia["id"], frente=texto, verso=texto)
    assert resposta.status_code == 201
    assert resposta.headers["content-type"].startswith("application/json")
    assert resposta.json()["frente"] == resposta.json()["verso"] == texto
    assert (await _listar(estudante, biologia["id"]))["itens"][0]["frente"] == texto


# --- Cenário 3: referência a uma fonte -----------------------------------------------------------


async def test_cartao_com_referencia_mostra_a_fonte_sem_selo_de_verificado(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], validos: dict[str, ArquivoGerado]
) -> None:
    """US1-3, RF-002 e D-002: "Criado por você" com a fonte, nunca verificado."""
    fonte = (
        await enviar(estudante, biologia["id"], validos["resumo.txt"], titulo="Citologia")
    ).json()

    resposta = await criar_cartao(estudante, biologia["id"], fonteId=fonte["id"])

    assert resposta.status_code == 201
    cartao = resposta.json()
    assert (cartao["origem"], cartao["verificado"]) == ("criado", False)
    assert cartao["referencia"] == {
        "fonteId": fonte["id"],
        "titulo": "Citologia",
        "nomeArquivo": "resumo.txt",
        "enviadaEm": fonte["enviadaEm"],
        "fonteApagada": False,
    }
    assert (await _listar(estudante, biologia["id"]))["itens"][0]["referencia"] == cartao[
        "referencia"
    ]


async def test_renomear_a_fonte_nao_muda_a_descricao_copiada(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], validos: dict[str, ArquivoGerado]
) -> None:
    """RN-05 e D-005 da 002: a cópia da origem não acompanha a renomeação."""
    fonte = (
        await enviar(estudante, biologia["id"], validos["resumo.txt"], titulo="Citologia")
    ).json()
    cartao = (await criar_cartao(estudante, biologia["id"], fonteId=fonte["id"])).json()

    renomeada = await estudante.patch(
        f"/api/v1/fontes/{fonte['id']}", json={"titulo": "Outro nome"}
    )
    assert renomeada.status_code == 200

    lista = await _listar(estudante, biologia["id"])
    assert lista["itens"][0]["id"] == cartao["id"]
    assert lista["itens"][0]["referencia"]["titulo"] == "Citologia"
    assert lista["itens"][0]["referencia"]["fonteId"] == fonte["id"]


@pytest.mark.parametrize(
    ("arquivo", "estado"),
    [("resumo.txt", "pendente"), ("digitalizado.pdf", "falhou"), ("resumo.txt", "concluido")],
    ids=["pendente", "falhou", "concluido"],
)
async def test_fonte_em_qualquer_estado_serve_de_referencia(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    biologia: dict[str, Any],
    fila: App,
    validos: dict[str, ArquivoGerado],
    invalidos: dict[str, ArquivoGerado],
    arquivo: str,
    estado: str,
) -> None:
    """DTEC 035: a referência copia só título, nome e data, que existem desde o envio."""
    origem = invalidos[arquivo] if arquivo in invalidos else validos[arquivo]
    fonte = (await enviar(estudante, biologia["id"], origem)).json()
    if estado != "pendente":
        await executar_jobs(fila)
    assert (await consultar_fonte(estudante, fonte["id"]))["estado"] == estado

    resposta = await criar_cartao(estudante, biologia["id"], fonteId=fonte["id"])

    assert resposta.status_code == 201
    assert resposta.json()["referencia"]["fonteId"] == fonte["id"]


async def test_fonte_id_nulo_equivale_a_sem_referencia(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    resposta = await criar_cartao(estudante, biologia["id"], fonteId=None)
    assert resposta.status_code == 201 and resposta.json()["referencia"] is None


@pytest.mark.parametrize("quem", ["inexistente", "de-outra-materia"])
async def test_fonte_invalida_responde_422_no_campo_fonte_id_e_nao_cria(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    biologia: dict[str, Any],
    validos: dict[str, ArquivoGerado],
    quem: str,
) -> None:
    if quem == "inexistente":
        fonte_id = str(uuid.uuid4())
    else:
        quimica = await criar_materia(estudante, "Química")
        fonte_id = (await enviar(estudante, quimica["id"], validos["resumo.txt"])).json()["id"]

    resposta = await criar_cartao(estudante, biologia["id"], fonteId=fonte_id)

    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "dados_invalidos"
    assert resposta.json()["campos"] == [
        {"campo": "fonteId", "mensagem": "Escolha uma fonte desta matéria."}
    ]
    assert (await _listar(estudante, biologia["id"]))["total"] == 0


# --- Fora das situações visíveis (DTEC 038) ------------------------------------------------------


async def test_cartao_aguardando_revisao_nao_aparece_na_lista_nem_no_total(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    biologia: dict[str, Any],
    situacoes_da_004: None,
) -> None:
    """Caso de borda da spec: o cartão gerado e ainda não aceito é tratado pela 004."""
    await criar_cartao(estudante, biologia["id"], frente="Visível")
    interno = await id_interno_da_materia(_fabrica(acervo), biologia["id"])
    async with unidade_de_trabalho(_fabrica(acervo)) as sessao:
        for situacao in ("aguardando_revisao", "recusado"):
            await sessao.execute(
                text(
                    "INSERT INTO cartoes (usuario_id, materia_id, frente, verso, origem, situacao) "
                    "SELECT usuario_id, :m, 'Escondido', 'Escondido', 'gerado_verificado', "
                    "CAST(:s AS situacao_cartao) FROM materias WHERE id = :m"
                ),
                {"m": interno, "s": situacao},
            )

    lista = await _listar(estudante, biologia["id"])

    assert [c["frente"] for c in lista["itens"]] == ["Visível"]
    assert lista["total"] == 1
