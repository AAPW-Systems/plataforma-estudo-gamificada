"""Hierarquia única de erros e conversão central no corpo `Erro` (DTEC 018).

Domínio e serviços lançam só subclasses de `ErroAplicacao`. Os handlers daqui convertem
essas exceções, os erros de validação do Pydantic e qualquer exceção inesperada no corpo
`{codigo, mensagem, campos?, idRequisicao}`, sempre com o `idRequisicao` da correlação.
"""

from __future__ import annotations

import math
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.nucleo.cookies import apagar_cookies
from app.nucleo.dtos import ErroCampoDTO, ErroDTO

logger = structlog.get_logger(__name__)


class CodigoErro(StrEnum):
    """Códigos estáveis do contrato. As specs acrescentam; nunca renomeiam nem removem."""

    REQUISICAO_MALFORMADA = "requisicao_malformada"
    DADOS_INVALIDOS = "dados_invalidos"
    EMAIL_EM_USO = "email_em_uso"
    CREDENCIAIS_INVALIDAS = "credenciais_invalidas"
    SENHA_ATUAL_INCORRETA = "senha_atual_incorreta"
    NAO_AUTENTICADO = "nao_autenticado"
    CSRF_INVALIDO = "csrf_invalido"
    ORIGEM_NAO_PERMITIDA = "origem_nao_permitida"
    RECURSO_NAO_ENCONTRADO = "recurso_nao_encontrado"
    MUITAS_TENTATIVAS = "muitas_tentativas"
    ERRO_INTERNO = "erro_interno"


@dataclass(frozen=True, slots=True)
class ErroCampo:
    campo: str
    mensagem: str


class ErroAplicacao(Exception):
    status: ClassVar[int] = 500
    codigo_padrao: ClassVar[CodigoErro] = CodigoErro.ERRO_INTERNO
    mensagem_padrao: ClassVar[str] = "Algo deu errado do nosso lado. Tente de novo em instantes."

    def __init__(
        self,
        mensagem: str | None = None,
        *,
        codigo: CodigoErro | None = None,
        campos: Sequence[ErroCampo] | None = None,
        cabecalhos: Mapping[str, str] | None = None,
    ) -> None:
        self.codigo = codigo or self.codigo_padrao
        self.mensagem = mensagem or self.mensagem_padrao
        self.campos = tuple(campos) if campos else ()
        self.cabecalhos = dict(cabecalhos or {})
        super().__init__(f"{self.codigo}: {self.mensagem}")


class RequisicaoMalformada(ErroAplicacao):
    status = 400
    codigo_padrao = CodigoErro.REQUISICAO_MALFORMADA
    mensagem_padrao = "A requisição não pôde ser lida."


class NaoAutenticado(ErroAplicacao):
    """401. A resposta também apaga os cookies de sessão e CSRF."""

    status = 401
    codigo_padrao = CodigoErro.NAO_AUTENTICADO
    mensagem_padrao = "Sua sessão terminou. Entre novamente."


class AcessoNegado(ErroAplicacao):
    status = 403
    codigo_padrao = CodigoErro.CSRF_INVALIDO
    mensagem_padrao = "Não foi possível confirmar a origem da requisição. Recarregue a página."


class RecursoNaoEncontrado(ErroAplicacao):
    """404 idêntico para recurso inexistente e recurso de outro estudante (DTEC 019)."""

    status = 404
    codigo_padrao = CodigoErro.RECURSO_NAO_ENCONTRADO
    mensagem_padrao = "Não encontramos o que você procurou."


class Conflito(ErroAplicacao):
    status = 409


class EntradaInvalida(ErroAplicacao):
    status = 422
    codigo_padrao = CodigoErro.DADOS_INVALIDOS
    mensagem_padrao = "Alguns campos precisam de correção."


class LimiteExcedido(ErroAplicacao):
    status = 429
    codigo_padrao = CodigoErro.MUITAS_TENTATIVAS
    mensagem_padrao = "Muitas tentativas. Tente de novo em alguns minutos."

    def __init__(self, segundos_para_tentar: float, mensagem: str | None = None) -> None:
        self.segundos_para_tentar = max(1, math.ceil(segundos_para_tentar))
        super().__init__(mensagem, cabecalhos={"Retry-After": str(self.segundos_para_tentar)})


# --- Mensagens de validação em português, por tipo de erro do Pydantic -------------------

_MENSAGENS: dict[str, str] = {
    "missing": "Campo obrigatório.",
    "extra_forbidden": "Campo não permitido.",
    "string_type": "Informe um texto.",
    "string_too_short": "Use pelo menos {min_length} caractere(s).",
    "string_too_long": "Use no máximo {max_length} caracteres.",
    "string_pattern_mismatch": "Formato inválido.",
    "int_type": "Informe um número inteiro.",
    "int_parsing": "Informe um número inteiro.",
    "int_from_float": "Informe um número inteiro.",
    "float_type": "Informe um número.",
    "float_parsing": "Informe um número.",
    "decimal_type": "Informe um número.",
    "decimal_parsing": "Informe um número.",
    "decimal_max_places": "Use no máximo {decimal_places} casa(s) decimal(is).",
    "multiple_of": "Use no máximo duas casas decimais.",
    "greater_than_equal": "Use um valor a partir de {ge}.",
    "greater_than": "Use um valor maior que {gt}.",
    "less_than_equal": "Use um valor até {le}.",
    "less_than": "Use um valor menor que {lt}.",
    "bool_type": "Informe verdadeiro ou falso.",
    "bool_parsing": "Informe verdadeiro ou falso.",
    "uuid_type": "Identificador inválido.",
    "uuid_parsing": "Identificador inválido.",
    "literal_error": "Valor não aceito.",
    "enum": "Valor não aceito.",
    "model_type": "Formato inválido.",
    "dict_type": "Formato inválido.",
    "list_type": "Informe uma lista.",
    "too_short": "Informe pelo menos {min_length} item(ns).",
    "too_long": "Informe no máximo {max_length} item(ns).",
}
_MENSAGEM_GENERICA = "Valor inválido."
MENSAGEM_CORPO_GRANDE = "A requisição é grande demais."


