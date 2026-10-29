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


# --- Acervo (plano da 002, "Variáveis de ambiente"; RQ-005) -------------------------------------


def test_acervo_tem_os_padroes_do_plano() -> None:
    config = _criar()
    assert config.fonte_tamanho_max_bytes == 2_097_152
    assert config.pdf_max_paginas == 500
    assert (config.cota_materias, config.cota_fontes_por_materia) == (50, 30)
    assert config.cota_armazenamento_bytes == 104_857_600
    assert (config.trecho_tamanho_alvo, config.trecho_tamanho_maximo) == (1200, 2000)
    assert config.trecho_sobreposicao == 150
    assert (config.validacao_arquivo_tempo_s, config.validacao_arquivo_memoria_mb) == (10, 256)
    assert config.validacao_arquivo_concorrencia == 2
    assert (config.extracao_tempo_s, config.extracao_memoria_mb) == (30, 512)
    assert config.reconciliacao_margem_min == 60
    assert config.fila_segundos_travado == 60


@pytest.mark.parametrize(
    "campo",
    [
        "fonte_tamanho_max_bytes",
        "pdf_max_paginas",
        "cota_materias",
        "cota_fontes_por_materia",
        "cota_armazenamento_bytes",
        "trecho_tamanho_alvo",
        "trecho_tamanho_maximo",
        "validacao_arquivo_tempo_s",
        "validacao_arquivo_memoria_mb",
        "validacao_arquivo_concorrencia",
        "extracao_tempo_s",
        "extracao_memoria_mb",
        "reconciliacao_margem_min",
        "fila_segundos_travado",
    ],
)
@pytest.mark.parametrize("valor", [0, -1])
def test_nao_sobe_com_cota_ou_limite_menor_que_1(campo: str, valor: int) -> None:
    with pytest.raises(ValidationError, match=campo):
        _criar(**{campo: valor})


def test_sobreposicao_pode_ser_zero_mas_nao_negativa() -> None:
    assert _criar(trecho_sobreposicao=0).trecho_sobreposicao == 0
    with pytest.raises(ValidationError, match="trecho_sobreposicao"):
        _criar(trecho_sobreposicao=-1)


@pytest.mark.parametrize("sobreposicao", [1200, 1201])
def test_nao_sobe_com_sobreposicao_igual_ou_maior_que_o_alvo(sobreposicao: int) -> None:
    with pytest.raises(ValidationError, match="TRECHO_SOBREPOSICAO"):
        _criar(trecho_sobreposicao=sobreposicao)


def test_nao_sobe_com_alvo_maior_que_o_maximo() -> None:
    with pytest.raises(ValidationError, match="TRECHO_TAMANHO_ALVO"):
        _criar(trecho_tamanho_alvo=2001, trecho_tamanho_maximo=2000)


def test_alvo_igual_ao_maximo_e_aceito() -> None:
    assert _criar(trecho_tamanho_alvo=2000).trecho_tamanho_alvo == 2000


def test_armazenamento_nao_e_menor_que_um_arquivo() -> None:
    with pytest.raises(ValidationError, match="COTA_ARMAZENAMENTO_BYTES"):
        _criar(cota_armazenamento_bytes=1000, fonte_tamanho_max_bytes=2000)


# --- Cartões (plano da 003, "Variáveis de ambiente"; D-004, DTEC 036) ---------------------------


def test_cartoes_tem_os_padroes_do_plano() -> None:
    config = _criar()
    assert config.cartao_frente_max == 1000
    assert config.cartao_verso_max == 2000
    assert config.cartao_explicacao_max == 1000


@pytest.mark.parametrize(
    ("campo", "teto"),
    [
        ("cartao_frente_max", 4000),
        ("cartao_verso_max", 8000),
        ("cartao_explicacao_max", 4000),
    ],
)
def test_limite_de_cartao_aceita_de_1_ate_o_teto(campo: str, teto: int) -> None:
    assert getattr(_criar(**{campo: 1}), campo) == 1
    assert getattr(_criar(**{campo: teto}), campo) == teto


