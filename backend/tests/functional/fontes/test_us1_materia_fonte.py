"""US1: criar a matéria e enviar uma fonte, cenários 1 a 8 (T019; RF-001 a RF-016, CS-001 a CS-003).

API e worker rodam em processo sobre o mesmo banco e armazenamento (fixture `acervo`); os
arquivos vêm da fábrica (`tests/fabricas_arquivos.py`).
"""

from __future__ import annotations

import time

import httpx
import pytest
from fastapi import FastAPI
from procrastinate import App
from sqlalchemy import delete

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
    tipo_do_nome,
    trechos_da_fonte,
)
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


def _fabrica(app: FastAPI) -> FabricaSessoes:
    fabrica: FabricaSessoes = app.state.fabrica_sessoes
    return fabrica


# --- Cenário 1 --------------------------------------------------------------------------------


async def test_cria_materia(estudante: httpx.AsyncClient) -> None:
    """US1-1: a matéria aparece na lista, vazia."""
    resposta = await estudante.post("/api/v1/materias", json={"nome": "Biologia"})
    assert resposta.status_code == 201
    materia = resposta.json()
    assert set(materia) == {
        "id",
        "nome",
        "totalFontes",
        "cartoesAtivos",
        "cartoesAguardandoRevisao",
        "criadoEm",
        "atualizadoEm",
    }
    assert materia["nome"] == "Biologia"
    assert (materia["totalFontes"], materia["cartoesAtivos"]) == (0, 0)
    assert materia["cartoesAguardandoRevisao"] == 0

    lista = (await estudante.get("/api/v1/materias")).json()
    assert [m["id"] for m in lista["itens"]] == [materia["id"]]
    assert (await estudante.get(f"/api/v1/materias/{materia['id']}")).json() == materia


async def test_lista_materias_ordenada_por_nome_com_contagens(
    estudante: httpx.AsyncClient, fila: App, validos: dict[str, ArquivoGerado]
) -> None:
    """RF-002: nome, quantidade de fontes e de cartões; ordenação sem diferenciar caixa."""
    for nome in ("zoologia", "Anatomia", "botânica"):
        await criar_materia(estudante, nome)
    anatomia = next(
        m
        for m in (await estudante.get("/api/v1/materias")).json()["itens"]
        if m["nome"] == "Anatomia"
    )
    for nome in ("resumo.txt", "anotacoes.md"):
        assert (await enviar(estudante, anatomia["id"], validos[nome])).status_code == 201

    itens = (await estudante.get("/api/v1/materias")).json()["itens"]

    assert [m["nome"] for m in itens] == ["Anatomia", "botânica", "zoologia"]
    assert [m["totalFontes"] for m in itens] == [2, 0, 0]


async def test_nome_repetido_sem_diferenciar_caixa_e_recusado(
    estudante: httpx.AsyncClient,
) -> None:
    await criar_materia(estudante, "Ciências")
    for repetido in ("CIÊNCIAS", "ciências", " Ciências "):
        resposta = await estudante.post("/api/v1/materias", json={"nome": repetido})
        assert resposta.status_code == 409, repetido
        assert resposta.json()["codigo"] == "materia_nome_em_uso"
        assert resposta.json()["campos"][0]["campo"] == "nome"


@pytest.mark.parametrize("nome", ["", "   ", "x" * 61, "Bio\nlogia"])
async def test_nome_invalido_e_recusado_com_o_erro_junto_do_campo(
    estudante: httpx.AsyncClient, nome: str
) -> None:
    resposta = await estudante.post("/api/v1/materias", json={"nome": nome})
    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "dados_invalidos"
    assert resposta.json()["campos"][0]["campo"] == "nome"


# --- Cenários 2 e 3: envio, estados e consulta ------------------------------------------------