def _formatar_numero(valor: object) -> str:
    if isinstance(valor, float):
        return f"{valor:g}".replace(".", ",")
    return str(valor)


def mensagem_validacao(erro: Mapping[str, Any]) -> str:
    tipo = str(erro.get("type", ""))
    contexto: Mapping[str, Any] = erro.get("ctx") or {}
    if tipo in {"value_error", "assertion_error"} and "error" in contexto:
        # Regras de domínio levantam ValueError já em português.
        return str(contexto["error"])
    modelo = _MENSAGENS.get(tipo)
    if modelo is None:
        return _MENSAGEM_GENERICA
    try:
        return modelo.format(**{chave: _formatar_numero(v) for chave, v in contexto.items()})
    except (KeyError, IndexError):
        return _MENSAGEM_GENERICA


def _corpo_ilegivel(erros: Iterable[Mapping[str, Any]]) -> bool:
    """JSON inválido, corpo ausente ou que não é objeto: a requisição não pôde ser lida."""
    return any(
        erro.get("type") == "json_invalid" or tuple(erro.get("loc", ())) == ("body",)
        for erro in erros
    )


def campos_de_validacao(erros: Iterable[Mapping[str, Any]]) -> list[ErroCampo]:
    """Uma mensagem por campo (a primeira), com o nome em camelCase como no corpo enviado."""
    vistos: set[str] = set()
    campos: list[ErroCampo] = []
    for erro in erros:
        nome = ".".join(str(parte) for parte in tuple(erro.get("loc", ()))[1:])
        if nome in vistos:
            continue
        vistos.add(nome)
        campos.append(ErroCampo(nome, mensagem_validacao(erro)))
    return campos


# --- Respostas -------------------------------------------------------------------------


def id_requisicao_de(escopo: Scope) -> uuid.UUID:
    estado = escopo.get("state") or {}
    valor = estado.get("id_requisicao")
    return valor if isinstance(valor, uuid.UUID) else uuid.uuid4()


def resposta_erro(escopo: Scope, erro: ErroAplicacao, status: int | None = None) -> JSONResponse:
    corpo = ErroDTO(
        codigo=erro.codigo,
        mensagem=erro.mensagem,
        campos=[ErroCampoDTO(campo=c.campo, mensagem=c.mensagem) for c in erro.campos] or None,
        id_requisicao=id_requisicao_de(escopo),
    )
    return JSONResponse(
        corpo.model_dump(mode="json", exclude_none=True),
        status_code=status or erro.status,
        headers=erro.cabecalhos,
    )


async def _tratar_erro_aplicacao(request: Request, exc: Exception) -> Response:
    if not isinstance(exc, ErroAplicacao):  # registrado só para este tipo
        raise exc
    resposta = resposta_erro(request.scope, exc)
    configuracao = getattr(request.app.state, "configuracao", None)
    if isinstance(exc, NaoAutenticado) and configuracao is not None:
        apagar_cookies(resposta, configuracao)
    return resposta


async def _tratar_validacao(request: Request, exc: Exception) -> Response:
    if not isinstance(exc, RequestValidationError):  # registrado só para este tipo
        raise exc
    erros = exc.errors()
    if _corpo_ilegivel(erros):
        return resposta_erro(request.scope, RequisicaoMalformada())
    return resposta_erro(request.scope, EntradaInvalida(campos=campos_de_validacao(erros)))


async def _tratar_http(request: Request, exc: Exception) -> Response:
    if not isinstance(exc, StarletteHTTPException):  # registrado só para este tipo
        raise exc
    erro: ErroAplicacao
    if exc.status_code == 404:
        erro = RecursoNaoEncontrado(cabecalhos=exc.headers)
    elif exc.status_code == 413:
        erro = RequisicaoMalformada(MENSAGEM_CORPO_GRANDE)
    else:
        erro = RequisicaoMalformada(cabecalhos=exc.headers)
    return resposta_erro(request.scope, erro, status=exc.status_code)


def registrar_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ErroAplicacao, _tratar_erro_aplicacao)
    app.add_exception_handler(RequestValidationError, _tratar_validacao)
    app.add_exception_handler(StarletteHTTPException, _tratar_http)


class MiddlewareErrosInesperados:
    """Converte qualquer exceção não tratada em `500 erro_interno`, sem detalhes no corpo.

    Fica dentro dos middlewares de correlação e de cabeçalhos, para que a resposta 500
    também tenha `X-Request-ID` e os cabeçalhos de segurança. A pilha vai só para o log.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        resposta_iniciada = False

        async def enviar(mensagem: Message) -> None:
            nonlocal resposta_iniciada
            if mensagem["type"] == "http.response.start":
                resposta_iniciada = True
            await send(mensagem)

        try:
            await self.app(scope, receive, enviar)
        except Exception:
            logger.exception("erro_inesperado")
            if resposta_iniciada:
                raise
            await resposta_erro(scope, ErroAplicacao())(scope, receive, send)
