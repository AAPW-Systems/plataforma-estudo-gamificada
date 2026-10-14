"""Segurança do acervo: isolamento, chave do objeto, logs e proteções herdadas (T021).

RQ-001 (o nome enviado nunca compõe a chave), RQ-002 (logs sem conteúdo) e RQ-003 (isolamento
entre estudantes, DTEC 019), com duas contas reais e o worker em processo.
"""

from __future__ import annotations

import io
import logging
import re
import sys
import tempfile
import uuid
from collections.abc import Iterator

import httpx
import pytest
import structlog
from fastapi import FastAPI
from procrastinate import App
from sqlalchemy import func, select

from app.fontes.modelos import Fonte
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from tests.apoio_acervo import (
    chave_da_fonte,
    consultar_fonte,
    criar_conta,
    criar_materia,
    enviar,
)
from tests.apoio_http import abrir_cliente, obter_csrf, sem_id_requisicao
from tests.conftest import executar_jobs
from tests.fabricas_arquivos import ArquivoGerado, validos
from tests.security.test_isolamento_rotas import CASOS_DE_ISOLAMENTO

pytestmark = pytest.mark.security

SENTINELA = "SENTINELA-DE-CONTEUDO-93517"
NOME_SECRETO = "relatorio-confidencial-xyz"


@pytest.fixture(scope="module")
def arquivo_com_sentinela() -> ArquivoGerado:
    texto = f"{SENTINELA}: o conteúdo do estudante não pode aparecer em log nenhum.\n"
    return ArquivoGerado(f"{NOME_SECRETO}.txt", texto.encode(), texto=texto)


@pytest.fixture(scope="module")
def pdf_simples() -> ArquivoGerado:
    return {a.nome: a for a in validos()}["pdf-uma-pagina.pdf"]


@pytest.fixture
def saida_de_logs(acervo: FastAPI) -> Iterator[io.StringIO]:
    """O texto que a aplicação realmente emite (depois do mascaramento), como JSON por linha."""
    raiz = logging.getLogger()
    formatador = next(
        h.formatter
        for h in raiz.handlers
        if isinstance(h.formatter, structlog.stdlib.ProcessorFormatter)
    )
    fluxo = io.StringIO()
    capturador = logging.StreamHandler(fluxo)
    capturador.setFormatter(formatador)
    raiz.addHandler(capturador)
    try:
        yield fluxo
    finally:
        raiz.removeHandler(capturador)


@pytest.fixture
async def ana(acervo: FastAPI, cliente_real: httpx.AsyncClient) -> httpx.AsyncClient:
    await criar_conta(cliente_real)
    return cliente_real


@pytest.fixture
async def bia(acervo: FastAPI) -> Iterator[httpx.AsyncClient]:  # type: ignore[misc]
    async with abrir_cliente(acervo, ip="198.51.100.91") as cliente_bia:
        await criar_conta(cliente_bia)
        yield cliente_bia


def _comparavel(resposta: httpx.Response) -> tuple[int, dict[str, object], dict[str, str]]:
    """Status, corpo sem `idRequisicao` e cabeçalhos sem o que varia por requisição."""
    cabecalhos = {
        k: v
        for k, v in resposta.headers.items()
        if k not in {"x-request-id", "date", "content-length"}
    }
    return resposta.status_code, sem_id_requisicao(resposta.json()), cabecalhos


async def _sao_identicas(de_outro: httpx.Response, inexistente: httpx.Response) -> None:
    assert de_outro.status_code == 404
    assert _comparavel(de_outro) == _comparavel(inexistente)
    assert de_outro.json()["codigo"] == "recurso_nao_encontrado"


# --- Isolamento: duas contas em cada rota com identificador (DTEC 019, RQ-003) ----------------


def test_a_tabela_de_isolamento_aponta_para_testes_que_existem() -> None:
    modulo = sys.modules[__name__]
    nomes = [n for chave, n in CASOS_DE_ISOLAMENTO.items() if chave[1].startswith("/api/v1/")]
    for nome in nomes:
        assert callable(getattr(modulo, nome, None)), f"{nome} não existe em {__name__}"


