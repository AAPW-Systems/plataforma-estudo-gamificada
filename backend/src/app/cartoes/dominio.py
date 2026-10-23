"""Regras puras dos cartões: texto, limites, estado inicial, rótulos (sem banco e sem HTTP).

A 004 reutiliza `normalizar_texto_cartao` e `validar_limites` ao aceitar e editar cartões
gerados (D-004, DTEC 036). Nada daqui calcula agendamento: o estado inicial vem do cartão novo da
biblioteca (RN-26, DTEC 037).
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import datetime

from fsrs import Card, State

from app.cartoes.modelos import EstadoFsrs, OrigemCartao
from app.nucleo.texto import tem_caractere_visivel

BUSCA_MAXIMA = 100  # caracteres do termo de busca (DTEC 033)
PAGINA_PADRAO = 50  # itens por página quando o `limite` não vem (DTEC 034)
PAGINA_MAXIMA = 100
ROTULO_FONTE_APAGADA = "Fonte apagada"

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


def validar_limites(
    frente: str, verso: str, explicacao: str | None, limites: LimitesTexto
) -> TextoCartao:
    """Normaliza e confere os três textos, juntando os erros de todos os campos.

    Frente e verso têm de ter de 1 a seu limite; a explicação é opcional, e vazia vira `None`.
    A contagem é em code points, depois da normalização, igual à da interface.
    """
    erros: dict[str, str] = {}
    normalizados: dict[str, str] = {}
    for campo, valor, maximo in (
        ("frente", frente, limites.frente),
        ("verso", verso, limites.verso),
    ):
        texto = _visivel(normalizar_texto_cartao(valor))
        if not 1 <= len(texto) <= maximo:
            erros[campo] = f"Use de 1 a {_milhares(maximo)} caracteres."
        normalizados[campo] = texto
    complemento = _visivel(normalizar_texto_cartao(explicacao or ""))
    if len(complemento) > limites.explicacao:
        erros["explicacao"] = f"Use até {_milhares(limites.explicacao)} caracteres."
    if erros:
        raise TextoInvalido(erros)
    return TextoCartao(normalizados["frente"], normalizados["verso"], complemento or None)


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
