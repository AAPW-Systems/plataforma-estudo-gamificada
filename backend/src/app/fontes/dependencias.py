"""Dependência do FastAPI das fontes: o serviço guardado em `app.state`."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.fontes.servicos import ServicoFontes


def obter_servico(request: Request) -> ServicoFontes:
    servico: ServicoFontes = request.app.state.fontes
    return servico


Servico = Annotated[ServicoFontes, Depends(obter_servico)]
