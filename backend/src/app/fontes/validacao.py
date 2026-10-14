"""Validação do arquivo no envio, em ordem e com código por recusa (DTEC 028; RF-004).

Verificação própria por assinatura e decodificação, sem dependência nova. A ordem é a da DTEC:
tamanho, extensão, assinatura, decodificação UTF-8 e texto visível; o PDF é aberto por último e
só num subprocesso isolado (DTEC 024), e só se a assinatura já confere. Uma recusa não guarda
nada. A ausência de camada de texto **não** é verificada aqui: é resultado da extração (CB-23).

As mensagens são específicas e nunca citam o nome do arquivo, o caminho nem o conteúdo (RQ-002).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from app.fontes import dominio, extracao
from app.fontes.excecoes import ArquivoMuitoGrande, ArquivoRecusado
from app.nucleo.codigos import CodigoErro
from app.nucleo.isolamento import ExecutorIsolado, StatusIsolado, executar_isolado
from app.nucleo.texto import tem_caractere_visivel

EXTENSOES_ACEITAS = (".pdf", ".txt", ".md", ".markdown")
_TIPOS_MIDIA = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
}
_JANELA_DA_ASSINATURA_PDF = 1024
_ASSINATURA_PDF = b"%PDF-"

# Texto não pode começar com a assinatura de um formato binário conhecido. Não entram marcas que
# também são texto comum (ex.: "BM" do BMP ou "MZ" de executáveis do Windows).
_ASSINATURAS_BINARIAS = (
    b"%PDF-",
    b"PK\x03\x04",
    b"PK\x05\x06",
    b"PK\x07\x08",
    b"\x89PNG\r\n\x1a\n",
    b"\xff\xd8\xff",
    b"GIF87a",
    b"GIF89a",
    b"\x1f\x8b",
    b"7z\xbc\xaf\x27\x1c",
    b"Rar!\x1a\x07",
    b"\x7fELF",
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
)
# UTF-16 e UTF-32 têm bytes nulos, mas são texto: pedem outra codificação, não "outro formato".
_BOMS_NAO_UTF8 = (b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff", b"\xff\xfe", b"\xfe\xff")
_CONTROLES_PERMITIDOS = frozenset("\t\n\r")

MENSAGEM_FORMATO = (
    "Este formato não é aceito. Envie um PDF com texto, um TXT ou um arquivo Markdown (.md)."
)
MENSAGEM_VAZIO = "O arquivo está vazio ou não tem texto. Envie um arquivo com conteúdo."
MENSAGEM_CODIFICACAO = (
    "Não foi possível ler o texto deste arquivo. Salve-o com a codificação UTF-8 e envie de novo."
)
MENSAGEM_CORROMPIDO = (
    "Não foi possível abrir este PDF. Ele pode estar corrompido; tente exportá-lo de novo."
)
MENSAGEM_PROTEGIDO = "Este PDF está protegido por senha. Remova a proteção e envie de novo."


@dataclass(frozen=True, slots=True)
class LimitesValidacao:
    tamanho_max_bytes: int
    max_paginas: int
    tempo_s: float
    memoria_mb: int


@dataclass(frozen=True, slots=True)
class ArquivoValidado:
    tipo_midia: str
    texto: str | None  # TXT e MD: o texto decodificado, sem o BOM
    total_paginas: int | None  # PDF


def _tipo_divergente(extensao: str) -> ArquivoRecusado:
    return ArquivoRecusado(
        CodigoErro.TIPO_DIVERGENTE,
        f"O conteúdo deste arquivo não corresponde à extensão {extensao}.",
    )


# --- Passos 3 a 7 (puros) ------------------------------------------------------------------------


def validar_tamanho(tamanho: int, limite: int) -> None:
    if tamanho <= 0:
        raise ArquivoRecusado(CodigoErro.ARQUIVO_VAZIO, MENSAGEM_VAZIO)
    if tamanho > limite:
        raise ArquivoMuitoGrande(limite)


def extensao_do_nome(nome_enviado: str) -> str:
    """A extensão do nome enviado, sem diferenciar caixa; só ela decide o formato esperado."""
    nome = dominio.nome_exibido(nome_enviado)
    posicao = nome.rfind(".")
    extensao = nome[posicao:].lower() if posicao > 0 else ""
    if extensao not in EXTENSOES_ACEITAS:
        raise ArquivoRecusado(CodigoErro.FORMATO_NAO_ACEITO, MENSAGEM_FORMATO)
    return extensao


def validar_assinatura_pdf(cabecalho: bytes, extensao: str) -> None:
    if _ASSINATURA_PDF not in cabecalho[:_JANELA_DA_ASSINATURA_PDF]:
        raise _tipo_divergente(extensao)


def validar_texto(extensao: str, conteudo: bytes) -> str:
    """TXT e MD: assinatura, UTF-8 estrito, controles e texto visível. Devolve o texto sem BOM."""
    if conteudo.startswith(_ASSINATURAS_BINARIAS):
        raise _tipo_divergente(extensao)
    if conteudo.startswith(_BOMS_NAO_UTF8):
        raise ArquivoRecusado(CodigoErro.CODIFICACAO_INVALIDA, MENSAGEM_CODIFICACAO)
    if b"\x00" in conteudo:
        raise _tipo_divergente(extensao)
    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ArquivoRecusado(CodigoErro.CODIFICACAO_INVALIDA, MENSAGEM_CODIFICACAO) from None
    if any(_controle_nao_permitido(c) for c in texto):
        raise _tipo_divergente(extensao)
    if not tem_caractere_visivel(texto):
        raise ArquivoRecusado(CodigoErro.ARQUIVO_VAZIO, MENSAGEM_VAZIO)
    return texto


def _controle_nao_permitido(caractere: str) -> bool:
    return caractere not in _CONTROLES_PERMITIDOS and (
        ord(caractere) < 0x20 or 0x7F <= ord(caractere) <= 0x9F
    )


# --- Passo 8: PDF no subprocesso isolado ---------------------------------------------------------


async def validar_pdf(
    caminho: Path,
    limites: LimitesValidacao,
    *,
    semaforo: asyncio.Semaphore | None,
    executor: ExecutorIsolado = executar_isolado,
) -> int:
    """Abre o PDF isolado: devolve o número de páginas ou recusa com o código específico."""
    resultado = await executor(
        extracao.verificar_pdf,
        (str(caminho), limites.max_paginas),
        tempo_limite_s=limites.tempo_s,
        memoria_max_mb=limites.memoria_mb,
        semaforo=semaforo,
    )
    corrompido = ArquivoRecusado(CodigoErro.ARQUIVO_CORROMPIDO, MENSAGEM_CORROMPIDO)
    if resultado.status is not StatusIsolado.OK:
        raise corrompido  # tempo ou memória esgotados, erro no filho ou filho morto
    veredito = resultado.valor.get("resultado")
    if veredito == "ok":
        return int(resultado.valor["paginas"])
    if veredito == "protegido":
        raise ArquivoRecusado(CodigoErro.PDF_PROTEGIDO, MENSAGEM_PROTEGIDO)
    if veredito == "paginas_excedidas":
        raise ArquivoRecusado(
            CodigoErro.PDF_PAGINAS_EXCEDIDAS,
            f"Este PDF tem páginas demais. O limite é de {limites.max_paginas} páginas.",
        )
    raise corrompido


# --- Orquestração --------------------------------------------------------------------------------


async def validar_arquivo(
    nome_enviado: str,
    caminho: Path,
    tamanho: int,
    limites: LimitesValidacao,
    *,
    semaforo: asyncio.Semaphore | None,
    executor: ExecutorIsolado = executar_isolado,
) -> ArquivoValidado:
    """Passos 3 a 8 da DTEC 028 sobre o arquivo temporário já gravado."""
    validar_tamanho(tamanho, limites.tamanho_max_bytes)
    extensao = extensao_do_nome(nome_enviado)
    tipo_midia = _TIPOS_MIDIA[extensao]
    if extensao == ".pdf":
        cabecalho = await asyncio.to_thread(_ler_inicio, caminho, _JANELA_DA_ASSINATURA_PDF)
        validar_assinatura_pdf(cabecalho, extensao)
        paginas = await validar_pdf(caminho, limites, semaforo=semaforo, executor=executor)
        return ArquivoValidado(tipo_midia, None, paginas)
    conteudo = await asyncio.to_thread(caminho.read_bytes)
    return ArquivoValidado(tipo_midia, validar_texto(extensao, conteudo), None)


def _ler_inicio(caminho: Path, quantidade: int) -> bytes:
    with caminho.open("rb") as arquivo:
        return arquivo.read(quantidade)
