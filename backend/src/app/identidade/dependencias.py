"""Dependências do FastAPI da identidade: serviço, contexto da requisição e `UsuarioAtual`."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.identidade.servicos import ContextoRequisicao, ServicoIdentidade, UsuarioAutenticado
from app.nucleo.configuracao import Configuracao
from app.nucleo.rede import endereco_cliente


def obter_configuracao(request: Request) -> Configuracao:
    configuracao: Configuracao = request.app.state.configuracao
    return configuracao


def obter_servico(request: Request) -> ServicoIdentidade:
    servico: ServicoIdentidade = request.app.state.identidade
    return servico


def obter_contexto(request: Request) -> ContextoRequisicao:
    configuracao = obter_configuracao(request)
    ip = endereco_cliente(request.scope, configuracao.proxies_confiaveis)
    return ContextoRequisicao(ip=str(ip), agente_usuario=request.headers.get("user-agent"))


async def usuario_atual(request: Request) -> UsuarioAutenticado:
    """Autentica pelo cookie de sessão; sem sessão válida, `401` sem dados do recurso."""
    configuracao = obter_configuracao(request)
    return await obter_servico(request).autenticar(
        request.cookies.get(configuracao.cookie_sessao_nome)
    )


UsuarioAtual = Annotated[UsuarioAutenticado, Depends(usuario_atual)]
Servico = Annotated[ServicoIdentidade, Depends(obter_servico)]
Configuracoes = Annotated[Configuracao, Depends(obter_configuracao)]
Contexto = Annotated[ContextoRequisicao, Depends(obter_contexto)]
