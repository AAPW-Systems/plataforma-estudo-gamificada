"""A tarefa `processar_fonte` e a reconciliação de objetos (DTEC 025 e 030; T020).

Cobre os estados, as falhas (de conteúdo e técnica), as novas tentativas, a exclusão no meio
(CB-16), a idempotência (RF-008), a limpeza do temporário e a compensação do envio.
O worker em si (fila real) é exercitado nos testes funcionais; aqui se chama a lógica direto.
"""

from __future__ import annotations

import asyncio
import io
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from procrastinate import RetryStrategy
from sqlalchemy import delete, func, select, text

from app.fontes.modelos import Fonte, Trecho
from app.fontes.servicos import ServicoFontes
from app.fontes.tarefas import (
    DependenciasTarefas,
    ResultadoProcessamento,
    executar_processar_fonte,
    executar_reconciliacao,
)
from app.nucleo.armazenamento import ArmazenamentoMemoria
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao
from app.nucleo.erros import RecursoNaoEncontrado
from app.nucleo.fila import ErroTransitorio, app_fila
from app.nucleo.isolamento import ResultadoIsolado, executar_isolado
from app.nucleo.participantes_acervo import RegistroAcervo
from tests import fabricas_arquivos as fab
from tests.apoio_acervo import recarregar_fonte, semear_fonte

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def arquivos() -> dict[str, fab.ArquivoGerado]:
    todos = [*fab.validos(), *fab.invalidos()]
    return {a.nome: a for a in todos}


@pytest.fixture
def armazenamento() -> ArmazenamentoMemoria:
    return ArmazenamentoMemoria()


@pytest.fixture
def deps(
    fabrica_sessoes: FabricaSessoes, armazenamento: ArmazenamentoMemoria, configuracao: Configuracao
) -> DependenciasTarefas:
    return DependenciasTarefas(
        fabrica=fabrica_sessoes, armazenamento=armazenamento, configuracao=configuracao
    )


async def _contar_trechos(fabrica: FabricaSessoes, fonte_id: int) -> int:
    async with unidade_de_trabalho(fabrica) as sessao:
        return int(
            (
                await sessao.execute(
                    select(func.count()).select_from(Trecho).where(Trecho.fonte_id == fonte_id)
                )
            ).scalar_one()
        )


# --- Sucesso e estados ------------------------------------------------------------------------


async def test_estados_sucesso_grava_trechos_e_conclui_na_mesma_transacao(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    _, _, fonte = await semear_fonte(
        deps.fabrica, armazenamento, arquivos["biologia-citologia.pdf"]
    )

    resultado = await executar_processar_fonte(fonte.id, deps, ultima_tentativa=False)

    assert resultado is ResultadoProcessamento.CONCLUIDA
    atual = await recarregar_fonte(deps.fabrica, fonte.id)
    assert atual is not None
    assert atual.estado == "concluido"
    assert atual.codigo_falha is None
    assert atual.total_paginas == 90
    assert atual.total_trechos == await _contar_trechos(deps.fabrica, fonte.id) > 0
    assert (atual.versao_extracao or "").startswith("v1-a1200-m2000-s150")
    assert atual.processada_em is not None
    async with unidade_de_trabalho(deps.fabrica) as sessao:
        ordens = (
            await sessao.execute(
                select(Trecho.ordem).where(Trecho.fonte_id == fonte.id).order_by(Trecho.ordem)
            )
        ).scalars()
        assert list(ordens) == list(range(atual.total_trechos or 0))


async def test_estados_a_fonte_fica_processando_enquanto_o_arquivo_e_extraido(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos["resumo.txt"])
    observado: list[str] = []

    async def espiao(*args: Any, **kwargs: Any) -> ResultadoIsolado:
        atual = await recarregar_fonte(deps.fabrica, fonte.id)
        observado.append(atual.estado if atual else "sumiu")
        return await executar_isolado(*args, **kwargs)

    await executar_processar_fonte(fonte.id, deps, ultima_tentativa=False, executor=espiao)

    assert observado == ["processando"]
    assert (await recarregar_fonte(deps.fabrica, fonte.id)).estado == "concluido"  # type: ignore[union-attr]


async def test_txt_processa_sem_pagina_e_md_tambem(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    for nome in ("resumo.txt", "anotacoes.md", "um-paragrafo.txt"):
        _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos[nome])
        assert await executar_processar_fonte(fonte.id, deps, ultima_tentativa=False) is (
            ResultadoProcessamento.CONCLUIDA
        )
        async with unidade_de_trabalho(deps.fabrica) as sessao:
            paginas = (
                (await sessao.execute(select(Trecho.pagina).where(Trecho.fonte_id == fonte.id)))
                .scalars()
                .all()
            )
        assert paginas and all(p is None for p in paginas)
        atual = await recarregar_fonte(deps.fabrica, fonte.id)
        assert atual is not None and atual.total_paginas is None


# --- Falhas de conteúdo (sem nova tentativa) --------------------------------------------------


async def test_pdf_sem_texto_vira_falhou_sem_texto_e_nao_gera_trecho(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos["digitalizado.pdf"])

    resultado = await executar_processar_fonte(fonte.id, deps, ultima_tentativa=False)

    assert resultado is ResultadoProcessamento.FALHOU
    atual = await recarregar_fonte(deps.fabrica, fonte.id)
    assert atual is not None
    assert (atual.estado, atual.codigo_falha) == ("falhou", "sem_texto")
    assert atual.total_trechos is None and atual.versao_extracao is None
    assert await _contar_trechos(deps.fabrica, fonte.id) == 0


@pytest.mark.parametrize("nome", ["corrompido.pdf", "protegido.pdf"])
async def test_arquivo_ilegivel_vira_falhou_conteudo_invalido(
    deps: DependenciasTarefas,
    armazenamento: ArmazenamentoMemoria,
    arquivos: dict[str, Any],
    nome: str,
) -> None:
    _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos[nome])
    assert await executar_processar_fonte(fonte.id, deps, ultima_tentativa=False) is (
        ResultadoProcessamento.FALHOU
    )
    atual = await recarregar_fonte(deps.fabrica, fonte.id)
    assert atual is not None
    assert (atual.estado, atual.codigo_falha) == ("falhou", "conteudo_invalido")