async def test_envia_pdf_e_acompanha_ate_concluido_com_trechos_e_paginas(
    estudante: httpx.AsyncClient, acervo: FastAPI, fila: App, validos: dict[str, ArquivoGerado]
) -> None:
    """US1-2 e US1-3, RF-003 e RF-005: pendente, depois concluído, com os dados da fonte."""
    materia = await criar_materia(estudante)
    arquivo = validos["biologia-citologia.pdf"]

    resposta = await enviar(estudante, materia["id"], arquivo, titulo="Citologia")

    assert resposta.status_code == 201, resposta.text
    fonte = resposta.json()
    assert fonte["estado"] == "pendente"
    assert fonte["titulo"] == "Citologia"
    assert fonte["materiaId"] == materia["id"]
    assert (fonte["codigoFalha"], fonte["mensagemFalha"]) == (None, None)
    assert fonte["podeTentarNovamente"] is False
    assert fonte["totalPaginas"] == 90
    assert fonte["totalTrechos"] is None and fonte["processadaEm"] is None
    assert [
        f["estado"]
        for f in (await estudante.get(f"/api/v1/materias/{materia['id']}/fontes")).json()["itens"]
    ] == ["pendente"]

    await executar_jobs(fila)

    pronta = await consultar_fonte(estudante, fonte["id"])
    assert pronta["estado"] == "concluido"
    assert pronta["nomeArquivo"] == "biologia-citologia.pdf"
    assert pronta["tipoMidia"] == "application/pdf"
    assert pronta["tamanhoBytes"] == len(arquivo.conteudo)
    assert pronta["totalPaginas"] == 90
    assert pronta["totalTrechos"] and pronta["totalTrechos"] > 0
    assert pronta["enviadaEm"] and pronta["processadaEm"]
    trechos = await trechos_da_fonte(_fabrica(acervo), fonte["id"])
    assert len(trechos) == pronta["totalTrechos"]


async def test_envia_pdf_sem_titulo_usa_o_nome_do_arquivo_sem_a_extensao(
    estudante: httpx.AsyncClient, validos: dict[str, ArquivoGerado]
) -> None:
    """RF-003: título padrão."""
    materia = await criar_materia(estudante)
    resposta = await enviar(estudante, materia["id"], validos["pdf-uma-pagina.pdf"])
    assert resposta.status_code == 201
    assert resposta.json()["titulo"] == "pdf-uma-pagina"


async def test_titulo_fora_dos_limites_e_recusado(
    estudante: httpx.AsyncClient, validos: dict[str, ArquivoGerado]
) -> None:
    materia = await criar_materia(estudante)
    for titulo in ("x" * 121, "   "):
        resposta = await enviar(estudante, materia["id"], validos["resumo.txt"], titulo=titulo)
        assert resposta.status_code == 422, titulo
        assert resposta.json()["campos"][0]["campo"] == "titulo"
    assert (await estudante.get(f"/api/v1/materias/{materia['id']}/fontes")).json()["itens"] == []


# --- Cenário 4: arquivos recusados (CS-002) ---------------------------------------------------


@pytest.mark.parametrize(
    ("nome", "status", "codigo"),
    [
        ("grande-3mb.pdf", 413, "arquivo_muito_grande"),
        ("disfarcado.pdf", 422, "tipo_divergente"),
        ("pdf-como-txt.txt", 422, "tipo_divergente"),
        ("vazio.txt", 422, "arquivo_vazio"),
        ("corrompido.pdf", 422, "arquivo_corrompido"),
        ("protegido.pdf", 422, "pdf_protegido"),
        ("latin1.txt", 422, "codificacao_invalida"),
        ("so-espacos.txt", 422, "arquivo_vazio"),
        ("byte-nulo.txt", 422, "tipo_divergente"),
    ],
)
async def test_cs002_invalidos_recusados(
    estudante: httpx.AsyncClient,
    acervo: FastAPI,
    invalidos: dict[str, ArquivoGerado],
    nome: str,
    status: int,
    codigo: str,
) -> None:
    """US1-4: cada recusa tem a sua explicação, e nada é guardado."""
    materia = await criar_materia(estudante)
    resposta = await enviar(estudante, materia["id"], invalidos[nome])

    assert resposta.status_code == status, resposta.text
    corpo = resposta.json()
    assert corpo["codigo"] == codigo
    assert corpo["mensagem"]
    assert nome not in corpo["mensagem"]
    assert acervo.state.armazenamento.objetos == {}, "nada foi guardado"
    assert (await estudante.get(f"/api/v1/materias/{materia['id']}/fontes")).json()["itens"] == []


