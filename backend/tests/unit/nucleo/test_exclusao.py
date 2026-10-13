"""Registro de exclusão por domínio: ordem e registro único (DTEC 021)."""

from __future__ import annotations

from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.exclusao import RegistroExclusao

pytestmark = pytest.mark.unit


def _gravador(chamadas: list[tuple[str, int]], nome: str):  # type: ignore[no-untyped-def]
    async def apagar(_sessao: AsyncSession, usuario_id: int) -> None:
        chamadas.append((nome, usuario_id))

    return apagar


async def test_apaga_na_ordem_crescente_independente_do_registro() -> None:
    registro = RegistroExclusao()
    chamadas: list[tuple[str, int]] = []
    registro.registrar(950, "identidade", _gravador(chamadas, "identidade"))
    registro.registrar(100, "materias", _gravador(chamadas, "materias"))
    registro.registrar(900, "revisao", _gravador(chamadas, "revisao"))

    await registro.apagar_dados_usuario(cast(AsyncSession, None), 7)

    assert chamadas == [("materias", 7), ("revisao", 7), ("identidade", 7)]


def test_registrar_de_novo_a_mesma_funcao_e_idempotente() -> None:
    registro = RegistroExclusao()
    funcao = _gravador([], "x")
    registro.registrar(100, "x", funcao)
    registro.registrar(100, "x", funcao)
    assert [p.dominio for p in registro.em_ordem()] == ["x"]


def test_dominio_nao_registra_duas_funcoes() -> None:
    registro = RegistroExclusao()
    registro.registrar(100, "x", _gravador([], "a"))
    with pytest.raises(ValueError, match="já registrou"):
        registro.registrar(110, "x", _gravador([], "b"))


def test_dois_dominios_nao_dividem_a_mesma_ordem() -> None:
    registro = RegistroExclusao()
    registro.registrar(100, "x", _gravador([], "x"))
    with pytest.raises(ValueError, match="ordem 100"):
        registro.registrar(100, "y", _gravador([], "y"))
