"""Regras de texto compartilhadas pelos domínios novos (nome da matéria, título da fonte...).

Sem banco e sem HTTP. Texto de estudante é normalizado em NFC e aparado nas extremidades
(`padroes-implementacao.md`, "Textos"). A 001 mantém as próprias regras de nome de pessoa.
"""

from __future__ import annotations

import unicodedata

# Controles de direção (U+202A a U+202E e U+2066 a U+2069) permitem falsificar a aparência de
# um texto na tela. As marcas LRM e RLM (U+200E e U+200F) seguem aceitas: escrevem em alfabetos
# da direita para a esquerda.
CONTROLES_DE_DIRECAO = frozenset(chr(c) for c in (*range(0x202A, 0x202F), *range(0x2066, 0x206A)))
# Controle, substituto isolado (não codifica em UTF-8) e uso privado.
_CATEGORIAS_PROIBIDAS = frozenset({"Cc", "Cs", "Co"})
# Espaços, separadores e qualquer "outro" (controle, formato, não atribuído): invisíveis.
_PREFIXOS_INVISIVEIS = ("Z", "C")


class ValorInvalido(ValueError):
    """Regra de domínio violada por um valor; a mensagem já é para o estudante."""

    def __init__(self, mensagem: str) -> None:
        self.mensagem = mensagem
        super().__init__(mensagem)


def normalizar(valor: str) -> str:
    """NFC e sem espaços nas extremidades."""
    return unicodedata.normalize("NFC", valor).strip()


def tem_caractere_proibido(texto: str) -> bool:
    """Controle, substituto isolado, uso privado ou controle de direção."""
    return any(
        unicodedata.category(c) in _CATEGORIAS_PROIBIDAS or c in CONTROLES_DE_DIRECAO for c in texto
    )


def remover_proibidos(texto: str) -> str:
    """O texto sem controle, substituto isolado, uso privado e controle de direção."""
    return "".join(
        c
        for c in texto
        if unicodedata.category(c) not in _CATEGORIAS_PROIBIDAS and c not in CONTROLES_DE_DIRECAO
    )


def tem_caractere_visivel(texto: str) -> bool:
    """Verdadeiro se há ao menos um caractere que não é espaço nem invisível."""
    return any(not unicodedata.category(c).startswith(_PREFIXOS_INVISIVEIS) for c in texto)
