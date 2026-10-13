"""Regras puras da identidade: normalização e validação de nome, e-mail, senha e fuso.

Sem banco e sem HTTP (DTEC 018). Os limites vêm de `preferencias`. A senha nunca é
normalizada (`padroes-implementacao.md`): só se confere o tamanho, o conteúdo e a lista
de senhas comuns (DTEC 022).
"""

from __future__ import annotations

import unicodedata
import zoneinfo
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from email_validator import EmailNotValidError, validate_email

from app.identidade import preferencias
from app.identidade.excecoes import ValorInvalido
from app.nucleo.erros import EntradaInvalida, ErroCampo

ARQUIVO_SENHAS_COMUNS = Path(__file__).parent / "dados" / "senhas_comuns.txt"

# Controles de direção (U+202A a U+202E e U+2066 a U+2069) permitem falsificar a aparência
# de um nome na tela. As marcas LRM e RLM (U+200E e U+200F) seguem aceitas: escrevem nomes
# em alfabetos da direita para a esquerda.
_CONTROLES_DE_DIRECAO = frozenset(chr(c) for c in (*range(0x202A, 0x202F), *range(0x2066, 0x206A)))
# Controle, substituto isolado (não codifica em UTF-8) e uso privado.
_CATEGORIAS_PROIBIDAS = frozenset({"Cc", "Cs", "Co"})


def _nfc(valor: str) -> str:
    return unicodedata.normalize("NFC", valor)


# --- Nome --------------------------------------------------------------------------------


def normalizar_nome(valor: str) -> str:
    return _nfc(valor).strip()


def validar_nome(valor: str) -> str:
    nome = normalizar_nome(valor)
    if len(nome) < preferencias.NOME_MINIMO:
        raise ValorInvalido("Informe o nome.")
    if len(nome) > preferencias.NOME_MAXIMO:
        raise ValorInvalido(f"Use no máximo {preferencias.NOME_MAXIMO} caracteres.")
    if any(
        unicodedata.category(c) in _CATEGORIAS_PROIBIDAS or c in _CONTROLES_DE_DIRECAO for c in nome
    ):
        raise ValorInvalido("O nome tem caracteres que não podem ser usados.")
    return nome


# --- E-mail ------------------------------------------------------------------------------


def validar_email(valor: str) -> str:
    """E-mail em NFC, sem espaços nas pontas e em minúsculas (RF-001)."""
    texto = _nfc(valor).strip()
    if not texto:
        raise ValorInvalido("Informe o e-mail.")
    if len(texto) > preferencias.EMAIL_MAXIMO:
        raise ValorInvalido("Informe um e-mail válido.")
    try:
        verificado = validate_email(texto, check_deliverability=False)
    except EmailNotValidError:
        raise ValorInvalido("Informe um e-mail válido.") from None
    email = verificado.normalized.lower()
    # RFC 5321: a parte local tem até 64 octetos; a biblioteca não impõe esse limite.
    if len(email) > preferencias.EMAIL_MAXIMO or len(verificado.local_part.encode()) > 64:
        raise ValorInvalido("Informe um e-mail válido.")
    return email


def normalizar_email_de_entrada(valor: str) -> str:
    """Forma comparável do e-mail digitado na entrada, válido ou não.

    Um e-mail malformado não tem conta, mas a entrada precisa tratá-lo como qualquer outro
    (mesmo custo, mesma resposta e mesma chave de limite): por isso não lança erro.
    """
    try:
        return validar_email(valor)
    except ValorInvalido:
        return _nfc(valor).strip().lower()


# --- Senha -------------------------------------------------------------------------------


