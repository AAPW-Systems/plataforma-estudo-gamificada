"""Regras puras do domínio `identidade` (T029; RF-001, RF-002, RF-009, D-001).

Sem banco e sem HTTP. Os limites das fronteiras vêm da spec: nome de 1 a 100 caracteres,
senha de 8 a 128, e-mail de até 254.
"""

from __future__ import annotations

import unicodedata

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.identidade import dominio, preferencias
from app.identidade.excecoes import ValorInvalido
from app.nucleo.erros import EntradaInvalida

pytestmark = pytest.mark.unit

COMUNS = frozenset({"password1", "12345678", "qwertyuiop", "#1baby"})
SENHA_BOA = "uma frase longa e incomum"


# --- Nome (RF-001) -----------------------------------------------------------------------


def test_nome_normaliza_nfc_e_remove_espacos_das_extremidades() -> None:
    decomposto = "  José Maria  "  # "e" + acento combinante
    assert dominio.validar_nome(decomposto) == "José Maria"


@pytest.mark.parametrize("nome", ["", "   ", "\t\n ", "  "])
def test_nome_vazio_ou_so_com_espacos_e_recusado(nome: str) -> None:
    with pytest.raises(ValorInvalido):
        dominio.validar_nome(nome)


def test_nome_aceita_100_e_recusa_101_caracteres() -> None:
    assert dominio.validar_nome("a" * 100) == "a" * 100
    with pytest.raises(ValorInvalido):
        dominio.validar_nome("a" * 101)


def test_nome_conta_caracteres_e_nao_bytes() -> None:
    assert dominio.validar_nome("ã" * 100) == "ã" * 100


def test_nome_apos_normalizar_pode_caber_em_100() -> None:
    # 100 letras + espaços nas pontas: o limite vale depois da normalização.
    assert dominio.validar_nome("  " + "b" * 100 + "  ") == "b" * 100


@pytest.mark.parametrize(
    "nome",
    [
        "Ana\x00",
        "Ana\nSilva",
        "Ana\tSilva",
        "Ana\x1b[31m",
        "Ana\x7f",
        "Ana‮evil",  # sobreposição de direção (RTL)
        "Ana⁦x",  # isolamento bidirecional
    ],
)
def test_nome_com_caracteres_de_controle_ou_direcao_e_recusado(nome: str) -> None:
    with pytest.raises(ValorInvalido):
        dominio.validar_nome(nome)


@pytest.mark.parametrize("nome", ["Zoë", "李雷", "Åsa 🙂", "O'Connor-Silva", "ا"])
def test_nome_aceita_letras_de_varios_alfabetos(nome: str) -> None:
    assert dominio.validar_nome(nome) == unicodedata.normalize("NFC", nome)


@given(st.text(max_size=300))
def test_nome_validado_respeita_o_contrato_para_qualquer_texto(texto: str) -> None:
    try:
        nome = dominio.validar_nome(texto)
    except ValorInvalido:
        return
    assert 1 <= len(nome) <= preferencias.NOME_MAXIMO
    assert nome == nome.strip()
    assert unicodedata.is_normalized("NFC", nome)
    assert all(unicodedata.category(c) != "Cc" for c in nome)
    assert dominio.validar_nome(nome) == nome  # idempotente


@given(st.text(max_size=200))
def test_normalizar_nome_e_idempotente(texto: str) -> None:
    uma_vez = dominio.normalizar_nome(texto)
    assert dominio.normalizar_nome(uma_vez) == uma_vez


# --- E-mail (RF-001, RF-012) -------------------------------------------------------------


def test_email_vai_para_minusculas_sem_espacos() -> None:
    assert dominio.validar_email("  Ana.Teste@Exemplo.COM ") == "ana.teste@exemplo.com"


def test_emails_com_caixa_diferente_viram_o_mesmo() -> None:
    assert dominio.validar_email("ANA@exemplo.com") == dominio.validar_email("ana@EXEMPLO.com")


@pytest.mark.parametrize(
    "email",
    [
        "",
        "   ",
        "sem-arroba",
        "@exemplo.com",
        "ana@",
        "ana@@exemplo.com",
        "ana @exemplo.com",
        "ana@exemplo .com",
        "ana\x00@exemplo.com",
        "ana@exemplo.com\r\nBcc: x@exemplo.com",
        "<script>@exemplo.com",
    ],
)
def test_email_invalido_e_recusado(email: str) -> None:
    with pytest.raises(ValorInvalido):
        dominio.validar_email(email)


