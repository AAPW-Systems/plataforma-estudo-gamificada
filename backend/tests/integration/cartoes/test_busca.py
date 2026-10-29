"""T034: busca e filtros da lista de cartões contra o PostgreSQL real (DTEC 033; RF-010).

A expressão é `lower(unaccent(coluna)) LIKE '%' || lower(unaccent(:termo)) || '%' ESCAPE '\\'`,
com `%`, `_` e `\\` escapados no termo, que vai sempre como parâmetro.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from typing import Any

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.cartoes.modelos import OrigemCartao, SituacaoCartao
from app.cartoes.repositorios import FiltrosCartoes, RepositorioCartoes, escapar_like
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from tests import fabricas_cartoes as fab
from tests.apoio_cartoes import AGORA, semear_estudante

pytestmark = pytest.mark.integration

TEXTOS: list[tuple[str, str, OrigemCartao, SituacaoCartao]] = [
    ("O que é a Célula?", "A unidade da vida.", OrigemCartao.CRIADO, SituacaoCartao.ATIVO),
    ("CÉLULA eucarionte", "Tem núcleo.", OrigemCartao.EDITADO, SituacaoCartao.SUSPENSO),
    ("Mitose", "Divide a celula em duas.", OrigemCartao.GERADO_VERIFICADO, SituacaoCartao.ATIVO),
    ("Qual é a ação da enzima?", "Catalisar.", OrigemCartao.CRIADO, SituacaoCartao.SUSPENSO),
    ("Taxa de 100% de acerto", "Meta_final", OrigemCartao.CRIADO, SituacaoCartao.ATIVO),
    ("Caminho C:\\dados", "Barra invertida", OrigemCartao.CRIADO, SituacaoCartao.ATIVO),
    ("Taxa de 100 acertos", "Metaxfinal", OrigemCartao.CRIADO, SituacaoCartao.ATIVO),
    ("Proteína", "Cadeia de aminoácidos.", OrigemCartao.CRIADO, SituacaoCartao.ATIVO),
]


async def _semear(sessao: AsyncSession) -> tuple[int, int]:
    usuario, materia = await semear_estudante(sessao)
    base = fab.cartao_ficticio()
    itens = [
        replace(base, frente=f, verso=v, origem=o, situacao=s, com_referencia=False)
        for f, v, o, s in TEXTOS
    ]
    await fab.inserir(
        sessao, usuario_id=usuario.id, materia_id=materia.id, itens=itens, agora=AGORA
    )
    # Outra conta com os mesmos textos: a busca nunca a alcança.
    outro, materia_outro = await semear_estudante(sessao, materia="Biologia do outro")
    await fab.inserir(
        sessao, usuario_id=outro.id, materia_id=materia_outro.id, itens=itens, agora=AGORA
    )
    return usuario.id, materia.id


async def _frentes(fabrica: FabricaSessoes, filtros: FiltrosCartoes) -> tuple[list[str], int]:
    async with unidade_de_trabalho(fabrica) as sessao:
        usuario_id, materia_id = await _semear(sessao)
        repositorio = RepositorioCartoes(sessao)
        linhas, _ = await repositorio.listar(usuario_id, materia_id, filtros=filtros, limite=100)
        total = await repositorio.contar(usuario_id, materia_id, filtros=filtros)
    return sorted(linha.cartao.frente for linha in linhas), total


@pytest.mark.parametrize(
    ("termo", "esperadas"),
    [
        ("celula", ["CÉLULA eucarionte", "Mitose", "O que é a Célula?"]),
        ("CÉLULA", ["CÉLULA eucarionte", "Mitose", "O que é a Célula?"]),
        ("Célula", ["CÉLULA eucarionte", "Mitose", "O que é a Célula?"]),
        ("ÇÃO", ["Qual é a ação da enzima?"]),
        ("acao", ["Qual é a ação da enzima?"]),
        ("aminoacidos", ["Proteína"]),  # só no verso, com acento no texto e não no termo
        ("PROTEINA", ["Proteína"]),
        ("ula euc", ["CÉLULA eucarionte"]),  # pedaço de palavra, com espaço no meio
    ],
)
async def test_busca_sem_diferenciar_maiusculas_e_acentos_na_frente_e_no_verso(
    fabrica_sessoes: FabricaSessoes, termo: str, esperadas: list[str]
) -> None:
    frentes, total = await _frentes(fabrica_sessoes, FiltrosCartoes(busca=termo))
    assert frentes == sorted(esperadas)
    assert total == len(esperadas)


@pytest.mark.parametrize(
    ("termo", "esperadas"),
    [
        ("100%", ["Taxa de 100% de acerto"]),  # sem o escape, "100%" acharia "100 acertos"
        ("%", ["Taxa de 100% de acerto"]),
        ("a_f", ["Taxa de 100% de acerto"]),  # sem o escape, "_" casaria também "Metaxfinal"
        ("_", ["Taxa de 100% de acerto"]),
        ("\\", ["Caminho C:\\dados"]),
        ("c:\\d", ["Caminho C:\\dados"]),
        ("%%", []),
        ("\\%", []),
    ],
)
async def test_curingas_e_barra_invertida_sao_literais(
    fabrica_sessoes: FabricaSessoes, termo: str, esperadas: list[str]
) -> None:
    frentes, total = await _frentes(fabrica_sessoes, FiltrosCartoes(busca=termo))
    assert frentes == sorted(esperadas)
    assert total == len(esperadas)


def test_escapar_like_protege_os_tres_caracteres_especiais() -> None:
    assert escapar_like("100%") == "100\\%"
    assert escapar_like("a_b") == "a\\_b"
    assert escapar_like("c:\\d") == "c:\\\\d"
    assert escapar_like("\\%_") == "\\\\\\%\\_"
    assert escapar_like("sem especiais") == "sem especiais"


@pytest.mark.parametrize(
    ("filtros", "esperadas"),
    [
        (
            FiltrosCartoes(situacao=SituacaoCartao.SUSPENSO),
            ["CÉLULA eucarionte", "Qual é a ação da enzima?"],
        ),
        (FiltrosCartoes(origem=OrigemCartao.EDITADO), ["CÉLULA eucarionte"]),
        (FiltrosCartoes(origem=OrigemCartao.GERADO_VERIFICADO), ["Mitose"]),
        (
            FiltrosCartoes(busca="celula", situacao=SituacaoCartao.ATIVO),
            ["Mitose", "O que é a Célula?"],
        ),
        (
            FiltrosCartoes(busca="celula", origem=OrigemCartao.CRIADO),
            ["O que é a Célula?"],
        ),
        (
            FiltrosCartoes(
                busca="celula", situacao=SituacaoCartao.SUSPENSO, origem=OrigemCartao.EDITADO
            ),
            ["CÉLULA eucarionte"],
        ),
        (
            FiltrosCartoes(
                busca="celula", situacao=SituacaoCartao.SUSPENSO, origem=OrigemCartao.CRIADO
            ),
            [],
        ),
        (FiltrosCartoes(), sorted(f for f, *_ in TEXTOS)),
    ],
)
async def test_busca_combina_com_situacao_e_origem(
    fabrica_sessoes: FabricaSessoes, filtros: FiltrosCartoes, esperadas: list[str]
) -> None:
    frentes, total = await _frentes(fabrica_sessoes, filtros)
    assert frentes == sorted(esperadas)
    assert total == len(esperadas)


@pytest.fixture
def consultas(engine: AsyncEngine) -> Iterator[list[tuple[str, Any]]]:
    """Cada comando enviado ao banco, com os parâmetros, enquanto o teste roda."""
    capturadas: list[tuple[str, Any]] = []

    def _capturar(_c: Any, _cur: Any, sql: str, parametros: Any, *_: Any) -> None:
        capturadas.append((sql, parametros))

    event.listen(engine.sync_engine, "before_cursor_execute", _capturar)
    yield capturadas
    event.remove(engine.sync_engine, "before_cursor_execute", _capturar)


async def test_o_termo_vai_como_parametro_e_nunca_dentro_do_sql(
    fabrica_sessoes: FabricaSessoes, consultas: list[tuple[str, Any]]
) -> None:
    termo = "x'); DROP TABLE cartoes; --"
    frentes, total = await _frentes(fabrica_sessoes, FiltrosCartoes(busca=termo))

    assert (frentes, total) == ([], 0)
    da_busca = [(sql, p) for sql, p in consultas if "unaccent" in sql]
    assert len(da_busca) == 2, "a listagem e a contagem usam a mesma expressão"
    for sql, parametros in da_busca:
        assert "DROP TABLE" not in sql and termo not in sql
        assert "ESCAPE" in sql.upper()
        assert any(termo in str(valor) for valor in dict(parametros).values()), parametros