async def test_tempo_esgotado_na_extracao_vira_conteudo_invalido(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos["pdf-uma-pagina.pdf"])
    deps_lentas = DependenciasTarefas(
        fabrica=deps.fabrica,
        armazenamento=armazenamento,
        configuracao=deps.configuracao.model_copy(update={"extracao_tempo_s": 1}),
    )

    async def estourar(funcao: Any, argumentos: Any, **kwargs: Any) -> ResultadoIsolado:
        kwargs["tempo_limite_s"] = 0.05
        return await executar_isolado(funcao, argumentos, **kwargs)

    resultado = await executar_processar_fonte(
        fonte.id, deps_lentas, ultima_tentativa=False, executor=estourar
    )
    assert resultado is ResultadoProcessamento.FALHOU
    atual = await recarregar_fonte(deps.fabrica, fonte.id)
    assert atual is not None and atual.codigo_falha == "conteudo_invalido"


# --- Falha técnica e novas tentativas (DTEC 030) ----------------------------------------------


class ArmazenamentoQueFalha(ArmazenamentoMemoria):
    async def ler_para_arquivo(self, chave: str, destino: Path) -> None:
        raise OSError("volume indisponível (detalhe interno)")


async def test_erro_transitorio_pede_nova_tentativa_e_a_fonte_segue_processando(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos["resumo.txt"])
    quebrado = ArmazenamentoQueFalha()
    quebrado.objetos = armazenamento.objetos
    com_falha = DependenciasTarefas(
        fabrica=deps.fabrica, armazenamento=quebrado, configuracao=deps.configuracao
    )

    with pytest.raises(ErroTransitorio):
        await executar_processar_fonte(fonte.id, com_falha, ultima_tentativa=False)

    atual = await recarregar_fonte(deps.fabrica, fonte.id)
    assert atual is not None and atual.estado == "processando"


async def test_tentativas_esgotadas_gravam_falha_tecnica_sem_relancar(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos["resumo.txt"])
    quebrado = ArmazenamentoQueFalha()
    quebrado.objetos = armazenamento.objetos
    com_falha = DependenciasTarefas(
        fabrica=deps.fabrica, armazenamento=quebrado, configuracao=deps.configuracao
    )

    resultado = await executar_processar_fonte(fonte.id, com_falha, ultima_tentativa=True)

    assert resultado is ResultadoProcessamento.FALHOU
    atual = await recarregar_fonte(deps.fabrica, fonte.id)
    assert atual is not None
    assert (atual.estado, atual.codigo_falha) == ("falhou", "falha_tecnica")


