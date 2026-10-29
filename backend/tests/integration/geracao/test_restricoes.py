"""Restrições da geração no banco (spec 004, T004): CHECKs, FKs compostas e índices.

Escritas diretas com SQL: o banco recusa o que a aplicação já impede, para que uma falha de
aplicação nunca produza dado incoerente (data-model da 004; DTEC 043 a 046).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any

import psycopg
import pytest
from psycopg import errors

from app.nucleo.configuracao import Configuracao

pytestmark = pytest.mark.integration

ENTRADA = "2026-10-01T12:00:00+00:00"


@pytest.fixture
def conexao(configuracao: Configuracao, banco_migrado: None) -> Iterator[psycopg.Connection]:
    """Conexão síncrona numa transação que é sempre desfeita."""
    with psycopg.connect(configuracao.conninfo()) as conexao:
        yield conexao
        conexao.rollback()


def _inserir(conexao: psycopg.Connection, tabela: str, **colunas: Any) -> int:
    nomes = ", ".join(colunas)
    marcadores = ", ".join(["%s"] * len(colunas))
    linha = conexao.execute(
        f"INSERT INTO {tabela}({nomes}) VALUES ({marcadores}) RETURNING id",  # noqa: S608
        list(colunas.values()),
    ).fetchone()
    assert linha is not None
    return int(linha[0])


def _usuario(conexao: psycopg.Connection, email: str) -> int:
    return _inserir(conexao, "usuarios", nome="Teste", email=email, senha_hash="hash-ficticio")


def _materia(conexao: psycopg.Connection, usuario_id: int, nome: str = "Biologia") -> int:
    return _inserir(conexao, "materias", usuario_id=usuario_id, nome=nome)


def _fonte(conexao: psycopg.Connection, usuario_id: int, materia_id: int) -> int:
    return _inserir(
        conexao,
        "fontes",
        usuario_id=usuario_id,
        materia_id=materia_id,
        titulo="Citologia",
        nome_arquivo="citologia.txt",
        chave_objeto=f"usuarios/u/fontes/{uuid.uuid4()}",
        tipo_midia="text/plain",
        tamanho_bytes=1000,
        hash_sha256=uuid.uuid4().bytes * 2,
    )


def _trecho(conexao: psycopg.Connection, fonte_id: int, texto: str, ordem: int = 0) -> int:
    return _inserir(
        conexao,
        "trechos",
        fonte_id=fonte_id,
        ordem=ordem,
        texto=texto,
        inicio_caractere=0,
        fim_caractere=len(texto),
    )


def _geracao(
    conexao: psycopg.Connection,
    usuario_id: int,
    materia_id: int,
    fonte_id: int | None,
    **extra: Any,
) -> int:
    colunas: dict[str, Any] = {
        "usuario_id": usuario_id,
        "materia_id": materia_id,
        "fonte_id": fonte_id,
        "chave_idempotencia": uuid.uuid4(),
        **extra,
    }
    return _inserir(conexao, "geracoes", **colunas)


def _concluida(**extra: Any) -> dict[str, Any]:
    return {
        "estado": "concluida",
        "quantidade_gerada": 1,
        "quantidade_aprovada": 1,
        "concluida_em": ENTRADA,
        **extra,
    }


def _cartao(conexao: psycopg.Connection, usuario_id: int, materia_id: int, **colunas: Any) -> int:
    """Um cartão gerado e aceito, válido, com as alterações pedidas."""
    valores: dict[str, Any] = {
        "usuario_id": usuario_id,
        "materia_id": materia_id,
        "frente": "Qual organela produz ATP?",
        "verso": "A mitocôndria.",
        "explicacao": "A mitocôndria produz ATP por respiração celular.",
        "origem": "gerado_verificado",
        "situacao": "ativo",
        "entrada_estudo_em": ENTRADA,
        **colunas,
    }
    return _inserir(conexao, "cartoes", **valores)


@pytest.fixture
def cenario(conexao: psycopg.Connection) -> dict[str, int]:
    """Estudante com matéria, fonte, trecho e uma geração concluída."""
    usuario = _usuario(conexao, "dono@exemplo.com")
    materia = _materia(conexao, usuario)
    fonte = _fonte(conexao, usuario, materia)
    trecho = _trecho(conexao, fonte, "A mitocôndria produz ATP por respiração celular.")
    geracao = _geracao(conexao, usuario, materia, fonte, **_concluida())
    return {
        "usuario": usuario,
        "materia": materia,
        "fonte": fonte,
        "trecho": trecho,
        "geracao": geracao,
    }


# --- Valores de enum ------------------------------------------------------------------------


def test_situacao_cartao_tem_os_quatro_valores(conexao: psycopg.Connection) -> None:
    """DTEC 038 e data-model da 004: a 0005 acrescenta `aguardando_revisao` e `recusado`."""
    linha = conexao.execute(
        "SELECT array_agg(enumlabel::text ORDER BY enumsortorder) FROM pg_enum "
        "WHERE enumtypid = 'situacao_cartao'::regtype"
    ).fetchone()
    assert linha == (["ativo", "suspenso", "aguardando_revisao", "recusado"],)


@pytest.mark.parametrize(
    "tipo,valores",
    [
        ("estado_geracao", ["pendente", "processando", "concluida", "falhou"]),
        (
            "codigo_falha_geracao",
            [
                "provedor_indisponivel",
                "limite_provedor",
                "resposta_invalida",
                "orcamento_esgotado",
                "fonte_excluida",
            ],
        ),
        ("motivo_recusa", ["incorreto", "irrelevante", "repetido", "mal_escrito"]),
        (
            "motivo_descarte",
            [
                "estrutura_invalida",
                "sem_evidencia",
                "citacao_nao_encontrada",
                "cobertura_insuficiente",
                "reprovado_verificador",
                "repetido",
                "excedente",
            ],
        ),
    ],
)
def test_enums_da_geracao(conexao: psycopg.Connection, tipo: str, valores: list[str]) -> None:
    linha = conexao.execute(
        "SELECT array_agg(enumlabel::text ORDER BY enumsortorder) FROM pg_enum "
        "WHERE enumtypid = %s::regtype",
        (tipo,),
    ).fetchone()
    assert linha == (valores,)


@pytest.mark.parametrize(
    "tabela",
    [
        "geracoes",
        "evidencias_cartoes",
        "cartoes_descartados",
        "consumo_ia",
    ],
)
def test_ids_gerados_pelo_banco(conexao: psycopg.Connection, tabela: str) -> None:
    """Convenções: `bigint generated always as identity`."""
    linha = conexao.execute(
        "SELECT data_type, identity_generation FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=%s AND column_name='id'",
        (tabela,),
    ).fetchone()
    assert linha == ("bigint", "ALWAYS")


# --- Cartões: situação × origem e colunas novas ---------------------------------------------


@pytest.mark.parametrize("situacao", ["aguardando_revisao", "recusado"])
def test_cartao_em_revisao_ou_recusado_e_aceito_quando_gerado(
    conexao: psycopg.Connection, cenario: dict[str, int], situacao: str
) -> None:
    _cartao(
        conexao,
        cenario["usuario"],
        cenario["materia"],
        situacao=situacao,
        entrada_estudo_em=None,
        geracao_id=cenario["geracao"],
    )


@pytest.mark.parametrize("situacao", ["aguardando_revisao", "recusado"])
@pytest.mark.parametrize("origem", ["editado", "criado"])
def test_aguardando_revisao_e_recusado_so_existem_em_gerado_verificado(
    conexao: psycopg.Connection, cenario: dict[str, int], situacao: str, origem: str
) -> None:
    with pytest.raises(errors.CheckViolation, match="cartoes_revisao_so_gerado_check"):
        _cartao(
            conexao,
            cenario["usuario"],
            cenario["materia"],
            situacao=situacao,
            origem=origem,
            entrada_estudo_em=None,
        )


@pytest.mark.parametrize("situacao", ["aguardando_revisao", "recusado"])
def test_aguardando_revisao_e_recusado_nao_tem_entrada_no_estudo(
    conexao: psycopg.Connection, cenario: dict[str, int], situacao: str
) -> None:
    with pytest.raises(errors.CheckViolation, match="cartoes_entrada_estudo_check"):
        _cartao(conexao, cenario["usuario"], cenario["materia"], situacao=situacao)


@pytest.mark.parametrize("situacao", ["ativo", "suspenso", "aguardando_revisao"])
def test_motivo_de_recusa_so_em_recusado(
    conexao: psycopg.Connection, cenario: dict[str, int], situacao: str
) -> None:
    entrada = ENTRADA if situacao in ("ativo", "suspenso") else None
    with pytest.raises(errors.CheckViolation, match="cartoes_motivo_recusa_check"):
        _cartao(
            conexao,
            cenario["usuario"],
            cenario["materia"],
            situacao=situacao,
            entrada_estudo_em=entrada,
            motivo_recusa="incorreto",
        )


@pytest.mark.parametrize("motivo", ["incorreto", "irrelevante", "repetido", "mal_escrito", None])
def test_recusado_aceita_os_motivos_e_a_ausencia(
    conexao: psycopg.Connection, cenario: dict[str, int], motivo: str | None
) -> None:
    _cartao(
        conexao,
        cenario["usuario"],
        cenario["materia"],
        situacao="recusado",
        entrada_estudo_em=None,
        motivo_recusa=motivo,
    )


def test_motivo_de_recusa_fora_do_enum_e_recusado(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    with pytest.raises(errors.InvalidTextRepresentation):
        _cartao(
            conexao,
            cenario["usuario"],
            cenario["materia"],
            situacao="recusado",
            entrada_estudo_em=None,
            motivo_recusa="chato",
        )


def test_cartao_gerado_exige_explicacao(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    """RF-008: o gerado sempre tem explicação."""
    with pytest.raises(errors.CheckViolation, match="cartoes_explicacao_gerado_check"):
        _cartao(conexao, cenario["usuario"], cenario["materia"], explicacao=None)


@pytest.mark.parametrize("origem", ["editado", "criado"])
def test_editado_e_criado_continuam_sem_explicacao_obrigatoria(
    conexao: psycopg.Connection, cenario: dict[str, int], origem: str
) -> None:
    _cartao(conexao, cenario["usuario"], cenario["materia"], origem=origem, explicacao=None)


def test_cartao_criado_nao_tem_geracao(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    with pytest.raises(errors.CheckViolation, match="cartoes_geracao_so_em_gerado_check"):
        _cartao(
            conexao,
            cenario["usuario"],
            cenario["materia"],
            origem="criado",
            geracao_id=cenario["geracao"],
        )


def test_cartao_editado_mantem_a_geracao(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    """Um gerado editado na aceitação continua ligado à geração (resumo e evidência)."""
    _cartao(
        conexao,
        cenario["usuario"],
        cenario["materia"],
        origem="editado",
        geracao_id=cenario["geracao"],
    )


def test_apagar_a_geracao_anula_o_geracao_id_do_cartao(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    cartao = _cartao(conexao, cenario["usuario"], cenario["materia"], geracao_id=cenario["geracao"])
    conexao.execute("DELETE FROM geracoes WHERE id = %s", (cenario["geracao"],))
    assert conexao.execute(
        "SELECT geracao_id FROM cartoes WHERE id = %s", (cartao,)
    ).fetchone() == (None,)


# --- Geração: estado, falha e quantidades ---------------------------------------------------


def test_geracao_nasce_pendente_com_ids_e_quantidades_zeradas(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    fonte = _fonte(conexao, cenario["usuario"], cenario["materia"])
    geracao = _geracao(conexao, cenario["usuario"], cenario["materia"], fonte)
    linha = conexao.execute(
        "SELECT estado::text, public_id IS NOT NULL, quantidade_gerada, quantidade_aprovada, "
        "pontos_contraditorios, criado_em IS NOT NULL FROM geracoes WHERE id = %s",
        (geracao,),
    ).fetchone()
    assert linha == ("pendente", True, 0, 0, 0, True)


@pytest.mark.parametrize(
    "estado,codigo",
    [
        ("pendente", "provedor_indisponivel"),
        ("processando", "limite_provedor"),
        ("concluida", "resposta_invalida"),
        ("falhou", None),
    ],
)
def test_codigo_de_falha_se_e_somente_se_falhou(
    conexao: psycopg.Connection, cenario: dict[str, int], estado: str, codigo: str | None
) -> None:
    fonte = _fonte(conexao, cenario["usuario"], cenario["materia"])
    terminou = estado in ("concluida", "falhou")
    with pytest.raises(errors.CheckViolation, match="geracoes_codigo_falha_check"):
        _geracao(
            conexao,
            cenario["usuario"],
            cenario["materia"],
            fonte,
            estado=estado,
            codigo_falha=codigo,
            concluida_em=ENTRADA if terminou else None,
        )


def test_falhou_com_codigo_e_aceita(conexao: psycopg.Connection, cenario: dict[str, int]) -> None:
    fonte = _fonte(conexao, cenario["usuario"], cenario["materia"])
    _geracao(
        conexao,
        cenario["usuario"],
        cenario["materia"],
        fonte,
        estado="falhou",
        codigo_falha="fonte_excluida",
        concluida_em=ENTRADA,
    )


@pytest.mark.parametrize(
    "estado,concluida_em",
    [("concluida", None), ("pendente", ENTRADA), ("processando", ENTRADA)],
)
def test_concluida_em_so_no_estado_final(
    conexao: psycopg.Connection, cenario: dict[str, int], estado: str, concluida_em: str | None
) -> None:
    fonte = _fonte(conexao, cenario["usuario"], cenario["materia"])
    with pytest.raises(errors.CheckViolation, match="geracoes_concluida_em_check"):
        _geracao(
            conexao,
            cenario["usuario"],
            cenario["materia"],
            fonte,
            estado=estado,
            concluida_em=concluida_em,
        )


@pytest.mark.parametrize(
    "gerada,aprovada,contraditorios,restricao",
    [
        # gerada negativa já fere `aprovada <= gerada`; a restrição própria é defesa redundante
        (-1, 0, 0, "quantidade_(gerada|aprovada)"),
        (11, 11, 0, "quantidade_aprovada"),
        (2, 3, 0, "quantidade_aprovada"),
        (0, -1, 0, "quantidade_aprovada"),
        (0, 0, -1, "pontos_contraditorios"),
    ],
)
def test_quantidades_da_geracao(
    conexao: psycopg.Connection,
    cenario: dict[str, int],
    gerada: int,
    aprovada: int,
    contraditorios: int,
    restricao: str,
) -> None:
    fonte = _fonte(conexao, cenario["usuario"], cenario["materia"])
    with pytest.raises(errors.CheckViolation, match=f"geracoes_{restricao}_check"):
        _geracao(
            conexao,
            cenario["usuario"],
            cenario["materia"],
            fonte,
            **_concluida(
                quantidade_gerada=gerada,
                quantidade_aprovada=aprovada,
                pontos_contraditorios=contraditorios,
            ),
        )


def test_quinze_gerados_e_dez_aprovados_sao_aceitos(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    fonte = _fonte(conexao, cenario["usuario"], cenario["materia"])
    _geracao(
        conexao,
        cenario["usuario"],
        cenario["materia"],
        fonte,
        **_concluida(quantidade_gerada=15, quantidade_aprovada=10),
    )


def test_chave_de_idempotencia_unica_por_estudante(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    chave = uuid.uuid4()
    outro = _usuario(conexao, "outro@exemplo.com")
    materia_outro = _materia(conexao, outro)
    _geracao(conexao, outro, materia_outro, None, chave_idempotencia=chave)
    _geracao(conexao, cenario["usuario"], cenario["materia"], None, chave_idempotencia=chave)
    with pytest.raises(errors.UniqueViolation, match="geracoes_usuario_chave_unica"):
        _geracao(conexao, cenario["usuario"], cenario["materia"], None, chave_idempotencia=chave)


# --- FK composta para a fonte ---------------------------------------------------------------


def test_geracao_com_fonte_de_outra_materia_e_recusada(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    quimica = _materia(conexao, cenario["usuario"], "Química")
    with pytest.raises(errors.ForeignKeyViolation, match="geracoes_fonte_id_fkey"):
        _geracao(conexao, cenario["usuario"], quimica, cenario["fonte"])


def test_geracao_com_fonte_de_outro_dono_e_recusada(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    outro = _usuario(conexao, "intruso@exemplo.com")
    materia_outro = _materia(conexao, outro)
    with pytest.raises(errors.ForeignKeyViolation):
        _geracao(conexao, outro, materia_outro, cenario["fonte"])


def test_geracao_numa_materia_de_outro_dono_e_recusada(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    outro = _usuario(conexao, "intruso@exemplo.com")
    with pytest.raises(errors.ForeignKeyViolation, match="geracoes_materia_id_fkey"):
        _geracao(conexao, outro, cenario["materia"], None)


def test_apagar_a_fonte_anula_so_o_fonte_id_da_geracao(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    """DTEC 046: a geração fica, sem a fonte, ainda presa à matéria e ao dono."""
    conexao.execute("DELETE FROM fontes WHERE id = %s", (cenario["fonte"],))
    linha = conexao.execute(
        "SELECT fonte_id, materia_id, usuario_id FROM geracoes WHERE id = %s",
        (cenario["geracao"],),
    ).fetchone()
    assert linha == (None, cenario["materia"], cenario["usuario"])
    # o trecho saiu em cascata com a fonte, e o registro da janela com ele
    assert conexao.execute(
        "SELECT count(*) FROM trechos WHERE id = %s", (cenario["trecho"],)
    ).fetchone() == (0,)


def test_apagar_a_materia_leva_as_geracoes(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    conexao.execute("DELETE FROM fontes WHERE materia_id = %s", (cenario["materia"],))
    conexao.execute("DELETE FROM materias WHERE id = %s", (cenario["materia"],))
    assert conexao.execute(
        "SELECT count(*) FROM geracoes WHERE id = %s", (cenario["geracao"],)
    ).fetchone() == (0,)


# --- Uma geração em andamento por fonte -----------------------------------------------------


@pytest.mark.parametrize("estado", ["pendente", "processando"])
def test_segunda_geracao_em_andamento_da_mesma_fonte_e_recusada(
    conexao: psycopg.Connection, cenario: dict[str, int], estado: str
) -> None:
    usuario, materia, fonte = cenario["usuario"], cenario["materia"], cenario["fonte"]
    _geracao(conexao, usuario, materia, fonte, estado=estado)
    for outro in ("pendente", "processando"):
        conexao.execute("SAVEPOINT s")
        with pytest.raises(errors.UniqueViolation, match="geracoes_fonte_em_andamento"):
            _geracao(conexao, usuario, materia, fonte, estado=outro)
        conexao.execute("ROLLBACK TO SAVEPOINT s")


def test_nova_geracao_e_aceita_depois_que_a_primeira_termina(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    usuario, materia, fonte = cenario["usuario"], cenario["materia"], cenario["fonte"]
    primeira = _geracao(conexao, usuario, materia, fonte)
    conexao.execute(
        "UPDATE geracoes SET estado = 'falhou', codigo_falha = 'provedor_indisponivel', "
        "concluida_em = now() WHERE id = %s",
        (primeira,),
    )
    segunda = _geracao(conexao, usuario, materia, fonte)
    conexao.execute(
        "UPDATE geracoes SET estado = 'concluida', concluida_em = now() WHERE id = %s",
        (segunda,),
    )
    _geracao(conexao, usuario, materia, fonte)


def test_geracoes_sem_fonte_nao_disputam_o_indice(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    _geracao(conexao, cenario["usuario"], cenario["materia"], None)
    _geracao(conexao, cenario["usuario"], cenario["materia"], None)


# --- Trechos da geração ---------------------------------------------------------------------


def test_trecho_da_geracao_e_unico_e_sai_com_a_geracao(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    conexao.execute(
        "INSERT INTO geracoes_trechos(geracao_id, trecho_id) VALUES (%s, %s)",
        (cenario["geracao"], cenario["trecho"]),
    )
    conexao.execute("SAVEPOINT s")
    with pytest.raises(errors.UniqueViolation):
        conexao.execute(
            "INSERT INTO geracoes_trechos(geracao_id, trecho_id) VALUES (%s, %s)",
            (cenario["geracao"], cenario["trecho"]),
        )
    conexao.execute("ROLLBACK TO SAVEPOINT s")
    conexao.execute("DELETE FROM geracoes WHERE id = %s", (cenario["geracao"],))
    assert conexao.execute("SELECT count(*) FROM geracoes_trechos").fetchone() == (0,)


# --- Evidências -----------------------------------------------------------------------------


def _evidencia(conexao: psycopg.Connection, cartao: int, trecho: int | None, **extra: Any) -> int:
    colunas: dict[str, Any] = {
        "cartao_id": cartao,
        "trecho_id": trecho,
        "fonte_titulo": "Citologia",
        "fonte_nome_arquivo": "citologia.txt",
        "fonte_enviada_em": ENTRADA,
        "citacao_inicio": 2,
        "citacao_fim": 13,
        **extra,
    }
    return _inserir(conexao, "evidencias_cartoes", **colunas)


@pytest.mark.parametrize("inicio,fim", [(5, 5), (6, 5), (-1, 3)])
def test_citacao_exige_inicio_menor_que_fim_e_nao_negativo(
    conexao: psycopg.Connection, cenario: dict[str, int], inicio: int, fim: int
) -> None:
    cartao = _cartao(conexao, cenario["usuario"], cenario["materia"], geracao_id=cenario["geracao"])
    with pytest.raises(errors.CheckViolation, match="evidencias_cartoes_citacao_check"):
        _evidencia(conexao, cartao, cenario["trecho"], citacao_inicio=inicio, citacao_fim=fim)


def test_pagina_da_evidencia_comeca_em_1(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    cartao = _cartao(conexao, cenario["usuario"], cenario["materia"], geracao_id=cenario["geracao"])
    with pytest.raises(errors.CheckViolation, match="evidencias_cartoes_pagina_check"):
        _evidencia(conexao, cartao, cenario["trecho"], pagina=0)


def test_evidencia_unica_por_cartao_e_trecho(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    cartao = _cartao(conexao, cenario["usuario"], cenario["materia"], geracao_id=cenario["geracao"])
    _evidencia(conexao, cartao, cenario["trecho"], pagina=3)
    with pytest.raises(errors.UniqueViolation):
        _evidencia(conexao, cartao, cenario["trecho"])


def test_apagar_a_fonte_anula_o_trecho_e_mantem_a_descricao_da_origem(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    """RN-05, US3-2: a evidência guarda a descrição da origem, sem o trecho."""
    cartao = _cartao(conexao, cenario["usuario"], cenario["materia"], geracao_id=cenario["geracao"])
    evidencia = _evidencia(conexao, cartao, cenario["trecho"])
    conexao.execute("DELETE FROM fontes WHERE id = %s", (cenario["fonte"],))
    linha = conexao.execute(
        "SELECT trecho_id, fonte_titulo, fonte_nome_arquivo FROM evidencias_cartoes WHERE id = %s",
        (evidencia,),
    ).fetchone()
    assert linha == (None, "Citologia", "citologia.txt")


def test_evidencia_sai_com_o_cartao(conexao: psycopg.Connection, cenario: dict[str, int]) -> None:
    cartao = _cartao(conexao, cenario["usuario"], cenario["materia"], geracao_id=cenario["geracao"])
    _evidencia(conexao, cartao, cenario["trecho"])
    conexao.execute("DELETE FROM cartoes WHERE id = %s", (cartao,))
    assert conexao.execute("SELECT count(*) FROM evidencias_cartoes").fetchone() == (0,)


# --- Descartados, consumo e ciência ---------------------------------------------------------


def _descartado(conexao: psycopg.Connection, cenario: dict[str, int], **extra: Any) -> int:
    colunas: dict[str, Any] = {
        "geracao_id": cenario["geracao"],
        "usuario_id": cenario["usuario"],
        "motivo": "sem_evidencia",
        **extra,
    }
    return _inserir(conexao, "cartoes_descartados", **colunas)


@pytest.mark.parametrize(
    "coluna,tamanho", [("frente", 4001), ("verso", 8001), ("explicacao", 4001), ("detalhe", 101)]
)
def test_descartado_respeita_os_tetos(
    conexao: psycopg.Connection, cenario: dict[str, int], coluna: str, tamanho: int
) -> None:
    with pytest.raises((errors.CheckViolation, errors.StringDataRightTruncation)):
        _descartado(conexao, cenario, **{coluna: "x" * tamanho})


def test_descartado_nos_tetos_e_sem_texto_e_aceito(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    _descartado(
        conexao,
        cenario,
        motivo="reprovado_verificador",
        detalhe="d" * 100,
        frente="f" * 4000,
        verso="v" * 8000,
        explicacao="e" * 4000,
    )
    _descartado(conexao, cenario, motivo="estrutura_invalida")


def test_descartado_sai_com_a_geracao(conexao: psycopg.Connection, cenario: dict[str, int]) -> None:
    _descartado(conexao, cenario)
    conexao.execute("DELETE FROM geracoes WHERE id = %s", (cenario["geracao"],))
    assert conexao.execute("SELECT count(*) FROM cartoes_descartados").fetchone() == (0,)


def _consumo(conexao: psycopg.Connection, cenario: dict[str, int], **extra: Any) -> int:
    colunas: dict[str, Any] = {
        "usuario_id": cenario["usuario"],
        "geracao_id": cenario["geracao"],
        "operacao": "gerar_cartoes",
        "provedor": "teste",
        "modelo": "simulado",
        "versao_instrucoes": "gerador-v1+juiza-v1",
        "latencia_ms": 120,
        "sucesso": True,
        **extra,
    }
    return _inserir(conexao, "consumo_ia", **colunas)


@pytest.mark.parametrize(
    "coluna,valor", [("tokens_entrada", -1), ("tokens_saida", -1), ("latencia_ms", -1)]
)
def test_consumo_sem_valores_negativos(
    conexao: psycopg.Connection, cenario: dict[str, int], coluna: str, valor: int
) -> None:
    with pytest.raises(errors.CheckViolation, match=f"consumo_ia_{coluna}_check"):
        _consumo(conexao, cenario, **{coluna: valor})


def test_consumo_fica_sem_a_geracao_apagada(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    """DTEC 040: o consumo permanece, sem conteúdo, quando a geração some."""
    consumo = _consumo(conexao, cenario, tokens_entrada=None, tokens_saida=None, sucesso=False)
    conexao.execute("DELETE FROM geracoes WHERE id = %s", (cenario["geracao"],))
    assert conexao.execute(
        "SELECT geracao_id FROM consumo_ia WHERE id = %s", (consumo,)
    ).fetchone() == (None,)


def test_ciencia_unica_por_estudante_e_versao(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    sql = "INSERT INTO ciencias_aviso_ia(usuario_id, versao_aviso) VALUES (%s, %s)"
    conexao.execute(sql, (cenario["usuario"], "gemini-v1"))
    conexao.execute(sql, (cenario["usuario"], "groq-v1"))
    with pytest.raises(errors.UniqueViolation):
        conexao.execute(sql, (cenario["usuario"], "gemini-v1"))


def test_versao_do_aviso_tem_ate_50_caracteres(
    conexao: psycopg.Connection, cenario: dict[str, int]
) -> None:
    with pytest.raises(errors.StringDataRightTruncation):
        conexao.execute(
            "INSERT INTO ciencias_aviso_ia(usuario_id, versao_aviso) VALUES (%s, %s)",
            (cenario["usuario"], "v" * 51),
        )
