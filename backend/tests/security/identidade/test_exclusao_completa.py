"""Exclusão completa da conta, linhas e objetos (T054; CS-004, RF-015, DTEC 021).

Pelo catálogo do PostgreSQL, toda tabela com a coluna `usuario_id` fica sem linhas da conta:
um domínio que esquecer de registrar a sua exclusão é detectado aqui, sem lista manual.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.identidade import tarefas
from app.nucleo.armazenamento import ArmazenamentoDisco, prefixo_usuario
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.exclusao import ParticipanteExclusao, registro_exclusao
from tests.apoio_http import cadastrar
from tests.fabricas import dados_conta

pytestmark = pytest.mark.security


async def tabelas_com_usuario_id(sessao: AsyncSession) -> list[str]:
    linhas = await sessao.execute(
        text(
            "select table_name from information_schema.columns "
            "where table_schema = 'public' and column_name = 'usuario_id' order by table_name"
        )
    )
    return [linha.table_name for linha in linhas]


async def tabelas_com_residuo(sessao: AsyncSession, usuario_id: int) -> list[str]:
    """As tabelas com `usuario_id` que ainda têm linhas da conta, mais `usuarios`, se sobrou."""
    residuo: list[str] = []
    for tabela in await tabelas_com_usuario_id(sessao):
        total = (
            await sessao.execute(
                text(f'select count(*) from "{tabela}" where usuario_id = :id'),  # noqa: S608
                {"id": usuario_id},
            )
        ).scalar_one()
        if total:
            residuo.append(tabela)
    if (
        await sessao.execute(
            text("select count(*) from usuarios where id = :id"), {"id": usuario_id}
        )
    ).scalar_one():
        residuo.append("usuarios")
    return residuo


async def _ids(fabrica: FabricaSessoes) -> tuple[int, str]:
    async with unidade_de_trabalho(fabrica) as sessao:
        linha = (await sessao.execute(text("select id, public_id from usuarios"))).one()
    return linha.id, str(linha.public_id)


async def test_nenhuma_tabela_com_usuario_id_guarda_linhas_da_conta_excluida(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    conta = dados_conta()
    assert (await cadastrar(cliente, conta)).status_code == 201
    usuario_id, _ = await _ids(fabrica_sessoes)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        tabelas = await tabelas_com_usuario_id(sessao)
        # Pré-condição: a conta tem linhas nas tabelas da 001 (senão o teste não provaria nada).
        assert {"sessoes", "parametros_fsrs"} <= set(tabelas)
        assert set(await tabelas_com_residuo(sessao, usuario_id)) >= {
            "sessoes",
            "parametros_fsrs",
            "usuarios",
        }

    resposta = await cliente.post("/api/v1/perfil/exclusao", json={"senhaAtual": conta.senha})
    assert resposta.status_code == 204

    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        assert await tabelas_com_residuo(sessao, usuario_id) == []


async def test_o_catalogo_acusa_uma_tabela_de_dominio_que_esqueceu_de_se_registrar(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    """Prova que o teste acima falha de verdade quando um domínio novo não registra a exclusão."""
    conta = dados_conta()
    await cadastrar(cliente, conta)
    usuario_id, _ = await _ids(fabrica_sessoes)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        await sessao.execute(
            text("create table dominio_esquecido (id serial primary key, usuario_id bigint)")
        )
        await sessao.execute(
            text("insert into dominio_esquecido (usuario_id) values (:id)"), {"id": usuario_id}
        )

    assert (
        await cliente.post("/api/v1/perfil/exclusao", json={"senhaAtual": conta.senha})
    ).status_code == 204

    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        assert await tabelas_com_residuo(sessao, usuario_id) == ["dominio_esquecido"]


async def test_falha_no_meio_da_exclusao_desfaz_tudo_e_nao_enfileira_a_tarefa(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Atomicidade (DTEC 021): linhas, usuário e tarefa saem juntos ou não saem."""

    async def falhar(sessao: AsyncSession, usuario_id: int) -> None:
        raise RuntimeError("falha simulada no meio da exclusão")

    monkeypatch.setitem(
        registro_exclusao._participantes, "falha", ParticipanteExclusao(999, "falha", falhar)
    )
    conta = dados_conta()
    await cadastrar(cliente, conta)
    usuario_id, _ = await _ids(fabrica_sessoes)

    resposta = await cliente.post("/api/v1/perfil/exclusao", json={"senhaAtual": conta.senha})

    assert resposta.status_code == 500
    assert resposta.json()["codigo"] == "erro_interno"
    assert "simulada" not in resposta.text
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        assert set(await tabelas_com_residuo(sessao, usuario_id)) == {
            "sessoes",
            "parametros_fsrs",
            "usuarios",
        }
        jobs = (await sessao.execute(text("select count(*) from procrastinate_jobs"))).scalar_one()
    assert jobs == 0
    assert (await cliente.get("/api/v1/perfil")).status_code == 200


