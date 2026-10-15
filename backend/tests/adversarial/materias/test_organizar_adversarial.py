"""Organizar sob concorrência e sob falhas: renomear e excluir a matéria (T041; DTEC 031, CB-16).

Usam conexões reais (`acervo`): as corridas precisam de transações de verdade. Cada teste cita a
mutação que o faz falhar sem a defesa que ele verifica (sem o `FOR UPDATE` nas fontes, sem o
recálculo do impacto, sem o objeto apagado antes das linhas, sem a compensação do envio, sem a
conferência do nome, sem a conferência da fonte pelo worker).
"""

from __future__ import annotations

import asyncio
import unicodedata
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from procrastinate import App
from sqlalchemy import text

from app.fontes.registros import participante_fontes
from app.fontes.tarefas import DependenciasTarefas, ResultadoProcessamento, executar_processar_fonte
from app.nucleo.armazenamento import Armazenamento, prefixo_usuario
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.isolamento import ResultadoIsolado, executar_isolado
from app.nucleo.participantes_acervo import ContagensAcervo, registro_acervo
from tests import fabricas_arquivos as fab
from tests.apoio_acervo import (
    chave_da_fonte,
    contar_linhas_da_materia,
    criar_conta,
    criar_materia,
    enviar,
    id_interno_da_fonte,
    id_interno_da_materia,
    trechos_da_fonte,
)
from tests.conftest import executar_jobs
from tests.fabricas_arquivos import ArquivoGerado
from tests.participantes_falsos import ParticipanteFalso

pytestmark = pytest.mark.adversarial

IMPACTO = {"fontes": 1, "cartoesAtivos": 4, "cartoesAguardandoRevisao": 2}


@pytest.fixture(scope="module")
def validos() -> dict[str, ArquivoGerado]:
    return {a.nome: a for a in fab.validos()}


@pytest.fixture
def cartoes() -> Iterator[ParticipanteFalso]:
    participante = ParticipanteFalso(nome="cartoes_falso")
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


