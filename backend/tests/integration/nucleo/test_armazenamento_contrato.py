"""Suíte de contrato do armazenamento, rodada contra os dois adaptadores (DTEC 010 e 021)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from app.nucleo.armazenamento import (
    Armazenamento,
    ArmazenamentoDisco,
    ArmazenamentoMemoria,
    ChaveInvalida,
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
