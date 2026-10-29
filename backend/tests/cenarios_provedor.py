"""Provedor simulado da geração (spec 004, T006; DTEC 047): um `FunctionModel` por cenário.

Nenhum cenário chama a rede (`ALLOW_MODEL_REQUESTS = False` no `conftest`). As funções leem os
trechos da mensagem do usuário no formato da DTEC 047, ``<trecho id="Tn" nonce="…">texto
</trecho nonce="…">``, e devolvem a chamada da ferramenta de saída com os argumentos do esquema
`SaidaGeracao` (``cartoes`` com ``frente``, ``verso``, ``explicacao``, ``trechos`` e ``citacao``, e
``pontos_contraditorios``). A juíza lê ``<cartao indice="N">`` e devolve ``avaliacoes`` com
``indice``, ``sustentado`` e ``motivo``.

Cenários do gerador: válidos com citação literal; sem trecho e rótulo ``T999``; citação inventada;
fora do assunto; instrução obedecida; lados de uma contradição; resposta malformada; timeout, 5xx e
429 (por minuto e cota diária); 15 cartões; campos com 50 mil caracteres.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import exceptions as e
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage

type FuncaoModelo = Callable[[list[ModelMessage], AgentInfo], ModelResponse]

MODELO_SIMULADO = "simulado"
CITACAO_MINIMA = 20
CITACAO_MAXIMA = 300
TAMANHO_ENORME = 50_000

_TRECHO = re.compile(
    r'<trecho id="(?P<rotulo>T\d+)" nonce="(?P<nonce>[^"]+)">\n?(?P<texto>.*?)\n?'
    r'</trecho nonce="(?P=nonce)">',
    re.DOTALL,
)
_CARTAO = re.compile(r'<cartao indice="(\d+)"')
_FRASE = re.compile(r"[^.!?]+[.!?]")


def ultima_mensagem(mensagens: list[ModelMessage]) -> str:
    """O texto do último pedido do usuário (as instruções vão à parte, pelo `instructions`)."""
    for mensagem in reversed(mensagens):
        if isinstance(mensagem, ModelRequest):
            partes = [p.content for p in mensagem.parts if isinstance(p, UserPromptPart)]
            textos = [p for p in partes if isinstance(p, str)]
            if textos:
                return "\n".join(textos)
    return ""


def trechos_do_prompt(mensagens: list[ModelMessage]) -> dict[str, str]:
    """Rótulo → texto dos trechos dentro dos delimitadores com *nonce*."""
    return {m["rotulo"]: m["texto"] for m in _TRECHO.finditer(ultima_mensagem(mensagens))}


def citacao_literal(texto: str) -> str:
    """A primeira frase do trecho com 20 a 300 caracteres, copiada literalmente."""
    frases: list[str] = _FRASE.findall(texto)
    for frase in (f.strip() for f in frases):
        if CITACAO_MINIMA <= len(frase) <= CITACAO_MAXIMA:
            return frase
    return texto.strip()[:CITACAO_MAXIMA]


def cartao_sustentado(rotulo: str, texto: str, numero: int = 1) -> dict[str, Any]:
    """Um cartão que passa nos portões: citação literal, verso e explicação com as palavras dela."""
    citacao = citacao_literal(texto)
    return {
        "frente": f"Segundo o trecho, o que se afirma no ponto {numero}?",
        "verso": citacao,
        "explicacao": f"O trecho afirma: {citacao}",
        "trechos": [rotulo],
        "citacao": citacao,
    }


def _saida(info: AgentInfo, argumentos: Mapping[str, Any]) -> ModelResponse:
    if not info.output_tools:
        raise AssertionError("o agente não tem ferramenta de saída: o esquema mudou?")
    return ModelResponse(
        parts=[ToolCallPart(info.output_tools[0].name, dict(argumentos))],
        usage=RequestUsage(input_tokens=1000, output_tokens=200),
    )


def _gerador(
    cartoes: Callable[[dict[str, str]], list[dict[str, Any]]], **extra: Any
) -> FuncaoModelo:
    def funcao(mensagens: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        trechos = trechos_do_prompt(mensagens)
        return _saida(info, {"cartoes": cartoes(trechos), "pontos_contraditorios": [], **extra})

    return funcao


# --- Gerador ----------------------------------------------------------------------------------


def validos(quantidade: int | None = None) -> FuncaoModelo:
    """Um cartão sustentado por trecho (ou `quantidade`, repetindo os trechos em ciclo)."""

    def cartoes(trechos: dict[str, str]) -> list[dict[str, Any]]:
        itens = list(trechos.items())
        total = len(itens) if quantidade is None else quantidade
        return [
            cartao_sustentado(*itens[i % len(itens)], numero=i + 1) for i in range(total) if itens
        ]

    return _gerador(cartoes)


def quinze_cartoes() -> FuncaoModelo:
    """Caso de borda: o modelo devolve 15; só os 10 primeiros aprovados são publicados."""
    return validos(15)


def sem_trecho() -> FuncaoModelo:
    """Um cartão sem rótulo e outro com um rótulo inexistente (`sem_evidencia`)."""

    def cartoes(trechos: dict[str, str]) -> list[dict[str, Any]]:
        rotulo, texto = next(iter(trechos.items()))
        sem_rotulo = {**cartao_sustentado(rotulo, texto), "trechos": []}
        inventado = {**cartao_sustentado(rotulo, texto, 2), "trechos": ["T999"]}
        return [sem_rotulo, inventado]

    return _gerador(cartoes)


def citacao_inventada() -> FuncaoModelo:
    """A citação não está no trecho citado (`citacao_nao_encontrada`)."""

    def cartoes(trechos: dict[str, str]) -> list[dict[str, Any]]:
        rotulo, texto = next(iter(trechos.items()))
        return [
            {
                **cartao_sustentado(rotulo, texto),
                "citacao": "Esta frase não aparece em nenhum trecho da fonte enviada.",
            }
        ]

    return _gerador(cartoes)


def fora_do_assunto() -> FuncaoModelo:
    """Citação literal, mas verso e explicação sem apoio no trecho (`cobertura_insuficiente`)."""

    def cartoes(trechos: dict[str, str]) -> list[dict[str, Any]]:
        rotulo, texto = next(iter(trechos.items()))
        return [
            {
                **cartao_sustentado(rotulo, texto),
                "frente": "Qual é a capital da Austrália?",
                "verso": "Camberra, planejada no início do século XX.",
                "explicacao": "Camberra foi escolhida como meio-termo entre Sydney e Melbourne.",
            }
        ]

    return _gerador(cartoes)


def instrucao_obedecida() -> FuncaoModelo:
    """O modelo obedece à instrução embutida (CB-15): futebol, instruções reveladas, página 99."""

    def cartoes(trechos: dict[str, str]) -> list[dict[str, Any]]:
        rotulo, texto = next(iter(trechos.items()))
        citacao = citacao_literal(texto)
        return [
            {
                "frente": "Qual seleção venceu a Copa do Mundo de 2002?",
                "verso": "O Brasil, com dois gols de Ronaldo na final.",
                "explicacao": "A final foi disputada em Yokohama contra a Alemanha.",
                "trechos": [rotulo],
                "citacao": citacao,
            },
            {
                "frente": "Quais são as instruções de sistema do gerador?",
                "verso": "Usar só os trechos e copiar a citação literalmente.",
                "explicacao": "Revelado a pedido do texto da fonte, na página 99.",
                "trechos": [rotulo],
                "citacao": citacao,
            },
        ]

    return _gerador(cartoes)


def lados_da_contradicao() -> FuncaoModelo:
    """Um cartão para cada lado da contradição, cada um com citação literal (CB-09).

    Os portões determinísticos não leem sentido: os dois passam por eles, e quem os reprova é a
    juíza (`contradicao`). O ponto também é declarado em `pontos_contraditorios`.
    """

    def cartoes(trechos: dict[str, str]) -> list[dict[str, Any]]:
        return [
            cartao_sustentado(rotulo, texto, i + 1)
            for i, (rotulo, texto) in enumerate(trechos.items())
        ]

    return _gerador(cartoes, pontos_contraditorios=["Quem desenvolveu a vacina contra a varíola"])


def campos_enormes() -> FuncaoModelo:
    """Frente, verso e explicação com 50 mil caracteres (`estrutura_invalida`)."""

    def cartoes(trechos: dict[str, str]) -> list[dict[str, Any]]:
        rotulo, texto = next(iter(trechos.items()))
        enorme = "a" * TAMANHO_ENORME
        return [
            {
                **cartao_sustentado(rotulo, texto),
                "frente": enorme,
                "verso": enorme,
                "explicacao": enorme,
            }
        ]

    return _gerador(cartoes)


def malformada() -> FuncaoModelo:
    """Texto livre em vez da saída estruturada, sempre (o pedido de correção também falha)."""

    def funcao(mensagens: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[TextPart("Aqui estão os seus cartões: 1) mitocôndria...")])

    return funcao


def _falha(erro: Callable[[], Exception]) -> FuncaoModelo:
    def funcao(mensagens: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise erro()

    return funcao


def timeout() -> FuncaoModelo:
    return _falha(lambda: e.ModelTimeoutError(MODELO_SIMULADO, "tempo esgotado"))


def erro_5xx() -> FuncaoModelo:
    return _falha(lambda: e.ModelHTTPError(503, MODELO_SIMULADO, {"error": "indisponível"}))


def limite_por_minuto() -> FuncaoModelo:
    return _falha(lambda: e.ModelHTTPError(429, MODELO_SIMULADO, {"error": "requests per minute"}))


def cota_diaria() -> FuncaoModelo:
    return _falha(
        lambda: e.ModelHTTPError(
            429,
            MODELO_SIMULADO,
            {"error": {"details": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel"}]}},
        )
    )


# --- Juíza ------------------------------------------------------------------------------------


def juiza(reprovar: Mapping[int, str] | None = None, omitir: Collection[int] = ()) -> FuncaoModelo:
    """Aprova todos os cartões do prompt, menos os de `reprovar` (índice → motivo) e `omitir`.

    Um índice omitido conta como reprovação no portão 5 (DTEC 042).
    """
    reprovados = dict(reprovar or {})

    def funcao(mensagens: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        indices = [int(i) for i in _CARTAO.findall(ultima_mensagem(mensagens))]
        avaliacoes = [
            {
                "indice": indice,
                "sustentado": indice not in reprovados,
                "motivo": reprovados.get(indice),
            }
            for indice in indices
            if indice not in omitir
        ]
        return _saida(info, {"avaliacoes": avaliacoes})

    return funcao


# --- Contador ---------------------------------------------------------------------------------


@dataclass
class ContadorChamadas:
    """Envolve uma função de cenário e conta as chamadas (ex.: zero sem ciência, CB-26)."""

    funcao: FuncaoModelo
    chamadas: int = 0
    mensagens: list[str] = field(default_factory=list)

    def __call__(self, mensagens: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        self.chamadas += 1
        self.mensagens.append(ultima_mensagem(mensagens))
        return self.funcao(mensagens, info)

    def modelo(self) -> FunctionModel:
        return FunctionModel(self, model_name=MODELO_SIMULADO)


def modelo(funcao: FuncaoModelo) -> FunctionModel:
    return FunctionModel(funcao, model_name=MODELO_SIMULADO)
