"""Envio de fontes sob entradas hostis e sob concorrência (T022; CB-04, CB-15, RF-008, RF-012).

Os testes de concorrência usam conexões reais (`acervo`) e clientes já com o token anti-CSRF,
para que as requisições saiam de fato juntas; cada um tem uma mutação que o faz falhar sem a
trava ou o índice que ele verifica (registradas no relatório da sessão).
"""

from __future__ import annotations

import asyncio
import gc
import json
import os
import tempfile
import uuid
from collections.abc import AsyncIterator, MutableMapping
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from procrastinate import App
from sqlalchemy import func, select

from app.fontes.modelos import Fonte
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from tests import fabricas_arquivos as fab
from tests.apoio_acervo import (
    ajustar_limites,
    chave_da_fonte,
    consultar_fonte,
    criar_conta,
    criar_materia,
    enviar,
    trechos_da_fonte,
)
from tests.apoio_http import COOKIE_CSRF, COOKIE_SESSAO, ORIGEM
from tests.conftest import executar_jobs
from tests.fabricas_arquivos import ArquivoGerado

pytestmark = pytest.mark.adversarial


@pytest.fixture(scope="module")
def validos() -> dict[str, ArquivoGerado]:
    return {a.nome: a for a in fab.validos()}


@pytest.fixture(scope="module")
def adversariais() -> dict[str, ArquivoGerado]:
    return {a.nome: a for a in fab.adversariais()}


@pytest.fixture
async def estudante(acervo: FastAPI, cliente_real: httpx.AsyncClient) -> httpx.AsyncClient:
    await criar_conta(cliente_real)
    return cliente_real


def _fabrica(app: FastAPI) -> FabricaSessoes:
    fabrica: FabricaSessoes = app.state.fabrica_sessoes
    return fabrica


async def _contar_fontes(fabrica: FabricaSessoes) -> int:
    async with unidade_de_trabalho(fabrica) as sessao:
        return int((await sessao.execute(select(func.count()).select_from(Fonte))).scalar_one())


# --- Arquivos disfarçados ---------------------------------------------------------------------


async def test_disfarcados_zip_com_extensao_md_e_pdf_com_extensao_txt(
    estudante: httpx.AsyncClient,
    acervo: FastAPI,
    adversariais: dict[str, ArquivoGerado],
    validos: dict[str, ArquivoGerado],
) -> None:
    materia = await criar_materia(estudante)
    pdf_como_txt = ("relatorio.txt", validos["pdf-uma-pagina.pdf"].conteudo)
    texto_como_pdf = ("relatorio.pdf", validos["resumo.txt"].conteudo)
    for arquivo in (adversariais["zip-como-md.md"], pdf_como_txt, texto_como_pdf):
        resposta = await enviar(estudante, materia["id"], arquivo)
        assert resposta.status_code == 422, resposta.text
        assert resposta.json()["codigo"] == "tipo_divergente"
    assert acervo.state.armazenamento.objetos == {}
    assert await _contar_fontes(_fabrica(acervo)) == 0


async def test_o_tipo_gravado_vem_do_conteudo_e_nao_do_cabecalho_do_navegador(
    estudante: httpx.AsyncClient, validos: dict[str, ArquivoGerado]
) -> None:
    materia = await criar_materia(estudante)
    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/fontes",
        files={"arquivo": ("aula.txt", validos["resumo.txt"].conteudo, "application/pdf")},
    )
    assert resposta.status_code == 201
    assert resposta.json()["tipoMidia"] == "text/plain"
    mentirosa = await estudante.post(
        f"/api/v1/materias/{materia['id']}/fontes",
        files={"arquivo": ("aula.pdf", validos["pdf-uma-pagina.pdf"].conteudo, "text/plain")},
    )
    assert mentirosa.status_code == 201
    assert mentirosa.json()["tipoMidia"] == "application/pdf"


# --- Corpo acima do limite (413) --------------------------------------------------------------


