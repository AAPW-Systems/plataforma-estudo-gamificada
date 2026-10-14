from fastapi import APIRouter, Request, Response

from app.saude.dtos import Saude
from app.saude.servicos import verificar_prontidao

roteador = APIRouter(tags=["saude"])


@roteador.get("/health", operation_id="verificarProcesso", response_model_exclude_none=True)
async def verificar_processo() -> Saude:
    return Saude(estado="ok")


@roteador.get("/health/ready", operation_id="verificarProntidao", responses={503: {"model": Saude}})
async def prontidao(request: Request, response: Response) -> Saude:
    verificacoes = await verificar_prontidao(
        request.app.state.fabrica_sessoes, request.app.state.armazenamento
    )
    disponivel = all(v == "ok" for v in verificacoes.values())
    response.status_code = 200 if disponivel else 503
    return Saude(estado="ok" if disponivel else "indisponivel", verificacoes=verificacoes)
