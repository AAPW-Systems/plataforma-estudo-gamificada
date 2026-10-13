"""Configuração validada ao iniciar (plano da 001, "Variáveis de ambiente"; casos de falha)."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from app.nucleo.configuracao import Configuracao

pytestmark = pytest.mark.unit

SEGREDO_VALIDO = "s" * 32


def _criar(**valores: Any) -> Configuracao:
    base: dict[str, Any] = {
        "postgres_user": "u",
        "postgres_password": "p",
        "postgres_db": "d",
        "segredo_aplicacao": SEGREDO_VALIDO,
        "origens_permitidas": "http://localhost:5173",
    }
    base.update(valores)
    return Configuracao(**base)


def test_configuracao_valida_tem_os_padroes_do_plano() -> None:
    config = _criar()
    assert config.sessao_dias_inatividade == 14
    assert config.sessao_dias_maximo == 30
    assert (config.limite_falhas_conta, config.limite_falhas_ip) == (5, 20)
    assert (config.janela_tentativas_min, config.bloqueio_min) == (15, 15)
    assert config.limite_cadastros_ip_hora == 10
    assert config.argon2_concorrencia == 4
    assert config.cookie_sessao_nome == "__Host-sessao"


def test_nao_sobe_sem_segredo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SEGREDO_APLICACAO", raising=False)
    with pytest.raises(ValidationError, match="segredo_aplicacao"):
        Configuracao(
            postgres_user="u",
            postgres_password="p",  # type: ignore[arg-type]
            postgres_db="d",
            origens_permitidas=["http://localhost:5173"],
        )


@pytest.mark.parametrize("segredo", ["", "curto", "x" * 31])
def test_nao_sobe_com_segredo_curto(segredo: str) -> None:
    with pytest.raises(ValidationError, match="32 bytes"):
        _criar(segredo_aplicacao=segredo)


def test_segredo_conta_bytes_e_nao_caracteres() -> None:
    # 16 caracteres de 2 bytes em UTF-8 somam 32 bytes.
    assert _criar(segredo_aplicacao="ç" * 16).segredo == ("ç" * 16).encode()


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("limite_falhas_conta", 0),
        ("limite_falhas_ip", -1),
        ("janela_tentativas_min", 0),
        ("bloqueio_min", "abc"),
        ("limite_cadastros_ip_hora", 0),
        ("argon2_concorrencia", 0),
        ("sessao_dias_maximo", 0),
        ("postgres_port", 70000),
    ],
)
def test_nao_sobe_com_limite_invalido(campo: str, valor: object) -> None:
    with pytest.raises(ValidationError, match=campo):
        _criar(**{campo: valor})


def test_inatividade_nao_passa_da_duracao_maxima() -> None:
    with pytest.raises(ValidationError, match="SESSAO_DIAS_INATIVIDADE"):
        _criar(sessao_dias_inatividade=31, sessao_dias_maximo=30)


def test_listas_separadas_por_virgula_vindas_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORIGENS_PERMITIDAS", "http://localhost:5173, https://exemplo.com")
    monkeypatch.setenv("PROXIES_CONFIAVEIS", "172.28.0.10,10.0.0.0/8")
    config = Configuracao(
        postgres_user="u",
        postgres_password="p",  # type: ignore[arg-type]
        postgres_db="d",
        segredo_aplicacao=SEGREDO_VALIDO,  # type: ignore[arg-type]
    )
    assert config.origens_permitidas == ["http://localhost:5173", "https://exemplo.com"]
    assert [str(rede) for rede in config.proxies_confiaveis] == ["172.28.0.10/32", "10.0.0.0/8"]


@pytest.mark.parametrize("origem", ["localhost:5173", "http://localhost:5173/", "ftp://x"])
def test_origem_mal_formada_e_recusada(origem: str) -> None:
    with pytest.raises(ValidationError, match="origem inválida"):
        _criar(origens_permitidas=origem)


def test_proxy_invalido_e_recusado() -> None:
    with pytest.raises(ValidationError):
        _criar(proxies_confiaveis="nao-e-ip")


def test_producao_exige_prefixo_host_nos_cookies() -> None:
    with pytest.raises(ValidationError, match="__Host-"):
        _criar(app_ambiente="producao", cookie_sessao_nome="sessao")


def test_segredo_nao_aparece_na_representacao() -> None:
    config = _criar(segredo_aplicacao="segredo-muito-secreto-de-teste-1234567")
    assert "segredo-muito-secreto" not in repr(config)
    assert "segredo-muito-secreto" not in str(config.model_dump())


def test_conninfo_escapa_a_senha() -> None:
    config = _criar(postgres_password="a b'c")
    assert r"password='a b\'c'" in config.conninfo()
    assert "dbname=outro" in config.conninfo("outro")
