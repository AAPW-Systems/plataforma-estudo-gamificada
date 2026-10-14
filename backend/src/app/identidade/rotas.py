"""Rotas HTTP da identidade (T036): CSRF, cadastro, entrada, saída e consulta do perfil."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request, Response

from app.identidade.dependencias import Configuracoes, Contexto, Servico, UsuarioAtual
from app.identidade.dtos import CadastroEntradaDTO, EntradaEntradaDTO, PerfilDTO
from app.identidade.mapeadores import perfil_para_dto
from app.identidade.servicos import SessaoIniciada
from app.nucleo.configuracao import Configuracao
from app.nucleo.cookies import apagar_cookies, definir_cookie_csrf, definir_cookie_sessao
from app.nucleo.dtos import ErroDTO
from app.nucleo.seguranca.csrf import emitir_token, vinculo_da_sessao, vinculo_dos_cookies
from app.nucleo.seguranca.sessoes import hash_token

roteador = APIRouter(prefix="/api/v1")

_ERRO: dict[str, Any] = {"model": ErroDTO}
_RESPOSTAS_CSRF: dict[int | str, dict[str, Any]] = {400: _ERRO, 403: _ERRO}


def _iniciar_sessao(resposta: Response, configuracao: Configuracao, sessao: SessaoIniciada) -> None:
    """Cookie da sessão e um novo token anti-CSRF ligado a ela (DTEC 023)."""
    definir_cookie_sessao(resposta, configuracao, sessao.token)
    vinculo = vinculo_da_sessao(hash_token(sessao.token))
    definir_cookie_csrf(resposta, configuracao, emitir_token(configuracao.segredo, vinculo))


@roteador.get(
    "/auth/csrf",
    status_code=204,
    operation_id="obterTokenCsrf",
    tags=["autenticacao"],
    response_class=Response,
)
async def obter_token_csrf(request: Request, configuracao: Configuracoes) -> Response:
    """Emite o token anti-CSRF, ligado à sessão atual ou, sem sessão, à pré-sessão."""
    vinculo = vinculo_dos_cookies(request.cookies, configuracao.cookie_sessao_nome)
    resposta = Response(status_code=204)
    definir_cookie_csrf(resposta, configuracao, emitir_token(configuracao.segredo, vinculo))
    return resposta


@roteador.post(
    "/auth/cadastro",
    status_code=201,
    operation_id="cadastrar",
    tags=["autenticacao"],
    responses={**_RESPOSTAS_CSRF, 409: _ERRO, 422: _ERRO, 429: _ERRO},
)
async def cadastrar(
    entrada: CadastroEntradaDTO,
    resposta: Response,
    servico: Servico,
    configuracao: Configuracoes,
    contexto: Contexto,
) -> PerfilDTO:
    sessao = await servico.cadastrar(
        nome=entrada.nome,
        email=entrada.email,
        senha=entrada.senha,
        fuso=entrada.fuso,
        contexto=contexto,
    )
    _iniciar_sessao(resposta, configuracao, sessao)
    return perfil_para_dto(sessao.perfil)


@roteador.post(
    "/auth/entrada",
    operation_id="entrar",
    tags=["autenticacao"],
    responses={**_RESPOSTAS_CSRF, 401: _ERRO, 422: _ERRO, 429: _ERRO},
)
async def entrar(
    entrada: EntradaEntradaDTO,
    resposta: Response,
    servico: Servico,
    configuracao: Configuracoes,
    contexto: Contexto,
) -> PerfilDTO:
    sessao = await servico.entrar(email=entrada.email, senha=entrada.senha, contexto=contexto)
    _iniciar_sessao(resposta, configuracao, sessao)
    return perfil_para_dto(sessao.perfil)


@roteador.post(
    "/auth/saida",
    status_code=204,
    operation_id="sair",
    tags=["autenticacao"],
    response_class=Response,
    responses={403: _ERRO},
)
async def sair(request: Request, servico: Servico, configuracao: Configuracoes) -> Response:
    await servico.sair(request.cookies.get(configuracao.cookie_sessao_nome))
    resposta = Response(status_code=204)
    apagar_cookies(resposta, configuracao)
    return resposta


@roteador.get("/perfil", operation_id="obterPerfil", tags=["perfil"], responses={401: _ERRO})
async def obter_perfil(atual: UsuarioAtual, servico: Servico) -> PerfilDTO:
    return perfil_para_dto(await servico.consultar_perfil(atual.usuario.id))