def _multipart(nome: str, conteudo: bytes, fronteira: str = "FRONTEIRA-DE-TESTE") -> bytes:
    cabecalho = (
        f'--{fronteira}\r\nContent-Disposition: form-data; name="arquivo"; filename="{nome}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode()
    return cabecalho + conteudo + f"\r\n--{fronteira}--\r\n".encode()


async def test_corpo_acima_do_limite_pelo_content_length_vira_413_sem_ler_o_corpo(
    estudante: httpx.AsyncClient, acervo: FastAPI
) -> None:
    materia = await criar_materia(estudante)
    corpo = _multipart("grande.txt", b"a" * (2 * 1024 * 1024 + 70 * 1024))
    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/fontes",
        content=corpo,
        headers={"Content-Type": "multipart/form-data; boundary=FRONTEIRA-DE-TESTE"},
    )
    assert resposta.status_code == 413
    assert resposta.json()["codigo"] == "arquivo_muito_grande"
    assert "2 MB" in resposta.json()["mensagem"]
    assert acervo.state.armazenamento.objetos == {}


async def test_corpo_acima_do_limite_sem_content_length_tambem_vira_413(
    estudante: httpx.AsyncClient, acervo: FastAPI
) -> None:
    materia = await criar_materia(estudante)
    corpo = _multipart("grande.txt", b"a" * (2 * 1024 * 1024 + 70 * 1024))

    async def em_blocos() -> AsyncIterator[bytes]:
        for inicio in range(0, len(corpo), 64 * 1024):
            yield corpo[inicio : inicio + 64 * 1024]

    pedido = estudante.build_request(
        "POST",
        f"/api/v1/materias/{materia['id']}/fontes",
        content=em_blocos(),
        headers={"Content-Type": "multipart/form-data; boundary=FRONTEIRA-DE-TESTE"},
    )
    assert "content-length" not in pedido.headers
    resposta = await estudante.send(pedido)
    assert resposta.status_code == 413
    assert resposta.json()["codigo"] == "arquivo_muito_grande"
    assert acervo.state.armazenamento.objetos == {}


async def test_arquivo_um_byte_acima_do_limite_cabe_no_corpo_mas_e_413_no_arquivo(
    estudante: httpx.AsyncClient, acervo: FastAPI
) -> None:
    """A sobrecarga do multipart (64 KiB) deixa o corpo passar; o tamanho do arquivo decide."""
    materia = await criar_materia(estudante)
    limite = 2 * 1024 * 1024
    no_limite = await enviar(estudante, materia["id"], ("exato.txt", b"a" * limite))
    assert no_limite.status_code == 201
    acima = await enviar(estudante, materia["id"], ("acima.txt", b"b" * (limite + 1)))
    assert acima.status_code == 413
    assert acima.json()["codigo"] == "arquivo_muito_grande"
    assert len(acervo.state.armazenamento.objetos) == 1


# --- Nomes maliciosos (RQ-001) ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("enviado", "exibido"),
    [
        ("../../etc/passwd.txt", "passwd.txt"),
        ("..\\..\\Windows\\sistema.txt", "sistema.txt"),
        ("C:\\Users\\Ana\\notas.txt", "notas.txt"),
        ("/absoluto/raiz.txt", "raiz.txt"),
        ("a\u202etxt.exe.txt", "atxt.exe.txt"),
        (("x" * 300) + ".txt", "x" * 251 + ".txt"),
    ],
)
async def test_nomes_maliciosos_sao_so_exibidos_e_nunca_viram_caminho(
    estudante: httpx.AsyncClient,
    acervo: FastAPI,
    fabrica_real: FabricaSessoes,
    enviado: str,
    exibido: str,
) -> None:
    materia = await criar_materia(estudante)
    resposta = await enviar(estudante, materia["id"], (enviado, b"Texto qualquer do estudante.\n"))
    assert resposta.status_code == 201, resposta.text
    nome = resposta.json()["nomeArquivo"]
    assert nome == exibido
    assert "/" not in nome and "\\" not in nome and "\x00" not in nome and "\u202e" not in nome
    chave = await chave_da_fonte(fabrica_real, resposta.json()["id"])
    assert chave in acervo.state.armazenamento.objetos
    assert ".." not in chave and "passwd" not in chave and "etc" not in chave.split("/")[2:]


