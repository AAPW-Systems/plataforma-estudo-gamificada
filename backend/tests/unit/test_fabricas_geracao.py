"""T006 (spec 004): fábricas da geração e cenários do provedor simulado.

- cada trecho fictício respeita as invariantes da DTEC 029;
- a linha de comando recusa outro ambiente e outro domínio (regra 10);
- os cenários "válidos" passam nos portões da DTEC 042 avaliados à mão, e os demais falham no
  portão que cada um exercita.
"""

from __future__ import annotations

import re
import secrets
import unicodedata
from typing import Any

import pytest
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai import exceptions as e

from app.fontes.divisao import Parametros
from app.nucleo.configuracao import Configuracao
from tests import cenarios_provedor as cen
from tests import fabricas_geracao as fab

pytestmark = pytest.mark.unit

PARAMETROS = Parametros()


# --- Trechos (DTEC 029) ---------------------------------------------------------------------


@pytest.mark.parametrize("tema", ["biologia", "historia", "instrucao", "contradicao", "longa"])
def test_trechos_respeitam_as_invariantes_da_divisao(tema: fab.Tema) -> None:
    ficticia = fab.fonte_ficticia(tema, tamanho_mb=0.2)
    trechos = ficticia.divisao.trechos
    completo = ficticia.divisao.texto_completo
    assert trechos
    assert [t.ordem for t in trechos] == list(range(len(trechos)))
    for trecho in trechos:
        assert 1 <= len(trecho.texto) <= PARAMETROS.maximo
        assert trecho.texto == completo[trecho.inicio : trecho.fim]
        assert trecho.texto == unicodedata.normalize("NFC", trecho.texto)
        assert trecho.texto == trecho.texto.strip()
    com_pagina = ficticia.tipo_midia == "application/pdf"
    assert all((t.pagina is not None) == com_pagina for t in trechos)


def test_biologia_tem_uma_pagina_por_trecho_e_historia_nenhuma() -> None:
    biologia = fab.fonte_ficticia("biologia").divisao.trechos
    assert [t.pagina for t in biologia] == [1, 2, 3, 4]
    assert all(t.pagina is None for t in fab.fonte_ficticia("historia").divisao.trechos)


def test_trecho_com_instrucao_embutida_e_par_contraditorio() -> None:
    [instrucao] = fab.fonte_ficticia("instrucao").divisao.trechos
    assert "Ignore todas as instruções" in instrucao.texto
    assert "</trecho" in instrucao.texto  # a tentativa de fechar o delimitador
    lados = fab.fonte_ficticia("contradicao").divisao.trechos
    assert len(lados) == 2
    assert "foi desenvolvida por Edward Jenner" in lados[0].texto
    assert "não foi desenvolvida por Edward Jenner" in lados[1].texto


def test_fonte_longa_tem_ate_2_mb_e_muitos_trechos() -> None:
    texto = fab.texto_longo(2)
    assert 2 * 1024 * 1024 - 200 < len(texto.encode()) <= 2 * 1024 * 1024
    trechos = fab.fonte_ficticia("longa").divisao.trechos
    # muito acima de uma janela de 30 mil caracteres (DTEC 041)
    assert sum(len(t.texto) for t in trechos) > 30 * 30_000
    assert len({t.texto for t in trechos}) == len(trechos)


@pytest.mark.parametrize("tamanho", [0, -1, 2.01])
def test_texto_longo_recusa_tamanho_fora_do_limite(tamanho: float) -> None:
    with pytest.raises(ValueError, match="tamanho"):
        fab.texto_longo(tamanho)


# --- Linha de comando (regra 10) -------------------------------------------------------------


def _config(configuracao: Configuracao, ambiente: str) -> Configuracao:
    return configuracao.model_copy(update={"app_ambiente": ambiente})