async def test_extensao_nao_aceita_e_formato_nao_aceito(estudante: httpx.AsyncClient) -> None:
    materia = await criar_materia(estudante)
    resposta = await enviar(estudante, materia["id"], ("planilha.xlsx", b"PK\x03\x04conteudo"))
    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "formato_nao_aceito"


async def test_pdf_com_501_paginas_e_recusado(estudante: httpx.AsyncClient) -> None:
    materia = await criar_materia(estudante)
    arquivo = {a.nome: a for a in fab.adversariais()}["pdf-501-paginas.pdf"]
    resposta = await enviar(estudante, materia["id"], arquivo)
    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "pdf_paginas_excedidas"
    assert "500" in resposta.json()["mensagem"]


async def test_cs002_dez_invalidos_nenhum_gera_trecho_e_todos_tem_explicacao_especifica(
    estudante: httpx.AsyncClient,
    acervo: FastAPI,
    fila: App,
    invalidos: dict[str, ArquivoGerado],
) -> None:
    """CS-002: dos 10 arquivos inválidos, 9 são recusados no envio e o PDF sem texto falha."""
    materia = await criar_materia(estudante)
    explicacoes: set[str] = set()
    aceitos: list[dict[str, object]] = []
    for arquivo in invalidos.values():
        resposta = await enviar(estudante, materia["id"], arquivo)
        if arquivo.codigo_esperado:
            assert resposta.status_code == arquivo.status_http, arquivo.nome
            assert resposta.json()["codigo"] == arquivo.codigo_esperado, arquivo.nome
            explicacoes.add(resposta.json()["mensagem"])
        else:
            assert resposta.status_code == 201, arquivo.nome
            aceitos.append(resposta.json())
    await executar_jobs(fila)

    assert len(aceitos) == 1
    sem_texto = await consultar_fonte(estudante, str(aceitos[0]["id"]))
    assert (sem_texto["estado"], sem_texto["codigoFalha"]) == ("falhou", "sem_texto")
    explicacoes.add(sem_texto["mensagemFalha"])
    assert len(explicacoes) >= 6, "cada tipo de problema tem a sua explicação"
    assert await trechos_da_fonte(_fabrica(acervo), str(aceitos[0]["id"])) == []


# --- Cenário 5: PDF sem camada de texto (CB-23) -----------------------------------------------


async def test_pdf_sem_texto_falha_com_explicacao_e_sem_nova_tentativa(
    estudante: httpx.AsyncClient, fila: App, invalidos: dict[str, ArquivoGerado]
) -> None:
    """US1-5, RF-007."""
    materia = await criar_materia(estudante)
    enviada = (await enviar(estudante, materia["id"], invalidos["digitalizado.pdf"])).json()
    await executar_jobs(fila)

    fonte = await consultar_fonte(estudante, enviada["id"])

    assert fonte["estado"] == "falhou"
    assert fonte["codigoFalha"] == "sem_texto"
    assert "digitalizados" in fonte["mensagemFalha"]
    assert fonte["podeTentarNovamente"] is False
    assert fonte["totalTrechos"] is None
    recusa = await estudante.post(f"/api/v1/fontes/{enviada['id']}/reprocessamento")
    assert recusa.status_code == 409
    assert recusa.json()["codigo"] == "reprocessamento_indisponivel"


# --- Cenário 6: nova tentativa sem duplicar trechos -------------------------------------------


