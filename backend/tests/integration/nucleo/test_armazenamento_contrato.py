"""Suíte de contrato do armazenamento, rodada contra os dois adaptadores (DTEC 010 e 021)."""

from __future__ import annotations

import os
import stat
import sys
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.nucleo.armazenamento import (
    Armazenamento,
    ArmazenamentoDisco,
    ArmazenamentoMemoria,
    ChaveInvalida,
    ObjetoInexistente,
    prefixo_usuario,
)

pytestmark = pytest.mark.integration

type Colocar = Callable[[str, bytes], None]


@pytest.fixture(params=["memoria", "disco"])
def adaptador(request: pytest.FixtureRequest, tmp_path: Path) -> tuple[Armazenamento, Colocar]:
    if request.param == "memoria":
        memoria = ArmazenamentoMemoria()
        return memoria, memoria.colocar

    raiz = tmp_path / "arquivos"
    raiz.mkdir()
    disco = ArmazenamentoDisco(raiz)

    def colocar(chave: str, dados: bytes) -> None:
        caminho = disco.caminho_objeto(chave)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(dados)

    return disco, colocar


A = "usuarios/0b8f9a4e-0000-4000-8000-00000000000a/"
B = "usuarios/0b8f9a4e-0000-4000-8000-00000000000b/"


async def test_apagar_prefixo_remove_so_os_objetos_do_prefixo(
    adaptador: tuple[Armazenamento, Colocar],
) -> None:
    armazenamento, colocar = adaptador
    colocar(A + "fontes/1", b"a1")
    colocar(A + "imagens/2", b"a2")
    colocar(B + "fontes/3", b"b3")

    assert await armazenamento.apagar_prefixo(A) == 2

    assert not await armazenamento.existe(A + "fontes/1")
    assert not await armazenamento.existe(A + "imagens/2")
    assert await armazenamento.existe(B + "fontes/3")


async def test_apagar_prefixo_e_idempotente(adaptador: tuple[Armazenamento, Colocar]) -> None:
    armazenamento, colocar = adaptador
    colocar(A + "fontes/1", b"x")
    assert await armazenamento.apagar_prefixo(A) == 1
    assert await armazenamento.apagar_prefixo(A) == 0


async def test_prefixo_parecido_nao_e_apagado(adaptador: tuple[Armazenamento, Colocar]) -> None:
    armazenamento, colocar = adaptador
    colocar("usuarios/abc/fontes/1", b"x")
    colocar("usuarios/abcd/fontes/1", b"y")
    assert await armazenamento.apagar_prefixo("usuarios/abc/") == 1
    assert await armazenamento.existe("usuarios/abcd/fontes/1")


@pytest.mark.parametrize(
    "prefixo",
    [
        "../",
        "usuarios/../",
        "usuarios/../../etc/",
        "/etc/",
        "usuarios\\x/",
        "usuarios//",
        "usuarios/./",
        "usuarios/a",  # sem barra final
        "",
        "/",
    ],
)
async def test_prefixo_que_escapa_da_raiz_e_recusado(
    adaptador: tuple[Armazenamento, Colocar], prefixo: str
) -> None:
    armazenamento, _ = adaptador
    with pytest.raises(ChaveInvalida):
        await armazenamento.apagar_prefixo(prefixo)


@pytest.mark.parametrize("chave", ["../segredo", "usuarios/a/../../x", "/abs", "a//b", ".oculto"])
async def test_chave_que_escapa_da_raiz_e_recusada(
    adaptador: tuple[Armazenamento, Colocar], chave: str
) -> None:
    armazenamento, _ = adaptador
    with pytest.raises(ChaveInvalida):
        await armazenamento.existe(chave)


def test_prefixo_do_usuario_segue_a_dtec_021() -> None:
    assert prefixo_usuario("0b8f9a4e-0000-4000-8000-00000000000a") == A


async def test_disco_nao_segue_link_simbolico_para_fora_da_raiz(tmp_path: Path) -> None:
    raiz = tmp_path / "arquivos"
    fora = tmp_path / "fora"
    (raiz / "usuarios").mkdir(parents=True)
    fora.mkdir()
    (fora / "valioso").write_bytes(b"nao apagar")
    try:
        (raiz / "usuarios" / "x").symlink_to(fora, target_is_directory=True)
    except OSError:
        pytest.skip("o sistema não permite criar links simbólicos")
    with pytest.raises(ChaveInvalida):
        await ArmazenamentoDisco(raiz).apagar_prefixo("usuarios/x/")
    assert (fora / "valioso").exists()


