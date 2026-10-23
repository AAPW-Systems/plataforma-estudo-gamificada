"""Dependência do FastAPI dos cartões: o serviço guardado em `app.state`."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.cartoes.servicos import ServicoCartoes


def obter_servico(request: Request) -> ServicoCartoes:
    servico: ServicoCartoes = request.app.state.cartoes
    return servico


Servico = Annotated[ServicoCartoes, Depends(obter_servico)]