async def test_nova_tentativa_apos_falha_tecnica_nao_duplica_trechos(
    estudante: httpx.AsyncClient,
    acervo: FastAPI,
    fila: App,
    validos: dict[str, ArquivoGerado],
) -> None:
    """US1-6, RF-007 e RF-008: o objeto some (falha técnica), volta, e o resultado é o de sempre."""
    materia = await criar_materia(estudante)
    arquivo = validos["resumo.txt"]
    referencia = (await enviar(estudante, materia["id"], arquivo, titulo="Referência")).json()
    outra_materia = await criar_materia(estudante, "Química")
    candidata = (await enviar(estudante, outra_materia["id"], arquivo, titulo="Candidata")).json()
    armazenamento = acervo.state.armazenamento
    chave = await chave_da_fonte(_fabrica(acervo), candidata["id"])
    conteudo = armazenamento.objetos.pop(chave)  # simula o volume indisponível para esta fonte
    await executar_jobs(fila)

    falha = await consultar_fonte(estudante, candidata["id"])
    assert (falha["estado"], falha["codigoFalha"]) == ("falhou", "falha_tecnica")
    assert falha["podeTentarNovamente"] is True
    assert "Tente novamente" in falha["mensagemFalha"]

    armazenamento.objetos[chave] = conteudo
    nova = await estudante.post(f"/api/v1/fontes/{candidata['id']}/reprocessamento")
    assert nova.status_code == 202, nova.text
    assert nova.json()["estado"] == "pendente" and nova.json()["codigoFalha"] is None
    await executar_jobs(fila)

    concluida = await consultar_fonte(estudante, candidata["id"])
    padrao = await consultar_fonte(estudante, referencia["id"])
    assert concluida["estado"] == padrao["estado"] == "concluido"
    assert concluida["totalTrechos"] == padrao["totalTrechos"]
    trechos = await trechos_da_fonte(_fabrica(acervo), candidata["id"])
    assert len(trechos) == concluida["totalTrechos"]
    assert [t.ordem for t in trechos] == list(range(len(trechos)))


# --- Cenário 7: duplicata (D-004) -------------------------------------------------------------


async def test_fonte_duplicada_na_mesma_materia_e_recusada_com_o_titulo_existente(
    estudante: httpx.AsyncClient, acervo: FastAPI, validos: dict[str, ArquivoGerado]
) -> None:
    """US1-7, RF-014."""
    materia = await criar_materia(estudante)
    arquivo = validos["resumo.txt"]
    primeira = await enviar(estudante, materia["id"], arquivo, titulo="Citologia")
    assert primeira.status_code == 201

    repetida = await enviar(estudante, materia["id"], arquivo, titulo="Outro título")

    assert repetida.status_code == 409
    assert repetida.json()["codigo"] == "fonte_duplicada"
    assert repetida.json()["mensagem"] == "Esta fonte já está nesta matéria: «Citologia»."
    assert len(acervo.state.armazenamento.objetos) == 1, "o objeto da recusa não foi guardado"


async def test_mesmo_arquivo_em_outra_materia_e_aceito(
    estudante: httpx.AsyncClient, validos: dict[str, ArquivoGerado]
) -> None:
    """D-004: a duplicata é por matéria."""
    primeira = await criar_materia(estudante, "Biologia")
    segunda = await criar_materia(estudante, "Química")
    arquivo = validos["resumo.txt"]
    assert (await enviar(estudante, primeira["id"], arquivo)).status_code == 201
    assert (await enviar(estudante, segunda["id"], arquivo)).status_code == 201


async def test_conteudo_igual_com_nome_diferente_tambem_e_duplicata(
    estudante: httpx.AsyncClient, validos: dict[str, ArquivoGerado]
) -> None:
    materia = await criar_materia(estudante)
    conteudo = validos["resumo.txt"].conteudo
    assert (await enviar(estudante, materia["id"], ("a.txt", conteudo))).status_code == 201
    recusa = await enviar(estudante, materia["id"], ("outro-nome.md", conteudo))
    assert recusa.status_code == 409 and recusa.json()["codigo"] == "fonte_duplicada"


# --- Cenário 8: pouco texto (RF-016, D-006) ---------------------------------------------------


async def test_pouco_texto_conclui(
    estudante: httpx.AsyncClient, fila: App, validos: dict[str, ArquivoGerado]
) -> None:
    """US1-8."""
    materia = await criar_materia(estudante)
    enviada = (await enviar(estudante, materia["id"], validos["um-paragrafo.txt"])).json()
    await executar_jobs(fila)
    fonte = await consultar_fonte(estudante, enviada["id"])
    assert (fonte["estado"], fonte["totalTrechos"]) == ("concluido", 1)
    assert fonte["totalPaginas"] is None


# --- Cotas (RF-012, D-003, D-010) -------------------------------------------------------------