async def _materia_com_fonte(
    app: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App | None,
    cartoes: ParticipanteFalso | None,
    arquivo: ArquivoGerado,
    nome: str = "Biologia",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    materia = await criar_materia(estudante, nome)
    fonte = (await enviar(estudante, materia["id"], arquivo, titulo="Citologia")).json()
    if fila is not None:
        await executar_jobs(fila)
    interno = await id_interno_da_materia(_fabrica(app), materia["id"])
    if cartoes is not None:
        cartoes.por_materia[interno] = ContagensAcervo(
            cartoes_ativos=3, cartoes_suspensos=1, cartoes_aguardando_revisao=2
        )
    return materia, fonte, interno


def _corpo(nome: str = "Biologia", **contagens: int) -> dict[str, Any]:
    return {"nomeConfirmacao": nome, "impactoConfirmado": {**IMPACTO, **contagens}}


# --- Exclusão da matéria durante um envio -------------------------------------------------------


class ArmazenamentoQueParaDepoisDeGravar:
    """Delega ao armazenamento real; depois de gravar um objeto, para até ser liberado."""

    def __init__(self, real: Armazenamento) -> None:
        self._real = real
        self.gravado = asyncio.Event()
        self.liberar = asyncio.Event()

    async def gravar(self, chave: str, origem: Path) -> None:
        await self._real.gravar(chave, origem)
        self.gravado.set()
        await self.liberar.wait()

    async def ler_para_arquivo(self, chave: str, destino: Path) -> None:
        await self._real.ler_para_arquivo(chave, destino)

    async def apagar(self, chave: str) -> bool:
        return await self._real.apagar(chave)

    async def apagar_prefixo(self, prefixo: str) -> int:
        return await self._real.apagar_prefixo(prefixo)

    async def listar_prefixo(self, prefixo: str) -> Any:
        return await self._real.listar_prefixo(prefixo)

    async def existe(self, chave: str) -> bool:
        return await self._real.existe(chave)


async def test_excluir_a_materia_durante_um_envio_da_404_e_o_objeto_e_compensado(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    validos: dict[str, ArquivoGerado],
) -> None:
    """O objeto já está gravado quando a matéria some: o envio responde 404 e apaga o objeto."""
    materia = await criar_materia(estudante)
    interno = await id_interno_da_materia(_fabrica(acervo), materia["id"])
    real = _armazenamento(acervo)
    parado = ArmazenamentoQueParaDepoisDeGravar(real)
    acervo.state.fontes._armazenamento = parado
    try:
        envio = asyncio.create_task(enviar(estudante, materia["id"], validos["resumo.txt"]))
        await asyncio.wait_for(parado.gravado.wait(), 30)

        exclusao = await estudante.post(
            f"/api/v1/materias/{materia['id']}/exclusao",
            json=_corpo(fontes=0, cartoesAtivos=0, cartoesAguardandoRevisao=0),
        )
        assert exclusao.status_code == 204, "a matéria ainda não tinha fontes: a exclusão passa"
        parado.liberar.set()
        resposta = await asyncio.wait_for(envio, 30)
    finally:
        parado.liberar.set()
        acervo.state.fontes._armazenamento = real

    assert resposta.status_code == 404 and resposta.json()["codigo"] == "recurso_nao_encontrado"
    assert await contar_linhas_da_materia(_fabrica(acervo), interno) == (0, 0, 0)
    async with unidade_de_trabalho(_fabrica(acervo)) as sessao:
        assert (await sessao.execute(text("select count(*) from fontes"))).scalar_one() == 0
        assert (
            await sessao.execute(text("select count(*) from procrastinate_jobs"))
        ).scalar_one() == 0, "nenhum job ficou para uma fonte que não existe"
    async with unidade_de_trabalho(_fabrica(acervo)) as sessao:
        dono = (await sessao.execute(text("select public_id from usuarios"))).scalar_one()
    assert await real.listar_prefixo(prefixo_usuario(str(dono))) == [], (
        "o objeto gravado foi compensado (DTEC 025)"
    )


# --- Exclusão com fonte em processamento (RF-013, CB-16) ---------------------------------------


async def test_excluir_a_materia_durante_a_extracao_nao_deixa_trecho_nenhum(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteFalso,
) -> None:
    materia, fonte, interno = await _materia_com_fonte(
        acervo, estudante, None, cartoes, validos["biologia-citologia.pdf"]
    )
    interno_fonte = await id_interno_da_fonte(_fabrica(acervo), fonte["id"])
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
    tarefa = asyncio.create_task(
        executar_processar_fonte(
            interno_fonte, deps, ultima_tentativa=False, executor=executor_parado
        )
    )
    try:
        await asyncio.wait_for(extraindo.wait(), 30)
        exibido = (await estudante.get(f"/api/v1/materias/{materia['id']}/impacto-exclusao")).json()
        assert exibido["contagens"]["fontes"] == 1

        exclusao = await estudante.post(
            f"/api/v1/materias/{materia['id']}/exclusao",
            json={"nomeConfirmacao": "Biologia", "impactoConfirmado": exibido["contagens"]},
        )
        assert exclusao.status_code == 204, "a exclusão não espera o worker (DTEC 031)"
        liberar.set()
        resultado = await asyncio.wait_for(tarefa, 60)
    finally:
        liberar.set()
        if not tarefa.done():
            tarefa.cancel()
        await asyncio.gather(tarefa, return_exceptions=True)

    assert resultado is ResultadoProcessamento.SEM_EFEITO
    assert await contar_linhas_da_materia(_fabrica(acervo), interno) == (0, 0, 0)
    assert await trechos_da_fonte(_fabrica(acervo), fonte["id"]) == []
    assert not await _armazenamento(acervo).existe(chave)


# --- Impacto alterado entre a consulta e a confirmação ------------------------------------------


@pytest.mark.parametrize(
    "mudanca",
    [
        ("cartoes_ativos", 4),
        ("cartoes_ativos", 2),
        ("cartoes_suspensos", 0),
        ("cartoes_suspensos", 2),
        ("cartoes_aguardando_revisao", 3),
        ("cartoes_aguardando_revisao", 0),
    ],
    ids=[
        "ativo-novo",
        "ativo-a-menos",
        "suspenso-reativado",
        "suspenso-novo",
        "geracao-terminou",
        "recusado-em-outra-aba",
    ],
)
async def test_impacto_alterado_devolve_409_e_nao_apaga_nada(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteFalso,
    mudanca: tuple[str, int],
) -> None:
    materia, fonte, interno = await _materia_com_fonte(
        acervo, estudante, fila, cartoes, validos["biologia-citologia.pdf"]
    )
    chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])
    linhas = await contar_linhas_da_materia(_fabrica(acervo), interno)
    exibido = (await estudante.get(f"/api/v1/materias/{materia['id']}/impacto-exclusao")).json()
    assert exibido["contagens"] == IMPACTO

    # Em outra aba, as contagens mudam depois de o diálogo ser aberto.
    campo, valor = mudanca
    atual = cartoes.por_materia[interno]
    cartoes.por_materia[interno] = _com(atual, campo, valor)

    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/exclusao",
        json={"nomeConfirmacao": "Biologia", "impactoConfirmado": exibido["contagens"]},
    )

    assert resposta.status_code == 409
    assert resposta.json()["codigo"] == "impacto_alterado"
    assert cartoes.exclusoes_de_materia == [], "nenhum participante foi chamado"
    assert await _armazenamento(acervo).existe(chave), "o arquivo segue lá"
    assert await contar_linhas_da_materia(_fabrica(acervo), interno) == linhas

    # A interface consulta de novo e o estudante confirma o que passou a ver.
    novo = (await estudante.get(f"/api/v1/materias/{materia['id']}/impacto-exclusao")).json()
    assert novo["contagens"] != exibido["contagens"]
    ok = await estudante.post(
        f"/api/v1/materias/{materia['id']}/exclusao",
        json={"nomeConfirmacao": "Biologia", "impactoConfirmado": novo["contagens"]},
    )
    assert ok.status_code == 204
    assert len(cartoes.exclusoes_de_materia) == 1


