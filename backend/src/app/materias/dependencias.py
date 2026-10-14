"""Dependência do FastAPI das matérias: o serviço guardado em `app.state`."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.materias.servicos import ServicoMaterias


def obter_servico(request: Request) -> ServicoMaterias:
    servico: ServicoMaterias = request.app.state.materias
    return servico


Servico = Annotated[ServicoMaterias, Depends(obter_servico)]