async def test_cota_de_materias_atingida(acervo: FastAPI, estudante: httpx.AsyncClient) -> None:
    ajustar_limites(acervo, cota_materias=2)
    await criar_materia(estudante, "Um")
    await criar_materia(estudante, "Dois")
    resposta = await estudante.post("/api/v1/materias", json={"nome": "Três"})
    assert resposta.status_code == 409
    assert resposta.json()["codigo"] == "cota_materias_excedida"
    assert "2 matérias" in resposta.json()["mensagem"]


async def test_cota_de_fontes_da_materia_conta_a_fonte_que_falhou(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
    invalidos: dict[str, ArquivoGerado],
) -> None:
    """D-010: `falhou` ocupa a cota até ser excluída."""
    ajustar_limites(acervo, cota_fontes_por_materia=2)
    materia = await criar_materia(estudante)
    assert (
        await enviar(estudante, materia["id"], invalidos["digitalizado.pdf"])
    ).status_code == 201
    assert (await enviar(estudante, materia["id"], validos["resumo.txt"])).status_code == 201
    await executar_jobs(fila)

    resposta = await enviar(estudante, materia["id"], validos["anotacoes.md"])

    assert resposta.status_code == 409
    assert resposta.json()["codigo"] == "cota_fontes_excedida"
    assert "2 fontes" in resposta.json()["mensagem"]
    outra = await criar_materia(estudante, "Outra")
    assert (await enviar(estudante, outra["id"], validos["anotacoes.md"])).status_code == 201


async def test_cota_de_armazenamento_soma_todas_as_fontes_do_estudante(
    acervo: FastAPI, estudante: httpx.AsyncClient, validos: dict[str, ArquivoGerado]
) -> None:
    a, b = validos["resumo.txt"], validos["anotacoes.md"]
    ajustar_limites(
        acervo,
        cota_armazenamento_bytes=max(len(a.conteudo) + len(b.conteudo) - 1, len(a.conteudo)),
    )
    primeira = await criar_materia(estudante, "Biologia")
    segunda = await criar_materia(estudante, "Química")
    assert (await enviar(estudante, primeira["id"], a)).status_code == 201

    resposta = await enviar(estudante, segunda["id"], b)

    assert resposta.status_code == 409
    assert resposta.json()["codigo"] == "cota_armazenamento_excedida"
    assert acervo.state.armazenamento.objetos and len(acervo.state.armazenamento.objetos) == 1


async def test_uso_acervo_traz_os_limites_vigentes_e_o_uso(
    acervo: FastAPI, estudante: httpx.AsyncClient, validos: dict[str, ArquivoGerado]
) -> None:
    """RQ-005: a interface lê os limites da API."""
    antes = (await estudante.get("/api/v1/acervo/uso")).json()
    assert antes == {
        "tamanhoMaximoBytes": 2097152,
        "extensoesAceitas": [".pdf", ".txt", ".md", ".markdown"],
        "paginasMaximasPdf": 500,
        "cotaMaterias": 50,
        "totalMaterias": 0,
        "cotaFontesPorMateria": 30,
        "cotaArmazenamentoBytes": 104857600,
        "usoArmazenamentoBytes": 0,
    }
    materia = await criar_materia(estudante)
    arquivo = validos["resumo.txt"]
    await enviar(estudante, materia["id"], arquivo)
    depois = (await estudante.get("/api/v1/acervo/uso")).json()
    assert depois["totalMaterias"] == 1
    assert depois["usoArmazenamentoBytes"] == len(arquivo.conteudo)

    ajustar_limites(acervo, fonte_tamanho_max_bytes=1000, pdf_max_paginas=7)
    configurado = (await estudante.get("/api/v1/acervo/uso")).json()
    assert (configurado["tamanhoMaximoBytes"], configurado["paginasMaximasPdf"]) == (1000, 7)


async def test_o_limite_de_tamanho_configurado_vale_para_o_envio(
    acervo: FastAPI, estudante: httpx.AsyncClient, validos: dict[str, ArquivoGerado]
) -> None:
    ajustar_limites(acervo, fonte_tamanho_max_bytes=1000)
    materia = await criar_materia(estudante)
    resposta = await enviar(estudante, materia["id"], validos["resumo.txt"])
    assert resposta.status_code == 413
    assert resposta.json()["codigo"] == "arquivo_muito_grande"