def _com(atual: ContagensAcervo, campo: str, valor: int) -> ContagensAcervo:
    campos = {c: getattr(atual, c) for c in atual.__dataclass_fields__}
    campos[campo] = valor
    return ContagensAcervo(**campos)


async def test_fonte_nova_entre_a_consulta_e_a_confirmacao_e_conflito(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteFalso,
) -> None:
    """A contagem de fontes também é conferida: ninguém apaga uma fonte que não viu listada."""
    materia, _, interno = await _materia_com_fonte(
        acervo, estudante, fila, cartoes, validos["biologia-citologia.pdf"]
    )
    exibido = (await estudante.get(f"/api/v1/materias/{materia['id']}/impacto-exclusao")).json()
    assert (await enviar(estudante, materia["id"], validos["resumo.txt"])).status_code == 201

    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/exclusao",
        json={"nomeConfirmacao": "Biologia", "impactoConfirmado": exibido["contagens"]},
    )

    assert resposta.status_code == 409 and resposta.json()["codigo"] == "impacto_alterado"
    assert (await contar_linhas_da_materia(_fabrica(acervo), interno))[1] == 2


async def test_confirmar_contagens_inventadas_e_conflito_e_nada_e_apagado(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteFalso,
) -> None:
    """Um cliente que não consultou o impacto não consegue apagar com zeros no chute."""
    materia, _, interno = await _materia_com_fonte(
        acervo, estudante, fila, cartoes, validos["resumo.txt"]
    )

    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/exclusao",
        json=_corpo(fontes=0, cartoesAtivos=0, cartoesAguardandoRevisao=0),
    )

    assert resposta.status_code == 409 and resposta.json()["codigo"] == "impacto_alterado"
    assert (await contar_linhas_da_materia(_fabrica(acervo), interno))[:2] == (1, 1)
    assert cartoes.exclusoes_de_materia == []


