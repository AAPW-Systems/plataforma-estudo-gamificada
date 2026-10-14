"""US2: excluir uma fonte e decidir sobre os cartões, cenários 1 a 6 (T033; CS-004).

Os cartões ainda não existem (003 e 004): um participante falso com estado em memória faz o
papel deles (DTEC 027). API e worker rodam em processo, sobre o mesmo banco e armazenamento.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from procrastinate import App
from structlog.testing import capture_logs

from app.nucleo.armazenamento import Armazenamento
from app.nucleo.banco import FabricaSessoes
from app.nucleo.participantes_acervo import ModoCartoes, registro_acervo
from tests import fabricas_arquivos as fab
from tests.apoio_acervo import (
    chave_da_fonte,
    consultar_fonte,
    contar_linhas_da_fonte,
    criar_conta,
    criar_materia,
    enviar,
    id_interno_da_fonte,
)
from tests.conftest import executar_jobs
from tests.fabricas_arquivos import ArquivoGerado
from tests.participantes_falsos import ParticipanteDeCartoesFalso

pytestmark = pytest.mark.functional

PRIORIDADE_FALSA = 100


@pytest.fixture(scope="module")
def validos() -> dict[str, ArquivoGerado]:
    return {a.nome: a for a in fab.validos()}


@pytest.fixture(scope="module")
def invalidos() -> dict[str, ArquivoGerado]:
    return {a.nome: a for a in fab.invalidos()}


@pytest.fixture
def cartoes() -> Iterator[ParticipanteDeCartoesFalso]:
    """Registra o participante falso e o remove ao final: o registro é global."""
    participante = ParticipanteDeCartoesFalso()
    registro_acervo.registrar(PRIORIDADE_FALSA, "cartoes_falso", participante)
    try:
        yield participante
    finally:
        registro_acervo.remover("cartoes_falso")


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


CONTAGENS = {"cartoesGeradosAceitos": 3, "cartoesAguardandoRevisao": 2, "cartoesReferencia": 1}


async def _fonte_concluida(
    app: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    arquivo: ArquivoGerado,
    cartoes: ParticipanteDeCartoesFalso,
    *,
    titulo: str = "Citologia",
    com_cartoes: bool = True,
) -> tuple[dict[str, Any], int]:
    """Uma fonte processada, com 3 cartões aceitos, 2 aguardando e 1 de referência."""
    materia = await criar_materia(estudante)
    fonte = (await enviar(estudante, materia["id"], arquivo, titulo=titulo)).json()
    await executar_jobs(fila)
    interno = await id_interno_da_fonte(_fabrica(app), fonte["id"])
    if com_cartoes:
        cartoes.definir(interno, aceitos=3, aguardando=2, referencia=1)
    return fonte, interno


def _corpo(modo: str, **contagens: int) -> dict[str, Any]:
    return {"modoCartoes": modo, "impactoConfirmado": {**CONTAGENS, **contagens}}


# --- Cenário 1: o diálogo mostra o impacto -----------------------------------------------------


async def test_impacto_mostra_titulo_estado_e_as_tres_contagens_separadas(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteDeCartoesFalso,
) -> None:
    fonte, _ = await _fonte_concluida(
        acervo, estudante, fila, validos["pdf-uma-pagina.pdf"], cartoes
    )

    resposta = await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")

    assert resposta.status_code == 200
    assert resposta.json() == {"titulo": "Citologia", "estado": "concluido", "contagens": CONTAGENS}
    assert resposta.headers["Cache-Control"] == "no-store"


async def test_impacto_sem_cartoes_devolve_zeros(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
) -> None:
    """Antes de existirem cartões (003 e 004), todas as contagens valem zero."""
    materia = await criar_materia(estudante)
    fonte = (await enviar(estudante, materia["id"], validos["resumo.txt"])).json()
    resposta = await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")
    assert resposta.json()["contagens"] == {
        "cartoesGeradosAceitos": 0,
        "cartoesAguardandoRevisao": 0,
        "cartoesReferencia": 0,
    }


# --- Cenários 2 e 3: manter ou excluir os cartões -----------------------------------------------


@pytest.mark.parametrize(
    ("modo", "aceitos_apagados"), [("manter", 0), ("excluir", 3)], ids=["manter", "excluir"]
)
async def test_exclusao_apaga_arquivo_trechos_e_fonte_e_aplica_o_modo(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteDeCartoesFalso,
    modo: str,
    aceitos_apagados: int,
) -> None:
    """US2-2 e 3 e o teste independente: o participante recebe o modo escolhido."""
    fonte, interno = await _fonte_concluida(
        acervo, estudante, fila, validos["biologia-citologia.pdf"], cartoes
    )
    chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])
    assert await _armazenamento(acervo).existe(chave)
    assert (await contar_linhas_da_fonte(_fabrica(acervo), interno))[1] > 0

    resposta = await estudante.post(f"/api/v1/fontes/{fonte['id']}/exclusao", json=_corpo(modo))

    assert resposta.status_code == 204 and resposta.content == b""
    assert cartoes.modos == [ModoCartoes(modo)]
    assert cartoes.apagados == [{"aguardando": 2, "aceitos": aceitos_apagados, "referencia": 0}], (
        "os aguardando revisão sempre saem; os de referência nunca"
    )
    assert not await _armazenamento(acervo).existe(chave), "o arquivo foi apagado"
    assert await contar_linhas_da_fonte(_fabrica(acervo), interno) == (0, 0)
    assert (await estudante.get(f"/api/v1/fontes/{fonte['id']}")).status_code == 404
    lista = (await estudante.get(f"/api/v1/materias/{fonte['materiaId']}/fontes")).json()
    assert lista["itens"] == []
    materia = (await estudante.get(f"/api/v1/materias/{fonte['materiaId']}")).json()
    assert materia["totalFontes"] == 0


# --- Cenários 4 e 5: aguardando sempre; referência separada e nunca afetada ---------------------


@pytest.mark.parametrize("modo", ["manter", "excluir"])
async def test_aguardando_revisao_sempre_sai_e_referencia_nunca_e_tocada(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteDeCartoesFalso,
    modo: str,
) -> None:
    fonte, interno = await _fonte_concluida(acervo, estudante, fila, validos["resumo.txt"], cartoes)

    assert (
        await estudante.post(f"/api/v1/fontes/{fonte['id']}/exclusao", json=_corpo(modo))
    ).status_code == 204

    restantes = cartoes.por_fonte[interno]
    assert restantes.aguardando == 0, "US2-4: com qualquer opção"
    assert restantes.referencia == 1, "US2-5 (D-009): nunca afetados pelo modo"
    assert restantes.aceitos == (0 if modo == "excluir" else 3)


# --- Cenário 6: cancelar não muda nada ---------------------------------------------------------


async def test_cancelar_nao_chama_nada_e_a_fonte_segue_intacta(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteDeCartoesFalso,
) -> None:
    """Abrir o diálogo é só consultar o impacto: nada é gravado, apagado nem chamado."""
    fonte, interno = await _fonte_concluida(acervo, estudante, fila, validos["resumo.txt"], cartoes)
    antes = await consultar_fonte(estudante, fonte["id"])
    chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])
    linhas = await contar_linhas_da_fonte(_fabrica(acervo), interno)

    for _ in range(3):
        assert (
            await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")
        ).status_code == 200

    assert cartoes.modos == [] and cartoes.apagados == []
    assert await consultar_fonte(estudante, fonte["id"]) == antes
    assert await _armazenamento(acervo).existe(chave)
    assert await contar_linhas_da_fonte(_fabrica(acervo), interno) == linhas


# --- Estados da fonte e escolha obrigatória ----------------------------------------------------


@pytest.mark.parametrize(
    "arquivo_e_estado",
    [("digitalizado.pdf", "falhou"), ("resumo.txt", "pendente"), ("resumo.txt", "concluido")],
    ids=["falhou-sem-texto", "pendente", "concluido"],
)
async def test_fonte_em_qualquer_estado_pode_ser_excluida(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    invalidos: dict[str, ArquivoGerado],
    cartoes: ParticipanteDeCartoesFalso,
    arquivo_e_estado: tuple[str, str],
) -> None:
    """RF-012 e D-010: inclusive a que `falhou` e a que ainda nem começou a processar."""
    nome, estado = arquivo_e_estado
    arquivo = invalidos[nome] if nome in invalidos else validos[nome]
    materia = await criar_materia(estudante)
    fonte = (await enviar(estudante, materia["id"], arquivo)).json()
    if estado != "pendente":
        await executar_jobs(fila)
    assert (await consultar_fonte(estudante, fonte["id"]))["estado"] == estado

    resposta = await estudante.post(
        f"/api/v1/fontes/{fonte['id']}/exclusao",
        json=_corpo(
            "manter", cartoesGeradosAceitos=0, cartoesAguardandoRevisao=0, cartoesReferencia=0
        ),
    )

    assert resposta.status_code == 204
    assert (await estudante.get(f"/api/v1/fontes/{fonte['id']}")).status_code == 404
    # O job que ficou na fila termina sem efeito, sem erro.
    await executar_jobs(fila)


@pytest.mark.parametrize(
    "corpo",
    [
        {"impactoConfirmado": CONTAGENS},
        {"modoCartoes": None, "impactoConfirmado": CONTAGENS},
        {"modoCartoes": "apagar", "impactoConfirmado": CONTAGENS},
        {"modoCartoes": "manter"},
        {"modoCartoes": "manter", "impactoConfirmado": {"cartoesReferencia": 1}},
        {"modoCartoes": "manter", "impactoConfirmado": {**CONTAGENS, "cartoesAtivos": 1}},
        {"modoCartoes": "manter", "impactoConfirmado": CONTAGENS, "forcar": True},
    ],
    ids=[
        "sem-modo",
        "modo-nulo",
        "modo-invalido",
        "sem-impacto",
        "impacto-incompleto",
        "impacto-extra",
        "campo-extra",
    ],
)
async def test_sem_escolha_valida_nada_e_apagado(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteDeCartoesFalso,
    corpo: dict[str, Any],
) -> None:
    """A escolha é do estudante (Princípio III): sem `manter` ou `excluir`, é 422 e nada muda."""
    fonte, interno = await _fonte_concluida(acervo, estudante, fila, validos["resumo.txt"], cartoes)
    chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])

    resposta = await estudante.post(f"/api/v1/fontes/{fonte['id']}/exclusao", json=corpo)

    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "dados_invalidos"
    assert cartoes.modos == []
    assert await _armazenamento(acervo).existe(chave)
    assert (await contar_linhas_da_fonte(_fabrica(acervo), interno))[0] == 1


# --- CS-004: o que se vê é o que se apaga ------------------------------------------------------


@pytest.mark.parametrize("modo", ["manter", "excluir"])
async def test_cs004_contagens_exibidas_iguais_as_recebidas_e_ao_apagado(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteDeCartoesFalso,
    modo: str,
) -> None:
    fonte, interno = await _fonte_concluida(
        acervo, estudante, fila, validos["biologia-citologia.pdf"], cartoes
    )
    chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])
    total_trechos = (await consultar_fonte(estudante, fonte["id"]))["totalTrechos"]
    exibido = (await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")).json()[
        "contagens"
    ]
    assert total_trechos and total_trechos > 0

    with capture_logs() as registros:
        resposta = await estudante.post(
            f"/api/v1/fontes/{fonte['id']}/exclusao",
            json={"modoCartoes": modo, "impactoConfirmado": exibido},
        )

    assert resposta.status_code == 204
    apagado = cartoes.apagados[0]
    assert apagado["aguardando"] == exibido["cartoesAguardandoRevisao"]
    assert apagado["aceitos"] == (exibido["cartoesGeradosAceitos"] if modo == "excluir" else 0)
    assert cartoes.por_fonte[interno].referencia == exibido["cartoesReferencia"], "mantidos"
    assert not await _armazenamento(acervo).existe(chave)
    assert await contar_linhas_da_fonte(_fabrica(acervo), interno) == (0, 0)

    eventos = [r for r in registros if r["event"] == "fonte_excluida"]
    assert len(eventos) == 1
    assert eventos[0]["modo"] == modo
    assert eventos[0]["fonte_public_id"] == fonte["id"]
    assert "Citologia" not in str(registros) and "biologia-citologia" not in str(registros)
