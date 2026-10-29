"""T003 (spec 004): configuração do domínio `ia` validada ao iniciar (DTEC 039 e 040)."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from app.ia.configuracao import AVISOS, PROVEDORES, ConfiguracaoIa, Provedor

pytestmark = pytest.mark.unit


def _criar(**valores: Any) -> ConfiguracaoIa:
    base: dict[str, Any] = {"app_ambiente": "desenvolvimento", "ia_provedor": "teste"}
    base.update(valores)
    return ConfiguracaoIa(**base)


def test_sobe_com_os_padroes_do_plano(monkeypatch: pytest.MonkeyPatch) -> None:
    for variavel in ("IA_PROVEDOR", "IA_TIMEOUT_SEGUNDOS", "IA_ORCAMENTO_TOKENS_DIA"):
        monkeypatch.delenv(variavel, raising=False)
    config = ConfiguracaoIa(app_ambiente="desenvolvimento")
    assert config.ia_provedor == "teste"
    assert config.ia_timeout_segundos == 60
    assert config.ia_orcamento_tokens_dia == 300_000
    assert config.modelo_geracao and config.modelo_verificador


def test_nao_sobe_com_provedor_de_teste_em_producao() -> None:
    """Plano da 004: `IA_PROVEDOR=teste` fora dos testes e do desenvolvimento não sobe."""
    with pytest.raises(ValidationError, match="IA_PROVEDOR=teste"):
        _criar(app_ambiente="producao", ia_provedor="teste")


@pytest.mark.parametrize("ambiente", ["desenvolvimento", "teste"])
def test_provedor_de_teste_sobe_fora_de_producao(ambiente: str) -> None:
    assert _criar(app_ambiente=ambiente).ia_provedor == "teste"


@pytest.mark.parametrize("provedor,chave", [("gemini", "GEMINI_API_KEY"), ("groq", "GROQ_API_KEY")])
def test_nao_sobe_com_provedor_real_sem_a_chave(
    monkeypatch: pytest.MonkeyPatch, provedor: str, chave: str
) -> None:
    """Plano da 004, casos de falha: provedor real sem a chave falha com mensagem clara."""
    monkeypatch.delenv(chave, raising=False)
    with pytest.raises(ValidationError, match=chave):
        _criar(ia_provedor=provedor)
    with pytest.raises(ValidationError, match=chave):
        _criar(ia_provedor=provedor, **{chave.lower(): "   "})


@pytest.mark.parametrize("provedor,chave", [("gemini", "gemini_api_key"), ("groq", "groq_api_key")])
def test_provedor_real_com_a_chave_sobe_e_a_esconde(provedor: str, chave: str) -> None:
    config = _criar(app_ambiente="producao", ia_provedor=provedor, **{chave: "chave-ficticia"})
    assert config.ia_provedor == provedor
    assert "chave-ficticia" not in repr(config)
    assert "chave-ficticia" not in str(config.model_dump())


def test_provedor_desconhecido_nao_sobe() -> None:
    with pytest.raises(ValidationError, match="ia_provedor"):
        _criar(ia_provedor="outro")


@pytest.mark.parametrize("campo", ["ia_timeout_segundos", "ia_orcamento_tokens_dia"])
def test_limites_operacionais_positivos(campo: str) -> None:
    with pytest.raises(ValidationError, match=campo):
        _criar(**{campo: 0})


def test_modelos_vem_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IA_MODELO_GERACAO", "modelo-a")
    monkeypatch.setenv("IA_MODELO_VERIFICADOR", "modelo-b")
    config = _criar()
    assert (config.modelo_geracao, config.modelo_verificador) == ("modelo-a", "modelo-b")


@pytest.mark.parametrize("provedor", PROVEDORES)
def test_todo_provedor_tem_versao_e_texto_do_aviso(provedor: Provedor) -> None:
    """DTEC 039: cada provedor configurável tem versão e parágrafos do aviso."""
    aviso = AVISOS[provedor]
    assert aviso.versao.startswith(f"{provedor}-v")
    assert 1 <= len(aviso.versao) <= 50
    assert aviso.paragrafos and all(p.strip() for p in aviso.paragrafos)


@pytest.mark.parametrize("provedor", ["gemini", "groq"])
def test_aviso_do_provedor_real_diz_o_que_a_dtec_039_exige(provedor: Provedor) -> None:
    texto = " ".join(AVISOS[provedor].paragrafos)
    nome = {"gemini": "Gemini", "groq": "Groq"}[provedor]
    assert nome in texto
    assert "trechos" in texto
    assert "dados pessoais" in texto
    assert "confidenciais" in texto


def test_aviso_vigente_e_o_do_provedor_configurado() -> None:
    config = _criar(app_ambiente="producao", ia_provedor="groq", groq_api_key="chave-ficticia")
    assert config.aviso is AVISOS["groq"]


def test_a_api_nao_sobe_com_provedor_real_sem_chave(monkeypatch: pytest.MonkeyPatch) -> None:
    """Plano da 004: a configuração da IA é validada ao criar a aplicação, não na 1ª geração."""
    from app.ia.configuracao import obter_configuracao_ia
    from app.nucleo.configuracao import Configuracao
    from app.principal import criar_aplicacao
    from tests.conftest import SEGREDO_TESTE

    configuracao = Configuracao(
        postgres_user="u",
        postgres_password="p",  # type: ignore[arg-type]
        postgres_db="d",
        segredo_aplicacao=SEGREDO_TESTE,  # type: ignore[arg-type]
        origens_permitidas=["http://localhost:5173"],
    )
    monkeypatch.setenv("IA_PROVEDOR", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    obter_configuracao_ia.cache_clear()
    try:
        with pytest.raises(ValidationError, match="GEMINI_API_KEY"):
            criar_aplicacao(configuracao)
    finally:
        obter_configuracao_ia.cache_clear()


def test_os_testes_rodam_com_o_provedor_simulado_e_sem_rede() -> None:
    """T003: a suíte nunca chama o provedor real (DTEC 047)."""
    from pydantic_ai import models

    from app.ia.configuracao import obter_configuracao_ia

    assert models.ALLOW_MODEL_REQUESTS is False
    assert obter_configuracao_ia().ia_provedor == "teste"


async def test_o_worker_nao_sobe_com_provedor_de_teste_em_producao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app import worker
    from app.ia.configuracao import obter_configuracao_ia

    monkeypatch.setenv("APP_AMBIENTE", "producao")
    monkeypatch.setenv("IA_PROVEDOR", "teste")
    obter_configuracao_ia.cache_clear()
    try:
        with pytest.raises(ValidationError, match="IA_PROVEDOR=teste"):
            worker.validar_configuracao()
    finally:
        obter_configuracao_ia.cache_clear()