async def test_a_fonte_travada_por_outra_transacao_faz_a_exclusao_esperar_e_recalcular(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteFalso,
) -> None:
    """A exclusão trava as fontes antes de contar (DTEC 031).

    Uma transação que publica cartões segura a fonte (`FOR SHARE`, DTEC 031/043). A exclusão
    espera por ela e só então recalcula: com os cartões novos, o impacto confirmado já não vale.
    Sem o `FOR UPDATE` nas fontes, a exclusão contaria antes e daria 204 com o número velho.
    """
    materia, fonte, interno = await _materia_com_fonte(
        acervo, estudante, fila, cartoes, validos["biologia-citologia.pdf"]
    )
    interno_fonte = await id_interno_da_fonte(_fabrica(acervo), fonte["id"])
    exibido = (await estudante.get(f"/api/v1/materias/{materia['id']}/impacto-exclusao")).json()
    publicadora = _fabrica(acervo)()
    exclusao: asyncio.Task[httpx.Response] | None = None
    try:
        await publicadora.execute(
            text("SELECT id FROM fontes WHERE id = :id FOR SHARE"), {"id": interno_fonte}
        )
        exclusao = asyncio.create_task(
            estudante.post(
                f"/api/v1/materias/{materia['id']}/exclusao",
                json={"nomeConfirmacao": "Biologia", "impactoConfirmado": exibido["contagens"]},
            )
        )
        await asyncio.sleep(0.5)
        assert not exclusao.done(), "a exclusão espera a transação que segura a fonte"

        # A publicação termina: dois cartões ativos novos, e a transação libera a fonte.
        cartoes.por_materia[interno] = _com(cartoes.por_materia[interno], "cartoes_ativos", 5)
        await publicadora.commit()
        resposta = await asyncio.wait_for(exclusao, 30)
    finally:
        await publicadora.close()
        if exclusao is not None and not exclusao.done():
            exclusao.cancel()

    assert resposta.status_code == 409 and resposta.json()["codigo"] == "impacto_alterado"
    assert (await contar_linhas_da_materia(_fabrica(acervo), interno))[:2] == (1, 1)
    assert cartoes.exclusoes_de_materia == []


# --- Duas exclusões paralelas -------------------------------------------------------------------


async def test_duas_exclusoes_paralelas_resultam_em_um_204_e_um_404(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteFalso,
) -> None:
    materia, _, interno = await _materia_com_fonte(
        acervo, estudante, fila, cartoes, validos["resumo.txt"]
    )
    cartoes.atraso_s = 0.3  # alarga a janela: a segunda chega enquanto a primeira ainda trava
    url = f"/api/v1/materias/{materia['id']}/exclusao"
    corpo = _corpo(fontes=1)

    respostas = await asyncio.gather(
        estudante.post(url, json=corpo), estudante.post(url, json=corpo)
    )

    assert sorted(r.status_code for r in respostas) == [204, 404]
    assert len(cartoes.exclusoes_de_materia) == 1, "os cartões foram tratados uma única vez"
    assert await contar_linhas_da_materia(_fabrica(acervo), interno) == (0, 0, 0)


async def test_excluir_a_materia_e_uma_fonte_dela_ao_mesmo_tempo_nao_trava_nem_sobra_nada(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteFalso,
) -> None:
    """Sem *deadlock*: cada caminho trava na mesma ordem (matéria, fontes por id)."""
    materia, fonte, interno = await _materia_com_fonte(
        acervo, estudante, fila, cartoes, validos["resumo.txt"]
    )
    corpo_fonte = {
        "modoCartoes": "manter",
        "impactoConfirmado": {
            "cartoesGeradosAceitos": 0,
            "cartoesAguardandoRevisao": 0,
            "cartoesReferencia": 0,
        },
    }

    respostas = await asyncio.wait_for(
        asyncio.gather(
            estudante.post(f"/api/v1/fontes/{fonte['id']}/exclusao", json=corpo_fonte),
            estudante.post(f"/api/v1/materias/{materia['id']}/exclusao", json=_corpo(fontes=1)),
        ),
        60,
    )

    por_rota = [r.status_code for r in respostas]
    assert por_rota[0] in {204, 404} and por_rota[1] in {204, 409, 404}, por_rota
    assert 204 in por_rota
    # Seja qual for a ordem, a matéria excluída não deixa fonte nem trecho.
    if por_rota[1] == 204:
        assert await contar_linhas_da_materia(_fabrica(acervo), interno) == (0, 0, 0)


# --- Falha do armazenamento ao apagar um objeto (DTEC 025) --------------------------------------


class ArmazenamentoQueNaoApaga(ArmazenamentoQueParaDepoisDeGravar):
    """Delega tudo ao real, mas `apagar` falha enquanto `falhando` for verdadeiro."""

    def __init__(self, real: Armazenamento) -> None:
        super().__init__(real)
        self.falhando = True

    async def gravar(self, chave: str, origem: Path) -> None:
        await self._real.gravar(chave, origem)

    async def apagar(self, chave: str) -> bool:
        if self.falhando:
            raise OSError("volume indisponível (detalhe interno)")
        return await self._real.apagar(chave)