async def test_consulta_de_materia_de_outro_estudante_e_404(
    ana: httpx.AsyncClient, bia: httpx.AsyncClient
) -> None:
    materia = await criar_materia(ana, "Biologia da Ana")
    de_outro = await bia.get(f"/api/v1/materias/{materia['id']}")
    inexistente = await bia.get(f"/api/v1/materias/{uuid.uuid4()}")
    await _sao_identicas(de_outro, inexistente)
    assert "Ana" not in de_outro.text and materia["id"] not in de_outro.text
    assert (await bia.get("/api/v1/materias")).json() == {"itens": []}
    assert (await ana.get(f"/api/v1/materias/{materia['id']}")).status_code == 200


async def test_acervo_de_outro_estudante_e_404(
    ana: httpx.AsyncClient, bia: httpx.AsyncClient, pdf_simples: ArquivoGerado
) -> None:
    materia = await criar_materia(ana)
    await enviar(ana, materia["id"], pdf_simples, titulo="Segredo da Ana")
    de_outro = await bia.get(f"/api/v1/materias/{materia['id']}/fontes")
    inexistente = await bia.get(f"/api/v1/materias/{uuid.uuid4()}/fontes")
    await _sao_identicas(de_outro, inexistente)
    assert "Segredo da Ana" not in de_outro.text


async def test_envio_para_materia_de_outro_e_404(
    acervo: FastAPI, ana: httpx.AsyncClient, bia: httpx.AsyncClient, pdf_simples: ArquivoGerado
) -> None:
    materia = await criar_materia(ana)
    de_outro = await enviar(bia, materia["id"], pdf_simples)
    inexistente = await enviar(bia, str(uuid.uuid4()), pdf_simples)
    await _sao_identicas(de_outro, inexistente)
    assert acervo.state.armazenamento.objetos == {}, "nada foi guardado para a invasora"
    assert (await ana.get(f"/api/v1/materias/{materia['id']}/fontes")).json() == {"itens": []}


async def test_materia_de_outro_no_corpo_multipart_nao_vale(
    acervo: FastAPI, ana: httpx.AsyncClient, bia: httpx.AsyncClient, pdf_simples: ArquivoGerado
) -> None:
    """Só o `{materiaId}` do caminho decide; um `materiaId` no formulário é campo proibido."""
    da_ana = await criar_materia(ana)
    da_bia = await criar_materia(bia, "Da Bia")
    resposta = await bia.post(
        f"/api/v1/materias/{da_bia['id']}/fontes",
        files={"arquivo": (pdf_simples.nome, pdf_simples.conteudo, "application/pdf")},
        data={"materiaId": da_ana["id"]},
    )
    assert resposta.status_code == 422
    assert resposta.json()["campos"][0]["campo"] == "materiaId"
    assert acervo.state.armazenamento.objetos == {}
    assert (await ana.get(f"/api/v1/materias/{da_ana['id']}/fontes")).json() == {"itens": []}


async def test_consulta_de_fonte_de_outro_estudante_e_404(
    ana: httpx.AsyncClient, bia: httpx.AsyncClient, pdf_simples: ArquivoGerado
) -> None:
    materia = await criar_materia(ana)
    fonte = (await enviar(ana, materia["id"], pdf_simples, titulo="Segredo da Ana")).json()
    de_outro = await bia.get(f"/api/v1/fontes/{fonte['id']}")
    inexistente = await bia.get(f"/api/v1/fontes/{uuid.uuid4()}")
    await _sao_identicas(de_outro, inexistente)
    assert "Segredo da Ana" not in de_outro.text and fonte["id"] not in de_outro.text


