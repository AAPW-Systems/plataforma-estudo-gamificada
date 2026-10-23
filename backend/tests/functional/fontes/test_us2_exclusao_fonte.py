"""US2: excluir uma fonte e decidir sobre os cartões, cenários 1 a 6 (T033; CS-004).

Os cartões gerados (004) ainda não existem: um participante falso com estado em memória faz o
papel deles (DTEC 027). Os cartões criados pelo estudante (003) são reais: a última seção
reexecuta a exclusão com o participante real (T011 da 003). API e worker rodam em processo,
sobre o mesmo banco e armazenamento.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from procrastinate import App
from sqlalchemy import select
from structlog.testing import capture_logs

from app.cartoes.modelos import SituacaoCartao
from app.fontes.modelos import Fonte
from app.nucleo.armazenamento import Armazenamento
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
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
    id_interno_da_materia,
)
from tests.apoio_cartoes import criar_cartao
from tests.conftest import executar_jobs
from tests.fabricas_arquivos import ArquivoGerado
from tests.fabricas_cartoes import ReferenciaFonte, cartao_ficticio
from tests.fabricas_cartoes import inserir as inserir_cartoes
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


# --- T011 (spec 003): a mesma exclusão com cartões reais, sem o participante falso ---------------
#
# O participante falso acima faz o papel dos cartões gerados (004); aqui o participante real dos
# cartões criados pelo estudante (003) responde pelas contagens de referência (DTEC 027, D-006).


async def _fonte_com_cartoes_reais(
    app: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    arquivo: ArquivoGerado,
    *,
    referencias: int = 2,
    soltos: int = 1,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    materia = await criar_materia(estudante)
    fonte = (await enviar(estudante, materia["id"], arquivo, titulo="Citologia")).json()
    await executar_jobs(fila)
    citando = [
        (
            await criar_cartao(estudante, materia["id"], frente=f"Cita {n}", fonteId=fonte["id"])
        ).json()
        for n in range(referencias)
    ]
    for n in range(soltos):
        await criar_cartao(estudante, materia["id"], frente=f"Solto {n}")
    return fonte, materia, citando


async def _cartoes_da_lista(estudante: httpx.AsyncClient, materia_id: str) -> list[dict[str, Any]]:
    lista = (await estudante.get(f"/api/v1/materias/{materia_id}/cartoes")).json()
    itens: list[dict[str, Any]] = lista["itens"]
    return itens


async def test_impacto_conta_os_cartoes_de_referencia_reais(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
) -> None:
    fonte, _, _ = await _fonte_com_cartoes_reais(acervo, estudante, fila, validos["resumo.txt"])

    resposta = await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")

    assert resposta.json()["contagens"] == {
        "cartoesGeradosAceitos": 0,
        "cartoesAguardandoRevisao": 0,
        "cartoesReferencia": 2,
    }


@pytest.mark.parametrize("modo", ["manter", "excluir"])
async def test_excluir_a_fonte_mantem_os_cartoes_de_referencia_com_fonte_apagada(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    modo: str,
) -> None:
    """US2-5 e D-006/D-009: nos dois modos os cartões do estudante ficam, com a cópia intacta."""
    fonte, materia, citando = await _fonte_com_cartoes_reais(
        acervo, estudante, fila, validos["biologia-citologia.pdf"]
    )
    chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])
    interno = await id_interno_da_fonte(_fabrica(acervo), fonte["id"])
    exibido = (await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")).json()

    resposta = await estudante.post(
        f"/api/v1/fontes/{fonte['id']}/exclusao",
        json={"modoCartoes": modo, "impactoConfirmado": exibido["contagens"]},
    )

    assert resposta.status_code == 204
    assert not await _armazenamento(acervo).existe(chave)
    assert await contar_linhas_da_fonte(_fabrica(acervo), interno) == (0, 0)
    cartoes = await _cartoes_da_lista(estudante, materia["id"])
    assert len(cartoes) == 3, "nenhum cartão foi apagado"
    por_id = {c["id"]: c for c in cartoes}
    for original in citando:
        atual = por_id[original["id"]]
        assert atual["origem"] == "criado" and atual["verificado"] is False
        assert atual["frente"] == original["frente"]
        assert atual["referencia"] == {
            "fonteId": None,
            "titulo": "Citologia",
            "nomeArquivo": "biologia-citologia.pdf",
            "enviadaEm": original["referencia"]["enviadaEm"],
            "fonteApagada": True,
        }
    soltos = [c for c in cartoes if c["referencia"] is None]
    assert [c["frente"] for c in soltos] == ["Solto 0"]


async def test_cs004_contagem_de_referencia_exibida_e_a_marcada_e_o_log_nao_traz_texto(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
) -> None:
    fonte, materia, _ = await _fonte_com_cartoes_reais(
        acervo, estudante, fila, validos["resumo.txt"], referencias=3
    )
    exibido = (await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")).json()

    with capture_logs() as registros:
        resposta = await estudante.post(
            f"/api/v1/fontes/{fonte['id']}/exclusao",
            json={"modoCartoes": "excluir", "impactoConfirmado": exibido["contagens"]},
        )

    assert resposta.status_code == 204
    marcados = [c for c in await _cartoes_da_lista(estudante, materia["id"]) if c["referencia"]]
    assert len(marcados) == exibido["contagens"]["cartoesReferencia"] == 3
    assert all(c["referencia"]["fonteApagada"] for c in marcados)
    eventos = [r for r in registros if r["event"] == "cartoes_referencia_marcados"]
    assert [e["quantidade"] for e in eventos] == [3]
    assert "Citologia" not in str(registros) and "Cita 0" not in str(registros)


async def test_cartao_suspenso_que_cita_a_fonte_tambem_conta_e_e_mantido(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
) -> None:
    fonte, materia, _ = await _fonte_com_cartoes_reais(
        acervo, estudante, fila, validos["resumo.txt"], referencias=1, soltos=0
    )
    interno = await id_interno_da_fonte(_fabrica(acervo), fonte["id"])
    interno_materia = await id_interno_da_materia(_fabrica(acervo), materia["id"])
    async with unidade_de_trabalho(_fabrica(acervo)) as sessao:
        usuario_id = (
            await sessao.execute(select(Fonte.usuario_id).where(Fonte.id == interno))
        ).scalar_one()
        await inserir_cartoes(
            sessao,
            usuario_id=usuario_id,
            materia_id=interno_materia,
            itens=[cartao_ficticio(situacao=SituacaoCartao.SUSPENSO, com_referencia=True)],
            agora=datetime.now(UTC),
            fonte=ReferenciaFonte(interno, "Resumo", "resumo.txt", datetime.now(UTC)),
        )

    exibido = (await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")).json()
    assert exibido["contagens"]["cartoesReferencia"] == 2

    assert (
        await estudante.post(
            f"/api/v1/fontes/{fonte['id']}/exclusao",
            json={"modoCartoes": "excluir", "impactoConfirmado": exibido["contagens"]},
        )
    ).status_code == 204
    cartoes = await _cartoes_da_lista(estudante, materia["id"])
    assert sorted(c["situacao"] for c in cartoes) == ["ativo", "suspenso"]
    assert all(c["referencia"]["fonteApagada"] for c in cartoes)


async def test_cartao_criado_depois_de_ver_o_impacto_faz_a_exclusao_pedir_nova_confirmacao(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
) -> None:
    """DTEC 031: o servidor recalcula; contagem velha responde `409 impacto_alterado`."""
    fonte, materia, _ = await _fonte_com_cartoes_reais(
        acervo, estudante, fila, validos["resumo.txt"]
    )
    visto = (await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")).json()
    await criar_cartao(estudante, materia["id"], frente="Outro", fonteId=fonte["id"])
    chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])

    resposta = await estudante.post(
        f"/api/v1/fontes/{fonte['id']}/exclusao",
        json={"modoCartoes": "manter", "impactoConfirmado": visto["contagens"]},
    )

    assert resposta.status_code == 409 and resposta.json()["codigo"] == "impacto_alterado"
    assert await _armazenamento(acervo).existe(chave), "nada foi apagado"
    assert (await consultar_fonte(estudante, fonte["id"]))["estado"] == "concluido"
    ainda_citam = [c for c in await _cartoes_da_lista(estudante, materia["id"]) if c["referencia"]]
    assert all(not c["referencia"]["fonteApagada"] for c in ainda_citam)
    novo = (await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")).json()
    assert novo["contagens"]["cartoesReferencia"] == 3


async def test_consultar_o_impacto_varias_vezes_nao_mexe_nos_cartoes(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
) -> None:
    fonte, materia, _ = await _fonte_com_cartoes_reais(
        acervo, estudante, fila, validos["resumo.txt"]
    )
    antes = await _cartoes_da_lista(estudante, materia["id"])
    for _ in range(3):
        assert (
            await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")
        ).status_code == 200
    assert await _cartoes_da_lista(estudante, materia["id"]) == antes
