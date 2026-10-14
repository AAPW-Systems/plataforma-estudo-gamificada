"""Regras puras da exclusão de uma fonte (T032; DTEC 031, RN-14, D-009).

O impacto que o estudante confirmou é comparado com o recalculado dentro da transação, e a
escolha sobre os cartões é obrigatória e só admite `manter` ou `excluir`.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.fontes.dominio import impacto_confere
from app.fontes.dtos import ContagensExclusaoFonteDTO, ExclusaoFonteEntradaDTO
from app.nucleo.participantes_acervo import ContagensAcervo, ModoCartoes

pytestmark = pytest.mark.unit

BASE = ContagensAcervo(
    cartoes_gerados_aceitos=3, cartoes_aguardando_revisao=2, cartoes_referencia=1
)


def test_impacto_igual_confere() -> None:
    igual = ContagensAcervo(
        cartoes_gerados_aceitos=3, cartoes_aguardando_revisao=2, cartoes_referencia=1
    )
    assert impacto_confere(BASE, igual) is True
    assert impacto_confere(ContagensAcervo(), ContagensAcervo()) is True


@pytest.mark.parametrize(
    "alteracao",
    [
        {"cartoes_gerados_aceitos": 4},
        {"cartoes_gerados_aceitos": 2},
        {"cartoes_aguardando_revisao": 3},
        {"cartoes_aguardando_revisao": 0},
        {"cartoes_referencia": 2},
        {"cartoes_referencia": 0},
    ],
)
def test_qualquer_contagem_diferente_nao_confere(alteracao: dict[str, int]) -> None:
    atual = ContagensAcervo(
        **{
            "cartoes_gerados_aceitos": 3,
            "cartoes_aguardando_revisao": 2,
            "cartoes_referencia": 1,
            **alteracao,
        }
    )
    assert impacto_confere(BASE, atual) is False


def test_so_as_tres_contagens_da_fonte_contam() -> None:
    """Contagens de matéria (fontes, ativos, suspensos) não fazem parte do diálogo da fonte."""
    atual = ContagensAcervo(
        fontes=9,
        cartoes_ativos=7,
        cartoes_suspensos=5,
        cartoes_gerados_aceitos=3,
        cartoes_aguardando_revisao=2,
        cartoes_referencia=1,
    )
    assert impacto_confere(BASE, atual) is True


# --- O corpo da exclusão -----------------------------------------------------------------------


def _corpo(**alteracoes: object) -> dict[str, object]:
    base: dict[str, object] = {
        "modoCartoes": "manter",
        "impactoConfirmado": {
            "cartoesGeradosAceitos": 3,
            "cartoesAguardandoRevisao": 2,
            "cartoesReferencia": 1,
        },
    }
    return {**base, **alteracoes}


@pytest.mark.parametrize("modo", ["manter", "excluir"])
def test_modo_valido_e_convertido(modo: str) -> None:
    entrada = ExclusaoFonteEntradaDTO.model_validate(_corpo(modoCartoes=modo))
    assert entrada.modo_cartoes is ModoCartoes(modo)
    assert entrada.impacto_confirmado == ContagensExclusaoFonteDTO.model_validate(
        {"cartoesGeradosAceitos": 3, "cartoesAguardandoRevisao": 2, "cartoesReferencia": 1}
    )


@pytest.mark.parametrize("modo", [None, "", "apagar", "MANTER", "Excluir", "manter ", 1, True])
def test_modo_ausente_ou_fora_da_lista_e_recusado(modo: object) -> None:
    with pytest.raises(ValidationError):
        ExclusaoFonteEntradaDTO.model_validate(_corpo(modoCartoes=modo))


def test_modo_obrigatorio() -> None:
    corpo = _corpo()
    del corpo["modoCartoes"]
    with pytest.raises(ValidationError):
        ExclusaoFonteEntradaDTO.model_validate(corpo)


def test_impacto_confirmado_obrigatorio_e_completo() -> None:
    corpo = _corpo()
    del corpo["impactoConfirmado"]
    with pytest.raises(ValidationError):
        ExclusaoFonteEntradaDTO.model_validate(corpo)
    with pytest.raises(ValidationError):
        ExclusaoFonteEntradaDTO.model_validate(
            _corpo(impactoConfirmado={"cartoesGeradosAceitos": 3, "cartoesAguardandoRevisao": 2})
        )


@pytest.mark.parametrize(
    "campo", ["cartoesGeradosAceitos", "cartoesAguardandoRevisao", "cartoesReferencia"]
)
@pytest.mark.parametrize("valor", [-1, 1.5, "3", None])
def test_contagens_confirmadas_sao_inteiros_nao_negativos(campo: str, valor: object) -> None:
    contagens = {
        "cartoesGeradosAceitos": 3,
        "cartoesAguardandoRevisao": 2,
        "cartoesReferencia": 1,
        campo: valor,
    }
    with pytest.raises(ValidationError):
        ExclusaoFonteEntradaDTO.model_validate(_corpo(impactoConfirmado=contagens))


def test_campos_extras_e_nomes_em_snake_case_sao_recusados() -> None:
    with pytest.raises(ValidationError):
        ExclusaoFonteEntradaDTO.model_validate(_corpo(forcar=True))
    with pytest.raises(ValidationError):
        ExclusaoFonteEntradaDTO.model_validate(
            {
                "modo_cartoes": "manter",
                "impacto_confirmado": {
                    "cartoes_gerados_aceitos": 3,
                    "cartoes_aguardando_revisao": 2,
                    "cartoes_referencia": 1,
                },
            }
        )