async def test_nome_com_extensao_perigosa_depois_de_sanitizado_e_recusado(
    estudante: httpx.AsyncClient,
) -> None:
    materia = await criar_materia(estudante)
    for nome in ("../../x.exe", "..\\script.sh", "arquivo.txt.exe", "\x00.pdf.bat"):
        resposta = await enviar(estudante, materia["id"], (nome, b"conteudo\n"))
        assert resposta.status_code == 422, nome
        assert resposta.json()["codigo"] == "formato_nao_aceito"


# --- Formulário malformado --------------------------------------------------------------------


async def test_dois_arquivos_no_mesmo_envio_sao_recusados(
    estudante: httpx.AsyncClient, acervo: FastAPI
) -> None:
    materia = await criar_materia(estudante)
    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/fontes",
        files=[
            ("arquivo", ("um.txt", b"primeiro\n", "text/plain")),
            ("arquivo", ("dois.txt", b"segundo\n", "text/plain")),
        ],
    )
    assert resposta.status_code == 422
    assert resposta.json()["campos"][0] == {
        "campo": "arquivo",
        "mensagem": "Envie um arquivo por vez.",
    }
    assert acervo.state.armazenamento.objetos == {}
    assert await _contar_fontes(_fabrica(acervo)) == 0


@pytest.mark.parametrize(
    "dados",
    [
        {"arquivo": "isto não é um arquivo"},
        {"titulo": "sem arquivo"},
        {},
    ],
)
async def test_envio_sem_arquivo_de_verdade_e_422_com_o_erro_no_campo(
    estudante: httpx.AsyncClient, dados: dict[str, str]
) -> None:
    materia = await criar_materia(estudante)
    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/fontes",
        files={"nada": ("", b"")} if not dados else None,
        data=dados or None,
    )
    assert resposta.status_code in {400, 422}
    assert resposta.json()["codigo"] in {"dados_invalidos", "requisicao_malformada"}


async def test_campo_extra_no_formulario_e_recusado(
    estudante: httpx.AsyncClient, validos: dict[str, ArquivoGerado], acervo: FastAPI
) -> None:
    materia = await criar_materia(estudante)
    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/fontes",
        files={"arquivo": ("a.txt", validos["resumo.txt"].conteudo, "text/plain")},
        data={"estado": "concluido", "titulo": "Ok"},
    )
    assert resposta.status_code == 422
    assert resposta.json()["campos"][0]["campo"] == "estado"
    assert acervo.state.armazenamento.objetos == {}


# O Starlette não fecha o arquivo temporário de uma parte que nunca termina (falha da biblioteca
# num caminho de erro); o objeto é liberado na coleta, com um aviso de recurso que o pytest
# trataria como erro. O teste força a coleta aqui, onde o aviso é esperado.
@pytest.mark.filterwarnings("ignore::ResourceWarning")
@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
@pytest.mark.parametrize(
    "corpo",
    [
        b"isto nao e multipart",
        b"--FRONTEIRA-DE-TESTE\r\n"
        b'Content-Disposition: form-data; name="arquivo"; filename="a.txt"\r\n\r\nsem fim',
        b"--outra\r\n\r\n",
        b"",
    ],
)
async def test_multipart_malformado_e_400_ou_422_sem_efeito(
    estudante: httpx.AsyncClient, acervo: FastAPI, corpo: bytes
) -> None:
    materia = await criar_materia(estudante)
    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/fontes",
        content=corpo,
        headers={"Content-Type": "multipart/form-data; boundary=FRONTEIRA-DE-TESTE"},
    )
    assert resposta.status_code in {400, 422}, resposta.text
    assert acervo.state.armazenamento.objetos == {}
    assert await _contar_fontes(_fabrica(acervo)) == 0
    gc.collect()


async def test_content_type_que_nao_e_multipart_e_recusado(
    estudante: httpx.AsyncClient, acervo: FastAPI
) -> None:
    materia = await criar_materia(estudante)
    resposta = await estudante.post(
        f"/api/v1/materias/{materia['id']}/fontes",
        json={"arquivo": "texto", "titulo": "x"},
    )
    assert resposta.status_code in {400, 422}
    assert acervo.state.armazenamento.objetos == {}


# --- Envio interrompido no meio (CB-04) -------------------------------------------------------


