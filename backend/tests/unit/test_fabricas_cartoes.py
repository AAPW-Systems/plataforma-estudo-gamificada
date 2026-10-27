"""T004: a fábrica de cartões respeita os limites e os CHECK do banco, e a CLI se recusa (regra 10).

Os mesmos cartões são inseridos no banco em `tests/integration/cartoes/test_fabrica_insercao.py`,
que prova os CHECK de verdade; aqui as regras são conferidas sem banco.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import pytest

from app.cartoes.modelos import EstadoFsrs, OrigemCartao, SituacaoCartao
from app.nucleo.configuracao import Configuracao
from tests import fabricas_cartoes as fab
from tests.fabricas_cartoes import CartaoFicticio

pytestmark = pytest.mark.unit

LIMITES = {"frente": 1000, "verso": 2000, "explicacao": 1000}


def _sem_acentos(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c)).lower()


@pytest.fixture(scope="module")
def cartoes() -> list[CartaoFicticio]:
    return fab.gerar(120)


def test_gera_a_quantidade_pedida_e_e_deterministica() -> None:
    assert len(fab.gerar(120)) == 120
    assert fab.gerar(37) == fab.gerar(37)
    assert fab.gerar(0) == []
    assert fab.gerar(5) == fab.gerar(120)[:5], "a sequência é um prefixo da maior"


@pytest.mark.parametrize("quantidade", [-1, 5001])
def test_quantidade_fora_da_faixa_e_recusada(quantidade: int) -> None:
    with pytest.raises(ValueError, match="quantidade"):
        fab.gerar(quantidade)


def test_textos_respeitam_os_limites_padrao(cartoes: list[CartaoFicticio]) -> None:
    for c in cartoes:
        assert 1 <= len(c.frente) <= LIMITES["frente"]
        assert 1 <= len(c.verso) <= LIMITES["verso"]
        assert c.explicacao is None or 1 <= len(c.explicacao) <= LIMITES["explicacao"]


def test_textos_ja_vem_normalizados(cartoes: list[CartaoFicticio]) -> None:
    """NFC, sem espaços nas extremidades e sem controles além de `\\n` e `\\t` (DTEC 036)."""
    for c in cartoes:
        for texto in (c.frente, c.verso, c.explicacao or "x"):
            assert unicodedata.normalize("NFC", texto) == texto
            assert texto == texto.strip()
            assert "\r" not in texto
            assert all(unicodedata.category(ch) != "Cc" or ch in "\n\t" for ch in texto), repr(
                texto
            )


def test_a_variedade_pedida_pelo_plano_esta_presente(cartoes: list[CartaoFicticio]) -> None:
    assert {c.origem for c in cartoes} == set(OrigemCartao)
    assert {c.situacao for c in cartoes} == set(SituacaoCartao)
    assert {c.estado_fsrs for c in cartoes} == set(EstadoFsrs)
    suspensos = sum(c.situacao is SituacaoCartao.SUSPENSO for c in cartoes)
    assert 0 < suspensos < len(cartoes) // 2, "uma parte fica suspensa"
    assert any(c.com_referencia for c in cartoes)
    todos = "\n".join(f"{c.frente}\n{c.verso}" for c in cartoes)
    assert "<script>" in todos and "onerror" in todos, "marcação e script (RQ-001)"
    assert "%" in todos and "_" in todos and "\\" in todos, "curingas do LIKE (DTEC 033)"
    assert "\n" in todos, "quebras de linha (RF-011)"
    assert any(ord(ch) > 0xFFFF for ch in todos), "emoji fora do plano básico"
    assert any(ch in "çÇ" for ch in todos) and any(ch in "ãõ" for ch in todos)
    frentes = [_sem_acentos(c.frente + " " + c.verso) for c in cartoes]
    assert sum("celula" in f for f in frentes) >= 10, "a busca por 'celula' tem o que achar"
    palavras = re.findall(r"\w+", "\n".join(f"{c.frente} {c.verso}" for c in cartoes))
    caixas = {w for w in palavras if w.lower() == "célula"}
    assert {"Célula", "CÉLULA", "célula"} <= caixas, "variações de caixa e acento"


def test_referencia_so_em_cartao_criado(cartoes: list[CartaoFicticio]) -> None:
    """CHECK do banco: referência só em `origem = criado` (DTEC 035)."""
    for c in cartoes:
        if c.com_referencia:
            assert c.origem is OrigemCartao.CRIADO


def test_estado_do_fsrs_segue_o_card(cartoes: list[CartaoFicticio]) -> None:
    for c in cartoes:
        if c.estado_fsrs is EstadoFsrs.APRENDIZADO:  # cartão novo: o estado de `fsrs.Card()`
            assert (c.passo, c.estabilidade, c.dificuldade) == (0, None, None)
            assert c.ultima_revisao_em is None
        else:
            assert c.vencimento_em is not None and c.ultima_revisao_em is not None
            assert c.ultima_revisao_em < c.vencimento_em
            assert c.estabilidade is not None and c.estabilidade > 0
            assert c.dificuldade is not None and 1 <= c.dificuldade <= 10
            assert c.passo is None if c.estado_fsrs is EstadoFsrs.REVISAO else c.passo == 0


def test_cartoes_de_cada_estado_do_fsrs_existem_em_ativo_e_suspenso(
    cartoes: list[CartaoFicticio],
) -> None:
    """CS-002 e CS-003 precisam de cartões em todos os estados, ativos e suspensos."""
    combinacoes = {(c.estado_fsrs, c.situacao) for c in cartoes}
    assert {(EstadoFsrs.REVISAO, s) for s in SituacaoCartao} <= combinacoes
    assert (EstadoFsrs.APRENDIZADO, SituacaoCartao.ATIVO) in combinacoes
    assert (EstadoFsrs.REAPRENDIZADO, SituacaoCartao.ATIVO) in combinacoes


@pytest.mark.parametrize("tamanho", [1, 2, 1000, 1001, 4000])
def test_texto_com_tamanho_tem_exatamente_o_numero_de_code_points(tamanho: int) -> None:
    texto = fab.texto_com_tamanho(tamanho)
    assert len(texto) == tamanho
    assert unicodedata.normalize("NFC", texto) == texto and texto == texto.strip()


def test_cartao_no_limite_e_um_acima(cartoes: list[CartaoFicticio]) -> None:
    no_limite = fab.cartao_no_limite(**LIMITES)
    assert (len(no_limite.frente), len(no_limite.verso), len(no_limite.explicacao or "")) == (
        1000,
        2000,
        1000,
    )
    for campo, limite in LIMITES.items():
        acima = fab.cartao_acima_do_limite(campo, **LIMITES)
        assert len(getattr(acima, campo)) == limite + 1


def test_cartao_ficticio_padrao_e_um_cartao_novo_ativo_criado() -> None:
    c = fab.cartao_ficticio()
    assert (c.origem, c.situacao, c.estado_fsrs) == (
        OrigemCartao.CRIADO,
        SituacaoCartao.ATIVO,
        EstadoFsrs.APRENDIZADO,
    )
    assert fab.cartao_ficticio(situacao=SituacaoCartao.SUSPENSO).situacao is SituacaoCartao.SUSPENSO


# --- Linha de comando (regra 10) ----------------------------------------------------------------


def _config(**alteracoes: Any) -> Configuracao:
    base: dict[str, Any] = {
        "postgres_user": "u",
        "postgres_password": "p",
        "postgres_db": "d",
        "postgres_host": "banco.invalido",
        "segredo_aplicacao": "s" * 32,
        "origens_permitidas": "http://localhost:5173",
        "app_ambiente": "desenvolvimento",
    }
    base.update(alteracoes)
    return Configuracao(**base)


@pytest.fixture
def sem_banco(monkeypatch: pytest.MonkeyPatch) -> None:
    """Qualquer tentativa de abrir o banco faz o teste falhar: a recusa vem antes dele."""

    def _proibido(*_: object, **__: object) -> None:
        raise AssertionError("a CLI abriu o banco antes de recusar")

    monkeypatch.setattr(fab, "criar_engine", _proibido)


@pytest.mark.parametrize("ambiente", ["teste", "producao"])
def test_cli_recusa_outro_ambiente(
    ambiente: str, sem_banco: None, capsys: pytest.CaptureFixture[str]
) -> None:
    configuracao = _config(app_ambiente=ambiente)
    codigo = fab.principal(
        ["--email", "ana@exemplo.com", "--materia", "Biologia", "--quantidade", "5"], configuracao
    )
    assert codigo == 2
    assert "APP_AMBIENTE=desenvolvimento" in capsys.readouterr().err


@pytest.mark.parametrize(
    "email",
    [
        "ana@gmail.com",
        "ana@exemplo.com.br",
        "ana@sub.exemplo.com",
        "ana@exemplo.com.evil.com",
        "ana@exemplo.comx",
        "exemplo.com",
        "ana@",
        "@exemplo.com",
        "ana@evil.com@exemplo.com",
        "ana@exemplo.com ",
    ],
)
def test_cli_recusa_conta_fora_do_dominio_exemplo(
    email: str, sem_banco: None, capsys: pytest.CaptureFixture[str]
) -> None:
    codigo = fab.principal(
        ["--email", email, "--materia", "Biologia", "--quantidade", "5"], _config()
    )
    assert codigo == 2
    assert "exemplo.com" in capsys.readouterr().err


@pytest.mark.parametrize("quantidade", ["0", "-3", "5001", "abc"])
def test_cli_recusa_quantidade_invalida(
    quantidade: str, sem_banco: None, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as saida:
        fab.principal(
            ["--email", "ana@exemplo.com", "--materia", "Biologia", "--quantidade", quantidade],
            _config(),
        )
    assert saida.value.code == 2
    assert "quantidade" in capsys.readouterr().err


def test_dominio_aceito_ignora_caixa_mas_nao_aceita_subdominio() -> None:
    assert fab.email_de_exemplo("Ana.Teste@EXEMPLO.com")
    assert not fab.email_de_exemplo("ana@sub.exemplo.com")
    assert not fab.email_de_exemplo("ana@exemplo.com.br")