def test_identidade_e_revisao_estao_no_registro_de_exclusao_em_ordem() -> None:
    import app.identidade.registros  # noqa: F401
    import app.revisao.registros  # noqa: F401

    ordem = [p.dominio for p in registro_exclusao.em_ordem()]
    assert "revisao" in ordem and "identidade" in ordem
    assert ordem.index("revisao") < ordem.index("identidade"), "parâmetros antes do usuário"


# --- Objetos no armazenamento (CS-004) ------------------------------------------------------


def _criar_objetos(raiz: Path, public_id: str, n: int = 3) -> list[Path]:
    arquivos = []
    for i in range(n):
        caminho = raiz / "usuarios" / public_id / ("fontes" if i % 2 else "imagens") / f"{i}.bin"
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(b"conteudo ficticio")
        arquivos.append(caminho)
    return arquivos


async def test_nenhum_objeto_resta_sob_o_prefixo_do_usuario_depois_da_tarefa(
    tmp_path: Path,
) -> None:
    public_id = "11111111-2222-4333-8444-555555555555"
    outro = "99999999-2222-4333-8444-555555555555"
    meus = _criar_objetos(tmp_path, public_id, 5)
    dele = _criar_objetos(tmp_path, outro, 2)
    armazenamento = ArmazenamentoDisco(tmp_path)

    apagados = await tarefas.executar_apagar_objetos(armazenamento, public_id)

    assert apagados == 5
    assert not any(p.exists() for p in meus)
    assert not (tmp_path / "usuarios" / public_id).exists()
    assert all(p.exists() for p in dele), "o prefixo de outro estudante não é tocado"
    assert await armazenamento.existe(f"{prefixo_usuario(outro)}fontes/1.bin")


async def test_apagar_objetos_e_idempotente_e_aceita_usuario_sem_objetos(tmp_path: Path) -> None:
    public_id = "11111111-2222-4333-8444-555555555555"
    _criar_objetos(tmp_path, public_id, 2)
    armazenamento = ArmazenamentoDisco(tmp_path)
    assert await tarefas.executar_apagar_objetos(armazenamento, public_id) == 2
    assert await tarefas.executar_apagar_objetos(armazenamento, public_id) == 0
    assert (
        await tarefas.executar_apagar_objetos(armazenamento, "00000000-0000-4000-8000-000000000000")
        == 0
    )


@pytest.mark.parametrize("public_id", ["../outro", "..", "a/b", "", "x" * 300, "/etc"])
async def test_identificador_hostil_nunca_sai_do_prefixo_de_usuarios(
    tmp_path: Path, public_id: str
) -> None:
    sentinela = tmp_path / "fora.txt"
    sentinela.write_text("nao apague")
    with pytest.raises(ValueError):
        await tarefas.executar_apagar_objetos(ArmazenamentoDisco(tmp_path), public_id)
    assert sentinela.exists()


async def test_a_tarefa_registrada_apaga_pelo_armazenamento_configurado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    public_id = "11111111-2222-4333-8444-555555555555"
    _criar_objetos(tmp_path, public_id, 2)
    monkeypatch.setattr(tarefas, "criar_armazenamento_padrao", lambda: ArmazenamentoDisco(tmp_path))
    assert await tarefas.apagar_objetos_usuario(public_id=public_id) == 2
    assert not (tmp_path / "usuarios" / public_id).exists()
