"""Normalização do texto e divisão em trechos (DTEC 029; RF-006, RF-016).

Funções puras, sem banco e sem HTTP, e deterministas: o mesmo texto e os mesmos parâmetros
dão sempre os mesmos trechos (Princípio IV). Os trechos são fatias do texto normalizado da fonte
inteira (`texto_completo[inicio:fim] == trecho.texto`), nunca atravessam uma unidade (página de PDF,
seção de Markdown) e levam a página física só em PDF (Princípio I).

Unidades: cada página do PDF; no Markdown, cada seção iniciada por um título ATX fora de bloco
cercado; no TXT, o documento inteiro. Dentro da unidade, parágrafos são acumulados até o tamanho
alvo; um parágrafo acima do máximo é cortado em fim de frase (ou no último espaço, ou no limite);
o trecho seguinte começa com até `sobreposicao` caracteres do anterior, no início de uma palavra.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

VERSAO_BASE = "v2"  # v2: hifenização desfeita depois da extração do PDF (DTEC 029)
SOBRA_MINIMA = 200  # uma sobra final menor que isto é unida ao trecho anterior, se couber
_FIM_DE_FRASE = ".!?…"
_SEPARADOR_DE_PARAGRAFOS = re.compile(r"\n{2,}")
_TITULO_ATX = re.compile(r" {0,3}#{1,6} +\S")
_CERCA = re.compile(r" {0,3}(`{3,}|~{3,})")
_TABULACOES_E_ESPACOS = re.compile(r"[ \t]+")
_ESPACOS_ANTES_DA_QUEBRA = re.compile(r" +\n")
_QUEBRAS_EXCESSIVAS = re.compile(r"\n{3,}")


@dataclass(frozen=True, slots=True)
class Parametros:
    alvo: int = 1200
    maximo: int = 2000
    sobreposicao: int = 150

    def __post_init__(self) -> None:
        if not (0 <= self.sobreposicao < self.alvo <= self.maximo):
            raise ValueError(
                "parâmetros de divisão incoerentes: 0 <= sobreposição < alvo <= máximo"
            )


@dataclass(frozen=True, slots=True)
class TrechoDividido:
    ordem: int
    texto: str
    pagina: int | None
    inicio: int
    fim: int


@dataclass(frozen=True, slots=True)
class TextoDividido:
    texto_completo: str
    trechos: list[TrechoDividido]


@dataclass(frozen=True, slots=True)
class _Unidade:
    inicio: int
    fim: int
    pagina: int | None


def versao_extracao(p: Parametros) -> str:
    """Versão do extrator e dos parâmetros, guardada em `fontes.versao_extracao`."""
    return f"{VERSAO_BASE}-a{p.alvo}-m{p.maximo}-s{p.sobreposicao}"


# --- Normalização --------------------------------------------------------------------------------


def normalizar_texto(texto: str) -> str:
    """NFC; quebras de linha unificadas; sem controles (exceto `\\n` e `\\t`); espaços
    repetidos viram um; sem espaços no fim da linha; no máximo uma linha em branco seguida."""
    unificado = texto.replace("\r\n", "\n").replace("\r", "\n")
    # Controles saem antes do NFC: remover um controle entre a base e a marca as aproxima.
    sem_controles = "".join(c for c in unificado if c in "\n\t" or unicodedata.category(c) != "Cc")
    texto_nfc = unicodedata.normalize("NFC", sem_controles)
    texto_nfc = _TABULACOES_E_ESPACOS.sub(" ", texto_nfc)
    texto_nfc = _ESPACOS_ANTES_DA_QUEBRA.sub("\n", texto_nfc)
    texto_nfc = _QUEBRAS_EXCESSIVAS.sub("\n\n", texto_nfc)
    return texto_nfc.strip()


def tem_texto(texto: str) -> bool:
    """Há ao menos um caractere alfanumérico? Sem ele, o PDF não tem camada de texto (CB-23)."""
    return any(c.isalnum() for c in texto)


# --- Divisão -------------------------------------------------------------------------------------


def dividir_pdf(paginas: Sequence[str], p: Parametros) -> TextoDividido:
    """`paginas` é o texto bruto de cada página física, na ordem (a primeira é a página 1).

    Páginas sem texto depois da normalização não geram trecho, e a numeração segue física.
    """
    partes: list[str] = []
    unidades: list[_Unidade] = []
    posicao = 0
    for numero, bruto in enumerate(paginas, start=1):
        texto = normalizar_texto(bruto)
        if not texto:
            continue
        if partes:
            posicao += 2  # o separador "\n\n" entre as páginas
        unidades.append(_Unidade(posicao, posicao + len(texto), numero))
        partes.append(texto)
        posicao += len(texto)
    texto_completo = "\n\n".join(partes)
    return TextoDividido(texto_completo, _dividir_unidades(texto_completo, unidades, p))


def dividir_texto(texto: str, *, markdown: bool, p: Parametros) -> TextoDividido:
    """`texto` já normalizado. No Markdown, cada seção de título é uma unidade."""
    if markdown:
        faixas = _secoes_markdown(texto)
    else:
        faixas = [(0, len(texto))]
    unidades = [_Unidade(a, b, None) for a, b in (_aparar(texto, f, g) for f, g in faixas) if a < b]
    return TextoDividido(texto, _dividir_unidades(texto, unidades, p))


def _aparar(texto: str, inicio: int, fim: int) -> tuple[int, int]:
    """A faixa sem espaços nas pontas; vazia (`a == b`) se só houver espaços."""
    while inicio < fim and texto[inicio].isspace():
        inicio += 1
    while fim > inicio and texto[fim - 1].isspace():
        fim -= 1
    return inicio, fim


def _secoes_markdown(texto: str) -> list[tuple[int, int]]:
    """Faixas de cada seção: o que vem antes do primeiro título e uma por título ATX.

    Títulos dentro de bloco de código cercado (``` ou ~~~) não abrem seção.
    """
    inicios = [0]
    cerca: tuple[str, int] | None = None
    posicao = 0
    for linha in texto.split("\n"):
        achada = _CERCA.match(linha)
        if cerca is not None:
            if achada and achada.group(1)[0] == cerca[0] and len(achada.group(1)) >= cerca[1]:
                if not linha[achada.end() :].strip():
                    cerca = None
        elif achada:
            cerca = (achada.group(1)[0], len(achada.group(1)))
        elif _TITULO_ATX.match(linha) and posicao > inicios[-1]:
            inicios.append(posicao)
        posicao += len(linha) + 1
    fins = [*inicios[1:], len(texto)]
    return list(zip(inicios, fins, strict=True))


def _dividir_unidades(
    texto: str, unidades: Sequence[_Unidade], p: Parametros
) -> list[TrechoDividido]:
    trechos: list[TrechoDividido] = []
    for unidade in unidades:
        for inicio, fim in _faixas_da_unidade(texto, unidade, p):
            trechos.append(
                TrechoDividido(len(trechos), texto[inicio:fim], unidade.pagina, inicio, fim)
            )
    return trechos


def _faixas_da_unidade(texto: str, unidade: _Unidade, p: Parametros) -> list[tuple[int, int]]:
    segmentos = _segmentos(texto, unidade, p)
    faixas: list[tuple[int, int, int]] = []  # início, fim e início do conteúdo novo
    superposicao: int | None = None
    i = 0
    while i < len(segmentos):
        primeiro_inicio, fim = segmentos[i]
        inicio = superposicao if superposicao is not None else primeiro_inicio
        j = i + 1
        while j < len(segmentos) and segmentos[j][1] - inicio <= p.alvo:
            fim = segmentos[j][1]
            j += 1
        if fim - inicio > p.maximo:
            # A sobreposição não cabe com o conteúdo novo: encurta-a até o máximo.
            alinhado = _inicio_de_palavra(texto, max(inicio, fim - p.maximo), primeiro_inicio + 1)
            inicio = primeiro_inicio if alinhado is None else alinhado
        faixas.append((inicio, fim, primeiro_inicio))
        superposicao = None
        if j < len(segmentos) and p.sobreposicao and fim - inicio > p.sobreposicao:
            candidato = _inicio_de_palavra(texto, fim - p.sobreposicao, fim)
            if candidato is not None and candidato > inicio:
                superposicao = candidato
        i = j
    if len(faixas) >= 2:
        anterior, ultimo = faixas[-2], faixas[-1]
        if ultimo[1] - ultimo[2] < SOBRA_MINIMA and ultimo[1] - anterior[0] <= p.maximo:
            faixas[-2:] = [(anterior[0], ultimo[1], anterior[2])]
    return [(inicio, fim) for inicio, fim, _ in faixas]


def _inicio_de_palavra(texto: str, a_partir_de: int, limite: int) -> int | None:
    """O primeiro início de palavra em `[a_partir_de, limite)`, se houver."""
    for posicao in range(a_partir_de, limite):
        if not texto[posicao].isspace() and (posicao == 0 or texto[posicao - 1].isspace()):
            return posicao
    return None


def _segmentos(texto: str, unidade: _Unidade, p: Parametros) -> list[tuple[int, int]]:
    """Parágrafos da unidade; os que passam do máximo são cortados em partes."""
    limite_da_parte = p.maximo - p.sobreposicao - 2
    if limite_da_parte < 1:
        limite_da_parte = p.maximo
    segmentos: list[tuple[int, int]] = []
    inicio = unidade.inicio
    separadores = [
        (m.start(), m.end())
        for m in _SEPARADOR_DE_PARAGRAFOS.finditer(texto, unidade.inicio, unidade.fim)
    ]
    for fim_do_paragrafo, proximo_inicio in [*separadores, (unidade.fim, unidade.fim)]:
        a, b = _aparar(texto, inicio, fim_do_paragrafo)
        if a < b:
            if b - a <= p.maximo:
                segmentos.append((a, b))
            else:
                segmentos.extend(_cortar(texto, a, b, limite_da_parte))
        inicio = proximo_inicio
    return segmentos


def _cortar(texto: str, inicio: int, fim: int, limite: int) -> list[tuple[int, int]]:
    """Parte `[inicio, fim)` em pedaços de até `limite`: no fim de frase, senão no último
    espaço, senão no próprio limite."""
    partes: list[tuple[int, int]] = []
    atual = inicio
    while fim - atual > limite:
        teto = atual + limite
        corte = _fim_de_frase(texto, atual, teto, fim)
        if corte is None:
            corte = _ultimo_espaco(texto, atual, teto)
        if corte is None:
            corte = teto
        while corte > atual and texto[corte - 1].isspace():
            corte -= 1
        if corte <= atual:  # defesa: nunca devolver parte vazia
            corte = teto
        partes.append((atual, corte))
        atual = corte
        while atual < fim and texto[atual].isspace():
            atual += 1
    if atual < fim:
        partes.append((atual, fim))
    return partes


def _fim_de_frase(texto: str, inicio: int, teto: int, fim: int) -> int | None:
    for corte in range(teto, inicio, -1):
        if texto[corte - 1] in _FIM_DE_FRASE and (corte >= fim or texto[corte].isspace()):
            return corte
    return None


def _ultimo_espaco(texto: str, inicio: int, teto: int) -> int | None:
    for corte in range(teto, inicio, -1):
        if texto[corte].isspace():
            return corte
    return None
