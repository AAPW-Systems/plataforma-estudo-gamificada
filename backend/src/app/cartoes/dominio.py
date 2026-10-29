"""Regras puras dos cartões: texto, limites, estado inicial, rótulos (sem banco e sem HTTP).

A 004 reutiliza `normalizar_texto_cartao` e `validar_limites` ao aceitar e editar cartões
gerados (D-004, DTEC 036). Nada daqui calcula agendamento: o estado inicial vem do cartão novo da
biblioteca (RN-26, DTEC 037).
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from fsrs import Card, State

from app.cartoes.modelos import EstadoFsrs, OrigemCartao, SituacaoCartao
from app.nucleo.texto import tem_caractere_visivel

# As enumerações moram em `modelos`; os DTOs as importam daqui (não importam `modelos`, DTEC 018).
__all__ = ["EstadoFsrs", "OrigemCartao", "SituacaoCartao"]

BUSCA_MAXIMA = 100  # caracteres do termo de busca (DTEC 033)
PAGINA_PADRAO = 50  # itens por página quando o `limite` não vem (DTEC 034)
PAGINA_MAXIMA = 100
ROTULO_FONTE_APAGADA = "Fonte apagada"
_CAMPOS_DE_TEXTO = frozenset({"frente", "verso", "explicacao"})

_ROTULOS_ORIGEM = {
    OrigemCartao.GERADO_VERIFICADO: "Gerado e verificado",
    OrigemCartao.EDITADO: "Editado por você",
    OrigemCartao.CRIADO: "Criado por você",
}

# Cada estado da biblioteca tem de ter um correspondente: se uma versão nova criar outro, o
# teste do mapeamento falha e o plano é revisto.
_ESTADOS = {
    State.Learning: EstadoFsrs.APRENDIZADO,
    State.Review: EstadoFsrs.REVISAO,
    State.Relearning: EstadoFsrs.REAPRENDIZADO,
}


# --- Texto (RF-001, RF-011, DTEC 036) ------------------------------------------------------------


def normalizar_texto_cartao(texto: str) -> str:
    """Texto puro do cartão: quebras `\\n`, sem controles, em NFC e sem pontas em branco.

    - `\\r\\n` e `\\r` viram `\\n`;
    - saem os controles C0 e C1 (exceto `\\n` e `\\t`) e os substitutos isolados, que não
      codificam em UTF-8 nem entram no PostgreSQL;
    - os controles saem **antes** do NFC, para que um controle entre a letra e o acento não
      deixe a sequência fora da forma normal;
    - quebras e espaços internos ficam: fazem parte do conteúdo. Caracteres bidirecionais e de
      largura zero ficam (podem ser legítimos); a exibição como texto puro impede abuso (RQ-001).
    """
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = "".join(c for c in texto if c in "\n\t" or unicodedata.category(c) not in {"Cc", "Cs"})
    return unicodedata.normalize("NFC", texto).strip()


def normalizar_busca(termo: str | None) -> str | None:
    """O termo de busca com a mesma normalização do texto do cartão; vazio vira `None`.

    Assim, buscar só espaços equivale a não buscar, e o termo e o texto comparados passaram pela
    mesma limpeza (NFC, sem controles e sem pontas). O teto de `BUSCA_MAXIMA` é conferido na
    entrada, antes daqui (DTEC 033).
    """
    if termo is None:
        return None
    return normalizar_texto_cartao(termo) or None


@dataclass(frozen=True, slots=True)
class LimitesTexto:
    """Limites vigentes em caracteres (code points), configuráveis por ambiente (D-004)."""

    frente: int
    verso: int
    explicacao: int


@dataclass(frozen=True, slots=True)
class TextoCartao:
    """Frente, verso e explicação já normalizados e dentro dos limites."""

    frente: str
    verso: str
    explicacao: str | None


class TextoInvalido(Exception):  # noqa: N818
    """Um ou mais campos fora das regras; `campos` leva uma mensagem por campo."""

    def __init__(self, campos: dict[str, str]) -> None:
        self.campos = campos
        super().__init__(str(campos))


def _milhares(numero: int) -> str:
    return f"{numero:,}".replace(",", ".")


def _visivel(texto: str) -> str:
    """Texto sem nenhum caractere visível (só espaços, controles ou largura zero) vale vazio."""
    return texto if tem_caractere_visivel(texto) else ""


def _validar_campo(campo: str, valor: str | None, limites: LimitesTexto) -> str | None:
    """O texto normalizado do campo, ou `TextoInvalido` com a mensagem dele."""
    texto = _visivel(normalizar_texto_cartao(valor or ""))
    if campo == "explicacao":
        if len(texto) > limites.explicacao:
            raise TextoInvalido({campo: f"Use até {_milhares(limites.explicacao)} caracteres."})
        return texto or None
    maximo = {"frente": limites.frente, "verso": limites.verso}[campo]
    if not 1 <= len(texto) <= maximo:
        raise TextoInvalido({campo: f"Use de 1 a {_milhares(maximo)} caracteres."})
    return texto


def _validar_campos(
    valores: Mapping[str, str | None], limites: LimitesTexto
) -> dict[str, str | None]:
    erros: dict[str, str] = {}
    normalizados: dict[str, str | None] = {}
    for campo, valor in valores.items():
        try:
            normalizados[campo] = _validar_campo(campo, valor, limites)
        except TextoInvalido as erro:
            erros.update(erro.campos)
    if erros:
        raise TextoInvalido(erros)
    return normalizados


def validar_limites(
    frente: str, verso: str, explicacao: str | None, limites: LimitesTexto
) -> TextoCartao:
    """Normaliza e confere os três textos, juntando os erros de todos os campos.

    Frente e verso têm de ter de 1 a seu limite; a explicação é opcional, e vazia vira `None`.
    A contagem é em code points, depois da normalização, igual à da interface.
    """
    textos = _validar_campos({"frente": frente, "verso": verso, "explicacao": explicacao}, limites)
    return TextoCartao(str(textos["frente"]), str(textos["verso"]), textos["explicacao"])


def validar_edicao(
    atual: TextoCartao, alteracoes: Mapping[str, str | None], limites: LimitesTexto
) -> TextoCartao:
    """O texto depois da edição parcial: só os campos enviados são normalizados e conferidos.

    Um campo ausente fica como está, mesmo que um limite configurado depois seja menor que ele
    (D-004). `explicacao` nula ou vazia remove a explicação. Campo fora dos três é erro de
    programação (`KeyError`): o DTO já recusa campos extras.
    """
    for campo in alteracoes:
        if campo not in _CAMPOS_DE_TEXTO:
            raise KeyError(campo)
    textos = _validar_campos(alteracoes, limites)
    return TextoCartao(
        frente=str(textos.get("frente", atual.frente)),
        verso=str(textos.get("verso", atual.verso)),
        explicacao=textos["explicacao"] if "explicacao" in textos else atual.explicacao,
    )


def houve_mudanca(atual: TextoCartao, novo: TextoCartao) -> bool:
    """Mudança efetiva, comparando os textos já normalizados (US2-3).

    Espaços nas pontas, `\r\n` no lugar de `\n` e explicação vazia no lugar de nula não são
    mudança; maiúsculas e minúsculas são (o estudante quis mudar).
    """
    return atual != novo


def origem_apos_edicao(origem: OrigemCartao, *, mudou: bool) -> OrigemCartao:
    """`gerado_verificado` com mudança efetiva vira `editado` e perde o selo (RF-006, DTEC 038).

    `editado` e `criado` não mudam, e a origem nunca volta a `gerado_verificado`.
    """
    if mudou and origem is OrigemCartao.GERADO_VERIFICADO:
        return OrigemCartao.EDITADO
    return origem


# --- Estado de agendamento (RF-003, DTEC 037) ----------------------------------------------------


@dataclass(frozen=True, slots=True)
class EstadoInicial:
    """As colunas do FSRS de um cartão novo, espelho do `Card` da biblioteca fixada."""

    estado_fsrs: EstadoFsrs
    passo: int | None
    estabilidade: float | None
    dificuldade: float | None
    vencimento: datetime
    ultima_revisao: datetime | None


def estado_inicial(agora: datetime) -> EstadoInicial:
    """O cartão novo vence no instante da criação e ainda não tem revisão."""
    if agora.tzinfo is None:
        raise ValueError("o instante da criação precisa ter fuso")
    card = Card(due=agora)
    return EstadoInicial(
        estado_fsrs=_ESTADOS[card.state],
        passo=card.step,
        estabilidade=card.stability,
        dificuldade=card.difficulty,
        vencimento=card.due,
        ultima_revisao=card.last_review,
    )


# --- Rótulos e derivados (RF-009, D-002) ---------------------------------------------------------


def rotulo_origem(origem: OrigemCartao) -> str:
    return _ROTULOS_ORIGEM[origem]


def verificado(origem: OrigemCartao) -> bool:
    """O selo de verificado só existe em cartão gerado e sustentado; nunca no do estudante."""
    return origem is OrigemCartao.GERADO_VERIFICADO


def fonte_apagada(referencia_titulo: str | None, fonte_id: int | None) -> bool:
    """Há a descrição copiada de uma fonte que já não existe (D-006)."""
    return referencia_titulo is not None and fonte_id is None