# --- Critérios de sucesso ---------------------------------------------------------------------


async def test_cs001_validos_concluem_com_paginas(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    validos: dict[str, ArquivoGerado],
) -> None:
    """CS-001: os 10 arquivos válidos chegam a `concluido`; nos PDFs, a página confere."""
    materia = await criar_materia(estudante)
    enviadas = {}
    for nome, arquivo in validos.items():
        resposta = await enviar(estudante, materia["id"], arquivo)
        assert resposta.status_code == 201, (nome, resposta.text)
        enviadas[nome] = resposta.json()
    await executar_jobs(fila)

    for nome, arquivo in validos.items():
        fonte = await consultar_fonte(estudante, enviadas[nome]["id"])
        assert fonte["estado"] == "concluido", nome
        assert fonte["tipoMidia"] == tipo_do_nome(nome)
        trechos = await trechos_da_fonte(_fabrica(acervo), fonte["id"])
        assert trechos and len(trechos) == fonte["totalTrechos"], nome
        if arquivo.paginas is None:
            assert all(t.pagina is None for t in trechos), nome
            assert fonte["totalPaginas"] is None
            continue
        assert fonte["totalPaginas"] == len(arquivo.paginas)
        com_texto = {n for n, texto in enumerate(arquivo.paginas, start=1) if texto}
        assert {t.pagina for t in trechos} == com_texto, nome
        for trecho in trechos:
            esperado = arquivo.paginas[trecho.pagina - 1]
            assert trecho.texto in esperado, f"{nome}: trecho fora da página {trecho.pagina}"


async def test_cs003_pdf_de_2mb_chega_a_concluido_em_menos_de_60_segundos(
    estudante: httpx.AsyncClient, fila: App, validos: dict[str, ArquivoGerado]
) -> None:
    """CS-003, D-008: do envio a `concluido`, no ambiente do teste."""
    materia = await criar_materia(estudante)
    arquivo = validos["pdf-2mb.pdf"]
    assert 1_800_000 <= len(arquivo.conteudo) <= 2 * 1024 * 1024
    inicio = time.monotonic()

    enviada = (await enviar(estudante, materia["id"], arquivo)).json()
    await executar_jobs(fila)
    fonte = await consultar_fonte(estudante, enviada["id"])

    decorrido = time.monotonic() - inicio
    assert fonte["estado"] == "concluido"
    assert decorrido < 60, f"levou {decorrido:.1f} s"
    print(f"\nCS-003: PDF de {len(arquivo.conteudo)} bytes concluído em {decorrido:.1f} s")


# --- Estado visto pela interface (RF-005) -----------------------------------------------------


async def test_a_listagem_traz_o_estado_de_cada_fonte_para_o_acompanhamento(
    estudante: httpx.AsyncClient, acervo: FastAPI, fila: App, validos: dict[str, ArquivoGerado]
) -> None:
    materia = await criar_materia(estudante)
    await enviar(estudante, materia["id"], validos["resumo.txt"], titulo="Primeira")
    await enviar(estudante, materia["id"], validos["anotacoes.md"], titulo="Segunda")

    antes = (await estudante.get(f"/api/v1/materias/{materia['id']}/fontes")).json()["itens"]
    assert [f["titulo"] for f in antes] == ["Segunda", "Primeira"], "a mais recente primeiro"
    assert {f["estado"] for f in antes} == {"pendente"}

    await executar_jobs(fila)
    depois = (await estudante.get(f"/api/v1/materias/{materia['id']}/fontes")).json()["itens"]
    assert {f["estado"] for f in depois} == {"concluido"}


async def test_fonte_excluida_do_banco_some_da_listagem(
    estudante: httpx.AsyncClient, acervo: FastAPI, validos: dict[str, ArquivoGerado]
) -> None:
    materia = await criar_materia(estudante)
    enviada = (await enviar(estudante, materia["id"], validos["resumo.txt"])).json()
    async with unidade_de_trabalho(_fabrica(acervo)) as sessao:
        await sessao.execute(delete(Fonte))
    assert (await estudante.get(f"/api/v1/fontes/{enviada['id']}")).status_code == 404