def test_email_aceita_ate_254_caracteres_e_recusa_acima() -> None:
    sufixo = "@" + "d" * 63 + "." + "d" * 63 + "." + "d" * 57 + ".com"
    no_limite = "a" * (254 - len(sufixo)) + sufixo
    assert len(no_limite) == 254
    assert dominio.validar_email(no_limite) == no_limite
    with pytest.raises(ValorInvalido):
        dominio.validar_email("a" + no_limite)
    with pytest.raises(ValorInvalido):  # parte local acima de 64 caracteres
        dominio.validar_email("a" * 65 + "@exemplo.com")


@given(st.text(max_size=300))
def test_email_validado_e_estavel_para_qualquer_texto(texto: str) -> None:
    try:
        email = dominio.validar_email(texto)
    except ValorInvalido:
        return
    assert len(email) <= preferencias.EMAIL_MAXIMO
    assert email == email.lower()
    assert email == email.strip()
    assert dominio.validar_email(email) == email  # idempotente


# --- Senha (RF-002, D-002) ---------------------------------------------------------------


def test_senha_aceita_8_e_128_caracteres() -> None:
    assert dominio.validar_senha("abcdefg1" * 1, COMUNS) == "abcdefg1"
    assert dominio.validar_senha("é" * 128, COMUNS) == "é" * 128


@pytest.mark.parametrize("tamanho", [0, 1, 7])
def test_senha_curta_e_recusada_com_explicacao(tamanho: int) -> None:
    with pytest.raises(ValorInvalido) as erro:
        dominio.validar_senha("x" * tamanho, COMUNS)
    assert "8" in erro.value.mensagem


def test_senha_acima_de_128_e_recusada() -> None:
    with pytest.raises(ValorInvalido) as erro:
        dominio.validar_senha("x" * 129, COMUNS)
    assert "128" in erro.value.mensagem


@pytest.mark.parametrize("senha", [" " * 8, " " * 20, "\t" * 10, " " * 9])
def test_senha_so_com_espacos_e_recusada(senha: str) -> None:
    with pytest.raises(ValorInvalido):
        dominio.validar_senha(senha, COMUNS)


@pytest.mark.parametrize("senha", ["password1", "PASSWORD1", "PassWord1", "12345678", "QWERTYUIOP"])
def test_senha_da_lista_comum_e_recusada_em_qualquer_caixa(senha: str) -> None:
    with pytest.raises(ValorInvalido) as erro:
        dominio.validar_senha(senha, COMUNS)
    assert erro.value.mensagem == "Esta senha é muito comum. Escolha outra."


def test_senha_nao_e_normalizada_nem_tem_regra_de_composicao() -> None:
    senha = "  espaços nas pontas valem  "
    assert dominio.validar_senha(senha, COMUNS) == senha
    assert dominio.validar_senha("apenasletrasminusculas", COMUNS)


def test_senha_com_espacos_nas_pontas_nao_vira_senha_comum() -> None:
    assert dominio.validar_senha(" password1 ", COMUNS) == " password1 "


# --- Lista de senhas comuns (DTEC 022) -------------------------------------------------


def test_lista_empacotada_tem_ncsc_e_lista_em_portugues() -> None:
    comuns = dominio.carregar_senhas_comuns()
    assert len(comuns) > 90_000
    assert {"12345678", "qwertyuiop", "flamengo", "senha123"} <= comuns
    assert "#1baby" in comuns, "linhas iniciadas por # são senhas, não comentários"
    assert all(item == item.casefold() for item in comuns)
    assert not any(item.startswith("# Lista local") for item in comuns)


def test_lista_ausente_impede_o_carregamento(tmp_path: pytest.TempPathFactory) -> None:
    with pytest.raises(FileNotFoundError):
        dominio.carregar_senhas_comuns(tmp_path / "nao-existe.txt")  # type: ignore[operator]


def test_lista_vazia_impede_o_carregamento(tmp_path: pytest.TempPathFactory) -> None:
    arquivo = tmp_path / "vazia.txt"  # type: ignore[operator]
    arquivo.write_text("# só cabeçalho\n\n", encoding="utf-8")
    with pytest.raises(ValueError, match="vazia"):
        dominio.carregar_senhas_comuns(arquivo)