# --- Operações da 002: gravar, ler_para_arquivo, apagar e listar_prefixo (DTEC 025) -----------

CHAVE = A + "fontes/0b8f9a4e-0000-4000-8000-0000000000f1"


def _arquivo(tmp_path: Path, conteudo: bytes, nome: str = "origem.bin") -> Path:
    caminho = tmp_path / nome
    caminho.write_bytes(conteudo)
    return caminho


async def test_gravar_e_ler_devolvem_os_mesmos_bytes(
    adaptador: tuple[Armazenamento, Colocar], tmp_path: Path
) -> None:
    armazenamento, _ = adaptador
    await armazenamento.gravar(CHAVE, _arquivo(tmp_path, b"conteudo\x00binario"))
    destino = tmp_path / "saida.bin"
    await armazenamento.ler_para_arquivo(CHAVE, destino)
    assert destino.read_bytes() == b"conteudo\x00binario"
    assert await armazenamento.existe(CHAVE)


async def test_gravar_sobre_chave_existente_substitui(
    adaptador: tuple[Armazenamento, Colocar], tmp_path: Path
) -> None:
    armazenamento, _ = adaptador
    await armazenamento.gravar(CHAVE, _arquivo(tmp_path, b"um"))
    await armazenamento.gravar(CHAVE, _arquivo(tmp_path, b"dois", "outro.bin"))
    destino = tmp_path / "saida.bin"
    await armazenamento.ler_para_arquivo(CHAVE, destino)
    assert destino.read_bytes() == b"dois"


async def test_ler_objeto_inexistente_levanta_objeto_inexistente(
    adaptador: tuple[Armazenamento, Colocar], tmp_path: Path
) -> None:
    armazenamento, _ = adaptador
    destino = tmp_path / "saida.bin"
    with pytest.raises(ObjetoInexistente):
        await armazenamento.ler_para_arquivo(CHAVE, destino)
    assert not destino.exists()


async def test_apagar_e_idempotente_e_so_atinge_a_chave(
    adaptador: tuple[Armazenamento, Colocar], tmp_path: Path
) -> None:
    armazenamento, _ = adaptador
    vizinha = A + "fontes/vizinha"
    await armazenamento.gravar(CHAVE, _arquivo(tmp_path, b"x"))
    await armazenamento.gravar(vizinha, _arquivo(tmp_path, b"y", "v.bin"))
    assert await armazenamento.apagar(CHAVE) is True
    assert await armazenamento.apagar(CHAVE) is False
    assert not await armazenamento.existe(CHAVE)
    assert await armazenamento.existe(vizinha)


async def test_listar_prefixo_devolve_chave_e_data_de_criacao(
    adaptador: tuple[Armazenamento, Colocar], tmp_path: Path
) -> None:
    armazenamento, _ = adaptador
    antes = datetime.now(UTC) - timedelta(seconds=5)
    await armazenamento.gravar(A + "fontes/b", _arquivo(tmp_path, b"1"))
    await armazenamento.gravar(A + "fontes/a", _arquivo(tmp_path, b"2", "2.bin"))
    await armazenamento.gravar(B + "fontes/c", _arquivo(tmp_path, b"3", "3.bin"))

    itens = await armazenamento.listar_prefixo(A)

    assert [item.chave for item in itens] == [A + "fontes/a", A + "fontes/b"]
    for item in itens:
        assert item.criado_em.tzinfo is not None
        assert antes <= item.criado_em <= datetime.now(UTC) + timedelta(seconds=5)
    assert await armazenamento.listar_prefixo("usuarios/inexistente/") == []


async def test_listar_prefixo_nao_mistura_prefixo_parecido(
    adaptador: tuple[Armazenamento, Colocar], tmp_path: Path
) -> None:
    armazenamento, _ = adaptador
    await armazenamento.gravar("usuarios/abc/fontes/1", _arquivo(tmp_path, b"1"))
    await armazenamento.gravar("usuarios/abcd/fontes/1", _arquivo(tmp_path, b"2", "2.bin"))
    assert [i.chave for i in await armazenamento.listar_prefixo("usuarios/abc/")] == [
        "usuarios/abc/fontes/1"
    ]