async def test_reprocessar_fonte_de_outro_e_404(
    acervo: FastAPI,
    ana: httpx.AsyncClient,
    bia: httpx.AsyncClient,
    fila: App,
    pdf_simples: ArquivoGerado,
) -> None:
    materia = await criar_materia(ana)
    fonte = (await enviar(ana, materia["id"], pdf_simples)).json()
    await executar_jobs(fila)
    antes = await consultar_fonte(ana, fonte["id"])

    de_outro = await bia.post(f"/api/v1/fontes/{fonte['id']}/reprocessamento")
    inexistente = await bia.post(f"/api/v1/fontes/{uuid.uuid4()}/reprocessamento")

    await _sao_identicas(de_outro, inexistente)
    assert await consultar_fonte(ana, fonte["id"]) == antes, "a fonte da Ana não foi tocada"


async def test_impacto_de_exclusao_de_fonte_de_outro_e_404(
    acervo: FastAPI,
    ana: httpx.AsyncClient,
    bia: httpx.AsyncClient,
    fila: App,
    pdf_simples: ArquivoGerado,
) -> None:
    materia = await criar_materia(ana)
    fonte = (await enviar(ana, materia["id"], pdf_simples, titulo="Segredo da Ana")).json()
    await executar_jobs(fila)

    # A rota existe para o dono: sem isto, o 404 de "rota inexistente" passaria pelo teste.
    assert (await ana.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")).status_code == 200

    de_outro = await bia.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")
    inexistente = await bia.get(f"/api/v1/fontes/{uuid.uuid4()}/impacto-exclusao")

    await _sao_identicas(de_outro, inexistente)
    assert "Segredo da Ana" not in de_outro.text, "nem o título vaza"


async def test_exclusao_de_fonte_de_outro_e_404(
    acervo: FastAPI,
    ana: httpx.AsyncClient,
    bia: httpx.AsyncClient,
    fila: App,
    pdf_simples: ArquivoGerado,
) -> None:
    materia = await criar_materia(ana)
    fonte = (await enviar(ana, materia["id"], pdf_simples)).json()
    await executar_jobs(fila)
    antes = await consultar_fonte(ana, fonte["id"])
    corpo = {
        "modoCartoes": "excluir",
        "impactoConfirmado": {
            "cartoesGeradosAceitos": 0,
            "cartoesAguardandoRevisao": 0,
            "cartoesReferencia": 0,
        },
    }

    # A rota existe para o dono (corpo vazio: 422, nada é apagado); sem isto, o 404 de "rota
    # inexistente" passaria pelo teste.
    assert (await ana.post(f"/api/v1/fontes/{fonte['id']}/exclusao", json={})).status_code == 422

    de_outro = await bia.post(f"/api/v1/fontes/{fonte['id']}/exclusao", json=corpo)
    inexistente = await bia.post(f"/api/v1/fontes/{uuid.uuid4()}/exclusao", json=corpo)

    await _sao_identicas(de_outro, inexistente)
    assert await consultar_fonte(ana, fonte["id"]) == antes, "a fonte da Ana segue intacta"
    chave = await chave_da_fonte(acervo.state.fabrica_sessoes, fonte["id"])
    assert await acervo.state.armazenamento.existe(chave), "e o arquivo também"


async def test_identificador_malformado_tambem_e_404_em_toda_rota_com_identificador(
    ana: httpx.AsyncClient,
) -> None:
    """Um 422 aqui distinguiria 'formato errado' de 'inexistente'; os dois são 404."""
    existente = await ana.get(f"/api/v1/materias/{uuid.uuid4()}")
    for metodo, caminho in (
        ("GET", "/api/v1/materias/nao-e-uuid"),
        ("GET", "/api/v1/materias/nao-e-uuid/fontes"),
        ("GET", "/api/v1/fontes/123"),
        ("POST", "/api/v1/fontes/%00/reprocessamento"),
        ("GET", "/api/v1/fontes/" + "a" * 500),
    ):
        resposta = await ana.request(metodo, caminho)
        assert resposta.status_code == 404, (metodo, caminho)
        assert sem_id_requisicao(resposta.json()) == sem_id_requisicao(existente.json())


# --- Chave do objeto e nome do arquivo (RQ-001) -----------------------------------------------


async def test_chave_sem_nome_enviado(
    acervo: FastAPI, ana: httpx.AsyncClient, arquivo_com_sentinela: ArquivoGerado
) -> None:
    materia = await criar_materia(ana)
    perfil = (await ana.get("/api/v1/perfil")).json()
    assert perfil["email"]
    resposta = await enviar(ana, materia["id"], arquivo_com_sentinela)
    assert resposta.status_code == 201

    chaves = list(acervo.state.armazenamento.objetos)
    assert len(chaves) == 1
    padrao = re.compile(r"usuarios/[0-9a-f-]{36}/fontes/[0-9a-f-]{36}")
    assert padrao.fullmatch(chaves[0]), chaves[0]
    assert NOME_SECRETO not in chaves[0] and "txt" not in chaves[0]
    # O nome só é exibido, sem caminho nem controles.
    assert resposta.json()["nomeArquivo"] == f"{NOME_SECRETO}.txt"


async def test_chave_do_objeto_pertence_ao_prefixo_do_dono_e_a_api_nunca_a_expoe(
    acervo: FastAPI,
    ana: httpx.AsyncClient,
    fabrica_real: FabricaSessoes,
    arquivo_com_sentinela: ArquivoGerado,
) -> None:
    materia = await criar_materia(ana)
    fonte = (await enviar(ana, materia["id"], arquivo_com_sentinela)).json()
    async with unidade_de_trabalho(fabrica_real) as sessao:
        chave = (await sessao.execute(select(Fonte.chave_objeto))).scalar_one()
    corpos = [
        fonte,
        (await ana.get(f"/api/v1/fontes/{fonte['id']}")).json(),
        (await ana.get(f"/api/v1/materias/{materia['id']}/fontes")).json(),
    ]
    for corpo in corpos:
        assert chave not in str(corpo) and "usuarios/" not in str(corpo)
        assert "chave" not in str(corpo).lower() and "hash" not in str(corpo).lower()


# --- Logs sem conteúdo (RQ-002) ---------------------------------------------------------------


async def test_logs_sem_conteudo(
    acervo: FastAPI,
    ana: httpx.AsyncClient,
    fila: App,
    saida_de_logs: io.StringIO,
    arquivo_com_sentinela: ArquivoGerado,
    pdf_simples: ArquivoGerado,
) -> None:
    """Nem o texto dos trechos, nem o conteúdo, nem o nome do arquivo aparecem nos logs."""
    materia = await criar_materia(ana, "Matéria Reservada 7")
    enviada = (
        await enviar(ana, materia["id"], arquivo_com_sentinela, titulo="Título Reservado 9")
    ).json()
    recusada = await enviar(ana, materia["id"], (f"{NOME_SECRETO}-2.txt", b"abc\x00def"))
    assert recusada.status_code == 422
    await enviar(ana, materia["id"], pdf_simples)
    await executar_jobs(fila)
    await consultar_fonte(ana, enviada["id"])
    await ana.get(f"/api/v1/materias/{materia['id']}/fontes")

    saida = saida_de_logs.getvalue()
    for evento in (
        "fonte_recebida",
        "fonte_recusada",
        "processamento_iniciado",
        "processamento_concluido",
    ):
        assert evento in saida, f"evento esperado ausente: {evento}"
    for proibido in (
        SENTINELA,
        NOME_SECRETO,
        "o conteúdo do estudante",
        "Título Reservado 9",
        "Matéria Reservada 7",
        "Página 1, linha 1",
    ):
        assert proibido not in saida, f"vazou em log: {proibido!r}"


async def test_logs_da_falha_e_da_recusa_nao_trazem_caminho_nem_excecao_com_dados(
    acervo: FastAPI, ana: httpx.AsyncClient, fila: App, saida_de_logs: io.StringIO
) -> None:
    materia = await criar_materia(ana)
    corrompido = {
        a.nome: a for a in __import__("tests.fabricas_arquivos", fromlist=["x"]).invalidos()
    }["digitalizado.pdf"]
    await enviar(ana, materia["id"], corrompido)
    await executar_jobs(fila)
    saida = saida_de_logs.getvalue()
    assert "processamento_falhou" in saida and "sem_texto" in saida
    assert tempfile.gettempdir() not in saida and "Traceback" not in saida
    assert corrompido.nome not in saida


# --- Proteções herdadas nas rotas novas -------------------------------------------------------

ROTAS_NOVAS = [
    ("GET", "/api/v1/acervo/uso"),
    ("GET", "/api/v1/materias"),
    ("POST", "/api/v1/materias"),
    ("GET", "/api/v1/materias/{id}"),
    ("GET", "/api/v1/materias/{id}/fontes"),
    ("POST", "/api/v1/materias/{id}/fontes"),
    ("GET", "/api/v1/fontes/{id}"),
    ("POST", "/api/v1/fontes/{id}/reprocessamento"),
]


@pytest.mark.parametrize(("metodo", "caminho"), ROTAS_NOVAS)
async def test_sem_sessao_toda_rota_nova_responde_401_sem_dados(
    cliente_real: httpx.AsyncClient, metodo: str, caminho: str
) -> None:
    await obter_csrf(cliente_real)
    resposta = await cliente_real.request(
        metodo, caminho.replace("{id}", str(uuid.uuid4())), json={} if metodo == "POST" else None
    )
    assert resposta.status_code == 401
    assert set(resposta.json()) == {"codigo", "mensagem", "idRequisicao"}
    assert resposta.json()["codigo"] == "nao_autenticado"


@pytest.mark.parametrize(("metodo", "caminho"), [r for r in ROTAS_NOVAS if r[0] == "POST"])
async def test_sem_csrf_toda_rota_nova_que_altera_estado_responde_403(
    ana: httpx.AsyncClient, metodo: str, caminho: str
) -> None:
    resposta = await ana.request(
        metodo,
        caminho.replace("{id}", str(uuid.uuid4())),
        headers={"X-CSRF-Token": ""},
        json={"nome": "x"},
    )
    assert resposta.status_code == 403
    assert resposta.json()["codigo"] in {"csrf_invalido", "origem_nao_permitida"}


async def test_origem_estranha_nao_envia_fonte(
    acervo: FastAPI, ana: httpx.AsyncClient, pdf_simples: ArquivoGerado
) -> None:
    materia = await criar_materia(ana)
    resposta = await ana.post(
        f"/api/v1/materias/{materia['id']}/fontes",
        files={"arquivo": (pdf_simples.nome, pdf_simples.conteudo, "application/pdf")},
        headers={"Origin": "https://malvado.exemplo"},
    )
    assert resposta.status_code == 403
    assert acervo.state.armazenamento.objetos == {}


async def test_as_listagens_nao_ficam_em_cache(ana: httpx.AsyncClient) -> None:
    """DTEC 026: o acompanhamento por polling nunca recebe uma resposta velha do cache."""
    materia = await criar_materia(ana)
    for caminho in (
        "/api/v1/materias",
        f"/api/v1/materias/{materia['id']}/fontes",
        "/api/v1/acervo/uso",
    ):
        assert (await ana.get(caminho)).headers["cache-control"] == "no-store", caminho


async def test_a_resposta_de_erro_do_envio_nao_vaza_caminho_nem_pilha(
    acervo: FastAPI, ana: httpx.AsyncClient
) -> None:
    materia = await criar_materia(ana)
    for conteudo in (b"%PDF-1.7\n" + b"\x00" * 50, b"\xff\xfe\x00\x00lixo", b"PK\x03\x04zip"):
        for nome in ("a.pdf", "a.txt"):
            resposta = await enviar(ana, materia["id"], (nome, conteudo))
            texto = resposta.text
            assert "Traceback" not in texto and tempfile.gettempdir() not in texto
            assert 'File "' not in texto
            assert "pymupdf" not in texto.lower() and "mupdf" not in texto.lower()
    contagem = await _contar_fontes(acervo.state.fabrica_sessoes)
    assert contagem == 0


async def _contar_fontes(fabrica: FabricaSessoes) -> int:
    async with unidade_de_trabalho(fabrica) as sessao:
        return int((await sessao.execute(select(func.count()).select_from(Fonte))).scalar_one())
