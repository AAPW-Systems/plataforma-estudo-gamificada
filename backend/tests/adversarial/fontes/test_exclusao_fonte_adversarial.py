"""Exclusão de fonte sob concorrência e sob falhas (T034; DTEC 031, CB-16, RF-013, CS-004).

Usam conexões reais (`acervo`): as corridas precisam de transações de verdade. Cada teste
tem uma mutação que o faz falhar sem a defesa que ele verifica (registradas no relatório da
sessão): sem o `FOR UPDATE`, sem o recálculo do impacto, sem apagar o objeto antes das linhas
ou sem que o worker confira a fonte na transação B.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from procrastinate import App

from app.fontes.tarefas import DependenciasTarefas, ResultadoProcessamento, executar_processar_fonte
from app.nucleo.armazenamento import Armazenamento
from app.nucleo.banco import FabricaSessoes
from app.nucleo.isolamento import ResultadoIsolado, executar_isolado
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
    trechos_da_fonte,
)
from tests.conftest import executar_jobs
from tests.fabricas_arquivos import ArquivoGerado
from tests.participantes_falsos import ParticipanteDeCartoesFalso

pytestmark = pytest.mark.adversarial

CONTAGENS = {"cartoesGeradosAceitos": 3, "cartoesAguardandoRevisao": 2, "cartoesReferencia": 1}


@pytest.fixture(scope="module")
def validos() -> dict[str, ArquivoGerado]:
    return {a.nome: a for a in fab.validos()}


@pytest.fixture
def cartoes() -> Iterator[ParticipanteDeCartoesFalso]:
    participante = ParticipanteDeCartoesFalso()
    registro_acervo.registrar(100, "cartoes_falso", participante)
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


async def _fonte(
    app: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App | None,
    arquivo: ArquivoGerado,
    cartoes: ParticipanteDeCartoesFalso | None = None,
) -> tuple[dict[str, Any], int]:
    materia = await criar_materia(estudante)
    fonte = (await enviar(estudante, materia["id"], arquivo, titulo="Citologia")).json()
    if fila is not None:
        await executar_jobs(fila)
    interno = await id_interno_da_fonte(_fabrica(app), fonte["id"])
    if cartoes is not None:
        cartoes.definir(interno, aceitos=3, aguardando=2, referencia=1)
    return fonte, interno


def _corpo(modo: str = "manter", **contagens: int) -> dict[str, Any]:
    return {"modoCartoes": modo, "impactoConfirmado": {**CONTAGENS, **contagens}}


# --- Exclusão durante o processamento (RF-013, CB-16) ------------------------------------------


async def test_excluir_durante_a_extracao_nao_deixa_trecho_nenhum(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    validos: dict[str, ArquivoGerado],
) -> None:
    """O worker já marcou `processando` e está extraindo quando a fonte é excluída."""
    fonte, interno = await _fonte(acervo, estudante, None, validos["biologia-citologia.pdf"])
    chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])
    extraindo = asyncio.Event()
    liberar = asyncio.Event()

    async def executor_parado(*args: Any, **kwargs: Any) -> ResultadoIsolado:
        extraindo.set()
        await liberar.wait()
        return await executar_isolado(*args, **kwargs)

    deps = DependenciasTarefas(
        fabrica=_fabrica(acervo),
        armazenamento=_armazenamento(acervo),
        configuracao=acervo.state.configuracao,
    )
    # O objeto é lido antes de o executor parar: o worker já tem o arquivo temporário.
    tarefa = asyncio.create_task(
        executar_processar_fonte(interno, deps, ultima_tentativa=False, executor=executor_parado)
    )
    try:
        await asyncio.wait_for(extraindo.wait(), 30)
        assert (await consultar_fonte(estudante, fonte["id"]))["estado"] == "processando"

        exclusao = await estudante.post(
            f"/api/v1/fontes/{fonte['id']}/exclusao",
            json=_corpo(cartoesGeradosAceitos=0, cartoesAguardandoRevisao=0, cartoesReferencia=0),
        )
        assert exclusao.status_code == 204, "a exclusão não espera o worker (DTEC 031)"
        liberar.set()
        resultado = await asyncio.wait_for(tarefa, 60)
    finally:
        liberar.set()  # nunca deixa a tarefa parada, mesmo que uma asserção acima falhe
        if not tarefa.done():
            tarefa.cancel()
        await asyncio.gather(tarefa, return_exceptions=True)

    assert resultado is ResultadoProcessamento.SEM_EFEITO
    assert await contar_linhas_da_fonte(_fabrica(acervo), interno) == (0, 0)
    assert await trechos_da_fonte(_fabrica(acervo), fonte["id"]) == []
    assert not await _armazenamento(acervo).existe(chave)


async def test_job_que_sobrou_na_fila_termina_sem_efeito_e_sem_erro(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
) -> None:
    fonte, interno = await _fonte(acervo, estudante, None, validos["resumo.txt"])  # ainda na fila
    exclusao = await estudante.post(
        f"/api/v1/fontes/{fonte['id']}/exclusao",
        json=_corpo(cartoesGeradosAceitos=0, cartoesAguardandoRevisao=0, cartoesReferencia=0),
    )
    assert exclusao.status_code == 204

    await executar_jobs(fila)  # roda o job órfão: não pode levantar nem recriar nada

    assert await contar_linhas_da_fonte(_fabrica(acervo), interno) == (0, 0)


# --- Impacto alterado entre a consulta e a confirmação (DTEC 031) ------------------------------


@pytest.mark.parametrize(
    "mudanca",
    [
        {"aceitos": 4},
        {"aceitos": 2},
        {"aguardando": 3},
        {"aguardando": 1},
        {"referencia": 2},
        {"referencia": 0},
    ],
    ids=[
        "aceito-novo",
        "aceito-a-menos",
        "geracao-terminou",
        "recusado-em-outra-aba",
        "novo-manual",
        "referencia-saiu",
    ],
)
async def test_impacto_alterado_devolve_409_e_nao_apaga_nada(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteDeCartoesFalso,
    mudanca: dict[str, int],
) -> None:
    fonte, interno = await _fonte(
        acervo, estudante, fila, validos["biologia-citologia.pdf"], cartoes
    )
    chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])
    linhas = await contar_linhas_da_fonte(_fabrica(acervo), interno)
    exibido = (await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")).json()
    assert exibido["contagens"] == CONTAGENS

    # Em outra aba, as contagens mudam depois de o diálogo ser aberto.
    atual = cartoes.por_fonte[interno]
    for campo, valor in mudanca.items():
        setattr(atual, campo, valor)

    resposta = await estudante.post(
        f"/api/v1/fontes/{fonte['id']}/exclusao",
        json={"modoCartoes": "excluir", "impactoConfirmado": exibido["contagens"]},
    )

    assert resposta.status_code == 409
    assert resposta.json()["codigo"] == "impacto_alterado"
    assert cartoes.modos == [], "nenhum participante foi chamado"
    assert await _armazenamento(acervo).existe(chave), "o arquivo segue lá"
    assert await contar_linhas_da_fonte(_fabrica(acervo), interno) == linhas
    assert (await consultar_fonte(estudante, fonte["id"]))["estado"] == "concluido"

    # A interface consulta de novo e o estudante confirma o que passou a ver.
    novo = (await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")).json()
    assert novo["contagens"] != exibido["contagens"]
    ok = await estudante.post(
        f"/api/v1/fontes/{fonte['id']}/exclusao",
        json={"modoCartoes": "excluir", "impactoConfirmado": novo["contagens"]},
    )
    assert ok.status_code == 204
    assert cartoes.modos == [ModoCartoes.EXCLUIR]


async def test_confirmar_contagens_inventadas_e_conflito_e_nada_e_apagado(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteDeCartoesFalso,
) -> None:
    """Um cliente que não consultou o impacto não consegue apagar com zeros no chute."""
    fonte, interno = await _fonte(acervo, estudante, fila, validos["resumo.txt"], cartoes)

    resposta = await estudante.post(
        f"/api/v1/fontes/{fonte['id']}/exclusao",
        json=_corpo(
            "excluir", cartoesGeradosAceitos=0, cartoesAguardandoRevisao=0, cartoesReferencia=0
        ),
    )

    assert resposta.status_code == 409 and resposta.json()["codigo"] == "impacto_alterado"
    assert (await contar_linhas_da_fonte(_fabrica(acervo), interno))[0] == 1
    assert cartoes.por_fonte[interno].aceitos == 3


# --- Duas exclusões paralelas ------------------------------------------------------------------


async def test_duas_exclusoes_paralelas_resultam_em_um_204_e_um_404(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteDeCartoesFalso,
) -> None:
    fonte, interno = await _fonte(acervo, estudante, fila, validos["resumo.txt"], cartoes)
    cartoes.atraso_s = 0.3  # alarga a janela: a segunda chega enquanto a primeira ainda trava
    url = f"/api/v1/fontes/{fonte['id']}/exclusao"

    respostas = await asyncio.gather(
        estudante.post(url, json=_corpo("excluir")), estudante.post(url, json=_corpo("excluir"))
    )

    assert sorted(r.status_code for r in respostas) == [204, 404]
    assert cartoes.modos == [ModoCartoes.EXCLUIR], "os cartões foram tratados uma única vez"
    assert await contar_linhas_da_fonte(_fabrica(acervo), interno) == (0, 0)


async def test_excluir_de_novo_depois_de_excluida_e_404(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteDeCartoesFalso,
) -> None:
    fonte, _ = await _fonte(acervo, estudante, fila, validos["resumo.txt"], cartoes)
    url = f"/api/v1/fontes/{fonte['id']}/exclusao"
    assert (await estudante.post(url, json=_corpo())).status_code == 204
    repetida = await estudante.post(url, json=_corpo())
    assert repetida.status_code == 404
    assert (
        await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")
    ).status_code == 404


# --- Falha do armazenamento ao apagar o objeto (DTEC 025) -------------------------------------


class ArmazenamentoQueNaoApaga:
    """Delega tudo ao armazenamento real, mas `apagar` falha enquanto `falhando` for verdadeiro."""

    def __init__(self, real: Armazenamento) -> None:
        self._real = real
        self.falhando = True

    async def gravar(self, chave: str, origem: Path) -> None:
        await self._real.gravar(chave, origem)

    async def ler_para_arquivo(self, chave: str, destino: Path) -> None:
        await self._real.ler_para_arquivo(chave, destino)

    async def apagar(self, chave: str) -> bool:
        if self.falhando:
            raise OSError("volume indisponível (detalhe interno)")
        return await self._real.apagar(chave)

    async def apagar_prefixo(self, prefixo: str) -> int:
        return await self._real.apagar_prefixo(prefixo)

    async def listar_prefixo(self, prefixo: str) -> Any:
        return await self._real.listar_prefixo(prefixo)

    async def existe(self, chave: str) -> bool:
        return await self._real.existe(chave)


async def test_falha_do_armazenamento_desfaz_tudo_e_a_nova_tentativa_funciona(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteDeCartoesFalso,
) -> None:
    fonte, interno = await _fonte(
        acervo, estudante, fila, validos["biologia-citologia.pdf"], cartoes
    )
    chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])
    linhas = await contar_linhas_da_fonte(_fabrica(acervo), interno)
    real = _armazenamento(acervo)
    quebrado = ArmazenamentoQueNaoApaga(real)
    acervo.state.fontes._armazenamento = quebrado
    try:
        falha = await estudante.post(
            f"/api/v1/fontes/{fonte['id']}/exclusao", json=_corpo("excluir")
        )

        assert falha.status_code == 500
        assert falha.json()["codigo"] == "erro_interno"
        assert "volume" not in falha.text and chave not in falha.text, "sem detalhe interno"
        assert cartoes.modos == [], "os cartões não foram tocados"
        assert cartoes.por_fonte[interno].aceitos == 3
        assert await real.existe(chave)
        assert await contar_linhas_da_fonte(_fabrica(acervo), interno) == linhas
        assert (await consultar_fonte(estudante, fonte["id"]))["estado"] == "concluido"

        quebrado.falhando = False
        ok = await estudante.post(f"/api/v1/fontes/{fonte['id']}/exclusao", json=_corpo("excluir"))
    finally:
        acervo.state.fontes._armazenamento = real

    assert ok.status_code == 204
    assert cartoes.modos == [ModoCartoes.EXCLUIR]
    assert not await real.existe(chave)
    assert await contar_linhas_da_fonte(_fabrica(acervo), interno) == (0, 0)
