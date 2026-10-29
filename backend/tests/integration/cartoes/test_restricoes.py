"""Restrições dos cartões no banco (T003): CHECKs, FKs compostas, índices e extensão (RQ-002).

Escritas diretas com SQL: o banco precisa recusar o que a aplicação já impede, para que uma
falha de aplicação nunca produza dado incoerente (DTEC 035, 036 e 038; data-model).
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


def _fonte(conexao: psycopg.Connection, usuario_id: int, materia_id: int, chave: str = "f1") -> int:
    linha = conexao.execute(
        "INSERT INTO fontes(usuario_id, materia_id, titulo, nome_arquivo, chave_objeto, "
        "tipo_midia, tamanho_bytes, hash_sha256) "
        "VALUES (%s, %s, 'Citologia', 'citologia.pdf', %s, 'application/pdf', 1000, %s) "
        "RETURNING id",
        (usuario_id, materia_id, f"usuarios/u/fontes/{chave}", HASH),
    ).fetchone()
    assert linha is not None
    return int(linha[0])


COPIAS = {
    "referencia_titulo": "Citologia",
    "referencia_nome_arquivo": "citologia.pdf",
    "referencia_enviada_em": "2026-10-01T12:00:00+00:00",
}


def _cartao(conexao: psycopg.Connection, usuario_id: int, materia_id: int, **colunas: Any) -> int:
    """Insere um cartão manual válido, com as alterações pedidas."""
    valores: dict[str, Any] = {
        "usuario_id": usuario_id,
        "materia_id": materia_id,
        "frente": "Qual organela produz ATP?",
        "verso": "Mitocôndria",
        "origem": "criado",
        "situacao": "ativo",
        "entrada_estudo_em": "2026-10-01T12:00:00+00:00",
        **colunas,
    }
    nomes = ", ".join(valores)
    marcadores = ", ".join(["%s"] * len(valores))
    linha = conexao.execute(
        f"INSERT INTO cartoes({nomes}) VALUES ({marcadores}) RETURNING id",  # noqa: S608
        list(valores.values()),
    ).fetchone()
    assert linha is not None
    return int(linha[0])


@pytest.fixture
def cenario(conexao: psycopg.Connection) -> tuple[int, int]:
    """Um estudante com uma matéria: (usuario_id, materia_id)."""
    usuario = _usuario(conexao, "dono@exemplo.com")
    return usuario, _materia(conexao, usuario)


# --- Extensão e valores padrão ----------------------------------------------------------------


def test_extensao_unaccent_existe_e_remove_acentos(conexao: psycopg.Connection) -> None:
    """DTEC 033: a busca sem acentos depende da extensão criada pela 0004."""
    linha = conexao.execute("SELECT unaccent('Célula é ação')").fetchone()
    assert linha == ("Celula e acao",)


def test_cartao_nasce_com_os_padroes_do_fsrs_e_ids_gerados_pelo_banco(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    """DTEC 037: o estado inicial vem do `Card`; o banco só garante os padrões e os ids."""
    usuario, materia = cenario
    cartao = _cartao(conexao, usuario, materia)
    linha = conexao.execute(
        "SELECT public_id, estado_fsrs::text, passo, estabilidade, dificuldade, ultima_revisao, "
        "vencimento IS NOT NULL, criado_em IS NOT NULL, atualizado_em IS NOT NULL, "
        "explicacao, fonte_id "
        "FROM cartoes WHERE id = %s",
        (cartao,),
    ).fetchone()
    assert linha is not None
    assert linha[0] is not None
    assert linha[1:6] == ("aprendizado", None, None, None, None)
    assert linha[6:9] == (True, True, True)
    assert linha[9:] == (None, None)


def test_id_e_sempre_gerado_pelo_banco(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    """Convenção do projeto: `generated always as identity` recusa id escrito à mão."""
    usuario, materia = cenario
    with pytest.raises(errors.GeneratedAlways):
        _cartao(conexao, usuario, materia, id=999_999)
    conexao.rollback()


def test_public_id_e_unico_por_cartao(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    usuario, materia = cenario
    a = _cartao(conexao, usuario, materia)
    b = _cartao(conexao, usuario, materia)
    ids = conexao.execute(
        "SELECT count(DISTINCT public_id) FROM cartoes WHERE id IN (%s, %s)", (a, b)
    ).fetchone()
    assert ids == (2,)


# --- CHECK de tamanho (tetos absolutos, DTEC 036) ---------------------------------------------


@pytest.mark.parametrize(
    ("coluna", "teto"), [("frente", 4000), ("verso", 8000), ("explicacao", 4000)]
)
def test_texto_aceita_de_1_ate_o_teto(
    conexao: psycopg.Connection, cenario: tuple[int, int], coluna: str, teto: int
) -> None:
    usuario, materia = cenario
    _cartao(conexao, usuario, materia, **{coluna: "a"})
    _cartao(conexao, usuario, materia, **{coluna: "ç" * teto})


@pytest.mark.parametrize(
    ("coluna", "teto"), [("frente", 4000), ("verso", 8000), ("explicacao", 4000)]
)
@pytest.mark.parametrize("excesso", [False, True])
def test_texto_vazio_ou_acima_do_teto_e_recusado(
    conexao: psycopg.Connection,
    cenario: tuple[int, int],
    coluna: str,
    teto: int,
    excesso: bool,
) -> None:
    usuario, materia = cenario
    valor = "ç" * (teto + 1) if excesso else ""
    with pytest.raises(errors.CheckViolation):
        _cartao(conexao, usuario, materia, **{coluna: valor})


def test_tamanho_conta_caracteres_e_nao_bytes(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    """4.000 'ç' ocupam 8.000 bytes e mesmo assim cabem: o CHECK conta caracteres."""
    usuario, materia = cenario
    _cartao(conexao, usuario, materia, frente="ç" * 4000)


@pytest.mark.parametrize("coluna", ["frente", "verso"])
def test_frente_e_verso_sao_obrigatorios(
    conexao: psycopg.Connection, cenario: tuple[int, int], coluna: str
) -> None:
    usuario, materia = cenario
    with pytest.raises(errors.NotNullViolation):
        _cartao(conexao, usuario, materia, **{coluna: None})


def test_explicacao_e_opcional(conexao: psycopg.Connection, cenario: tuple[int, int]) -> None:
    usuario, materia = cenario
    _cartao(conexao, usuario, materia, explicacao=None)


@pytest.mark.parametrize("dificuldade", [0.99, 10.01, -1.0])
def test_dificuldade_fora_de_1_a_10_e_recusada(
    conexao: psycopg.Connection, cenario: tuple[int, int], dificuldade: float
) -> None:
    usuario, materia = cenario
    with pytest.raises(errors.CheckViolation):
        _cartao(conexao, usuario, materia, dificuldade=dificuldade)


@pytest.mark.parametrize("dificuldade", [1.0, 5.5, 10.0])
def test_dificuldade_de_1_a_10_e_aceita(
    conexao: psycopg.Connection, cenario: tuple[int, int], dificuldade: float
) -> None:
    usuario, materia = cenario
    _cartao(conexao, usuario, materia, dificuldade=dificuldade)


# --- CHECK das cópias da referência (DTEC 035) ------------------------------------------------


@pytest.mark.parametrize("ausente", list(COPIAS))
def test_copias_da_referencia_vem_juntas_ou_nenhuma(
    conexao: psycopg.Connection, cenario: tuple[int, int], ausente: str
) -> None:
    usuario, materia = cenario
    parciais = {chave: valor for chave, valor in COPIAS.items() if chave != ausente}
    with pytest.raises(errors.CheckViolation):
        _cartao(conexao, usuario, materia, **parciais)


@pytest.mark.parametrize("copia", list(COPIAS))
def test_cada_copia_sozinha_e_recusada(
    conexao: psycopg.Connection, cenario: tuple[int, int], copia: str
) -> None:
    usuario, materia = cenario
    with pytest.raises(errors.CheckViolation):
        _cartao(conexao, usuario, materia, **{copia: COPIAS[copia]})


def test_fonte_id_exige_as_copias(conexao: psycopg.Connection, cenario: tuple[int, int]) -> None:
    usuario, materia = cenario
    fonte = _fonte(conexao, usuario, materia)
    with pytest.raises(errors.CheckViolation):
        _cartao(conexao, usuario, materia, fonte_id=fonte)


def test_referencia_completa_com_fonte_e_aceita(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    usuario, materia = cenario
    fonte = _fonte(conexao, usuario, materia)
    cartao = _cartao(conexao, usuario, materia, fonte_id=fonte, **COPIAS)
    linha = conexao.execute(
        "SELECT fonte_id, referencia_titulo, referencia_nome_arquivo FROM cartoes WHERE id = %s",
        (cartao,),
    ).fetchone()
    assert linha == (fonte, "Citologia", "citologia.pdf")


@pytest.mark.parametrize("origem", ["editado", "gerado_verificado"])
def test_referencia_so_existe_em_cartao_criado(
    conexao: psycopg.Connection, cenario: tuple[int, int], origem: str
) -> None:
    """Princípio I: referência não é evidência, e só o cartão manual a tem."""
    usuario, materia = cenario
    with pytest.raises(errors.CheckViolation):
        _cartao(conexao, usuario, materia, origem=origem, **COPIAS)


@pytest.mark.parametrize("origem", ["editado", "gerado_verificado", "criado"])
def test_as_tres_origens_sao_aceitas_sem_referencia(
    conexao: psycopg.Connection, cenario: tuple[int, int], origem: str
) -> None:
    usuario, materia = cenario
    # Desde a 0005 (spec 004), o gerado exige explicação (RF-008 da 004).
    explicacao = "Explicação do gerado." if origem == "gerado_verificado" else None
    _cartao(conexao, usuario, materia, origem=origem, explicacao=explicacao)


def test_origem_desconhecida_e_recusada(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    usuario, materia = cenario
    with pytest.raises(errors.InvalidTextRepresentation):
        _cartao(conexao, usuario, materia, origem="importado")


# --- CHECK da entrada no estudo e situação ----------------------------------------------------


@pytest.mark.parametrize("situacao", ["ativo", "suspenso"])
def test_situacao_visivel_exige_entrada_no_estudo(
    conexao: psycopg.Connection, cenario: tuple[int, int], situacao: str
) -> None:
    usuario, materia = cenario
    with pytest.raises(errors.CheckViolation):
        _cartao(conexao, usuario, materia, situacao=situacao, entrada_estudo_em=None)


@pytest.mark.parametrize("situacao", ["ativo", "suspenso"])
def test_ativo_e_suspenso_com_entrada_sao_aceitos(
    conexao: psycopg.Connection, cenario: tuple[int, int], situacao: str
) -> None:
    usuario, materia = cenario
    _cartao(conexao, usuario, materia, situacao=situacao)


def test_situacao_cartao_tem_os_quatro_valores(conexao: psycopg.Connection) -> None:
    """DTEC 038: a 003 criou `ativo` e `suspenso`; a 0005 (spec 004) acrescentou os outros dois.

    Substitui `test_situacoes_da_004_ainda_nao_existem_no_enum` (as restrições dos valores novos
    estão em `tests/integration/geracao/test_restricoes.py`).
    """
    linha = conexao.execute(
        "SELECT array_agg(enumlabel::text ORDER BY enumsortorder) FROM pg_enum "
        "WHERE enumtypid = 'situacao_cartao'::regtype"
    ).fetchone()
    assert linha == (["ativo", "suspenso", "aguardando_revisao", "recusado"],)


def test_estado_do_fsrs_aceita_os_tres_valores_e_recusa_outros(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    usuario, materia = cenario
    for estado in ("aprendizado", "revisao", "reaprendizado"):
        _cartao(conexao, usuario, materia, estado_fsrs=estado)
    with pytest.raises(errors.InvalidTextRepresentation):
        _cartao(conexao, usuario, materia, estado_fsrs="dominado")


# --- FK composta da matéria (RN-01, DTEC 019) -------------------------------------------------


def test_cartao_numa_materia_de_outro_dono_e_recusado(conexao: psycopg.Connection) -> None:
    a = _usuario(conexao, "a@exemplo.com")
    b = _usuario(conexao, "b@exemplo.com")
    materia_de_a = _materia(conexao, a)
    with pytest.raises(errors.ForeignKeyViolation):
        _cartao(conexao, b, materia_de_a)


def test_materia_com_cartoes_nao_e_apagada_sem_o_participante(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    """`restrict`: esquecer o participante da exclusão vira falha ruidosa (DTEC 027)."""
    usuario, materia = cenario
    _cartao(conexao, usuario, materia)
    with pytest.raises(errors.ForeignKeyViolation):
        conexao.execute("DELETE FROM materias WHERE id = %s", (materia,))


# --- FK composta da fonte de referência (DTEC 035) --------------------------------------------


def test_referencia_a_fonte_de_outra_materia_e_recusada(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    usuario, materia = cenario
    outra = _materia(conexao, usuario, "Química")
    fonte_da_outra = _fonte(conexao, usuario, outra)
    with pytest.raises(errors.ForeignKeyViolation):
        _cartao(conexao, usuario, materia, fonte_id=fonte_da_outra, **COPIAS)


def test_referencia_a_fonte_de_outro_dono_e_recusada(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    usuario, materia = cenario
    outro = _usuario(conexao, "outro@exemplo.com")
    fonte_alheia = _fonte(conexao, outro, _materia(conexao, outro))
    with pytest.raises(errors.ForeignKeyViolation):
        _cartao(conexao, usuario, materia, fonte_id=fonte_alheia, **COPIAS)


def test_referencia_a_fonte_inexistente_e_recusada(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    usuario, materia = cenario
    with pytest.raises(errors.ForeignKeyViolation):
        _cartao(conexao, usuario, materia, fonte_id=987_654, **COPIAS)


def test_apagar_fonte_citada_falha_por_restrict(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    usuario, materia = cenario
    fonte = _fonte(conexao, usuario, materia)
    _cartao(conexao, usuario, materia, fonte_id=fonte, **COPIAS)
    with pytest.raises(errors.ForeignKeyViolation):
        conexao.execute("DELETE FROM fontes WHERE id = %s", (fonte,))


def test_com_fonte_id_nulo_a_linha_continua_valida_e_a_fonte_pode_ser_apagada(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    """D-006: o participante anula `fonte_id`; as cópias ficam e o cartão vira "Fonte apagada"."""
    usuario, materia = cenario
    fonte = _fonte(conexao, usuario, materia)
    cartao = _cartao(conexao, usuario, materia, fonte_id=fonte, **COPIAS)
    conexao.execute("UPDATE cartoes SET fonte_id = NULL WHERE id = %s", (cartao,))
    conexao.execute("DELETE FROM fontes WHERE id = %s", (fonte,))
    linha = conexao.execute(
        "SELECT fonte_id, referencia_titulo FROM cartoes WHERE id = %s", (cartao,)
    ).fetchone()
    assert linha == (None, "Citologia")


def test_cartao_sem_referencia_nao_depende_de_fonte(
    conexao: psycopg.Connection, cenario: tuple[int, int]
) -> None:
    usuario, materia = cenario
    fonte = _fonte(conexao, usuario, materia)
    _cartao(conexao, usuario, materia)
    conexao.execute("DELETE FROM fontes WHERE id = %s", (fonte,))


# --- Índices ----------------------------------------------------------------------------------


def _definicao_do_indice(conexao: psycopg.Connection, nome: str) -> str:
    linha = conexao.execute("SELECT indexdef FROM pg_indexes WHERE indexname = %s", (nome,))
    encontrado = linha.fetchone()
    assert encontrado is not None, f"índice {nome} ausente"
    return str(encontrado[0])


@pytest.mark.parametrize(
    ("nome", "trecho"),
    [
        ("cartoes_devidos", "(usuario_id, situacao, vencimento)"),
        ("cartoes_novos", "(usuario_id, situacao, entrada_estudo_em)"),
        ("cartoes_materia", "(materia_id, usuario_id, criado_em, id)"),
        ("cartoes_fonte_id_idx", "(fonte_id)"),
    ],
)
def test_indices_dos_cartoes_existem_com_as_colunas_do_plano(
    conexao: psycopg.Connection, nome: str, trecho: str
) -> None:
    definicao = _definicao_do_indice(conexao, nome)
    assert definicao.endswith(trecho)
    assert "UNIQUE" not in definicao


def test_indice_unico_de_fontes_e_o_alvo_da_fk_composta(conexao: psycopg.Connection) -> None:
    definicao = _definicao_do_indice(conexao, "fontes_id_materia_usuario")
    assert "UNIQUE" in definicao
    assert definicao.endswith("(id, materia_id, usuario_id)")
