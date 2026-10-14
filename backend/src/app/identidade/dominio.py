"""Regras puras da identidade: normalização e validação de nome, e-mail, senha e fuso.

Sem banco e sem HTTP (DTEC 018). Os limites vêm de `preferencias`. A senha nunca é
normalizada (`padroes-implementacao.md`): só se confere o tamanho, o conteúdo e a lista
de senhas comuns (DTEC 022).
"""

from __future__ import annotations

import hashlib
import hmac
import unicodedata
import zoneinfo
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
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


# --- Limites de tentativas (RQ-003, DTEC 020) --------------------------------------------

_PREFIXO_CHAVE_CONTA = b"chave-conta-v1|"


def chave_da_conta(segredo: bytes, email_normalizado: str) -> bytes:
    """HMAC-SHA-256 do e-mail normalizado: vale igual para e-mails com e sem conta (CS-003).

    O e-mail em si nunca é gravado na tabela de tentativas.
    """
    mensagem = _PREFIXO_CHAVE_CONTA + email_normalizado.encode("utf-8", errors="surrogatepass")
    return hmac.new(segredo, mensagem, hashlib.sha256).digest()


def bloqueado_ate(
    instantes: Sequence[datetime], *, limite: int, janela: timedelta, bloqueio: timedelta
) -> datetime | None:
    """Fim do bloqueio mais tardio causado pelas falhas, ou `None` se nunca houve.

    A L-ésima falha (`limite`) dentro da `janela` inicia um bloqueio de `bloqueio`. Quem chama
    compara o resultado com o instante atual; só precisa passar as falhas mais recentes que
    `agora - (janela + bloqueio)`, porque as anteriores não podem mais sustentar um bloqueio.
    """
    ordenados = sorted(instantes)
    ate: datetime | None = None
    for i in range(limite - 1, len(ordenados)):
        if ordenados[i] - ordenados[i - limite + 1] < janela:
            candidato = ordenados[i] + bloqueio
            ate = candidato if ate is None else max(ate, candidato)
    return ate


def liberado_cadastro_em(
    instantes: Sequence[datetime], *, agora: datetime, limite: int, janela: timedelta
) -> datetime | None:
    """Instante em que o endereço volta ao limite de cadastros, ou `None` se já está livre."""
    recentes = sorted(i for i in instantes if i > agora - janela)
    if len(recentes) < limite:
        return None
    return recentes[len(recentes) - limite] + janela


# --- Alteração do perfil (RF-008, RF-010, US3) -------------------------------------------

_CENTESIMO = Decimal("0.01")
_CAMPOS_ALTERAVEIS = frozenset(
    {"nome", "fuso", "meta_diaria", "tamanho_licao", "limite_novos_dia", "retencao_desejada"}
)
_NOME_JSON = {
    "meta_diaria": "metaDiaria",
    "tamanho_licao": "tamanhoLicao",
    "limite_novos_dia": "limiteNovosDia",
    "retencao_desejada": "retencaoDesejada",
}


@dataclass(frozen=True, slots=True)
class AlteracaoPerfil:
    """Só os campos enviados (e válidos) vêm preenchidos; `None` significa "não alterar"."""

    nome: str | None = None
    fuso: str | None = None
    meta_diaria: int | None = None
    tamanho_licao: int | None = None
    limite_novos_dia: int | None = None
    retencao_desejada: Decimal | None = None

    def vazia(self) -> bool:
        return all(getattr(self, campo) is None for campo in _CAMPOS_ALTERAVEIS)


def _inteiro_no_limite(valor: object, limite: preferencias.LimiteInteiro) -> int:
    # `bool` é subclasse de `int`: `true` não é um número de cartões.
    if isinstance(valor, bool) or not isinstance(valor, int) or not limite.contem(valor):
        raise ValorInvalido(f"Use um valor de {limite.minimo} a {limite.maximo}.")
    return valor


def _retencao(valor: object) -> Decimal:
    limite = preferencias.RETENCAO_DESEJADA
    mensagem = (
        f"Use um valor de {str(limite.minimo).replace('.', ',')} a "
        f"{str(limite.maximo).replace('.', ',')}, com no máximo duas casas decimais."
    )
    if isinstance(valor, bool) or not isinstance(valor, int | float | Decimal):
        raise ValorInvalido(mensagem)
    try:
        decimal = Decimal(str(valor))
        arredondado = decimal.quantize(_CENTESIMO)
    except InvalidOperation:
        raise ValorInvalido(mensagem) from None
    if not decimal.is_finite() or decimal != arredondado or not limite.contem(arredondado):
        raise ValorInvalido(mensagem)
    return arredondado


def _texto(valor: object, validar: Callable[[str], str], mensagem: str) -> str:
    if not isinstance(valor, str):
        raise ValorInvalido(mensagem)
    return validar(valor)


def validar_alteracao_perfil(enviados: Mapping[str, object]) -> AlteracaoPerfil:
    """Valida a alteração inteira ou nada (RF-008): informa todos os campos inválidos.

    `enviados` traz só os campos presentes no corpo, com nomes em snake_case. Um campo
    desconhecido é erro de programação (o DTO já recusa campos extras), não de entrada.
    """
    desconhecidos = set(enviados) - _CAMPOS_ALTERAVEIS
    if desconhecidos:
        raise ValueError(f"campo não alterável: {sorted(desconhecidos)}")
    if not enviados:
        raise EntradaInvalida("Informe ao menos um campo para alterar.")

    verificacoes: dict[str, Callable[[object], object]] = {
        "nome": lambda v: _texto(v, validar_nome, "Informe o nome."),
        "fuso": lambda v: _texto(v, validar_fuso, "Fuso desconhecido."),
        "meta_diaria": lambda v: _inteiro_no_limite(v, preferencias.META_DIARIA),
        "tamanho_licao": lambda v: _inteiro_no_limite(v, preferencias.TAMANHO_LICAO),
        "limite_novos_dia": lambda v: _inteiro_no_limite(v, preferencias.LIMITE_NOVOS_DIA),
        "retencao_desejada": _retencao,
    }
    erros: list[ErroCampo] = []
    validados: dict[str, object] = {}
    for campo, valor in enviados.items():
        try:
            validados[campo] = verificacoes[campo](valor)
        except ValorInvalido as erro:
            erros.append(ErroCampo(_NOME_JSON.get(campo, campo), erro.mensagem))
    if erros:
        raise EntradaInvalida(campos=erros)
    return AlteracaoPerfil(**validados)  # type: ignore[arg-type]
