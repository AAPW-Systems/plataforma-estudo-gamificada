"""T008 (spec 004, DTEC 021 e 039): a exclusão da conta apaga o consumo e as ciências."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.ia.modelos import CienciaAvisoIa, ConsumoIa
from app.ia.registros import ORDEM_EXCLUSAO, apagar_dados_usuario
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.exclusao import registro_exclusao
from tests.apoio_cartoes import semear_estudante

pytestmark = pytest.mark.integration


def _consumo(usuario_id: int) -> ConsumoIa:
    return ConsumoIa(
        usuario_id=usuario_id,
        operacao="gerar_cartoes",
        provedor="teste",
        modelo="simulado",
        latencia_ms=1,
        sucesso=True,
    )


async def test_apaga_so_as_linhas_do_usuario(fabrica_sessoes: FabricaSessoes) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        ana, _ = await semear_estudante(sessao)
        bia, _ = await semear_estudante(sessao)
        for usuario in (ana, bia):
            sessao.add_all(
                [
                    _consumo(usuario.id),
                    _consumo(usuario.id),
                    CienciaAvisoIa(usuario_id=usuario.id, versao_aviso="gemini-v1"),
                    CienciaAvisoIa(usuario_id=usuario.id, versao_aviso="groq-v1"),
                ]
            )
        await sessao.flush()

        await apagar_dados_usuario(sessao, ana.id)

        async def contar(modelo: type[ConsumoIa] | type[CienciaAvisoIa], usuario_id: int) -> int:
            consulta = select(func.count()).select_from(modelo).filter_by(usuario_id=usuario_id)
            return (await sessao.execute(consulta)).scalar_one()

        assert (await contar(ConsumoIa, ana.id), await contar(CienciaAvisoIa, ana.id)) == (0, 0)
        assert (await contar(ConsumoIa, bia.id), await contar(CienciaAvisoIa, bia.id)) == (2, 2)


def test_registrado_na_exclusao_da_conta_antes_da_identidade() -> None:
    import app.principal  # noqa: F401  (a composição importa os registros)

    participantes = {p.dominio: p for p in registro_exclusao.em_ordem()}
    assert participantes["ia"].apagar is apagar_dados_usuario
    assert participantes["ia"].ordem == ORDEM_EXCLUSAO < participantes["identidade"].ordem
