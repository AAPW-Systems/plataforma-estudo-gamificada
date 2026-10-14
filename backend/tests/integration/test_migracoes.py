"""T021: migrações reversíveis e invariantes de D-001 no PostgreSQL real."""

import psycopg
import pytest

from app.nucleo.configuracao import Configuracao
from tests.conftest import executar_alembic

pytestmark = pytest.mark.integration


def test_migracoes_sobem_descem(configuracao: Configuracao, banco_migrado: None) -> None:
    """T021: base → head → base → head, sem resíduos dos tipos da identidade."""
    tabelas = {"usuarios", "sessoes", "tentativas_acesso", "parametros_fsrs"}
    try:
        with psycopg.connect(configuracao.conninfo(), autocommit=True) as conexao:
            presentes = {
                r[0]
                for r in conexao.execute(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public'"
                )
            }
            assert tabelas <= presentes
            identidades = conexao.execute(
                "SELECT table_name, identity_generation FROM information_schema.columns "
                "WHERE table_schema='public' AND column_name='id' AND table_name = ANY(%s)",
                (list(tabelas),),
            ).fetchall()
            assert len(identidades) == 4
            assert all(geracao == "ALWAYS" for _, geracao in identidades)
        executar_alembic("downgrade", "0001")
        with psycopg.connect(configuracao.conninfo(), autocommit=True) as conexao:
            assert conexao.execute("SELECT to_regclass('usuarios')").fetchone() == (None,)
            assert conexao.execute("SELECT to_regclass('procrastinate_jobs')").fetchone() == (
                "procrastinate_jobs",
            )
        executar_alembic("upgrade", "head")
        executar_alembic("downgrade", "base")
        with psycopg.connect(configuracao.conninfo(), autocommit=True) as conexao:
            assert conexao.execute("SELECT to_regclass('usuarios')").fetchone() == (None,)
            assert conexao.execute(
                "SELECT count(*) FROM pg_type WHERE typname IN "
                "('papel_usuario', 'tipo_tentativa_acesso', 'origem_parametros_fsrs')"
            ).fetchone() == (0,)
    finally:
        executar_alembic("upgrade", "head")


def test_migracao_0003_do_acervo_sobe_e_desce(
    configuracao: Configuracao, banco_migrado: None
) -> None:
    """T008: a 0003 cria e remove tabelas e enums do acervo sem deixar resíduos."""
    acervo = {"materias", "fontes", "trechos"}
    try:
        with psycopg.connect(configuracao.conninfo(), autocommit=True) as conexao:
            presentes = {
                r[0]
                for r in conexao.execute(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public'"
                )
            }
            assert acervo <= presentes
        executar_alembic("downgrade", "0002")
        with psycopg.connect(configuracao.conninfo(), autocommit=True) as conexao:
            for tabela in acervo:
                assert conexao.execute("SELECT to_regclass(%s)", (tabela,)).fetchone() == (None,)
            assert conexao.execute(
                "SELECT count(*) FROM pg_type WHERE typname IN "
                "('estado_fonte', 'codigo_falha_fonte')"
            ).fetchone() == (0,)
            assert conexao.execute("SELECT to_regclass('usuarios')").fetchone() == ("usuarios",)
        executar_alembic("upgrade", "head")
    finally:
        executar_alembic("upgrade", "head")


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("meta_diaria", 0),
        ("meta_diaria", 201),
        ("tamanho_licao", 4),
        ("tamanho_licao", 51),
        ("limite_novos_dia", -1),
        ("limite_novos_dia", 101),
    ],
)
def test_preferencias_check_no_banco(
    configuracao: Configuracao, banco_migrado: None, campo: str, valor: int
) -> None:
    """D-001: limites não podem ser contornados por escrita direta."""
    with psycopg.connect(configuracao.conninfo()) as conexao:
        with pytest.raises(psycopg.errors.CheckViolation):
            conexao.execute(
                psycopg.sql.SQL(
                    "INSERT INTO usuarios (nome,email,senha_hash,{}) "
                    "VALUES ('Teste','limites@exemplo.com','hash-ficticio',%s)"
                ).format(psycopg.sql.Identifier(campo)),
                (valor,),
            )
        conexao.rollback()


def test_email_unico_sem_caixa(configuracao: Configuracao, banco_migrado: None) -> None:
    """RF-012: o índice resolve a unicidade sem diferenciar caixa."""
    with psycopg.connect(configuracao.conninfo()) as conexao:
        conexao.execute(
            "INSERT INTO usuarios(nome,email,senha_hash) "
            "VALUES ('Teste','indice@exemplo.com','hash-ficticio')"
        )
        with pytest.raises(psycopg.errors.UniqueViolation):
            conexao.execute(
                "INSERT INTO usuarios(nome,email,senha_hash) "
                "VALUES ('Teste','INDICE@exemplo.com','hash-ficticio')"
            )
        conexao.rollback()


@pytest.mark.parametrize("retencao,pesos", [("0.69", 21), ("0.98", 21), ("0.90", 20), ("0.90", 22)])
def test_parametros_fsrs_check_no_banco(
    configuracao: Configuracao, banco_migrado: None, retencao: str, pesos: int
) -> None:
    """D-001, RF-010: retenção e quantidade de pesos também são restrições do banco."""
    with psycopg.connect(configuracao.conninfo()) as conexao:
        linha = conexao.execute(
            "INSERT INTO usuarios(nome,email,senha_hash) "
            "VALUES ('Teste','fsrs@exemplo.com','hash-ficticio') RETURNING id"
        ).fetchone()
        assert linha is not None
        with pytest.raises(psycopg.errors.CheckViolation):
            conexao.execute(
                "INSERT INTO parametros_fsrs"
                "(usuario_id,versao,pesos,retencao_desejada,versao_biblioteca) "
                "VALUES (%s,1,%s,%s,'teste')",
                (linha[0], [1.0] * pesos, retencao),
            )
        conexao.rollback()


def test_modelos_concordam_com_migracao(configuracao: Configuracao, banco_migrado: None) -> None:
    """T021: detecta diferença entre o esquema persistido e os mapeamentos ORM."""
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from sqlalchemy import create_engine

    from app.modelos import Base
    from app.nucleo.banco import url_banco

    engine = create_engine(url_banco(configuracao))
    try:
        with engine.connect() as conexao:
            contexto = MigrationContext.configure(
                conexao,
                opts={
                    "include_object": lambda objeto, nome, tipo, refletido, comparado: (
                        not (tipo == "table" and nome.startswith("procrastinate_"))
                    )
                },
            )
            assert compare_metadata(contexto, Base.metadata) == []
    finally:
        engine.dispose()