@pytest.mark.parametrize(
    ("campo", "invalido"),
    [
        ("cartao_frente_max", 0),
        ("cartao_frente_max", -1),
        ("cartao_frente_max", 4001),
        ("cartao_verso_max", 0),
        ("cartao_verso_max", -1),
        ("cartao_verso_max", 8001),
        ("cartao_explicacao_max", 0),
        ("cartao_explicacao_max", -1),
        ("cartao_explicacao_max", 4001),
    ],
)
def test_nao_sobe_com_limite_de_cartao_fora_de_1_ate_o_teto(campo: str, invalido: int) -> None:
    with pytest.raises(ValidationError, match=campo):
        _criar(**{campo: invalido})


def test_limite_de_cartao_vem_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CARTAO_FRENTE_MAX", "500")
    monkeypatch.setenv("CARTAO_VERSO_MAX", "900")
    monkeypatch.setenv("CARTAO_EXPLICACAO_MAX", "300")
    config = Configuracao(
        postgres_user="u",
        postgres_password="p",  # type: ignore[arg-type]
        postgres_db="d",
        segredo_aplicacao=SEGREDO_VALIDO,  # type: ignore[arg-type]
        origens_permitidas=["http://localhost:5173"],
    )
    assert (config.cartao_frente_max, config.cartao_verso_max) == (500, 900)
    assert config.cartao_explicacao_max == 300


def test_geracao_tem_os_padroes_do_plano() -> None:
    """T003 (004): padrões da tabela de variáveis do plano."""
    config = _criar()
    assert config.geracao_limite_dia == 20
    assert config.geracao_cartoes_max == 10
    assert config.geracao_janela_max_caracteres == 30_000
    assert config.geracao_limiar_cobertura == 0.6
    assert config.geracao_limiar_repeticao == 0.7
    assert config.geracao_verificador_ia is True


@pytest.mark.parametrize("campo", ["geracao_limiar_cobertura", "geracao_limiar_repeticao"])
@pytest.mark.parametrize("invalido", [0, -0.1, 1.0001, 2])
def test_nao_sobe_com_limiar_fora_de_0_a_1(campo: str, invalido: float) -> None:
    """T003 (004, DTEC 041 e 042): limiar em (0, 1]."""
    with pytest.raises(ValidationError, match=campo):
        _criar(**{campo: invalido})


@pytest.mark.parametrize("campo", ["geracao_limiar_cobertura", "geracao_limiar_repeticao"])
def test_limiar_aceita_1(campo: str) -> None:
    assert getattr(_criar(**{campo: 1}), campo) == 1


@pytest.mark.parametrize("invalido", [0, 11])
def test_nao_sobe_com_cartoes_max_fora_de_1_a_10(invalido: int) -> None:
    """T003 (004, D-002): no máximo 10 cartões por geração, no mínimo 1."""
    with pytest.raises(ValidationError, match="geracao_cartoes_max"):
        _criar(geracao_cartoes_max=invalido)


@pytest.mark.parametrize("valido", [1, 10])
def test_cartoes_max_aceita_os_extremos(valido: int) -> None:
    assert _criar(geracao_cartoes_max=valido).geracao_cartoes_max == valido


def test_nao_sobe_com_janela_menor_que_um_trecho() -> None:
    """T003 (004, DTEC 041): a janela sempre cabe um trecho inteiro."""
    with pytest.raises(ValidationError, match="GERACAO_JANELA_MAX_CARACTERES"):
        _criar(trecho_tamanho_maximo=2000, geracao_janela_max_caracteres=1999)
    assert _criar(geracao_janela_max_caracteres=2000).geracao_janela_max_caracteres == 2000


def test_nao_sobe_com_limite_de_geracoes_zero() -> None:
    with pytest.raises(ValidationError, match="geracao_limite_dia"):
        _criar(geracao_limite_dia=0)


def test_geracao_vem_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GERACAO_LIMITE_DIA", "3")
    monkeypatch.setenv("GERACAO_VERIFICADOR_IA", "false")
    config = _criar()
    assert config.geracao_limite_dia == 3
    assert config.geracao_verificador_ia is False