def senha_codificavel(senha: str) -> bool:
    """Falso para texto com substituto isolado, que não vira UTF-8 (nem hash)."""
    try:
        senha.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def validar_senha(senha: str, senhas_comuns: frozenset[str]) -> str:
    """Valida sem alterar a senha (RF-002): 8 a 128 caracteres, sem regras de composição."""
    if len(senha) < preferencias.SENHA_MINIMA:
        raise ValorInvalido(f"Use pelo menos {preferencias.SENHA_MINIMA} caracteres.")
    if len(senha) > preferencias.SENHA_MAXIMA:
        raise ValorInvalido(f"Use no máximo {preferencias.SENHA_MAXIMA} caracteres.")
    if not senha.strip():
        raise ValorInvalido("A senha não pode ter só espaços.")
    if not senha_codificavel(senha):
        raise ValorInvalido("A senha tem caracteres que não podem ser usados.")
    if senha.casefold() in senhas_comuns:
        raise ValorInvalido("Esta senha é muito comum. Escolha outra.")
    return senha


def carregar_senhas_comuns(caminho: Path | None = None) -> frozenset[str]:
    """Lê a lista local (DTEC 022). Sem arquivo ou sem senhas, levanta erro: a app não sobe.

    O cabeçalho vai até a primeira linha em branco; depois dela toda linha é uma senha,
    inclusive as que começam com `#`. A comparação ignora a caixa.
    """
    if caminho is None:
        return _senhas_comuns_empacotadas()
    return _ler_senhas_comuns(caminho)


@lru_cache(maxsize=1)
def _senhas_comuns_empacotadas() -> frozenset[str]:
    return _ler_senhas_comuns(ARQUIVO_SENHAS_COMUNS)


def _ler_senhas_comuns(caminho: Path) -> frozenset[str]:
    linhas = caminho.read_text(encoding="utf-8").split("\n")
    inicio = linhas.index("") + 1 if "" in linhas else 0
    senhas = frozenset(
        linha.casefold() for linha in (item.rstrip("\r") for item in linhas[inicio:]) if linha
    )
    if not senhas:
        raise ValueError(f"a lista de senhas comuns está vazia: {caminho}")
    return senhas


# --- Fuso --------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _fusos_validos() -> frozenset[str]:
    return frozenset(zoneinfo.available_timezones())


def validar_fuso(valor: str) -> str:
    """Nome IANA existente na base `tzdata`; qualquer outro texto é recusado (RF-009)."""
    if len(valor) > preferencias.FUSO_MAXIMO or valor not in _fusos_validos():
        raise ValorInvalido("Fuso desconhecido.")
    return valor


def fuso_do_cadastro(valor: str | None) -> str:
    """Fuso detectado no navegador; ausente ou inválido vira o padrão, sem recusar (RF-009)."""
    if valor is not None:
        try:
            return validar_fuso(valor)
        except ValorInvalido:
            pass
    return preferencias.FUSO_PADRAO


# --- Cadastro ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CadastroValidado:
    nome: str
    email: str
    senha: str = ""
    fuso: str = preferencias.FUSO_PADRAO

    def __repr__(self) -> str:
        return f"CadastroValidado(nome={self.nome!r}, email=<oculto>, senha=<oculta>)"


def validar_cadastro(
    *,
    nome: str,
    email: str,
    senha: str,
    fuso: str | None,
    senhas_comuns: frozenset[str],
) -> CadastroValidado:
    """Valida os três campos e informa todos os inválidos de uma vez (cenário 2 da US1)."""
    erros: list[ErroCampo] = []
    valores: dict[str, str] = {}
    verificacoes: list[tuple[str, Callable[[], str]]] = [
        ("nome", lambda: validar_nome(nome)),
        ("email", lambda: validar_email(email)),
        ("senha", lambda: validar_senha(senha, senhas_comuns)),
    ]
    for campo, validar in verificacoes:
        try:
            valores[campo] = validar()
        except ValorInvalido as erro:
            erros.append(ErroCampo(campo, erro.mensagem))
    if erros:
        raise EntradaInvalida(campos=erros)
    return CadastroValidado(
        nome=valores["nome"],
        email=valores["email"],
        senha=valores["senha"],
        fuso=fuso_do_cadastro(fuso),
    )