async def test_erro_transitorio_seguido_de_sucesso_conclui_na_tentativa_seguinte(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos["resumo.txt"])
    quebrado = ArmazenamentoQueFalha()
    quebrado.objetos = armazenamento.objetos
    com_falha = DependenciasTarefas(
        fabrica=deps.fabrica, armazenamento=quebrado, configuracao=deps.configuracao
    )
    with pytest.raises(ErroTransitorio):
        await executar_processar_fonte(fonte.id, com_falha, ultima_tentativa=False)

    assert await executar_processar_fonte(fonte.id, deps, ultima_tentativa=False) is (
        ResultadoProcessamento.CONCLUIDA
    )
    atual = await recarregar_fonte(deps.fabrica, fonte.id)
    assert atual is not None and atual.estado == "concluido"


async def test_objeto_ausente_com_a_fonte_existente_e_falha_tecnica(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos["resumo.txt"])
    await armazenamento.apagar(fonte.chave_objeto)

    resultado = await executar_processar_fonte(fonte.id, deps, ultima_tentativa=False)

    assert resultado is ResultadoProcessamento.FALHOU
    atual = await recarregar_fonte(deps.fabrica, fonte.id)
    assert atual is not None and (atual.estado, atual.codigo_falha) == ("falhou", "falha_tecnica")


async def test_objeto_e_fonte_ausentes_terminam_sem_efeito(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos["resumo.txt"])
    await armazenamento.apagar(fonte.chave_objeto)

    async def sumir_antes(*args: Any, **kwargs: Any) -> ResultadoIsolado:
        raise AssertionError("não deveria extrair")

    # A fonte some entre a transação A e a leitura do objeto.
    original = armazenamento.ler_para_arquivo

    async def ler_e_sumir(chave: str, destino: Path) -> None:
        async with unidade_de_trabalho(deps.fabrica) as sessao:
            await sessao.execute(delete(Fonte).where(Fonte.id == fonte.id))
        await original(chave, destino)

    armazenamento.ler_para_arquivo = ler_e_sumir  # type: ignore[method-assign]
    resultado = await executar_processar_fonte(
        fonte.id, deps, ultima_tentativa=False, executor=sumir_antes
    )
    assert resultado is ResultadoProcessamento.SEM_EFEITO


# --- Exclusão durante o processamento e idempotência (CB-16, RF-013, RF-008) ------------------


