"""Validação do arquivo no envio (DTEC 028; RF-004, US1-4, CS-002; T016).

Uma linha por verificação da tabela da DTEC, com o código esperado. A abertura do PDF roda no
subprocesso (DTEC 024); aqui o executor é simulado, e o PDF real é coberto por T018 e T019.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from app.fontes import validacao
from app.fontes.excecoes import ArquivoMuitoGrande, ArquivoRecusado
from app.fontes.validacao import ArquivoValidado, LimitesValidacao
from app.nucleo.codigos import CodigoErro
from app.nucleo.erros import ConteudoMuitoGrande
from app.nucleo.isolamento import ResultadoIsolado, StatusIsolado

pytestmark = pytest.mark.unit

LIMITE = 2 * 1024 * 1024
CAMINHO_PDF = Path("pdf-de-teste.pdf")  # o executor é simulado: o arquivo não é aberto
LIMITES = LimitesValidacao(tamanho_max_bytes=LIMITE, max_paginas=500, tempo_s=10, memoria_mb=256)


def recusa(codigo: CodigoErro):  # type: ignore[no-untyped-def]
    return pytest.raises(ArquivoRecusado, check=lambda e: e.codigo == codigo)


# --- Passo 3: tamanho -------------------------------------------------------------------------


def test_arquivo_de_zero_byte_e_vazio() -> None:
    with recusa(CodigoErro.ARQUIVO_VAZIO):
        validacao.validar_tamanho(0, LIMITE)


@pytest.mark.parametrize("tamanho", [1, LIMITE - 1, LIMITE])
def test_tamanhos_dentro_do_limite_passam(tamanho: int) -> None:
    validacao.validar_tamanho(tamanho, LIMITE)


def test_arquivo_acima_do_limite_e_413_e_cita_o_limite() -> None:
    with pytest.raises(ArquivoMuitoGrande) as erro:
        validacao.validar_tamanho(LIMITE + 1, LIMITE)
    assert isinstance(erro.value, ConteudoMuitoGrande)
    assert erro.value.status == 413
    assert erro.value.codigo == CodigoErro.ARQUIVO_MUITO_GRANDE
    assert "2 MB" in erro.value.mensagem


# --- Passo 4: extensão ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nome", "extensao"),
    [
        ("a.pdf", ".pdf"),
        ("A.PDF", ".pdf"),
        ("nota.txt", ".txt"),
        ("NOTA.Txt", ".txt"),
        ("n.md", ".md"),
        ("n.MD", ".md"),
        ("n.markdown", ".markdown"),
        ("N.Markdown", ".markdown"),
        ("arquivo.tar.pdf", ".pdf"),
        ("../../x/a.pdf", ".pdf"),
        ("C:\\x\\a.txt", ".txt"),
        ("  a.pdf  ", ".pdf"),
    ],
)
def test_extensoes_aceitas_sem_diferenciar_caixa(nome: str, extensao: str) -> None:
    assert validacao.extensao_do_nome(nome) == extensao


@pytest.mark.parametrize(
    "nome",
    ["a.docx", "a.exe", "a.png", "a.zip", "a", "a.", ".pdf", ".txt", "a.pdf.exe", "", "/"],
)
def test_outras_extensoes_sao_formato_nao_aceito(nome: str) -> None:
    with recusa(CodigoErro.FORMATO_NAO_ACEITO) as erro:
        validacao.extensao_do_nome(nome)
    assert "formato" in erro.value.mensagem.lower()


def test_formato_nao_aceito_diz_quais_sao_aceitos() -> None:
    with pytest.raises(ArquivoRecusado) as erro:
        validacao.extensao_do_nome("a.docx")
    for aceito in ("PDF", "TXT", "Markdown"):
        assert aceito in erro.value.mensagem


# --- Passo 5: assinatura ----------------------------------------------------------------------


def test_pdf_exige_assinatura_nos_primeiros_1024_bytes() -> None:
    validacao.validar_assinatura_pdf(b"%PDF-1.7\nresto", ".pdf")
    validacao.validar_assinatura_pdf(b"lixo" * 100 + b"%PDF-1.4\n", ".pdf")  # offset 400
    validacao.validar_assinatura_pdf(b"x" * 1019 + b"%PDF-", ".pdf")  # termina no byte 1024


@pytest.mark.parametrize(
    "conteudo",
    [b"", b"Isto e um texto, nao um PDF", b"x" * 1020 + b"%PDF-1.7", b"%PD", b"%pdf-1.7"],
)
def test_pdf_sem_assinatura_e_tipo_divergente(conteudo: bytes) -> None:
    with recusa(CodigoErro.TIPO_DIVERGENTE) as erro:
        validacao.validar_assinatura_pdf(conteudo, ".pdf")
    assert ".pdf" in erro.value.mensagem


ASSINATURAS_BINARIAS = {
    "pdf": b"%PDF-1.7\n",
    "zip": b"PK\x03\x04conteudo",
    "zip-vazio": b"PK\x05\x06" + b"\x00" * 18,
    "png": b"\x89PNG\r\n\x1a\n....",
    "jpeg": b"\xff\xd8\xff\xe0....JFIF",
    "gif87": b"GIF87a....",
    "gif89": b"GIF89a....",
    "webp": b"RIFF\x00\x00\x00\x00WEBP....",
    "gzip": b"\x1f\x8b\x08\x00",
    "7z": b"7z\xbc\xaf\x27\x1c",
    "rar": b"Rar!\x1a\x07\x00",
    "elf": b"\x7fELF\x02\x01",
    "ole": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
}


@pytest.mark.parametrize("assinatura", ASSINATURAS_BINARIAS.values(), ids=ASSINATURAS_BINARIAS)
@pytest.mark.parametrize("extensao", [".txt", ".md", ".markdown"])
def test_texto_com_assinatura_de_formato_binario_e_tipo_divergente(
    extensao: str, assinatura: bytes
) -> None:
    with recusa(CodigoErro.TIPO_DIVERGENTE):
        validacao.validar_texto(extensao, assinatura + b" texto depois")


def test_texto_que_apenas_menciona_pdf_no_meio_nao_e_confundido() -> None:
    assert validacao.validar_texto(".txt", b"O formato %PDF- aparece no meio.\n") != ""


# --- Passos 5 a 7: texto ----------------------------------------------------------------------


def test_utf8_simples_e_devolvido_decodificado() -> None:
    assert (
        validacao.validar_texto(".txt", "Célula e organela.\n".encode()) == "Célula e organela.\n"
    )


def test_utf8_com_bom_tem_o_bom_removido() -> None:
    texto = validacao.validar_texto(".md", b"\xef\xbb\xbf# Titulo\n")
    assert texto == "# Titulo\n"


@pytest.mark.parametrize("extensao", [".txt", ".md", ".markdown"])
def test_latin1_e_codificacao_invalida(extensao: str) -> None:
    with recusa(CodigoErro.CODIFICACAO_INVALIDA) as erro:
        validacao.validar_texto(extensao, "Célula é básica".encode("latin-1"))
    assert "UTF-8" in erro.value.mensagem


@pytest.mark.parametrize(
    "conteudo",
    [
        b"\xff\xfeA\x00b\x00",  # UTF-16 LE com BOM
        b"\xfe\xff\x00A\x00b",  # UTF-16 BE com BOM
        b"\xff\xfe\x00\x00A\x00\x00\x00",  # UTF-32 LE com BOM
        b"\x00\x00\xfe\xff\x00\x00\x00A",  # UTF-32 BE com BOM
    ],
)
def test_utf16_e_utf32_com_bom_sao_codificacao_invalida_e_nao_binario(conteudo: bytes) -> None:
    with recusa(CodigoErro.CODIFICACAO_INVALIDA):
        validacao.validar_texto(".txt", conteudo)


def test_utf8_truncado_no_meio_de_um_caractere_e_codificacao_invalida() -> None:
    with recusa(CodigoErro.CODIFICACAO_INVALIDA):
        validacao.validar_texto(".txt", "ação".encode()[:-2])


def test_byte_nulo_e_tipo_divergente() -> None:
    with recusa(CodigoErro.TIPO_DIVERGENTE):
        validacao.validar_texto(".txt", b"abc\x00def")


@pytest.mark.parametrize(
    "controle", ["\x01", "\x07", "\x08", "\x0b", "\x0c", "\x1b", "\x7f", "\x85"]
)
def test_controles_alem_de_tab_e_quebras_sao_tipo_divergente(controle: str) -> None:
    with recusa(CodigoErro.TIPO_DIVERGENTE):
        validacao.validar_texto(".txt", f"antes{controle}depois".encode())


def test_tabulacao_quebra_de_linha_e_retorno_de_carro_sao_permitidos() -> None:
    assert validacao.validar_texto(".txt", b"a\tb\r\nc\rd\ne\n") == "a\tb\r\nc\rd\ne\n"


@pytest.mark.parametrize(
    "conteudo", [b" ", b"   \n\t \r\n", b"\xef\xbb\xbf  \n", "\u200b".encode(), b"\xc2\xa0"]
)
def test_texto_sem_caractere_visivel_e_arquivo_vazio(conteudo: bytes) -> None:
    with recusa(CodigoErro.ARQUIVO_VAZIO):
        validacao.validar_texto(".txt", conteudo)


def test_so_simbolos_conta_como_texto_visivel() -> None:
    assert validacao.validar_texto(".txt", b"### ***\n")


# --- Passo 8: PDF no subprocesso --------------------------------------------------------------


class ExecutorSimulado:
    def __init__(self, resultado: ResultadoIsolado) -> None:
        self.resultado = resultado
        self.chamadas: list[dict[str, Any]] = []

    async def __call__(
        self,
        funcao: Any,
        argumentos: tuple[Any, ...] = (),
        *,
        tempo_limite_s: float,
        memoria_max_mb: int,
        semaforo: asyncio.Semaphore | None = None,
    ) -> ResultadoIsolado:
        self.chamadas.append(
            {
                "funcao": funcao.__name__,
                "argumentos": argumentos,
                "tempo": tempo_limite_s,
                "memoria": memoria_max_mb,
                "semaforo": semaforo,
            }
        )
        return self.resultado


def _ok(valor: dict[str, Any]) -> ResultadoIsolado:
    return ResultadoIsolado(StatusIsolado.OK, valor=valor)


async def test_pdf_valido_devolve_o_total_de_paginas_e_usa_os_limites_da_configuracao() -> None:
    executor = ExecutorSimulado(_ok({"resultado": "ok", "paginas": 12}))
    semaforo = asyncio.Semaphore(2)
    paginas = await validacao.validar_pdf(
        CAMINHO_PDF, LIMITES, semaforo=semaforo, executor=executor
    )
    assert paginas == 12
    chamada = executor.chamadas[0]
    assert chamada["funcao"] == "verificar_pdf"
    assert chamada["argumentos"] == ("pdf-de-teste.pdf", 500)
    assert (chamada["tempo"], chamada["memoria"]) == (10, 256)
    assert chamada["semaforo"] is semaforo


@pytest.mark.parametrize(
    ("resultado", "codigo"),
    [
        (_ok({"resultado": "protegido"}), CodigoErro.PDF_PROTEGIDO),
        (_ok({"resultado": "paginas_excedidas", "paginas": 501}), CodigoErro.PDF_PAGINAS_EXCEDIDAS),
        (_ok({"resultado": "corrompido"}), CodigoErro.ARQUIVO_CORROMPIDO),
        (_ok({"resultado": "inesperado"}), CodigoErro.ARQUIVO_CORROMPIDO),
        (ResultadoIsolado(StatusIsolado.TEMPO_ESGOTADO), CodigoErro.ARQUIVO_CORROMPIDO),
        (ResultadoIsolado(StatusIsolado.MEMORIA_ESGOTADA), CodigoErro.ARQUIVO_CORROMPIDO),
        (ResultadoIsolado(StatusIsolado.ERRO, erro="RuntimeError"), CodigoErro.ARQUIVO_CORROMPIDO),
        (ResultadoIsolado(StatusIsolado.FALHA_PROCESSO), CodigoErro.ARQUIVO_CORROMPIDO),
    ],
)
async def test_pdf_recusado_pelo_subprocesso_tem_codigo_especifico(
    resultado: ResultadoIsolado, codigo: CodigoErro
) -> None:
    with recusa(codigo):
        await validacao.validar_pdf(
            CAMINHO_PDF, LIMITES, semaforo=None, executor=ExecutorSimulado(resultado)
        )


async def test_pdf_com_paginas_demais_cita_o_limite_na_mensagem() -> None:
    executor = ExecutorSimulado(_ok({"resultado": "paginas_excedidas", "paginas": 501}))
    with pytest.raises(ArquivoRecusado) as erro:
        await validacao.validar_pdf(CAMINHO_PDF, LIMITES, semaforo=None, executor=executor)
    assert "500" in erro.value.mensagem


# --- Orquestração -----------------------------------------------------------------------------


async def _arquivo(tmp_path: Path, conteudo: bytes) -> Path:
    caminho = tmp_path / "recebido"
    caminho.write_bytes(conteudo)
    return caminho


async def test_texto_valido_percorre_a_ordem_e_devolve_tipo_e_texto(tmp_path: Path) -> None:
    caminho = await _arquivo(tmp_path, "# Título\n\nTexto.\n".encode())
    resultado = await validacao.validar_arquivo(
        "aula.md", caminho, caminho.stat().st_size, LIMITES, semaforo=None
    )
    assert resultado == ArquivoValidado("text/markdown", "# Título\n\nTexto.\n", None)


@pytest.mark.parametrize(
    ("nome", "tipo"),
    [("a.txt", "text/plain"), ("a.md", "text/markdown"), ("a.markdown", "text/markdown")],
)
async def test_o_tipo_gravado_vem_da_extensao_verificada(
    tmp_path: Path, nome: str, tipo: str
) -> None:
    caminho = await _arquivo(tmp_path, b"texto simples\n")
    resultado = await validacao.validar_arquivo(
        nome, caminho, caminho.stat().st_size, LIMITES, semaforo=None
    )
    assert resultado.tipo_midia == tipo


async def test_pdf_valido_devolve_paginas_e_nao_texto(tmp_path: Path) -> None:
    caminho = await _arquivo(tmp_path, b"%PDF-1.7\n")
    resultado = await validacao.validar_arquivo(
        "a.pdf",
        caminho,
        caminho.stat().st_size,
        LIMITES,
        semaforo=None,
        executor=ExecutorSimulado(_ok({"resultado": "ok", "paginas": 3})),
    )
    assert resultado == ArquivoValidado("application/pdf", None, 3)


async def test_a_ordem_das_verificacoes_e_a_da_dtec_028(tmp_path: Path) -> None:
    """Tamanho antes de extensão; extensão antes de assinatura; assinatura antes do PDF."""
    caminho = await _arquivo(tmp_path, b"")
    with recusa(CodigoErro.ARQUIVO_VAZIO):
        await validacao.validar_arquivo("a.docx", caminho, 0, LIMITES, semaforo=None)
    with pytest.raises(ArquivoMuitoGrande):
        await validacao.validar_arquivo("a.docx", caminho, LIMITE + 1, LIMITES, semaforo=None)

    caminho = await _arquivo(tmp_path, b"texto")
    with recusa(CodigoErro.FORMATO_NAO_ACEITO):
        await validacao.validar_arquivo("a.docx", caminho, 5, LIMITES, semaforo=None)
    executor = ExecutorSimulado(_ok({"resultado": "ok", "paginas": 1}))
    with recusa(CodigoErro.TIPO_DIVERGENTE):
        await validacao.validar_arquivo(
            "a.pdf", caminho, 5, LIMITES, semaforo=None, executor=executor
        )
    assert executor.chamadas == [], "um PDF sem assinatura não chega a ser aberto"


async def test_texto_disfarcado_de_pdf_nao_e_aberto_pelo_parser(tmp_path: Path) -> None:
    caminho = await _arquivo(tmp_path, b"Isto e um texto com extensao .pdf\n")
    executor = ExecutorSimulado(_ok({"resultado": "ok", "paginas": 1}))
    with recusa(CodigoErro.TIPO_DIVERGENTE):
        await validacao.validar_arquivo(
            "x.pdf", caminho, caminho.stat().st_size, LIMITES, semaforo=None, executor=executor
        )
    assert executor.chamadas == []


async def test_a_mensagem_de_recusa_nunca_cita_o_nome_nem_o_conteudo(tmp_path: Path) -> None:
    caminho = await _arquivo(tmp_path, b"segredo-do-arquivo\x00")
    with pytest.raises(ArquivoRecusado) as erro:
        await validacao.validar_arquivo(
            "relatorio-secreto.txt", caminho, caminho.stat().st_size, LIMITES, semaforo=None
        )
    assert "relatorio-secreto" not in erro.value.mensagem
    assert "segredo-do-arquivo" not in erro.value.mensagem
    assert str(tmp_path) not in erro.value.mensagem