async def test_falha_do_armazenamento_desfaz_tudo_e_a_nova_tentativa_funciona(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteFalso,
) -> None:
    materia, fonte, interno = await _materia_com_fonte(
        acervo, estudante, fila, cartoes, validos["biologia-citologia.pdf"]
    )
    chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])
    linhas = await contar_linhas_da_materia(_fabrica(acervo), interno)
    real = _armazenamento(acervo)
    quebrado = ArmazenamentoQueNaoApaga(real)
    anterior = participante_fontes.armazenamento
    participante_fontes.armazenamento = quebrado
    try:
        falha = await estudante.post(f"/api/v1/materias/{materia['id']}/exclusao", json=_corpo())

        assert falha.status_code == 500 and falha.json()["codigo"] == "erro_interno"
        assert "volume" not in falha.text and chave not in falha.text, "sem detalhe interno"
        assert await real.existe(chave)
        assert await contar_linhas_da_materia(_fabrica(acervo), interno) == linhas
        assert (await estudante.get(f"/api/v1/materias/{materia['id']}")).status_code == 200

        quebrado.falhando = False
        ok = await estudante.post(f"/api/v1/materias/{materia['id']}/exclusao", json=_corpo())
    finally:
        participante_fontes.armazenamento = anterior

    assert ok.status_code == 204
    assert not await real.existe(chave)
    assert await contar_linhas_da_materia(_fabrica(acervo), interno) == (0, 0, 0)


async def test_falha_de_um_participante_desfaz_a_exclusao_inteira(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    cartoes: ParticipanteFalso,
) -> None:
    """Um participante que levanta no meio: nada é apagado (uma única transação)."""
    materia, fonte, interno = await _materia_com_fonte(
        acervo, estudante, fila, cartoes, validos["resumo.txt"]
    )

    class Quebrado(ParticipanteFalso):
        async def ao_excluir_materia(self, sessao: Any, usuario_id: int, materia_id: int) -> None:
            await super().ao_excluir_materia(sessao, usuario_id, materia_id)
            raise RuntimeError("falha simulada (detalhe interno)")

    registro_acervo.registrar(150, "quebrado", Quebrado(nome="quebrado"))
    try:
        falha = await estudante.post(
            f"/api/v1/materias/{materia['id']}/exclusao", json=_corpo(fontes=1)
        )
    finally:
        registro_acervo.remover("quebrado")

    assert falha.status_code == 500 and "simulada" not in falha.text
    assert (await contar_linhas_da_materia(_fabrica(acervo), interno))[:2] == (1, 1)
    chave = await chave_da_fonte(_fabrica(acervo), fonte["id"])
    assert await _armazenamento(acervo).existe(chave), "o objeto também permanece"


# --- Renomeações concorrentes -------------------------------------------------------------------


async def test_duas_renomeacoes_para_o_mesmo_nome_uma_e_recusada(
    acervo: FastAPI, estudante: httpx.AsyncClient
) -> None:
    primeira = await criar_materia(estudante, "Biologia")
    segunda = await criar_materia(estudante, "Química")

    respostas = await asyncio.gather(
        estudante.patch(f"/api/v1/materias/{primeira['id']}", json={"nome": "Genética"}),
        estudante.patch(f"/api/v1/materias/{segunda['id']}", json={"nome": "GENÉTICA"}),
    )

    assert sorted(r.status_code for r in respostas) == [200, 409]
    recusada = next(r for r in respostas if r.status_code == 409)
    assert recusada.json()["codigo"] == "materia_nome_em_uso"
    nomes = sorted(m["nome"] for m in (await estudante.get("/api/v1/materias")).json()["itens"])
    assert len({n.lower() for n in nomes}) == 2, "os dois nomes seguem distintos"


async def test_renomear_e_criar_com_o_mesmo_nome_ao_mesmo_tempo_uma_e_recusada(
    acervo: FastAPI, estudante: httpx.AsyncClient
) -> None:
    existente = await criar_materia(estudante, "Biologia")

    respostas = await asyncio.gather(
        estudante.patch(f"/api/v1/materias/{existente['id']}", json={"nome": "Genética"}),
        estudante.post("/api/v1/materias", json={"nome": "genética"}),
    )

    assert sorted(r.status_code for r in respostas) in ([200, 409], [201, 409])
    nomes = [m["nome"].lower() for m in (await estudante.get("/api/v1/materias")).json()["itens"]]
    assert len(nomes) == len(set(nomes))


