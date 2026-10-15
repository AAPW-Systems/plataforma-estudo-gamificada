"""US3: renomear matérias e fontes e excluir uma matéria em cascata, cenários 1 a 5 (T040; CS-004).

Os cartões ainda não existem (003 e 004): participantes falsos fazem o papel deles (DTEC 027) e
registram cada chamada. API e worker rodam em processo, sobre o mesmo banco e armazenamento.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from procrastinate import App
from sqlalchemy import select
from structlog.testing import capture_logs

from app.fontes.modelos import Fonte
from app.nucleo.armazenamento import Armazenamento
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.participantes_acervo import ContagensAcervo, registro_acervo
from tests import fabricas_arquivos as fab
from tests.apoio_acervo import (
    chave_da_fonte,
    consultar_fonte,
    contar_linhas_da_materia,
    criar_conta,
    criar_materia,
    enviar,
    id_interno_da_materia,
    trechos_da_fonte,
)
from tests.conftest import executar_jobs
from tests.fabricas_arquivos import ArquivoGerado
from tests.participantes_falsos import ParticipanteFalso

pytestmark = pytest.mark.functional


@pytest.fixture(scope="module")
def validos() -> dict[str, ArquivoGerado]:
    return {a.nome: a for a in fab.validos()}


@pytest.fixture
def cartoes() -> Iterator[tuple[ParticipanteFalso, ParticipanteFalso]]:
    """Dois participantes falsos de cartões, registrados fora de ordem e removidos ao final.

    O registro é global; a prioridade menor roda antes (100 antes de 200, e os dois antes de
    `fontes`, 900), qualquer que seja a ordem em que foram registrados.
    """
    chamadas: list[tuple[str, str, object]] = []
    geracoes = ParticipanteFalso(nome="geracoes_falso", chamadas=chamadas, observar_fontes=True)
    manuais = ParticipanteFalso(nome="manuais_falso", chamadas=chamadas, observar_fontes=True)
    registro_acervo.registrar(200, "geracoes_falso", geracoes)
    registro_acervo.registrar(100, "manuais_falso", manuais)
    try:
        yield manuais, geracoes
    finally:
        registro_acervo.remover("geracoes_falso")
        registro_acervo.remover("manuais_falso")


@pytest.fixture
async def estudante(acervo: FastAPI, cliente_real: httpx.AsyncClient) -> httpx.AsyncClient:
    await criar_conta(cliente_real)
    return cliente_real


def _fabrica(app: FastAPI) -> FabricaSessoes:
    fabrica: FabricaSessoes = app.state.fabrica_sessoes
    return fabrica


def _armazenamento(app: FastAPI) -> Armazenamento:
    armazenamento: Armazenamento = app.state.armazenamento
    return armazenamento


async def _nomes_na_lista(estudante: httpx.AsyncClient) -> list[str]:
    return [m["nome"] for m in (await estudante.get("/api/v1/materias")).json()["itens"]]


# --- Cenário 1: renomear a matéria -------------------------------------------------------------


async def test_renomear_para_nome_livre_aparece_na_lista_e_na_consulta(
    acervo: FastAPI, estudante: httpx.AsyncClient
) -> None:
    materia = await criar_materia(estudante, "Biologia")
    outra = await criar_materia(estudante, "Química")

    resposta = await estudante.patch(f"/api/v1/materias/{materia['id']}", json={"nome": "Genética"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["nome"] == "Genética" and corpo["id"] == materia["id"]
    assert corpo["atualizadoEm"] >= materia["atualizadoEm"]
    assert corpo["criadoEm"] == materia["criadoEm"]
    assert (await estudante.get(f"/api/v1/materias/{materia['id']}")).json()["nome"] == "Genética"
    assert await _nomes_na_lista(estudante) == ["Genética", "Química"]
    assert (await estudante.get(f"/api/v1/materias/{outra['id']}")).json()["nome"] == "Química"


async def test_renomear_normaliza_o_nome_como_na_criacao(
    acervo: FastAPI, estudante: httpx.AsyncClient
) -> None:
    materia = await criar_materia(estudante, "Biologia")
    decomposto = "Café e cultura"  # NFD, com espaços nas pontas

    resposta = await estudante.patch(
        f"/api/v1/materias/{materia['id']}", json={"nome": f"  {decomposto}  "}
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Café e cultura"  # NFC, sem espaços nas extremidades


async def test_renomear_a_propria_materia_so_na_caixa_ou_com_o_mesmo_nome_e_permitido(
    acervo: FastAPI, estudante: httpx.AsyncClient
) -> None:
    """O nome em uso é o de **outra** matéria: a própria não conflita consigo mesma."""
    materia = await criar_materia(estudante, "Biologia")
    url = f"/api/v1/materias/{materia['id']}"

    assert (await estudante.patch(url, json={"nome": "BIOLOGIA"})).json()["nome"] == "BIOLOGIA"
    assert (await estudante.patch(url, json={"nome": "BIOLOGIA"})).status_code == 200


@pytest.mark.parametrize(
    ("nome", "mensagem"),
    [
        ("", "Informe o nome."),
        ("   ", "Informe o nome."),
        ("x" * 61, "Use no máximo 60 caracteres."),
        ("Bio\x00logia", "O nome tem caracteres que não podem ser usados."),
    ],
    ids=["vazio", "so-espacos", "61-caracteres", "caractere-de-controle"],
)
async def test_nome_invalido_na_renomeacao_e_422_junto_do_campo(
    acervo: FastAPI, estudante: httpx.AsyncClient, nome: str, mensagem: str
) -> None:
    materia = await criar_materia(estudante, "Biologia")

    resposta = await estudante.patch(f"/api/v1/materias/{materia['id']}", json={"nome": nome})

    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "dados_invalidos"
    assert resposta.json()["campos"] == [{"campo": "nome", "mensagem": mensagem}]
    assert (await estudante.get(f"/api/v1/materias/{materia['id']}")).json()["nome"] == "Biologia"


async def test_nome_de_60_caracteres_e_aceito_na_renomeacao(
    acervo: FastAPI, estudante: httpx.AsyncClient
) -> None:
    materia = await criar_materia(estudante, "Biologia")
    resposta = await estudante.patch(f"/api/v1/materias/{materia['id']}", json={"nome": "y" * 60})
    assert resposta.status_code == 200 and len(resposta.json()["nome"]) == 60


async def test_renomear_nao_mexe_nas_fontes_nem_nas_contagens(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
) -> None:
    materia = await criar_materia(estudante, "Biologia")
    fonte = (await enviar(estudante, materia["id"], validos["resumo.txt"])).json()
    await executar_jobs(fila)

    resposta = await estudante.patch(f"/api/v1/materias/{materia['id']}", json={"nome": "Genética"})

    assert resposta.json()["totalFontes"] == 1
    assert (await consultar_fonte(estudante, fonte["id"]))["materiaId"] == materia["id"]
    assert (await estudante.get(f"/api/v1/materias/{materia['id']}/fontes")).json()["itens"][0][
        "id"
    ] == fonte["id"]


# --- Cenário 2: nome já usado -------------------------------------------------------------------


@pytest.mark.parametrize(
    "repetido", ["Química", "química", "QUÍMICA", "  Química  ", "Qui\u0301mica"]
)
async def test_nome_de_outra_materia_e_recusado_sem_diferenciar_caixa(
    acervo: FastAPI, estudante: httpx.AsyncClient, repetido: str
) -> None:
    materia = await criar_materia(estudante, "Biologia")
    await criar_materia(estudante, "Química")

    resposta = await estudante.patch(f"/api/v1/materias/{materia['id']}", json={"nome": repetido})

    assert resposta.status_code == 409
    assert resposta.json()["codigo"] == "materia_nome_em_uso"
    assert resposta.json()["campos"] == [
        {"campo": "nome", "mensagem": "Você já tem uma matéria com esse nome."}
    ]
    assert await _nomes_na_lista(estudante) == ["Biologia", "Química"], "nada mudou"


async def test_outro_estudante_pode_usar_o_mesmo_nome(
    acervo: FastAPI, estudante: httpx.AsyncClient
) -> None:
    """O nome é único por estudante: o de outra conta não conflita."""
    from tests.apoio_http import abrir_cliente

    await criar_materia(estudante, "Química")
    async with abrir_cliente(acervo, ip="198.51.100.77") as outro:
        await criar_conta(outro)
        materia = await criar_materia(outro, "Biologia")
        resposta = await outro.patch(f"/api/v1/materias/{materia['id']}", json={"nome": "Química"})
    assert resposta.status_code == 200


# --- Cenário 3: o impacto e a confirmação pelo nome ---------------------------------------------


async def _materia_com_dados(
    app: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: tuple[ParticipanteFalso, ParticipanteFalso],
    nome: str = "Biologia",
) -> tuple[dict[str, Any], int, list[dict[str, Any]]]:
    """Matéria com 2 fontes e, nos participantes, 5 cartões ativos, 2 suspensos e 3 aguardando."""
    materia = await criar_materia(estudante, nome)
    fontes = [
        (await enviar(estudante, materia["id"], validos[arquivo], titulo=titulo)).json()
        for arquivo, titulo in (
            ("biologia-citologia.pdf", "Citologia"),
            ("resumo.txt", "Resumo"),
        )
    ]
    await executar_jobs(fila)
    interno = await id_interno_da_materia(_fabrica(app), materia["id"])
    manuais, geracoes = cartoes
    manuais.por_materia[interno] = ContagensAcervo(cartoes_ativos=3, cartoes_suspensos=1)
    geracoes.por_materia[interno] = ContagensAcervo(
        cartoes_ativos=2, cartoes_suspensos=1, cartoes_aguardando_revisao=3
    )
    return materia, interno, fontes


IMPACTO = {"fontes": 2, "cartoesAtivos": 7, "cartoesAguardandoRevisao": 3}


async def test_impacto_mostra_o_nome_e_as_contagens_com_suspensos_somados(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: tuple[ParticipanteFalso, ParticipanteFalso],
) -> None:
    materia, _, _ = await _materia_com_dados(acervo, estudante, fila, validos, cartoes)

    resposta = await estudante.get(f"/api/v1/materias/{materia['id']}/impacto-exclusao")

    assert resposta.status_code == 200
    assert resposta.json() == {"nome": "Biologia", "contagens": IMPACTO}
    assert resposta.headers["Cache-Control"] == "no-store"
    # A lista de matérias mostra só os ativos, sem os suspensos (emenda da DTEC 027).
    na_lista = (await estudante.get("/api/v1/materias")).json()["itens"][0]
    assert na_lista["cartoesAtivos"] == 5 and na_lista["cartoesAguardandoRevisao"] == 3


async def test_impacto_sem_cartoes_devolve_zeros_e_conta_so_as_fontes(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
) -> None:
    materia = await criar_materia(estudante)
    await enviar(estudante, materia["id"], validos["resumo.txt"])
    resposta = await estudante.get(f"/api/v1/materias/{materia['id']}/impacto-exclusao")
    assert resposta.json()["contagens"] == {
        "fontes": 1,
        "cartoesAtivos": 0,
        "cartoesAguardandoRevisao": 0,
    }


async def test_impacto_conta_tambem_a_fonte_que_falhou(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
) -> None:
    """Fonte com `falhou` também será apagada: entra na conta (D-010)."""
    materia = await criar_materia(estudante)
    await enviar(estudante, materia["id"], ("a.txt", b"conteudo " * 20))
    async with unidade_de_trabalho(_fabrica(acervo)) as sessao:
        fonte = (await sessao.execute(select(Fonte))).scalar_one()
        fonte.estado = "falhou"
        fonte.codigo_falha = "sem_texto"
    resposta = await estudante.get(f"/api/v1/materias/{materia['id']}/impacto-exclusao")
    assert resposta.json()["contagens"]["fontes"] == 1


def _corpo(nome: str = "Biologia", **contagens: int) -> dict[str, Any]:
    return {"nomeConfirmacao": nome, "impactoConfirmado": {**IMPACTO, **contagens}}


async def test_exclusao_exige_o_nome_digitado_e_recusa_com_422_sem_apagar_nada(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: tuple[ParticipanteFalso, ParticipanteFalso],
) -> None:
    materia, interno, fontes = await _materia_com_dados(acervo, estudante, fila, validos, cartoes)
    antes = await contar_linhas_da_materia(_fabrica(acervo), interno)

    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/exclusao", json=_corpo("Quimica")
    )

    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "confirmacao_invalida"
    assert resposta.json()["mensagem"] == "O nome digitado não confere com o nome da matéria."
    assert resposta.json()["campos"] == [
        {"campo": "nomeConfirmacao", "mensagem": "Digite o nome exatamente como aparece."}
    ]
    assert await contar_linhas_da_materia(_fabrica(acervo), interno) == antes
    assert cartoes[0].exclusoes_de_materia == [] and cartoes[1].exclusoes_de_materia == []
    for fonte in fontes:
        chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])
        assert await _armazenamento(acervo).existe(chave)


# --- Cenário 4: a exclusão em cascata (CS-004) --------------------------------------------------


async def test_exclusao_apaga_materia_fontes_trechos_e_objetos_e_chama_os_participantes_na_ordem(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: tuple[ParticipanteFalso, ParticipanteFalso],
) -> None:
    materia, interno, fontes = await _materia_com_dados(acervo, estudante, fila, validos, cartoes)
    outra = await criar_materia(estudante, "Química")
    outra_fonte = (await enviar(estudante, outra["id"], validos["resumo.txt"])).json()
    await executar_jobs(fila)
    chaves = [await chave_da_fonte(_fabrica(acervo), f["id"]) for f in fontes]
    chave_outra = await chave_da_fonte(_fabrica(acervo), outra_fonte["id"])
    assert (await contar_linhas_da_materia(_fabrica(acervo), interno))[2] > 0
    manuais, geracoes = cartoes
    exibido = (await estudante.get(f"/api/v1/materias/{materia['id']}/impacto-exclusao")).json()

    with capture_logs() as registros:
        resposta = await estudante.post(
            f"/api/v1/materias/{materia['id']}/exclusao",
            json={"nomeConfirmacao": "Biologia", "impactoConfirmado": exibido["contagens"]},
        )

    assert resposta.status_code == 204 and resposta.content == b""
    # Nada da matéria sobra: linha, fontes, trechos e objetos.
    assert await contar_linhas_da_materia(_fabrica(acervo), interno) == (0, 0, 0)
    for chave in chaves:
        assert not await _armazenamento(acervo).existe(chave)
    for fonte in fontes:
        assert (await estudante.get(f"/api/v1/fontes/{fonte['id']}")).status_code == 404
        assert await trechos_da_fonte(_fabrica(acervo), fonte["id"]) == []
    assert (await estudante.get(f"/api/v1/materias/{materia['id']}")).status_code == 404
    assert await _nomes_na_lista(estudante) == ["Química"]
    # A outra matéria segue inteira.
    assert await _armazenamento(acervo).existe(chave_outra)
    assert (await consultar_fonte(estudante, outra_fonte["id"]))["estado"] == "concluido"
    # Cada participante recebeu a matéria certa uma única vez, na ordem de prioridade, e as
    # fontes ainda existiam quando os de cartões foram chamados (a de `fontes` roda por último).
    assert [(n, quando) for n, quando, _ in manuais.chamadas] == [
        ("manuais_falso", "materia"),
        ("geracoes_falso", "materia"),
    ]
    assert manuais.exclusoes_de_materia[0][1] == interno == geracoes.exclusoes_de_materia[0][1]
    assert manuais.fontes_vistas_ao_excluir_materia == [2]
    assert geracoes.fontes_vistas_ao_excluir_materia == [2]
    # Os participantes receberam a sessão (a transação) de quem os chamou, a mesma para todos.
    assert manuais.chamadas[0][2] is geracoes.chamadas[0][2]
    eventos = [r for r in registros if r["event"] == "materia_excluida"]
    assert len(eventos) == 1
    assert eventos[0]["materia_public_id"] == materia["id"]
    assert "Biologia" not in str(registros) and "citologia" not in str(registros).lower()


async def test_cs004_contagens_exibidas_sao_as_apagadas_na_exclusao_da_materia(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: tuple[ParticipanteFalso, ParticipanteFalso],
) -> None:
    """CS-004: o que o diálogo mostra coincide com o que os participantes e o banco apagam."""
    materia, interno, _ = await _materia_com_dados(acervo, estudante, fila, validos, cartoes)
    exibido = (await estudante.get(f"/api/v1/materias/{materia['id']}/impacto-exclusao")).json()
    fontes_antes = (await contar_linhas_da_materia(_fabrica(acervo), interno))[1]
    manuais, geracoes = cartoes
    por_participante = [p.por_materia[interno] for p in (manuais, geracoes)]
    recebido = por_participante[0] + por_participante[1]

    assert (
        await estudante.post(
            f"/api/v1/materias/{materia['id']}/exclusao",
            json={"nomeConfirmacao": "Biologia", "impactoConfirmado": exibido["contagens"]},
        )
    ).status_code == 204

    contagens = exibido["contagens"]
    assert contagens["fontes"] == fontes_antes
    assert contagens["cartoesAtivos"] == recebido.cartoes_ativos + recebido.cartoes_suspensos
    assert contagens["cartoesAguardandoRevisao"] == recebido.cartoes_aguardando_revisao
    assert len(manuais.exclusoes_de_materia) == len(geracoes.exclusoes_de_materia) == 1


async def test_depois_de_excluir_o_nome_e_a_cota_ficam_livres(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
) -> None:
    materia = await criar_materia(estudante)
    await enviar(estudante, materia["id"], validos["resumo.txt"])
    exibido = (await estudante.get(f"/api/v1/materias/{materia['id']}/impacto-exclusao")).json()
    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/exclusao",
        json={"nomeConfirmacao": "Biologia", "impactoConfirmado": exibido["contagens"]},
    )
    assert resposta.status_code == 204

    nova = await criar_materia(estudante, "Biologia")
    assert nova["id"] != materia["id"] and nova["totalFontes"] == 0
    uso = (await estudante.get("/api/v1/acervo/uso")).json()
    assert uso["totalMaterias"] == 1 and uso["usoArmazenamentoBytes"] == 0


async def test_excluir_materia_sem_fontes_nem_cartoes(
    acervo: FastAPI, estudante: httpx.AsyncClient
) -> None:
    materia = await criar_materia(estudante)
    zeros = {"fontes": 0, "cartoesAtivos": 0, "cartoesAguardandoRevisao": 0}
    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/exclusao",
        json={"nomeConfirmacao": "Biologia", "impactoConfirmado": zeros},
    )
    assert resposta.status_code == 204
    assert await _nomes_na_lista(estudante) == []


# --- Cenário 5: renomear a fonte ----------------------------------------------------------------


async def test_renomear_a_fonte_altera_so_o_titulo(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
) -> None:
    materia = await criar_materia(estudante)
    fonte = (
        await enviar(estudante, materia["id"], validos["biologia-citologia.pdf"], titulo="Antigo")
    ).json()
    await executar_jobs(fila)
    antes = await consultar_fonte(estudante, fonte["id"])
    trechos_antes = [
        (t.ordem, t.texto, t.pagina) for t in await trechos_da_fonte(_fabrica(acervo), fonte["id"])
    ]
    chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])

    resposta = await estudante.patch(f"/api/v1/fontes/{fonte['id']}", json={"titulo": "  Novo  "})

    assert resposta.status_code == 200
    depois = resposta.json()
    assert depois["titulo"] == "Novo"
    assert {k: v for k, v in depois.items() if k != "titulo"} == {
        k: v for k, v in antes.items() if k != "titulo"
    }, "nome do arquivo, tipo, tamanho, estado, páginas e trechos não mudam (D-005)"
    assert await consultar_fonte(estudante, fonte["id"]) == depois
    assert [
        (t.ordem, t.texto, t.pagina) for t in await trechos_da_fonte(_fabrica(acervo), fonte["id"])
    ] == trechos_antes
    assert await chave_da_fonte(_fabrica(acervo), fonte["id"]) == chave
    acervo_da_materia = (await estudante.get(f"/api/v1/materias/{materia['id']}/fontes")).json()
    assert [f["titulo"] for f in acervo_da_materia["itens"]] == ["Novo"]


@pytest.mark.parametrize("tamanho", [1, 120])
async def test_titulo_de_1_a_120_caracteres_e_aceito(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    validos: dict[str, ArquivoGerado],
    tamanho: int,
) -> None:
    materia = await criar_materia(estudante)
    fonte = (await enviar(estudante, materia["id"], validos["resumo.txt"])).json()
    resposta = await estudante.patch(
        f"/api/v1/fontes/{fonte['id']}", json={"titulo": "t" * tamanho}
    )
    assert resposta.status_code == 200 and len(resposta.json()["titulo"]) == tamanho


@pytest.mark.parametrize(
    ("titulo", "mensagem"),
    [
        ("", "Informe o título."),
        ("   ", "Informe o título."),
        ("t" * 121, "Use no máximo 120 caracteres."),
        ("Tí\x00tulo", "O título tem caracteres que não podem ser usados."),
    ],
    ids=["vazio", "so-espacos", "121-caracteres", "caractere-de-controle"],
)
async def test_titulo_invalido_e_422_junto_do_campo(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    validos: dict[str, ArquivoGerado],
    titulo: str,
    mensagem: str,
) -> None:
    materia = await criar_materia(estudante)
    fonte = (await enviar(estudante, materia["id"], validos["resumo.txt"], titulo="Antigo")).json()

    resposta = await estudante.patch(f"/api/v1/fontes/{fonte['id']}", json={"titulo": titulo})

    assert resposta.status_code == 422
    assert resposta.json()["campos"] == [{"campo": "titulo", "mensagem": mensagem}]
    assert (await consultar_fonte(estudante, fonte["id"]))["titulo"] == "Antigo"


async def test_titulo_repetido_em_outra_fonte_e_permitido(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    validos: dict[str, ArquivoGerado],
) -> None:
    """O título não é identificador: só o conteúdo repetido é recusado (D-004)."""
    materia = await criar_materia(estudante)
    primeira = (await enviar(estudante, materia["id"], validos["resumo.txt"], titulo="Aula")).json()
    segunda = (
        await enviar(estudante, materia["id"], validos["biologia-citologia.pdf"], titulo="Outra")
    ).json()
    resposta = await estudante.patch(f"/api/v1/fontes/{segunda['id']}", json={"titulo": "Aula"})
    assert resposta.status_code == 200 and primeira["titulo"] == resposta.json()["titulo"]


async def test_renomear_fonte_que_falhou_e_permitido(
    acervo: FastAPI, estudante: httpx.AsyncClient
) -> None:
    materia = await criar_materia(estudante)
    fonte = (await enviar(estudante, materia["id"], ("a.txt", b"conteudo " * 20))).json()
    async with unidade_de_trabalho(_fabrica(acervo)) as sessao:
        registro = (await sessao.execute(select(Fonte))).scalar_one()
        registro.estado = "falhou"
        registro.codigo_falha = "falha_tecnica"
    resposta = await estudante.patch(f"/api/v1/fontes/{fonte['id']}", json={"titulo": "Revisar"})
    assert resposta.status_code == 200
    assert resposta.json()["estado"] == "falhou" and resposta.json()["podeTentarNovamente"] is True