MALICIOSAS = ["../segredo", "usuarios/a/../../x", "/abs", "a//b", ".oculto", "usuarios\\a/b", ""]


@pytest.mark.parametrize("chave", MALICIOSAS)
async def test_path_traversal_e_recusado_em_todas_as_operacoes(
    adaptador: tuple[Armazenamento, Colocar], tmp_path: Path, chave: str
) -> None:
    armazenamento, _ = adaptador
    origem = _arquivo(tmp_path, b"x")
    with pytest.raises(ChaveInvalida):
        await armazenamento.gravar(chave, origem)
    with pytest.raises(ChaveInvalida):
        await armazenamento.ler_para_arquivo(chave, tmp_path / "saida.bin")
    with pytest.raises(ChaveInvalida):
        await armazenamento.apagar(chave)
    with pytest.raises(ChaveInvalida):
        await armazenamento.listar_prefixo(chave if chave.endswith("/") else chave + "/")


async def test_gravar_nao_grava_fora_da_raiz_mesmo_com_link_simbolico(tmp_path: Path) -> None:
    raiz = tmp_path / "arquivos"
    fora = tmp_path / "fora"
    (raiz / "usuarios").mkdir(parents=True)
    fora.mkdir()
    try:
        (raiz / "usuarios" / "x").symlink_to(fora, target_is_directory=True)
    except OSError:
        pytest.skip("o sistema não permite criar links simbólicos")
    with pytest.raises(ChaveInvalida):
        await ArmazenamentoDisco(raiz).gravar("usuarios/x/fontes/1", _arquivo(tmp_path, b"x"))
    assert list(fora.iterdir()) == []


# --- Específicos do disco --------------------------------------------------------------------


@pytest.mark.skipif(sys.platform == "win32", reason="permissões POSIX")
async def test_disco_grava_com_permissao_0600(tmp_path: Path) -> None:
    raiz = tmp_path / "arquivos"
    disco = ArmazenamentoDisco(raiz)
    await disco.gravar(CHAVE, _arquivo(tmp_path, b"x"))
    assert stat.S_IMODE(os.stat(disco.caminho_objeto(CHAVE)).st_mode) == 0o600


async def test_disco_grava_de_forma_atomica_sem_deixar_temporario(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raiz = tmp_path / "arquivos"
    disco = ArmazenamentoDisco(raiz)
    await disco.gravar(CHAVE, _arquivo(tmp_path, b"original"))
    assert [i.chave for i in await disco.listar_prefixo(A)] == [CHAVE]

    def falhar(*_: object, **__: object) -> None:
        raise OSError("disco cheio simulado")

    monkeypatch.setattr(os, "replace", falhar)
    with pytest.raises(OSError, match="simulado"):
        await disco.gravar(CHAVE, _arquivo(tmp_path, b"novo", "novo.bin"))
    monkeypatch.undo()

    # O objeto antigo está intacto e nenhum arquivo temporário sobrou.
    destino = tmp_path / "saida.bin"
    await disco.ler_para_arquivo(CHAVE, destino)
    assert destino.read_bytes() == b"original"
    assert [p.name for p in disco.caminho_objeto(CHAVE).parent.iterdir()] == [
        disco.caminho_objeto(CHAVE).name
    ]


async def test_disco_lista_a_data_pela_modificacao_do_arquivo(tmp_path: Path) -> None:
    disco = ArmazenamentoDisco(tmp_path / "arquivos")
    await disco.gravar(CHAVE, _arquivo(tmp_path, b"x"))
    antigo = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    os.utime(disco.caminho_objeto(CHAVE), (antigo.timestamp(), antigo.timestamp()))
    assert (await disco.listar_prefixo(A))[0].criado_em == antigo


async def test_memoria_aceita_data_de_criacao_para_testes_de_reconciliacao() -> None:
    memoria = ArmazenamentoMemoria()
    antigo = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    memoria.colocar(CHAVE, b"x", criado_em=antigo)
    assert (await memoria.listar_prefixo(A))[0].criado_em == antigo
