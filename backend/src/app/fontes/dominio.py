"""Regras puras das fontes (spec 002): sem banco e sem HTTP (DTEC 018).

Nome exibido e título (RQ-001, RF-003, RF-015), estados e transições (DTEC 030), catálogo das
mensagens de falha (RF-007) e os textos das recusas do envio. O nome que o estudante envia só é
exibido: nunca compõe o caminho do arquivo guardado (RQ-001).
"""

from __future__ import annotations

import os
import re
from enum import StrEnum

from app.nucleo.texto import (
    ValorInvalido,
    normalizar,
    remover_proibidos,
    tem_caractere_proibido,
    tem_caractere_visivel,
)

NOME_ARQUIVO_MAXIMO = 255
EXTENSAO_PRESERVADA_MAXIMA = 16
TITULO_MAXIMO = 120
NOME_ARQUIVO_PADRAO = "arquivo"
TITULO_PADRAO = "Fonte sem título"

_SEPARADORES_DE_CAMINHO = re.compile(r"[\\/]")


class EstadoFonte(StrEnum):
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    CONCLUIDO = "concluido"
    FALHOU = "falhou"


class CodigoFalhaFonte(StrEnum):
    """Nome do contrato (`CodigoFalhaFonte`); no código, `CodigoFalha` basta."""

    FALHA_TECNICA = "falha_tecnica"
    SEM_TEXTO = "sem_texto"
    CONTEUDO_INVALIDO = "conteudo_invalido"


CodigoFalha = CodigoFalhaFonte


# --- Nome exibido e título -----------------------------------------------------------------------


def nome_exibido(enviado: str) -> str:
    """O nome do arquivo para exibição: só o último segmento, sem controles, em NFC, até 255.

    Saem os caracteres de controle (C0 e C1), os de direção bidirecional, o uso privado e os
    substitutos isolados. Se nada sobrar, `arquivo`.
    """
    ultimo = _SEPARADORES_DE_CAMINHO.split(enviado)[-1]
    limpo = normalizar(remover_proibidos(ultimo))
    if len(limpo) > NOME_ARQUIVO_MAXIMO:
        limpo = _truncar_preservando_a_extensao(limpo)
    return limpo or NOME_ARQUIVO_PADRAO


def _truncar_preservando_a_extensao(nome: str) -> str:
    """Corta o nome em 255 caracteres sem perder a extensão, que decide o formato do arquivo."""
    radical, extensao = os.path.splitext(nome)
    if 0 < len(extensao) <= EXTENSAO_PRESERVADA_MAXIMA:
        return normalizar(radical[: NOME_ARQUIVO_MAXIMO - len(extensao)]) + extensao
    return normalizar(nome[:NOME_ARQUIVO_MAXIMO])


def titulo_padrao(nome: str) -> str:
    """O nome sem a extensão, truncado em 120 caracteres (RF-003); vazio vira `Fonte sem título`."""
    sem_extensao, _ = os.path.splitext(nome)
    titulo = normalizar(remover_proibidos(sem_extensao))[:TITULO_MAXIMO]
    titulo = normalizar(titulo)
    return titulo if tem_caractere_visivel(titulo) else TITULO_PADRAO


def validar_titulo(valor: str) -> str:
    """Título digitado: de 1 a 120 caracteres, em NFC e sem caracteres proibidos (RF-015)."""
    titulo = normalizar(valor)
    if not titulo or not tem_caractere_visivel(titulo):
        raise ValorInvalido("Informe o título.")
    if len(titulo) > TITULO_MAXIMO:
        raise ValorInvalido(f"Use no máximo {TITULO_MAXIMO} caracteres.")
    if tem_caractere_proibido(titulo):
        raise ValorInvalido("O título tem caracteres que não podem ser usados.")
    return titulo


# --- Estados e transições ------------------------------------------------------------------------

_TRANSICOES_DO_WORKER: frozenset[tuple[EstadoFonte, EstadoFonte]] = frozenset(
    {
        (EstadoFonte.PENDENTE, EstadoFonte.PROCESSANDO),
        (EstadoFonte.PROCESSANDO, EstadoFonte.PROCESSANDO),
        (EstadoFonte.PROCESSANDO, EstadoFonte.CONCLUIDO),
        (EstadoFonte.PROCESSANDO, EstadoFonte.FALHOU),
    }
)


def transicao_permitida(
    de: EstadoFonte, para: EstadoFonte, *, codigo_atual: CodigoFalha | None = None
) -> bool:
    """Transições do modelo de dados. `concluido` é final; `falhou` só volta a `pendente`
    por pedido do estudante e só depois de uma falha técnica (RF-007)."""
    if (de, para) in _TRANSICOES_DO_WORKER:
        return True
    return (
        de is EstadoFonte.FALHOU
        and para is EstadoFonte.PENDENTE
        and codigo_atual is CodigoFalha.FALHA_TECNICA
    )


def estado_final(estado: EstadoFonte) -> bool:
    return estado in {EstadoFonte.CONCLUIDO, EstadoFonte.FALHOU}


# --- Catálogo de falhas --------------------------------------------------------------------------

_MENSAGENS_DE_FALHA: dict[CodigoFalha, str] = {
    CodigoFalha.FALHA_TECNICA: (
        "Não conseguimos processar esta fonte por um problema técnico. Tente novamente."
    ),
    CodigoFalha.SEM_TEXTO: (
        "Este PDF não tem texto selecionável. PDFs digitalizados (imagens de páginas) não são "
        "aceitos."
    ),
    CodigoFalha.CONTEUDO_INVALIDO: (
        "Não foi possível ler o conteúdo deste arquivo. Verifique se ele abre normalmente e "
        "envie de novo."
    ),
}


def mensagem_falha(codigo: CodigoFalha) -> str:
    return _MENSAGENS_DE_FALHA[codigo]


def mensagem_do_estado(estado: EstadoFonte, codigo: CodigoFalha | None) -> str | None:
    """A explicação ao estudante: só existe em `falhou`."""
    if estado is EstadoFonte.FALHOU and codigo is not None:
        return mensagem_falha(codigo)
    return None


def pode_tentar_novamente(estado: EstadoFonte, codigo: CodigoFalha | None) -> bool:
    return estado is EstadoFonte.FALHOU and codigo is CodigoFalha.FALHA_TECNICA


# --- Mensagens das recusas do envio --------------------------------------------------------------


def mensagem_duplicada(titulo_existente: str) -> str:
    return f"Esta fonte já está nesta matéria: «{titulo_existente}»."


def formatar_megabytes(bytes_: int) -> str:
    """Megabytes (1 MB = 1.048.576 bytes) com vírgula decimal e sem zeros à direita."""
    valor = bytes_ / (1024 * 1024)
    texto = f"{valor:.1f}".rstrip("0").rstrip(".") if valor != int(valor) else str(int(valor))
    return texto.replace(".", ",")


def mensagem_arquivo_grande(limite_bytes: int) -> str:
    return f"O arquivo tem mais de {formatar_megabytes(limite_bytes)} MB. Envie um arquivo menor."
