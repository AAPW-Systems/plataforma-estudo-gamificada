"""Restrições do acervo no banco (T008): CHECKs, índices únicos e FK composta (RQ-003, D-004).

Escritas diretas com SQL: o banco precisa recusar o que a aplicação já impede, para que uma
falha de aplicação nunca produza dado incoerente.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import psycopg
import pytest
from psycopg import errors

from app.nucleo.configuracao import Configuracao

pytestmark = pytest.mark.integration

HASH = b"\x01" * 32


@pytest.fixture
def conexao(configuracao: Configuracao, banco_migrado: None) -> Iterator[psycopg.Connection]:
    """Conexão síncrona numa transação que é sempre desfeita."""
    with psycopg.connect(configuracao.conninfo()) as conexao:
        yield conexao
        conexao.rollback()


def _usuario(conexao: psycopg.Connection, email: str) -> int:
    linha = conexao.execute(
        "INSERT INTO usuarios(nome, email, senha_hash) VALUES ('Teste', %s, 'hash-ficticio') "
        "RETURNING id",
        (email,),
    ).fetchone()
    assert linha is not None
    return int(linha[0])


def _materia(conexao: psycopg.Connection, usuario_id: int, nome: str = "Biologia") -> int:
    linha = conexao.execute(
        "INSERT INTO materias(usuario_id, nome) VALUES (%s, %s) RETURNING id", (usuario_id, nome)
    ).fetchone()
    assert linha is not None
    return int(linha[0])


def _fonte(
    conexao: psycopg.Connection,
    usuario_id: int,
    materia_id: int,
    *,
    chave: str = "usuarios/u/fontes/1",
    hash_sha256: bytes = HASH,
    **colunas: Any,
) -> int:
    valores: dict[str, Any] = {
        "usuario_id": usuario_id,
        "materia_id": materia_id,
        "titulo": "Citologia",
        "nome_arquivo": "citologia.pdf",
        "chave_objeto": chave,
        "tipo_midia": "application/pdf",
        "tamanho_bytes": 1000,
        "hash_sha256": hash_sha256,
        **colunas,
    }
    nomes = ", ".join(valores)
    marcadores = ", ".join(["%s"] * len(valores))
    linha = conexao.execute(
        f"INSERT INTO fontes({nomes}) VALUES ({marcadores}) RETURNING id",  # noqa: S608
        list(valores.values()),
    ).fetchone()
    assert linha is not None
    return int(linha[0])


# --- Matérias --------------------------------------------------------------------------------


def test_nome_da_materia_e_unico_por_estudante_sem_diferenciar_caixa(
    conexao: psycopg.Connection,
) -> None:
    a = _usuario(conexao, "a@exemplo.com")
    b = _usuario(conexao, "b@exemplo.com")
    _materia(conexao, a, "Biologia")
    _materia(conexao, b, "biologia")  # outro estudante pode repetir
    with pytest.raises(errors.UniqueViolation):
        _materia(conexao, a, "BIOLOGIA")


# varchar(n) recusa o excesso antes do CHECK; os dois erros significam "o banco recusou".
RECUSA_DE_TAMANHO = (errors.CheckViolation, errors.StringDataRightTruncation)


@pytest.mark.parametrize("nome", ["", "x" * 61])
def test_nome_da_materia_de_1_a_60_caracteres(conexao: psycopg.Connection, nome: str) -> None:
    with pytest.raises(RECUSA_DE_TAMANHO):
        _materia(conexao, _usuario(conexao, "c@exemplo.com"), nome)


def test_materia_aceita_60_caracteres(conexao: psycopg.Connection) -> None:
    _materia(conexao, _usuario(conexao, "d@exemplo.com"), "x" * 60)


# --- Fontes ----------------------------------------------------------------------------------


def test_fonte_nasce_pendente_sem_codigo_de_falha(conexao: psycopg.Connection) -> None:
    usuario = _usuario(conexao, "e@exemplo.com")
    fonte = _fonte(conexao, usuario, _materia(conexao, usuario))
    linha = conexao.execute(
        "SELECT estado::text, codigo_falha, total_trechos, public_id FROM fontes WHERE id = %s",
        (fonte,),
    ).fetchone()
    assert linha is not None
    assert linha[:3] == ("pendente", None, None)
    assert linha[3] is not None


def test_conteudo_identico_na_mesma_materia_e_recusado_mas_vale_em_outra(
    conexao: psycopg.Connection,
) -> None:
    usuario = _usuario(conexao, "f@exemplo.com")
    m1 = _materia(conexao, usuario, "Biologia")
    m2 = _materia(conexao, usuario, "Química")
    _fonte(conexao, usuario, m1, chave="usuarios/u/fontes/1")
    _fonte(conexao, usuario, m2, chave="usuarios/u/fontes/2")  # outra matéria: aceito (D-004)
    with pytest.raises(errors.UniqueViolation):
        _fonte(conexao, usuario, m1, chave="usuarios/u/fontes/3")


def test_chave_do_objeto_e_unica(conexao: psycopg.Connection) -> None:
    usuario = _usuario(conexao, "g@exemplo.com")
    m = _materia(conexao, usuario)
    _fonte(conexao, usuario, m, chave="usuarios/u/fontes/1", hash_sha256=b"\x01" * 32)
    with pytest.raises(errors.UniqueViolation):
        _fonte(conexao, usuario, m, chave="usuarios/u/fontes/1", hash_sha256=b"\x02" * 32)


def test_fonte_numa_materia_de_outro_dono_e_recusada_pela_fk_composta(
    conexao: psycopg.Connection,
) -> None:
    """RQ-003, RN-01: o banco impede a fonte do estudante A numa matéria do estudante B."""
    a = _usuario(conexao, "h@exemplo.com")
    b = _usuario(conexao, "i@exemplo.com")
    materia_de_b = _materia(conexao, b)
    with pytest.raises(errors.ForeignKeyViolation):
        _fonte(conexao, a, materia_de_b)


def test_materia_com_fontes_nao_e_apagada_sem_apagar_as_fontes(
    conexao: psycopg.Connection,
) -> None:
    """A FK composta usa `restrict`: quem exclui a matéria apaga as fontes antes."""
    usuario = _usuario(conexao, "j@exemplo.com")
    m = _materia(conexao, usuario)
    _fonte(conexao, usuario, m)
    with pytest.raises(errors.ForeignKeyViolation):
        conexao.execute("DELETE FROM materias WHERE id = %s", (m,))


@pytest.mark.parametrize(
    ("coluna", "valor"),
    [
        ("titulo", ""),
        ("titulo", "x" * 121),
        ("nome_arquivo", ""),
        ("nome_arquivo", "x" * 256),
        ("tipo_midia", "image/png"),
        ("tamanho_bytes", 0),
        ("hash_sha256", b"\x01" * 31),
        ("total_paginas", 0),
    ],
)
def test_checks_das_colunas_da_fonte(
    conexao: psycopg.Connection, coluna: str, valor: object
) -> None:
    usuario = _usuario(conexao, "k@exemplo.com")
    m = _materia(conexao, usuario)
    colunas: dict[str, Any] = {coluna: valor}
    with pytest.raises(RECUSA_DE_TAMANHO):
        _fonte(conexao, usuario, m, **colunas)


def test_estado_falhou_exige_codigo_e_so_ele_aceita_codigo(conexao: psycopg.Connection) -> None:
    usuario = _usuario(conexao, "l@exemplo.com")
    m = _materia(conexao, usuario)
    with pytest.raises(errors.CheckViolation):
        _fonte(conexao, usuario, m, estado="falhou")
    conexao.rollback()
    usuario = _usuario(conexao, "l2@exemplo.com")
    m = _materia(conexao, usuario)
    with pytest.raises(errors.CheckViolation):
        _fonte(conexao, usuario, m, estado="processando", codigo_falha="sem_texto")
    conexao.rollback()
    usuario = _usuario(conexao, "l3@exemplo.com")
    m = _materia(conexao, usuario)
    _fonte(conexao, usuario, m, estado="falhou", codigo_falha="sem_texto")


def test_estado_concluido_exige_total_de_trechos_e_versao_e_so_ele_aceita(
    conexao: psycopg.Connection,
) -> None:
    usuario = _usuario(conexao, "m@exemplo.com")
    m = _materia(conexao, usuario)
    with pytest.raises(errors.CheckViolation):
        _fonte(conexao, usuario, m, estado="concluido")
    conexao.rollback()
    usuario = _usuario(conexao, "m2@exemplo.com")
    m = _materia(conexao, usuario)
    with pytest.raises(errors.CheckViolation):
        _fonte(conexao, usuario, m, estado="concluido", total_trechos=3)  # falta a versão
    conexao.rollback()
    usuario = _usuario(conexao, "m3@exemplo.com")
    m = _materia(conexao, usuario)
    with pytest.raises(errors.CheckViolation):
        _fonte(conexao, usuario, m, versao_extracao="v1")  # pendente com versão
    conexao.rollback()
    usuario = _usuario(conexao, "m4@exemplo.com")
    m = _materia(conexao, usuario)
    _fonte(conexao, usuario, m, estado="concluido", total_trechos=3, versao_extracao="v1")


# --- Trechos ---------------------------------------------------------------------------------


def _trecho(conexao: psycopg.Connection, fonte: int, **colunas: object) -> None:
    valores: dict[str, object] = {
        "fonte_id": fonte,
        "ordem": 0,
        "texto": "abc",
        "pagina": 1,
        "inicio_caractere": 0,
        "fim_caractere": 3,
        **colunas,
    }
    nomes = ", ".join(valores)
    marcadores = ", ".join(["%s"] * len(valores))
    conexao.execute(
        f"INSERT INTO trechos({nomes}) VALUES ({marcadores})",  # noqa: S608
        list(valores.values()),
    )


@pytest.fixture
def fonte(conexao: psycopg.Connection) -> int:
    usuario = _usuario(conexao, "t@exemplo.com")
    return _fonte(conexao, usuario, _materia(conexao, usuario))


def test_trecho_valido_e_ordem_unica_por_fonte(conexao: psycopg.Connection, fonte: int) -> None:
    _trecho(conexao, fonte, ordem=0)
    _trecho(conexao, fonte, ordem=1, inicio_caractere=2, fim_caractere=5)
    with pytest.raises(errors.UniqueViolation):
        _trecho(conexao, fonte, ordem=1)


def test_trecho_de_txt_nao_tem_pagina(conexao: psycopg.Connection, fonte: int) -> None:
    _trecho(conexao, fonte, pagina=None)


@pytest.mark.parametrize(
    "colunas",
    [
        {"ordem": -1},
        {"texto": ""},
        {"pagina": 0},
        {"inicio_caractere": -1, "fim_caractere": 2},
        {"inicio_caractere": 3, "fim_caractere": 3, "texto": ""},
        {"inicio_caractere": 0, "fim_caractere": 4},  # fim - inicio != comprimento do texto
        {"inicio_caractere": 5, "fim_caractere": 3},
    ],
)
def test_checks_do_trecho(
    conexao: psycopg.Connection, fonte: int, colunas: dict[str, object]
) -> None:
    with pytest.raises(errors.CheckViolation):
        _trecho(conexao, fonte, **colunas)


def test_apagar_a_fonte_apaga_os_trechos_em_cascata(
    conexao: psycopg.Connection, fonte: int
) -> None:
    _trecho(conexao, fonte)
    conexao.execute("DELETE FROM fontes WHERE id = %s", (fonte,))
    assert conexao.execute("SELECT count(*) FROM trechos").fetchone() == (0,)


def test_chaves_primarias_sao_generated_always(conexao: psycopg.Connection) -> None:
    linhas = conexao.execute(
        "SELECT table_name, identity_generation FROM information_schema.columns "
        "WHERE table_schema='public' AND column_name='id' "
        "AND table_name IN ('materias','fontes','trechos')"
    ).fetchall()
    assert sorted(linhas) == [("fontes", "ALWAYS"), ("materias", "ALWAYS"), ("trechos", "ALWAYS")]
