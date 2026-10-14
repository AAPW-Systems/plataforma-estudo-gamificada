"""Rotas HTTP das fontes (spec 002): acervo, envio, consulta e nova tentativa."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Form, Path, Request, UploadFile
from pydantic import ConfigDict, Field

from app.fontes.dependencias import Servico
from app.fontes.dominio import TITULO_MAXIMO
from app.fontes.dtos import FonteDTO, ListaFontesDTO, UsoAcervoDTO
from app.fontes.mapeadores import fonte_para_dto, fontes_para_dto
from app.identidade.dependencias import UsuarioAtual
from app.nucleo.dtos import EntradaDTO, ErroDTO
from app.nucleo.erros import EntradaInvalida, ErroCampo

roteador = APIRouter(prefix="/api/v1")

_ERRO: dict[str, Any] = {"model": ErroDTO}
# Os caminhos públicos são camelCase (`{materiaId}`, `{fonteId}`), como no contrato.
MateriaId = Annotated[UUID, Path(alias="materiaId", description="`public_id` da matéria")]
FonteId = Annotated[UUID, Path(alias="fonteId", description="`public_id` da fonte")]
_RESPOSTAS_CSRF: dict[int | str, dict[str, Any]] = {400: _ERRO, 403: _ERRO}


class EnvioFonteEntradaDTO(EntradaDTO):
    """Corpo *multipart* do envio: um arquivo e, opcionalmente, o título.

    Fica aqui, e não em `dtos.py`, porque `UploadFile` é um tipo do FastAPI (a camada de DTOs
    não importa o framework, DTEC 018): o formulário é um detalhe de transporte do controlador.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    arquivo: UploadFile = Field(
        json_schema_extra={
            "format": "binary",
            "description": "Um único arquivo .pdf, .txt, .md ou .markdown",
        }
    )
    titulo: str | None = Field(
        default=None, json_schema_extra={"minLength": 1, "maxLength": TITULO_MAXIMO}
    )


@roteador.get(
    "/acervo/uso", operation_id="consultarUsoAcervo", tags=["acervo"], responses={401: _ERRO}
)
async def consultar_uso_acervo(atual: UsuarioAtual, servico: Servico) -> UsoAcervoDTO:
    uso = await servico.uso_do_acervo(atual.usuario.id)
    return UsoAcervoDTO(
        tamanho_maximo_bytes=uso.tamanho_maximo_bytes,
        extensoes_aceitas=list(uso.extensoes_aceitas),
        paginas_maximas_pdf=uso.paginas_maximas_pdf,
        cota_materias=uso.cota_materias,
        total_materias=uso.total_materias,
        cota_fontes_por_materia=uso.cota_fontes_por_materia,
        cota_armazenamento_bytes=uso.cota_armazenamento_bytes,
        uso_armazenamento_bytes=uso.uso_armazenamento_bytes,
    )


@roteador.get(
    "/materias/{materiaId}/fontes",
    operation_id="listarFontes",
    tags=["fontes"],
    responses={401: _ERRO, 404: _ERRO},
)
async def listar_fontes(
    materia_id: MateriaId, atual: UsuarioAtual, servico: Servico
) -> ListaFontesDTO:
    consultadas = await servico.listar(atual.usuario.id, materia_id)
    return fontes_para_dto([c.fonte for c in consultadas], materia_id)


@roteador.post(
    "/materias/{materiaId}/fontes",
    status_code=201,
    operation_id="enviarFonte",
    tags=["fontes"],
    responses={
        **_RESPOSTAS_CSRF,
        401: _ERRO,
        404: _ERRO,
        409: _ERRO,
        413: _ERRO,
        422: _ERRO,
    },
)
async def enviar_fonte(
    materia_id: MateriaId,
    entrada: Annotated[EnvioFonteEntradaDTO, Form(media_type="multipart/form-data")],
    request: Request,
    atual: UsuarioAtual,
    servico: Servico,
) -> FonteDTO:
    # O modelo de formulário fica com a última parte de nome repetido: aqui se exige uma só.
    formulario = await request.form()
    if len(formulario.getlist("arquivo")) != 1:
        raise EntradaInvalida(campos=[ErroCampo("arquivo", "Envie um arquivo por vez.")])
    consultada = await servico.enviar(
        usuario_id=atual.usuario.id,
        usuario_public_id=atual.usuario.public_id,
        materia_id=materia_id,
        nome_enviado=entrada.arquivo.filename or "",
        origem=entrada.arquivo.file,
        titulo=entrada.titulo,
    )
    return fonte_para_dto(consultada.fonte, consultada.materia_public_id)


@roteador.get(
    "/fontes/{fonteId}",
    operation_id="consultarFonte",
    tags=["fontes"],
    responses={401: _ERRO, 404: _ERRO},
)
async def consultar_fonte(fonte_id: FonteId, atual: UsuarioAtual, servico: Servico) -> FonteDTO:
    consultada = await servico.consultar(atual.usuario.id, fonte_id)
    return fonte_para_dto(consultada.fonte, consultada.materia_public_id)


@roteador.post(
    "/fontes/{fonteId}/reprocessamento",
    status_code=202,
    operation_id="reprocessarFonte",
    tags=["fontes"],
    responses={**_RESPOSTAS_CSRF, 401: _ERRO, 404: _ERRO, 409: _ERRO},
)
async def reprocessar_fonte(fonte_id: FonteId, atual: UsuarioAtual, servico: Servico) -> FonteDTO:
    consultada = await servico.reprocessar(atual.usuario.id, fonte_id)
    return fonte_para_dto(consultada.fonte, consultada.materia_public_id)