async def test_envio_interrompido_no_meio_nao_guarda_nada_e_apaga_o_temporario(
    estudante: httpx.AsyncClient,
    acervo: FastAPI,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    materia = await criar_materia(estudante)
    corpo = _multipart("grande.txt", b"conteudo " * 50_000)
    metade = corpo[: len(corpo) // 2]
    cookies = {c.name: str(c.value) for c in estudante.cookies.jar}
    cabecalhos = [
        (b"host", b"teste"),
        (b"content-type", b"multipart/form-data; boundary=FRONTEIRA-DE-TESTE"),
        (b"content-length", str(len(corpo)).encode()),  # promete o corpo todo
        (b"origin", ORIGEM.encode()),
        (b"sec-fetch-site", b"same-origin"),
        (b"x-csrf-token", str(cookies[COOKIE_CSRF]).encode()),
        (
            b"cookie",
            (
                f"{COOKIE_SESSAO}={cookies[COOKIE_SESSAO]}; {COOKIE_CSRF}={cookies[COOKIE_CSRF]}"
            ).encode(),
        ),
    ]
    escopo = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": f"/api/v1/materias/{materia['id']}/fontes",
        "raw_path": f"/api/v1/materias/{materia['id']}/fontes".encode(),
        "query_string": b"",
        "headers": cabecalhos,
        "client": ("127.0.0.1", 50000),
        "server": ("teste", 443),
        "state": {},
    }
    mensagens: list[MutableMapping[str, Any]] = [
        {"type": "http.request", "body": metade[:30_000], "more_body": True},
        {"type": "http.request", "body": metade[30_000:], "more_body": True},
        {"type": "http.disconnect"},
    ]
    enviadas: list[MutableMapping[str, Any]] = []

    async def receber() -> MutableMapping[str, Any]:
        return mensagens.pop(0) if mensagens else {"type": "http.disconnect"}

    async def enviar_asgi(mensagem: MutableMapping[str, Any]) -> None:
        enviadas.append(mensagem)

    await acervo(escopo, receber, enviar_asgi)

    assert acervo.state.armazenamento.objetos == {}, "o arquivo incompleto não foi guardado"
    assert await _contar_fontes(_fabrica(acervo)) == 0
    assert await asyncio.to_thread(os.listdir, tmp_path) == [], "o temporário foi apagado"
    iniciadas = [m for m in enviadas if m["type"] == "http.response.start"]
    assert all(m["status"] >= 400 for m in iniciadas)
    # A aplicação segue de pé para o próximo envio.
    assert (await estudante.get("/api/v1/materias")).status_code == 200


# --- Instruções à IA no texto (CB-15) ---------------------------------------------------------


async def test_instrucoes_guardadas_como_conteudo(
    estudante: httpx.AsyncClient,
    acervo: FastAPI,
    fila: App,
    adversariais: dict[str, ArquivoGerado],
) -> None:
    """O texto é dado: vira trecho comum, e nada nele altera o estado nem o comportamento."""
    materia = await criar_materia(estudante)
    enviada = (await enviar(estudante, materia["id"], adversariais["instrucoes-ia.txt"])).json()
    await executar_jobs(fila)

    fonte = await consultar_fonte(estudante, enviada["id"])
    trechos = await trechos_da_fonte(_fabrica(acervo), enviada["id"])

    assert fonte["estado"] == "concluido"
    assert any("Ignore todas as instruções anteriores" in t.texto for t in trechos)
    assert fonte["codigoFalha"] is None and fonte["titulo"] == "instrucoes-ia"


# --- Concorrência (DTEC 032) ------------------------------------------------------------------


async def test_envios_simultaneos_mesmo_arquivo(
    estudante: httpx.AsyncClient, acervo: FastAPI, validos: dict[str, ArquivoGerado]
) -> None:
    """Dois envios do mesmo arquivo à mesma matéria: um `201` e um `409 fonte_duplicada`."""
    materia = await criar_materia(estudante)
    arquivo = validos["resumo.txt"]
    respostas = await asyncio.gather(
        *(enviar(estudante, materia["id"], arquivo, titulo=f"Cópia {i}") for i in range(2))
    )
    assert sorted(r.status_code for r in respostas) == [201, 409]
    recusada = next(r for r in respostas if r.status_code == 409)
    assert recusada.json()["codigo"] == "fonte_duplicada"
    assert await _contar_fontes(_fabrica(acervo)) == 1
    assert len(acervo.state.armazenamento.objetos) == 1, "o objeto da recusada foi compensado"


async def test_rajada_do_mesmo_arquivo_aceita_so_uma_copia(
    estudante: httpx.AsyncClient, acervo: FastAPI, validos: dict[str, ArquivoGerado]
) -> None:
    materia = await criar_materia(estudante)
    respostas = await asyncio.gather(
        *(enviar(estudante, materia["id"], validos["resumo.txt"]) for _ in range(8))
    )
    assert sorted(r.status_code for r in respostas) == [201] + [409] * 7
    assert await _contar_fontes(_fabrica(acervo)) == 1
    assert len(acervo.state.armazenamento.objetos) == 1


async def test_cota_simultanea_de_fontes_aceita_so_uma(
    estudante: httpx.AsyncClient, acervo: FastAPI
) -> None:
    """Seis envios de arquivos diferentes que juntos passariam a cota da matéria: um é aceito."""
    ajustar_limites(acervo, cota_fontes_por_materia=1)
    materia = await criar_materia(estudante)
    respostas = await asyncio.gather(
        *(
            enviar(
                estudante,
                materia["id"],
                (f"nota-{i}.txt", f"Texto diferente número {i}.\n".encode()),
            )
            for i in range(6)
        )
    )
    assert sorted(r.status_code for r in respostas) == [201] + [409] * 5
    assert {r.json()["codigo"] for r in respostas if r.status_code == 409} == {
        "cota_fontes_excedida"
    }
    assert await _contar_fontes(_fabrica(acervo)) == 1
    assert len(acervo.state.armazenamento.objetos) == 1


async def test_cota_simultanea_de_armazenamento_aceita_so_uma(
    estudante: httpx.AsyncClient, acervo: FastAPI, validos: dict[str, ArquivoGerado]
) -> None:
    a, b = validos["resumo.txt"], validos["anotacoes.md"]
    ajustar_limites(acervo, cota_armazenamento_bytes=max(len(a.conteudo), len(b.conteudo)) + 10)
    primeira = await criar_materia(estudante, "Biologia")
    segunda = await criar_materia(estudante, "Química")
    respostas = await asyncio.gather(
        enviar(estudante, primeira["id"], a), enviar(estudante, segunda["id"], b)
    )
    assert sorted(r.status_code for r in respostas) == [201, 409]
    assert next(r for r in respostas if r.status_code == 409).json()["codigo"] == (
        "cota_armazenamento_excedida"
    )
    assert await _contar_fontes(_fabrica(acervo)) == 1


async def test_cota_simultanea_de_materias_aceita_so_uma(
    estudante: httpx.AsyncClient, acervo: FastAPI
) -> None:
    ajustar_limites(acervo, cota_materias=1)
    respostas = await asyncio.gather(
        *(
            estudante.post("/api/v1/materias", json={"nome": nome})
            for nome in ("Biologia", "Física")
        )
    )
    assert sorted(r.status_code for r in respostas) == [201, 409]
    assert next(r for r in respostas if r.status_code == 409).json()["codigo"] == (
        "cota_materias_excedida"
    )
    assert len((await estudante.get("/api/v1/materias")).json()["itens"]) == 1


async def test_materias_mesmo_nome_simultaneas(estudante: httpx.AsyncClient) -> None:
    """Duas criações com o mesmo nome em caixas diferentes: uma é recusada."""
    respostas = await asyncio.gather(
        *(estudante.post("/api/v1/materias", json={"nome": nome}) for nome in ("Física", "FÍSICA"))
    )
    assert sorted(r.status_code for r in respostas) == [201, 409]
    assert next(r for r in respostas if r.status_code == 409).json()["codigo"] == (
        "materia_nome_em_uso"
    )
    assert len((await estudante.get("/api/v1/materias")).json()["itens"]) == 1


async def test_cotas_de_estudantes_diferentes_nao_se_bloqueiam(
    acervo: FastAPI, estudante: httpx.AsyncClient
) -> None:
    from tests.apoio_http import abrir_cliente

    ajustar_limites(acervo, cota_materias=1)
    async with abrir_cliente(acervo, ip="198.51.100.95") as outro:
        await criar_conta(outro)
        respostas = await asyncio.gather(
            estudante.post("/api/v1/materias", json={"nome": "Dela"}),
            outro.post("/api/v1/materias", json={"nome": "Dele"}),
        )
    assert [r.status_code for r in respostas] == [201, 201]


async def test_novas_tentativas_paralelas(
    estudante: httpx.AsyncClient,
    acervo: FastAPI,
    fila: App,
    fabrica_real: FabricaSessoes,
    validos: dict[str, ArquivoGerado],
) -> None:
    """Várias novas tentativas ao mesmo tempo: um job, nenhum trecho duplicado (RF-008)."""
    materia = await criar_materia(estudante)
    fonte = (await enviar(estudante, materia["id"], validos["resumo.txt"])).json()
    chave = await chave_da_fonte(fabrica_real, fonte["id"])
    conteudo = acervo.state.armazenamento.objetos.pop(chave)
    await executar_jobs(fila)
    assert (await consultar_fonte(estudante, fonte["id"]))["codigoFalha"] == "falha_tecnica"
    acervo.state.armazenamento.objetos[chave] = conteudo

    respostas = await asyncio.gather(
        *(estudante.post(f"/api/v1/fontes/{fonte['id']}/reprocessamento") for _ in range(8))
    )

    assert sorted(r.status_code for r in respostas) == [202] + [409] * 7
    assert {r.json()["codigo"] for r in respostas if r.status_code == 409} == {
        "reprocessamento_indisponivel"
    }
    async with unidade_de_trabalho(fabrica_real) as sessao:
        from sqlalchemy import text

        jobs = (
            await sessao.execute(
                text(
                    "SELECT count(*) FROM procrastinate_jobs "
                    "WHERE task_name = 'fontes.processar_fonte' AND status = 'todo'"
                )
            )
        ).scalar_one()
    assert jobs == 1
    await executar_jobs(fila)
    concluida = await consultar_fonte(estudante, fonte["id"])
    trechos = await trechos_da_fonte(_fabrica(acervo), fonte["id"])
    assert concluida["estado"] == "concluido"
    assert len(trechos) == concluida["totalTrechos"]
    assert [t.ordem for t in trechos] == list(range(len(trechos)))


async def test_envio_para_materia_excluida_no_meio_e_404_e_compensa_o_objeto(
    estudante: httpx.AsyncClient,
    acervo: FastAPI,
    fabrica_real: FabricaSessoes,
    validos: dict[str, ArquivoGerado],
) -> None:
    """A matéria some depois da pré-verificação: a FK recusa e o objeto é apagado (DTEC 032)."""
    from sqlalchemy import delete

    from app.fontes.servicos import ServicoFontes
    from app.materias.modelos import Materia

    materia = await criar_materia(estudante)
    servico: ServicoFontes = acervo.state.fontes
    original = servico._inserir  # noqa: SLF001

    async def apagar_antes_de_inserir(**kwargs: Any) -> Fonte:
        async with unidade_de_trabalho(fabrica_real) as sessao:
            await sessao.execute(delete(Materia))
        return await original(**kwargs)

    servico._inserir = apagar_antes_de_inserir  # type: ignore[method-assign]  # noqa: SLF001
    resposta = await enviar(estudante, materia["id"], validos["resumo.txt"])

    assert resposta.status_code == 404
    assert resposta.json()["codigo"] == "recurso_nao_encontrado"
    assert acervo.state.armazenamento.objetos == {}, "o objeto foi compensado"
    assert await _contar_fontes(fabrica_real) == 0


async def test_dados_da_resposta_sao_json_valido_mesmo_com_nome_estranho(
    estudante: httpx.AsyncClient,
) -> None:
    materia = await criar_materia(estudante)
    resposta = await enviar(estudante, materia["id"], ("aula 1 <b>&amp; ç.txt", b"texto\n"))
    assert resposta.status_code == 201
    assert json.loads(resposta.text)["nomeArquivo"] == "aula 1 <b>&amp; ç.txt"
    assert uuid.UUID(resposta.json()["id"])