# --- Confirmação pelo nome: caixa, espaços e normalização --------------------------------------


@pytest.mark.parametrize(
    ("digitado", "aceito"),
    [
        ("Biologia Celular", True),
        ("  Biologia Celular  ", True),
        ("\tBiologia Celular\n", True),
        ("biologia celular", False),
        ("BIOLOGIA CELULAR", False),
        ("Biologia  Celular", False),
        ("Biologia", False),
        ("Biologia Celular 2", False),
        ("Química", False),
        ("Biologia Celulár", False),
    ],
    ids=[
        "exato",
        "espacos-nas-pontas",
        "tab-e-quebra-nas-pontas",
        "minusculas",
        "maiusculas",
        "espaco-duplo-no-meio",
        "parcial",
        "com-sufixo",
        "outra-materia",
        "letra-diferente",
    ],
)
async def test_so_a_caixa_e_o_meio_diferentes_recusam_a_confirmacao(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    cartoes: ParticipanteFalso,
    digitado: str,
    aceito: bool,
) -> None:
    materia = await criar_materia(estudante, "Biologia Celular")
    await criar_materia(estudante, "Química")
    zeros = {"fontes": 0, "cartoesAtivos": 0, "cartoesAguardandoRevisao": 0}

    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/exclusao",
        json={"nomeConfirmacao": digitado, "impactoConfirmado": zeros},
    )

    if aceito:
        assert resposta.status_code == 204
    else:
        assert resposta.status_code == 422, resposta.text
        assert resposta.json()["codigo"] == "confirmacao_invalida"
        assert (await estudante.get(f"/api/v1/materias/{materia['id']}")).status_code == 200


async def test_o_nome_decomposto_confere_com_o_nome_composto(
    acervo: FastAPI, estudante: httpx.AsyncClient
) -> None:
    """NFC dos dois lados: o teclado pode entregar o acento separado da letra."""
    materia = await criar_materia(estudante, "Química")
    zeros = {"fontes": 0, "cartoesAtivos": 0, "cartoesAguardandoRevisao": 0}
    decomposto = unicodedata.normalize("NFD", "Química")
    assert decomposto != "Química"

    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/exclusao",
        json={"nomeConfirmacao": decomposto, "impactoConfirmado": zeros},
    )

    assert resposta.status_code == 204


@pytest.mark.parametrize(
    "corpo",
    [
        {},
        {"nomeConfirmacao": "Biologia"},
        {"impactoConfirmado": {"fontes": 0, "cartoesAtivos": 0, "cartoesAguardandoRevisao": 0}},
        {
            "nomeConfirmacao": "Biologia",
            "impactoConfirmado": {"fontes": "0", "cartoesAtivos": 0, "cartoesAguardandoRevisao": 0},
        },
        {
            "nomeConfirmacao": "Biologia",
            "impactoConfirmado": {"fontes": -1, "cartoesAtivos": 0, "cartoesAguardandoRevisao": 0},
        },
        {
            "nomeConfirmacao": "Biologia",
            "impactoConfirmado": {"fontes": 0, "cartoesAtivos": 0, "cartoesAguardandoRevisao": 0},
            "extra": 1,
        },
        {
            "nomeConfirmacao": 123,
            "impactoConfirmado": {"fontes": 0, "cartoesAtivos": 0, "cartoesAguardandoRevisao": 0},
        },
    ],
    ids=[
        "vazio",
        "sem-impacto",
        "sem-nome",
        "contagem-texto",
        "contagem-negativa",
        "extra",
        "nome-numero",
    ],
)
async def test_corpo_malformado_da_exclusao_e_422_e_nada_e_apagado(
    acervo: FastAPI, estudante: httpx.AsyncClient, corpo: dict[str, Any]
) -> None:
    materia = await criar_materia(estudante, "Biologia")
    resposta = await estudante.post(f"/api/v1/materias/{materia['id']}/exclusao", json=corpo)
    assert resposta.status_code == 422 and resposta.json()["codigo"] == "dados_invalidos"
    assert (await estudante.get(f"/api/v1/materias/{materia['id']}")).status_code == 200
