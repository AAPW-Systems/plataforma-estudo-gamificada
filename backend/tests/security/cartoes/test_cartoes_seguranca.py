"""Segurança dos cartões na US1: isolamento, propriedade, logs e proteções herdadas (T012).

RQ-002 (isolamento entre estudantes, DTEC 019 e 035) e a privacidade do texto do estudante nos
logs (data-model, "Privacidade"), com duas contas reais.
"""

from __future__ import annotations

import importlib
import io
import logging
import pkgutil
import uuid
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import structlog
from fastapi import FastAPI

from tests.apoio_acervo import criar_conta, criar_materia, enviar
from tests.apoio_cartoes import criar_cartao
from tests.apoio_http import abrir_cliente, obter_csrf, sem_id_requisicao
from tests.fabricas_arquivos import ArquivoGerado, validos
from tests.security.test_isolamento_rotas import CASOS_DE_ISOLAMENTO

pytestmark = pytest.mark.security

SENTINELA = "SENTINELA-DE-CARTAO-48213"


@pytest.fixture(scope="module")
def resumo() -> ArquivoGerado:
    return {a.nome: a for a in validos()}["resumo.txt"]


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
async def bia(acervo: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with abrir_cliente(acervo, ip="198.51.100.92") as cliente_bia:
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


# --- Isolamento: duas contas em cada rota com identificador (DTEC 019, RQ-002) ---------------


def test_a_tabela_de_isolamento_aponta_para_testes_que_existem() -> None:
    """Os casos das rotas de cartões ficam nos módulos de `tests/security/cartoes/`."""
    import tests.security.cartoes as pacote

    modulos = [
        importlib.import_module(f"{pacote.__name__}.{info.name}")
        for info in pkgutil.iter_modules(pacote.__path__)
    ]
    nomes = [n for chave, n in CASOS_DE_ISOLAMENTO.items() if "/cartoes" in chave[1]]
    assert nomes, "nenhuma rota de cartões na tabela de isolamento"
    for nome in nomes:
        assert any(callable(getattr(m, nome, None)) for m in modulos), (
            f"{nome} não existe em tests/security/cartoes/"
        )


async def test_lista_de_cartoes_de_outro_e_404(
    ana: httpx.AsyncClient, bia: httpx.AsyncClient
) -> None:
    materia = await criar_materia(ana, "Biologia da Ana")
    await criar_cartao(ana, materia["id"], frente=f"Segredo da Ana {SENTINELA}")
    # A rota existe para o dono: sem isto, o 404 de "rota inexistente" passaria pelo teste.
    assert (await ana.get(f"/api/v1/materias/{materia['id']}/cartoes")).json()["total"] == 1

    de_outro = await bia.get(f"/api/v1/materias/{materia['id']}/cartoes")
    inexistente = await bia.get(f"/api/v1/materias/{uuid.uuid4()}/cartoes")

    await _sao_identicas(de_outro, inexistente)
    assert SENTINELA not in de_outro.text and materia["id"] not in de_outro.text


async def test_criar_cartao_em_materia_de_outro_e_404(
    ana: httpx.AsyncClient, bia: httpx.AsyncClient
) -> None:
    materia = await criar_materia(ana, "Biologia da Ana")

    de_outro = await criar_cartao(bia, materia["id"], frente=f"Invasão {SENTINELA}")
    inexistente = await criar_cartao(bia, str(uuid.uuid4()), frente=f"Invasão {SENTINELA}")

    await _sao_identicas(de_outro, inexistente)
    assert (await ana.get(f"/api/v1/materias/{materia['id']}/cartoes")).json()["total"] == 0
    # A rota existe para a dona.
    assert (await criar_cartao(ana, materia["id"])).status_code == 201


async def test_cursor_de_outra_conta_nao_serve_e_nao_revela_nada(
    ana: httpx.AsyncClient, bia: httpx.AsyncClient
) -> None:
    da_ana = await criar_materia(ana)
    da_bia = await criar_materia(bia)
    for numero in range(5):
        await criar_cartao(ana, da_ana["id"], frente=f"Da Ana {numero}")
        await criar_cartao(bia, da_bia["id"], frente=f"Da Bia {numero}")
    pagina = (await ana.get(f"/api/v1/materias/{da_ana['id']}/cartoes?limite=2")).json()
    assert pagina["proximoCursor"]

    # O cursor da Ana usado pela Bia, na matéria da Bia e na da Ana.
    na_propria = await bia.get(
        f"/api/v1/materias/{da_bia['id']}/cartoes?cursor={pagina['proximoCursor']}"
    )
    na_da_ana = await bia.get(
        f"/api/v1/materias/{da_ana['id']}/cartoes?cursor={pagina['proximoCursor']}"
    )

    assert na_propria.status_code == 422 and na_propria.json()["codigo"] == "cursor_invalido"
    assert na_da_ana.status_code == 404, "a matéria alheia continua sendo 404, com ou sem cursor"
    assert "Da Ana" not in na_propria.text + na_da_ana.text


async def test_identificador_malformado_tambem_e_404_nas_rotas_de_cartoes(
    ana: httpx.AsyncClient,
) -> None:
    """Um 422 aqui distinguiria 'formato errado' de 'inexistente'; os dois são 404."""
    existente = await ana.get(f"/api/v1/materias/{uuid.uuid4()}/cartoes")
    for metodo, caminho in (
        ("GET", "/api/v1/materias/nao-e-uuid/cartoes"),
        ("GET", "/api/v1/materias/" + "a" * 500 + "/cartoes"),
        ("POST", "/api/v1/materias/%00/cartoes"),
    ):
        resposta = await ana.request(
            metodo, caminho, json={"frente": "f", "verso": "v"} if metodo == "POST" else None
        )
        assert resposta.status_code == 404, (metodo, caminho)
        assert sem_id_requisicao(resposta.json()) == sem_id_requisicao(existente.json())


# --- Propriedade da fonte de referência (DTEC 035) --------------------------------------------


async def test_fonte_alheia_de_outra_materia_ou_inexistente_dao_o_mesmo_422(
    ana: httpx.AsyncClient, bia: httpx.AsyncClient, resumo: ArquivoGerado
) -> None:
    """Os três casos são indistinguíveis: a API não confirma que a fonte de outro existe."""
    da_ana = await criar_materia(ana, "Biologia")
    outra_da_ana = await criar_materia(ana, "Química")
    fonte_da_ana = (await enviar(ana, da_ana["id"], resumo, titulo=f"Título {SENTINELA}")).json()
    da_bia = await criar_materia(bia, "Biologia")
    fonte_da_bia_em_outra = (
        await enviar(bia, (await criar_materia(bia, "Química"))["id"], resumo, titulo="Da Bia")
    ).json()

    # 1) fonte de outro estudante; 2) fonte do mesmo estudante em outra matéria; 3) inexistente.
    alheia = await criar_cartao(bia, da_bia["id"], fonteId=fonte_da_ana["id"])
    de_outra_materia = await criar_cartao(bia, da_bia["id"], fonteId=fonte_da_bia_em_outra["id"])
    inexistente = await criar_cartao(bia, da_bia["id"], fonteId=str(uuid.uuid4()))
    # E a fonte da Ana citada na matéria errada da própria Ana.
    na_materia_errada = await criar_cartao(ana, outra_da_ana["id"], fonteId=fonte_da_ana["id"])

    for resposta in (alheia, de_outra_materia, inexistente, na_materia_errada):
        assert resposta.status_code == 422
        assert resposta.json()["campos"] == [
            {"campo": "fonteId", "mensagem": "Escolha uma fonte desta matéria."}
        ]
        assert SENTINELA not in resposta.text and "Da Bia" not in resposta.text
    assert (
        _comparavel(alheia)[1:] == _comparavel(inexistente)[1:] == _comparavel(de_outra_materia)[1:]
    )
    for cliente, materia in ((bia, da_bia), (ana, outra_da_ana)):
        assert (await cliente.get(f"/api/v1/materias/{materia['id']}/cartoes")).json()["total"] == 0


async def test_cartao_de_referencia_nao_expoe_dados_internos_da_fonte(
    ana: httpx.AsyncClient, resumo: ArquivoGerado
) -> None:
    materia = await criar_materia(ana)
    fonte = (await enviar(ana, materia["id"], resumo)).json()
    cartao = (await criar_cartao(ana, materia["id"], fonteId=fonte["id"])).json()
    texto = str(cartao).lower()
    assert "usuarios/" not in texto and "chave" not in texto and "hash" not in texto
    assert set(cartao["referencia"]) == {
        "fonteId",
        "titulo",
        "nomeArquivo",
        "enviadaEm",
        "fonteApagada",
    }


# --- Logs sem conteúdo (data-model, "Privacidade") --------------------------------------------


async def test_logs_sem_frente_verso_explicacao_nem_titulo_da_referencia(
    ana: httpx.AsyncClient, saida_de_logs: io.StringIO, resumo: ArquivoGerado
) -> None:
    materia = await criar_materia(ana, "Matéria Reservada 3")
    fonte = (
        await enviar(ana, materia["id"], resumo, titulo=f"Título Reservado {SENTINELA}")
    ).json()
    criado = await criar_cartao(
        ana,
        materia["id"],
        frente=f"Frente {SENTINELA}",
        verso=f"Verso {SENTINELA}",
        explicacao=f"Explicação {SENTINELA}",
        fonteId=fonte["id"],
    )
    assert criado.status_code == 201
    # Falhas também não podem vazar: texto acima do limite, vazio, fonte inválida e cursor ruim.
    await criar_cartao(ana, materia["id"], frente=f"{SENTINELA} " * 400)
    await criar_cartao(ana, materia["id"], frente="   ", verso=f"Verso {SENTINELA}")
    await criar_cartao(ana, materia["id"], frente=f"Frente {SENTINELA}", fonteId=str(uuid.uuid4()))
    await ana.get(f"/api/v1/materias/{materia['id']}/cartoes?cursor=cursor-inventado")
    await ana.get(f"/api/v1/materias/{materia['id']}/cartoes")

    saida = saida_de_logs.getvalue()
    assert "cartao_criado" in saida, "o evento esperado do plano está ausente"
    for proibido in (SENTINELA, "Título Reservado", "Matéria Reservada 3", "resumo.txt"):
        assert proibido not in saida, f"vazou em log: {proibido!r}"
    assert "Traceback" not in saida


async def test_log_de_criacao_traz_so_identificadores_e_se_ha_referencia(
    ana: httpx.AsyncClient, resumo: ArquivoGerado
) -> None:
    from structlog.testing import capture_logs

    materia = await criar_materia(ana)
    fonte = (await enviar(ana, materia["id"], resumo)).json()
    with capture_logs() as registros:
        com = (await criar_cartao(ana, materia["id"], fonteId=fonte["id"])).json()
        sem = (await criar_cartao(ana, materia["id"])).json()

    eventos = [r for r in registros if r["event"] == "cartao_criado"]
    assert [e["com_referencia"] for e in eventos] == [True, False]
    assert [e["cartao_public_id"] for e in eventos] == [com["id"], sem["id"]]
    for evento in eventos:
        assert set(evento) <= {
            "event",
            "log_level",
            "cartao_public_id",
            "usuario_public_id",
            "materia_public_id",
            "com_referencia",
        }, evento
        uuid.UUID(evento["usuario_public_id"])


# --- Proteções herdadas nas rotas novas ---------------------------------------------------------

ROTAS = [
    ("GET", "/api/v1/cartoes/limites"),
    ("GET", "/api/v1/materias/{id}/cartoes"),
    ("POST", "/api/v1/materias/{id}/cartoes"),
]


@pytest.mark.parametrize(("metodo", "caminho"), ROTAS)
async def test_sem_sessao_toda_rota_de_cartoes_responde_401_sem_dados(
    cliente_real: httpx.AsyncClient, metodo: str, caminho: str
) -> None:
    await obter_csrf(cliente_real)
    resposta = await cliente_real.request(
        metodo,
        caminho.replace("{id}", str(uuid.uuid4())),
        json={"frente": "f", "verso": "v"} if metodo != "GET" else None,
    )
    assert resposta.status_code == 401
    assert set(resposta.json()) == {"codigo", "mensagem", "idRequisicao"}
    assert resposta.json()["codigo"] == "nao_autenticado"


@pytest.mark.parametrize(("metodo", "caminho"), [r for r in ROTAS if r[0] != "GET"])
async def test_sem_csrf_toda_rota_de_cartoes_que_altera_estado_responde_403(
    ana: httpx.AsyncClient, metodo: str, caminho: str
) -> None:
    materia = await criar_materia(ana)
    resposta = await ana.request(
        metodo,
        caminho.replace("{id}", materia["id"]),
        headers={"X-CSRF-Token": ""},
        json={"frente": "f", "verso": "v"},
    )
    assert resposta.status_code == 403
    assert resposta.json()["codigo"] == "csrf_invalido"
    assert (await ana.get(f"/api/v1/materias/{materia['id']}/cartoes")).json()["total"] == 0


async def test_origem_estranha_nao_cria_cartao(ana: httpx.AsyncClient) -> None:
    materia = await criar_materia(ana)
    resposta = await ana.post(
        f"/api/v1/materias/{materia['id']}/cartoes",
        json={"frente": "f", "verso": "v"},
        headers={"Origin": "https://malvado.exemplo"},
    )
    assert resposta.status_code == 403
    assert resposta.json()["codigo"] == "origem_nao_permitida"
    assert (await ana.get(f"/api/v1/materias/{materia['id']}/cartoes")).json()["total"] == 0


async def test_as_leituras_de_cartoes_nao_ficam_em_cache(ana: httpx.AsyncClient) -> None:
    materia = await criar_materia(ana)
    for caminho in ("/api/v1/cartoes/limites", f"/api/v1/materias/{materia['id']}/cartoes"):
        assert (await ana.get(caminho)).headers["cache-control"] == "no-store", caminho
    criado = await criar_cartao(ana, materia["id"])
    assert criado.headers["cache-control"] == "no-store"