def test_cabecalho_termina_na_primeira_linha_em_branco(tmp_path: pytest.TempPathFactory) -> None:
    arquivo = tmp_path / "lista.txt"  # type: ignore[operator]
    arquivo.write_text("# cabeçalho\n# mais\n\nABC12345\n#1baby\n\nfim\n", encoding="utf-8")
    assert dominio.carregar_senhas_comuns(arquivo) == {"abc12345", "#1baby", "fim"}


# --- Fuso (RF-009) -----------------------------------------------------------------------


@pytest.mark.parametrize("fuso", ["America/Recife", "America/Sao_Paulo", "UTC", "Asia/Tokyo"])
def test_fuso_iana_valido_e_aceito(fuso: str) -> None:
    assert dominio.validar_fuso(fuso) == fuso


@pytest.mark.parametrize(
    "fuso",
    [
        "",
        "Marte/Phobos",
        "../../etc/passwd",
        "/etc/passwd",
        "America/Sao_Paulo ",
        " America/Sao_Paulo",
        "america/sao_paulo",
        "America/Sao_Paulo\x00",
        "A" * 65,
        "America//Recife",
    ],
)
def test_fuso_invalido_e_recusado(fuso: str) -> None:
    with pytest.raises(ValorInvalido):
        dominio.validar_fuso(fuso)


def test_america_sao_paulo_existe_na_base_de_fusos() -> None:
    assert dominio.validar_fuso(preferencias.FUSO_PADRAO) == "America/Sao_Paulo"


@pytest.mark.parametrize("fuso", [None, "", "Marte/Phobos", "../../etc/passwd", "x" * 500])
def test_cadastro_com_fuso_ausente_ou_invalido_usa_o_padrao(fuso: str | None) -> None:
    assert dominio.fuso_do_cadastro(fuso) == "America/Sao_Paulo"


def test_cadastro_com_fuso_valido_usa_o_detectado() -> None:
    assert dominio.fuso_do_cadastro("America/Recife") == "America/Recife"


# --- Cadastro completo -------------------------------------------------------------------


def test_validar_cadastro_devolve_valores_normalizados() -> None:
    validado = dominio.validar_cadastro(
        nome="  Ana  ",
        email=" ANA@Exemplo.com ",
        senha=SENHA_BOA,
        fuso="America/Recife",
        senhas_comuns=COMUNS,
    )
    assert (validado.nome, validado.email, validado.senha, validado.fuso) == (
        "Ana",
        "ana@exemplo.com",
        SENHA_BOA,
        "America/Recife",
    )


def test_validar_cadastro_lista_todos_os_campos_invalidos_em_camel_case() -> None:
    with pytest.raises(EntradaInvalida) as erro:
        dominio.validar_cadastro(
            nome="   ",
            email="sem-arroba",
            senha="12345678",
            fuso=None,
            senhas_comuns=COMUNS,
        )
    campos = {c.campo: c.mensagem for c in erro.value.campos}
    assert set(campos) == {"nome", "email", "senha"}
    assert campos["senha"] == "Esta senha é muito comum. Escolha outra."
    assert erro.value.status == 422


def test_validar_cadastro_nao_inclui_a_senha_nas_mensagens() -> None:
    senha = "segredo-muito-especial-123"
    with pytest.raises(EntradaInvalida) as erro:
        dominio.validar_cadastro(
            nome="", email="x@exemplo.com", senha=senha, fuso=None, senhas_comuns=COMUNS
        )
    assert senha not in str(erro.value)
    assert all(senha not in c.mensagem for c in erro.value.campos)


# --- Preferências padrão (D-001) --------------------------------------------------------


def test_padroes_e_limites_de_d001() -> None:
    assert (preferencias.META_DIARIA.padrao, preferencias.META_DIARIA.minimo) == (20, 1)
    assert preferencias.META_DIARIA.maximo == 200
    assert (preferencias.TAMANHO_LICAO.padrao, preferencias.TAMANHO_LICAO.minimo) == (10, 5)
    assert preferencias.TAMANHO_LICAO.maximo == 50
    assert (preferencias.LIMITE_NOVOS_DIA.padrao, preferencias.LIMITE_NOVOS_DIA.minimo) == (20, 0)
    assert preferencias.LIMITE_NOVOS_DIA.maximo == 100
    assert str(preferencias.RETENCAO_DESEJADA.padrao) == "0.90"
    assert str(preferencias.RETENCAO_DESEJADA.minimo) == "0.70"
    assert str(preferencias.RETENCAO_DESEJADA.maximo) == "0.97"
    assert preferencias.FUSO_PADRAO == "America/Sao_Paulo"