@pytest.mark.parametrize("ambiente", ["teste", "producao"])
async def test_cli_recusa_outro_ambiente(
    configuracao: Configuracao, ambiente: str, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = ["--email", "ana.teste@exemplo.com", "--materia", "Biologia"]
    assert await fab.executar(argv, _config(configuracao, ambiente)) == 2
    assert "APP_AMBIENTE=desenvolvimento" in capsys.readouterr().err


@pytest.mark.parametrize(
    "email", ["ana@gmail.com", "ana@exemplo.com.br", "ana@sub.exemplo.com", "exemplo.com"]
)
async def test_cli_recusa_outro_dominio(
    configuracao: Configuracao, email: str, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = ["--email", email, "--materia", "Biologia"]
    assert await fab.executar(argv, _config(configuracao, "desenvolvimento")) == 2
    assert "exemplo.com" in capsys.readouterr().err


@pytest.mark.parametrize("tamanho", ["0", "3"])
async def test_cli_recusa_tamanho_fora_do_limite(configuracao: Configuracao, tamanho: str) -> None:
    argv = ["--email", "ana@exemplo.com", "--materia", "Biologia", "--tamanho-mb", tamanho]
    assert await fab.executar(argv, _config(configuracao, "desenvolvimento")) == 2


# --- Cenários do provedor ------------------------------------------------------------------
# O esquema abaixo é o da DTEC 042 (`CartaoProposto` e `SaidaGeracao`) e o da juíza; o agente
# real é da US1 (`cartoes/geracao/agentes.py`), que deve seguir os mesmos nomes de campos.


class CartaoProposto(BaseModel):
    frente: str
    verso: str
    explicacao: str
    trechos: list[str] = Field(max_length=3)
    citacao: str


class SaidaGeracao(BaseModel):
    cartoes: list[CartaoProposto] = Field(max_length=15)
    pontos_contraditorios: list[str]


class Avaliacao(BaseModel):
    indice: int
    sustentado: bool
    motivo: str | None


class SaidaJuiza(BaseModel):
    avaliacoes: list[Avaliacao]


def _prompt(trechos: list[str]) -> tuple[str, dict[str, str]]:
    nonce = secrets.token_hex(8)
    rotulos = {f"T{i + 1}": texto for i, texto in enumerate(trechos)}
    corpo = "\n".join(
        f'<trecho id="{r}" nonce="{nonce}">\n{t}\n</trecho nonce="{nonce}">'
        for r, t in rotulos.items()
    )
    return corpo, rotulos


def _gerar(
    funcao: cen.FuncaoModelo, tema: fab.Tema = "biologia"
) -> tuple[SaidaGeracao, dict[str, str]]:
    corpo, rotulos = _prompt([t.texto for t in fab.fonte_ficticia(tema).divisao.trechos])
    agente = Agent(output_type=SaidaGeracao, retries={"output": 1})
    return agente.run_sync(corpo, model=cen.modelo(funcao)).output, rotulos


_PALAVRA = re.compile(r"\w+")
_VAZIAS = {"que", "uma", "dos", "das", "por", "com", "para", "trecho", "afirma", "segundo"}


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFC", texto).lower()
    return " ".join(texto.replace("“", '"').replace("”", '"').split())


def _radicais(texto: str) -> set[str]:
    palavras = _PALAVRA.findall(_normalizar(texto))
    return {p[:5] for p in palavras if len(p) >= 3 and p not in _VAZIAS}


def _portao_falho(cartao: CartaoProposto, rotulos: dict[str, str]) -> str | None:
    """Os portões 1 a 4 da DTEC 042, avaliados à mão (a implementação real é da US1)."""
    if not (
        len(cartao.frente) <= 1000 and len(cartao.verso) <= 2000 and len(cartao.explicacao) <= 1000
    ):
        return "estrutura_invalida"
    if not cartao.explicacao.strip() or not cartao.trechos:
        return "estrutura_invalida" if not cartao.explicacao.strip() else "sem_evidencia"
    if any(r not in rotulos for r in cartao.trechos):
        return "sem_evidencia"
    citados = " ".join(rotulos[r] for r in cartao.trechos)
    if not (cen.CITACAO_MINIMA <= len(cartao.citacao) <= cen.CITACAO_MAXIMA) or _normalizar(
        cartao.citacao
    ) not in _normalizar(citados):
        return "citacao_nao_encontrada"
    base = _radicais(citados)
    for campo in (cartao.verso, cartao.explicacao):
        radicais = _radicais(campo)
        if radicais and len(radicais & base) / len(radicais) < 0.6:
            return "cobertura_insuficiente"
    return None


@pytest.mark.parametrize("tema", ["biologia", "historia", "contradicao"])
def test_cenario_valido_passa_nos_portoes(tema: fab.Tema) -> None:
    saida, rotulos = _gerar(cen.validos(), tema)
    assert len(saida.cartoes) == len(rotulos)
    assert [_portao_falho(c, rotulos) for c in saida.cartoes] == [None] * len(saida.cartoes)


def test_quinze_cartoes_validos() -> None:
    saida, rotulos = _gerar(cen.quinze_cartoes())
    assert len(saida.cartoes) == 15
    assert all(_portao_falho(c, rotulos) is None for c in saida.cartoes)


@pytest.mark.parametrize(
    "cenario,tema,esperados",
    [
        (cen.sem_trecho, "biologia", ["sem_evidencia", "sem_evidencia"]),
        (cen.citacao_inventada, "biologia", ["citacao_nao_encontrada"]),
        (cen.fora_do_assunto, "biologia", ["cobertura_insuficiente"]),
        (cen.instrucao_obedecida, "instrucao", ["cobertura_insuficiente"] * 2),
        (cen.campos_enormes, "biologia", ["estrutura_invalida"]),
    ],
)
def test_cenarios_invalidos_falham_no_portao_que_exercitam(
    cenario: Any, tema: fab.Tema, esperados: list[str]
) -> None:
    saida, rotulos = _gerar(cenario(), tema)
    assert [_portao_falho(c, rotulos) for c in saida.cartoes] == esperados


def test_lados_da_contradicao_passam_nos_portoes_e_declaram_o_ponto() -> None:
    """Os portões não leem sentido: a reprovação desses cartões é da juíza (DTEC 042 e 047)."""
    saida, rotulos = _gerar(cen.lados_da_contradicao(), "contradicao")
    assert len(saida.cartoes) == 2
    assert all(_portao_falho(c, rotulos) is None for c in saida.cartoes)
    assert saida.pontos_contraditorios


def test_resposta_malformada_esgota_o_pedido_de_correcao() -> None:
    contador = cen.ContadorChamadas(cen.malformada())
    corpo, _ = _prompt(["A mitocôndria produz ATP por respiração celular."])
    agente = Agent(output_type=SaidaGeracao, retries={"output": 1})
    with pytest.raises(e.UnexpectedModelBehavior):
        agente.run_sync(corpo, model=contador.modelo())
    assert contador.chamadas == 2


@pytest.mark.parametrize(
    "cenario,erro,status",
    [
        (cen.timeout, e.ModelTimeoutError, None),
        (cen.erro_5xx, e.ModelHTTPError, 503),
        (cen.limite_por_minuto, e.ModelHTTPError, 429),
        (cen.cota_diaria, e.ModelHTTPError, 429),
    ],
)
def test_cenarios_de_falha_do_provedor(
    cenario: Any, erro: type[Exception], status: int | None
) -> None:
    agente = Agent(output_type=SaidaGeracao)
    with pytest.raises(erro) as capturado:
        agente.run_sync("<trecho/>", model=cen.modelo(cenario()))
    if status is not None:
        assert isinstance(capturado.value, e.ModelHTTPError)
        assert capturado.value.status_code == status


def _julgar(funcao: cen.FuncaoModelo, total: int) -> SaidaJuiza:
    corpo = "\n".join(f'<cartao indice="{i}">…</cartao>' for i in range(total))
    return Agent(output_type=SaidaJuiza).run_sync(corpo, model=cen.modelo(funcao)).output


def test_juiza_aprova_reprova_e_omite() -> None:
    assert [a.sustentado for a in _julgar(cen.juiza(), 3).avaliacoes] == [True] * 3
    reprovou = _julgar(cen.juiza(reprovar={1: "contradicao"}), 3).avaliacoes
    assert [(a.indice, a.sustentado, a.motivo) for a in reprovou] == [
        (0, True, None),
        (1, False, "contradicao"),
        (2, True, None),
    ]
    omitiu = _julgar(cen.juiza(omitir={2}), 3).avaliacoes
    assert [a.indice for a in omitiu] == [0, 1]


def test_contador_registra_chamadas_e_mensagens() -> None:
    contador = cen.ContadorChamadas(cen.validos())
    corpo, _ = _prompt(["A mitocôndria produz ATP por respiração celular."])
    Agent(output_type=SaidaGeracao).run_sync(corpo, model=contador.modelo())
    assert contador.chamadas == 1
    assert "mitocôndria" in contador.mensagens[0]