async def test_fonte_apagada_antes_da_gravacao_termina_sem_trechos(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    _, _, fonte = await semear_fonte(
        deps.fabrica, armazenamento, arquivos["biologia-citologia.pdf"]
    )

    async def apagar_durante_a_extracao(*args: Any, **kwargs: Any) -> ResultadoIsolado:
        resultado = await executar_isolado(*args, **kwargs)
        async with unidade_de_trabalho(deps.fabrica) as sessao:
            await sessao.execute(delete(Fonte).where(Fonte.id == fonte.id))
        return resultado

    resultado = await executar_processar_fonte(
        fonte.id, deps, ultima_tentativa=False, executor=apagar_durante_a_extracao
    )

    assert resultado is ResultadoProcessamento.SEM_EFEITO
    assert await recarregar_fonte(deps.fabrica, fonte.id) is None
    assert await _contar_trechos(deps.fabrica, fonte.id) == 0


async def test_reexecucao_concluida_sem_efeito_nao_substitui_os_trechos(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos["resumo.txt"])
    await executar_processar_fonte(fonte.id, deps, ultima_tentativa=False)
    async with unidade_de_trabalho(deps.fabrica) as sessao:
        antes = (
            (
                await sessao.execute(
                    select(Trecho.id).where(Trecho.fonte_id == fonte.id).order_by(Trecho.id)
                )
            )
            .scalars()
            .all()
        )

    segunda = await executar_processar_fonte(fonte.id, deps, ultima_tentativa=False)

    assert segunda is ResultadoProcessamento.SEM_EFEITO
    async with unidade_de_trabalho(deps.fabrica) as sessao:
        depois = (
            (
                await sessao.execute(
                    select(Trecho.id).where(Trecho.fonte_id == fonte.id).order_by(Trecho.id)
                )
            )
            .scalars()
            .all()
        )
    assert depois == antes


async def test_execucao_anterior_incompleta_nao_deixa_trechos_duplicados(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    _, _, fonte = await semear_fonte(
        deps.fabrica, armazenamento, arquivos["resumo.txt"], estado="processando"
    )
    async with unidade_de_trabalho(deps.fabrica) as sessao:
        sessao.add(
            Trecho(fonte_id=fonte.id, ordem=0, texto="resto", inicio_caractere=0, fim_caractere=5)
        )
        sessao.add(
            Trecho(fonte_id=fonte.id, ordem=1, texto="velho", inicio_caractere=6, fim_caractere=11)
        )

    assert await executar_processar_fonte(fonte.id, deps, ultima_tentativa=False) is (
        ResultadoProcessamento.CONCLUIDA
    )

    atual = await recarregar_fonte(deps.fabrica, fonte.id)
    assert atual is not None and atual.total_trechos == await _contar_trechos(
        deps.fabrica, fonte.id
    )
    async with unidade_de_trabalho(deps.fabrica) as sessao:
        textos = (
            (await sessao.execute(select(Trecho.texto).where(Trecho.fonte_id == fonte.id)))
            .scalars()
            .all()
        )
    assert "resto" not in textos and "velho" not in textos


async def test_fonte_inexistente_ou_ja_em_estado_final_termina_sem_efeito(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    assert await executar_processar_fonte(999_999, deps, ultima_tentativa=False) is (
        ResultadoProcessamento.SEM_EFEITO
    )
    _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos["digitalizado.pdf"])
    await executar_processar_fonte(fonte.id, deps, ultima_tentativa=False)
    assert await executar_processar_fonte(fonte.id, deps, ultima_tentativa=False) is (
        ResultadoProcessamento.SEM_EFEITO
    )
    atual = await recarregar_fonte(deps.fabrica, fonte.id)
    assert atual is not None and atual.codigo_falha == "sem_texto"


async def test_o_arquivo_temporario_e_apagado_no_sucesso_e_na_falha(
    deps: DependenciasTarefas,
    armazenamento: ArmazenamentoMemoria,
    arquivos: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    for nome in ("resumo.txt", "corrompido.pdf"):
        _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos[nome])
        await executar_processar_fonte(fonte.id, deps, ultima_tentativa=False)
    assert await asyncio.to_thread(os.listdir, tmp_path) == []


async def test_o_arquivo_temporario_e_apagado_mesmo_com_erro_transitorio(
    deps: DependenciasTarefas,
    armazenamento: ArmazenamentoMemoria,
    arquivos: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    _, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos["resumo.txt"])
    quebrado = ArmazenamentoQueFalha()
    quebrado.objetos = armazenamento.objetos
    com_falha = DependenciasTarefas(
        fabrica=deps.fabrica, armazenamento=quebrado, configuracao=deps.configuracao
    )
    with pytest.raises(ErroTransitorio):
        await executar_processar_fonte(fonte.id, com_falha, ultima_tentativa=False)
    assert await asyncio.to_thread(os.listdir, tmp_path) == []


# --- Registro da tarefa (DTEC 030) ------------------------------------------------------------


def test_processar_fonte_esta_registrada_com_novas_tentativas_so_para_erro_transitorio() -> None:
    tarefa = app_fila.tasks["fontes.processar_fonte"]
    estrategia = tarefa.retry_strategy
    assert isinstance(estrategia, RetryStrategy)
    assert estrategia.max_attempts == 2
    assert estrategia.exponential_wait == 5
    assert set(estrategia.retry_exceptions or ()) == {ErroTransitorio}


def test_reconciliar_objetos_roda_todo_dia_as_3h30_utc() -> None:
    periodicas = {
        nome: tarefa.cron for (nome, _), tarefa in app_fila.periodic_registry.periodic_tasks.items()
    }
    assert periodicas["fontes.reconciliar_objetos"] == "30 3 * * *"


# --- Envio: rollback compensa o objeto (DTEC 025) ---------------------------------------------


async def test_rollback_compensa_objeto_e_nao_deixa_linha_nem_job(
    fabrica_real: FabricaSessoes,
    configuracao: Configuracao,
    monkeypatch: pytest.MonkeyPatch,
    arquivos: dict[str, Any],
) -> None:
    armazenamento = ArmazenamentoMemoria()
    usuario, materia, _ = await semear_fonte(fabrica_real, armazenamento, arquivos["resumo.txt"])
    servico = ServicoFontes(fabrica_real, configuracao, armazenamento, RegistroAcervo())
    objetos_antes = set(armazenamento.objetos)

    from app.fontes import servicos

    original = servicos.enfileirar

    async def enfileirar_e_falhar(*args: Any, **kwargs: Any) -> int:
        await original(*args, **kwargs)
        raise RuntimeError("falha depois de enfileirar")

    monkeypatch.setattr(servicos, "enfileirar", enfileirar_e_falhar)

    with pytest.raises(RuntimeError, match="falha depois"):
        await servico.enviar(
            usuario_id=usuario.id,
            usuario_public_id=usuario.public_id,
            materia_id=materia.public_id,
            nome_enviado="novo.txt",
            origem=io.BytesIO(b"Texto novo e diferente.\n"),
            titulo=None,
        )

    assert set(armazenamento.objetos) == objetos_antes, "o objeto gravado foi compensado"
    async with unidade_de_trabalho(fabrica_real) as sessao:
        fontes = (await sessao.execute(select(func.count()).select_from(Fonte))).scalar_one()
        jobs = (
            await sessao.execute(
                text(
                    "SELECT count(*) FROM procrastinate_jobs "
                    "WHERE task_name = 'fontes.processar_fonte'"
                )
            )
        ).scalar_one()
    assert fontes == 1, "só a fonte semeada; a nova não ficou"
    assert jobs == 0


async def test_envio_para_materia_inexistente_nao_grava_objeto(
    fabrica_sessoes: FabricaSessoes, configuracao: Configuracao, arquivos: dict[str, Any]
) -> None:
    armazenamento = ArmazenamentoMemoria()
    usuario, _, _ = await semear_fonte(fabrica_sessoes, armazenamento, arquivos["resumo.txt"])
    servico = ServicoFontes(fabrica_sessoes, configuracao, armazenamento, RegistroAcervo())
    antes = set(armazenamento.objetos)
    import uuid

    with pytest.raises(RecursoNaoEncontrado):
        await servico.enviar(
            usuario_id=usuario.id,
            usuario_public_id=usuario.public_id,
            materia_id=uuid.uuid4(),
            nome_enviado="x.txt",
            origem=io.BytesIO(b"texto\n"),
            titulo=None,
        )
    assert set(armazenamento.objetos) == antes


# --- Reconciliação (DTEC 025) -----------------------------------------------------------------


async def test_reconciliacao_apaga_so_orfaos_mais_antigos_que_a_margem(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria, arquivos: dict[str, Any]
) -> None:
    usuario, _, fonte = await semear_fonte(deps.fabrica, armazenamento, arquivos["resumo.txt"])
    prefixo = f"usuarios/{usuario.public_id}/"
    agora = datetime.now(UTC)
    velho = agora - timedelta(hours=3)
    recente = agora - timedelta(minutes=5)
    armazenamento.colocar(prefixo + "fontes/orfao-velho", b"x", criado_em=velho)
    armazenamento.colocar(prefixo + "fontes/orfao-recente", b"x", criado_em=recente)
    armazenamento.colocar(prefixo + "imagens/outra-spec", b"x", criado_em=velho)
    armazenamento.colocar("sistema/sondas/qualquer", b"x", criado_em=velho)
    armazenamento.colocar(fonte.chave_objeto, b"conteudo", criado_em=velho)

    apagados = await executar_reconciliacao(deps, agora)

    assert apagados == 1
    restantes = set(armazenamento.objetos)
    assert prefixo + "fontes/orfao-velho" not in restantes
    assert {
        prefixo + "fontes/orfao-recente",
        prefixo + "imagens/outra-spec",
        "sistema/sondas/qualquer",
        fonte.chave_objeto,
    } <= restantes


async def test_reconciliacao_e_idempotente_e_respeita_a_margem_da_configuracao(
    deps: DependenciasTarefas, armazenamento: ArmazenamentoMemoria
) -> None:
    agora = datetime.now(UTC)
    chave = "usuarios/0b8f9a4e-0000-4000-8000-0000000000aa/fontes/orfao"
    armazenamento.colocar(chave, b"x", criado_em=agora - timedelta(minutes=61))
    assert await executar_reconciliacao(deps, agora) == 1
    assert await executar_reconciliacao(deps, agora) == 0

    armazenamento.colocar(chave, b"x", criado_em=agora - timedelta(minutes=59))
    assert await executar_reconciliacao(deps, agora) == 0
    assert await asyncio.to_thread(lambda: chave in armazenamento.objetos)
