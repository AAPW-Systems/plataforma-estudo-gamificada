"""Limites de D-001 nas fronteiras e validação da alteração do perfil (T046; RF-008, US3).

A alteração é tudo ou nada: `validar_alteracao_perfil` informa todos os campos inválidos de
uma vez e só devolve valores quando todos os enviados são válidos.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.identidade import dominio, preferencias
from app.nucleo.erros import EntradaInvalida

pytestmark = pytest.mark.unit

INTEIROS = [
    ("meta_diaria", "metaDiaria", preferencias.META_DIARIA),
    ("tamanho_licao", "tamanhoLicao", preferencias.TAMANHO_LICAO),
    ("limite_novos_dia", "limiteNovosDia", preferencias.LIMITE_NOVOS_DIA),
]


def _campos_invalidos(**enviados: object) -> dict[str, str]:
    with pytest.raises(EntradaInvalida) as erro:
        dominio.validar_alteracao_perfil(enviados)
    return {c.campo: c.mensagem for c in erro.value.campos}


@pytest.mark.parametrize("campo,json,limite", INTEIROS)
def test_inteiros_aceitam_as_duas_fronteiras(campo: str, json: str, limite) -> None:  # type: ignore[no-untyped-def]
    for valor in (limite.minimo, limite.maximo, limite.padrao):
        alteracao = dominio.validar_alteracao_perfil({campo: valor})
        assert getattr(alteracao, campo) == valor


@pytest.mark.parametrize("campo,json,limite", INTEIROS)
def test_inteiros_recusam_um_abaixo_e_um_acima(campo: str, json: str, limite) -> None:  # type: ignore[no-untyped-def]
    for valor in (limite.minimo - 1, limite.maximo + 1, -1, 10**9):
        assert json in _campos_invalidos(**{campo: valor})


@pytest.mark.parametrize("campo,json,limite", INTEIROS)
@pytest.mark.parametrize("valor", [True, False, 5.5, 5.0, "5", None, [5], {"a": 1}])
def test_inteiros_recusam_outros_tipos(campo: str, json: str, limite, valor: object) -> None:  # type: ignore[no-untyped-def]
    assert json in _campos_invalidos(**{campo: valor})


def test_limites_do_dominio_coincidem_com_os_da_spec() -> None:
    assert [(limite.minimo, limite.maximo) for _, _, limite in INTEIROS] == [
        (1, 200),
        (5, 50),
        (0, 100),
    ]
    assert (preferencias.RETENCAO_DESEJADA.minimo, preferencias.RETENCAO_DESEJADA.maximo) == (
        Decimal("0.70"),
        Decimal("0.97"),
    )


@pytest.mark.parametrize("valor", [0.70, 0.7, 0.97, 0.9, 0.85, 1 - 0.03, Decimal("0.80")])
def test_retencao_aceita_o_intervalo_com_duas_casas(valor: float | Decimal) -> None:
    alteracao = dominio.validar_alteracao_perfil({"retencao_desejada": valor})
    assert alteracao.retencao_desejada == Decimal(str(valor)).quantize(Decimal("0.01"))
    assert alteracao.retencao_desejada is not None
    assert alteracao.retencao_desejada.as_tuple().exponent == -2


@pytest.mark.parametrize(
    "valor",
    [
        0.69,
        0.98,
        0.0,
        1.0,
        1,
        0,
        -0.9,
        0.925,
        0.9001,
        0.699,
        0.971,
        1e-9,
        float("nan"),
        float("inf"),
        True,
        "0.9",
        None,
    ],
)
def test_retencao_recusa_fora_do_intervalo_tres_casas_e_outros_tipos(valor: object) -> None:
    mensagens = _campos_invalidos(retencao_desejada=valor)
    assert "retencaoDesejada" in mensagens


def test_a_mensagem_da_retencao_explica_o_intervalo() -> None:
    mensagem = _campos_invalidos(retencao_desejada=0.99)["retencaoDesejada"]
    assert "0,70" in mensagem and "0,97" in mensagem


def test_nome_e_fuso_seguem_as_regras_do_cadastro() -> None:
    alteracao = dominio.validar_alteracao_perfil({"nome": "  Ana  ", "fuso": "America/Manaus"})
    assert (alteracao.nome, alteracao.fuso) == ("Ana", "America/Manaus")
    campos = _campos_invalidos(nome="   ", fuso="../../etc/passwd")
    assert set(campos) == {"nome", "fuso"}
    assert campos["fuso"] == "Fuso desconhecido."


def test_fuso_invalido_na_alteracao_e_recusado_e_nao_vira_o_padrao() -> None:
    assert "fuso" in _campos_invalidos(fuso="Marte/Phobos")
    assert "fuso" in _campos_invalidos(fuso=None)


def test_alteracao_e_tudo_ou_nada_e_lista_todos_os_campos_invalidos() -> None:
    campos = _campos_invalidos(
        nome="Ana",
        fuso="Marte/Phobos",
        meta_diaria=0,
        tamanho_licao=51,
        limite_novos_dia=101,
        retencao_desejada=0.5,
    )
    assert set(campos) == {
        "fuso",
        "metaDiaria",
        "tamanhoLicao",
        "limiteNovosDia",
        "retencaoDesejada",
    }


def test_so_os_campos_enviados_aparecem_na_alteracao() -> None:
    alteracao = dominio.validar_alteracao_perfil({"meta_diaria": 30})
    assert alteracao.meta_diaria == 30
    assert alteracao.nome is None and alteracao.fuso is None
    assert alteracao.tamanho_licao is None and alteracao.retencao_desejada is None
    assert not alteracao.vazia()


def test_corpo_vazio_e_recusado() -> None:
    with pytest.raises(EntradaInvalida) as erro:
        dominio.validar_alteracao_perfil({})
    assert "ao menos um" in erro.value.mensagem.lower() or erro.value.campos == ()


def test_campo_desconhecido_e_erro_de_programacao_e_nao_de_entrada() -> None:
    with pytest.raises(ValueError, match="papel"):
        dominio.validar_alteracao_perfil({"papel": "admin"})


@given(
    st.dictionaries(
        st.sampled_from(["meta_diaria", "tamanho_licao", "limite_novos_dia"]),
        st.integers(-1000, 1000),
        min_size=1,
    )
)
def test_propriedade_valores_validos_passam_e_invalidos_sao_listados(
    enviados: dict[str, int],
) -> None:
    limites = {
        "meta_diaria": preferencias.META_DIARIA,
        "tamanho_licao": preferencias.TAMANHO_LICAO,
        "limite_novos_dia": preferencias.LIMITE_NOVOS_DIA,
    }
    invalidos = {c for c, v in enviados.items() if not limites[c].contem(v)}
    if invalidos:
        with pytest.raises(EntradaInvalida) as erro:
            dominio.validar_alteracao_perfil(enviados)
        assert len(erro.value.campos) == len(invalidos)
    else:
        alteracao = dominio.validar_alteracao_perfil(enviados)
        assert all(getattr(alteracao, c) == v for c, v in enviados.items())
