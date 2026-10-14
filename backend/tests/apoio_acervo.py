"""Apoio aos testes da spec 002: semear dados, enviar arquivos e acompanhar fontes.

Os arquivos vêm de `tests/fabricas_arquivos.py` (nada real, regra 10). Os atalhos HTTP usam o
cliente com cookies e CSRF de `tests/apoio_http.py`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select

from app.fontes.modelos import Fonte
from app.identidade.modelos import Usuario
from app.identidade.repositorios import RepositorioUsuarios
from app.materias.modelos import Materia
from app.nucleo.armazenamento import Armazenamento
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from tests.apoio_http import cadastrar
from tests.fabricas import DadosConta, dados_conta
from tests.fabricas_arquivos import ArquivoGerado

TIPOS = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
}


def tipo_do_nome(nome: str) -> str:
    return TIPOS[Path(nome).suffix.lower()]


# --- HTTP -------------------------------------------------------------------------------------


async def criar_conta(cliente: httpx.AsyncClient) -> DadosConta:
    conta = dados_conta()
    resposta = await cadastrar(cliente, conta)
    assert resposta.status_code == 201, resposta.text
    return conta


async def criar_materia(cliente: httpx.AsyncClient, nome: str = "Biologia") -> dict[str, Any]:
    resposta = await cliente.post("/api/v1/materias", json={"nome": nome})
    assert resposta.status_code == 201, resposta.text
    corpo: dict[str, Any] = resposta.json()
    return corpo


async def enviar(
    cliente: httpx.AsyncClient,
    materia_id: str,
    arquivo: ArquivoGerado | tuple[str, bytes],
    *,
    titulo: str | None = None,
) -> httpx.Response:
    nome, conteudo = (
        (arquivo.nome, arquivo.conteudo) if isinstance(arquivo, ArquivoGerado) else arquivo
    )
    return await cliente.post(
        f"/api/v1/materias/{materia_id}/fontes",
        files={"arquivo": (nome, conteudo, "application/octet-stream")},
        data={"titulo": titulo} if titulo is not None else None,
    )


async def consultar_fonte(cliente: httpx.AsyncClient, fonte_id: str) -> dict[str, Any]:
    resposta = await cliente.get(f"/api/v1/fontes/{fonte_id}")
    assert resposta.status_code == 200, resposta.text
    corpo: dict[str, Any] = resposta.json()
    return corpo


# --- Banco ------------------------------------------------------------------------------------


async def semear_fonte(
    fabrica: FabricaSessoes,
    armazenamento: Armazenamento,
    arquivo: ArquivoGerado,
    *,
    estado: str = "pendente",
    titulo: str = "Fonte de teste",
    sufixo: str | None = None,
) -> tuple[Usuario, Materia, Fonte]:
    """Cria usuário, matéria e uma fonte com o objeto já no armazenamento (sem passar pela API)."""
    sufixo = sufixo or uuid.uuid4().hex[:8]
    agora = datetime.now(UTC)
    async with unidade_de_trabalho(fabrica) as sessao:
        usuario = await RepositorioUsuarios(sessao).criar(
            nome="Estudante Teste",
            email=f"semeado.{sufixo}@exemplo.com",
            senha_hash="hash-ficticio",
            fuso="America/Recife",
            agora=agora,
        )
        materia = Materia(usuario_id=usuario.id, nome="Biologia")
        sessao.add(materia)
        await sessao.flush()
        chave = f"usuarios/{usuario.public_id}/fontes/{uuid.uuid4()}"
        fonte = Fonte(
            usuario_id=usuario.id,
            materia_id=materia.id,
            titulo=titulo,
            nome_arquivo=arquivo.nome,
            chave_objeto=chave,
            tipo_midia=tipo_do_nome(arquivo.nome),
            tamanho_bytes=len(arquivo.conteudo),
            hash_sha256=bytes(32),
            estado=estado,
        )
        sessao.add(fonte)
        await sessao.flush()
    await _guardar(armazenamento, chave, arquivo.conteudo)
    return usuario, materia, fonte


async def _guardar(armazenamento: Armazenamento, chave: str, conteudo: bytes) -> None:
    import tempfile

    with tempfile.NamedTemporaryFile() as temporario:
        temporario.write(conteudo)
        temporario.flush()
        await armazenamento.gravar(chave, Path(temporario.name))


async def recarregar_fonte(fabrica: FabricaSessoes, fonte_id: int) -> Fonte | None:
    async with unidade_de_trabalho(fabrica) as sessao:
        return (
            await sessao.execute(select(Fonte).where(Fonte.id == fonte_id))
        ).scalar_one_or_none()


def ajustar_limites(aplicacao: Any, **alteracoes: Any) -> None:
    """Troca limites da configuração dos serviços de uma aplicação já criada (cotas, tamanhos)."""
    nova = aplicacao.state.configuracao.model_copy(update=alteracoes)
    aplicacao.state.materias._configuracao = nova
    aplicacao.state.fontes._configuracao = nova
    aplicacao.state.configuracao = nova


async def trechos_da_fonte(fabrica: FabricaSessoes, fonte_public_id: str) -> list[Any]:
    """Os trechos de uma fonte, na ordem do texto (para conferir páginas e conteúdo)."""
    from app.fontes.modelos import Trecho

    async with unidade_de_trabalho(fabrica) as sessao:
        consulta = (
            select(Trecho)
            .join(Fonte, Fonte.id == Trecho.fonte_id)
            .where(Fonte.public_id == uuid.UUID(fonte_public_id))
            .order_by(Trecho.ordem)
        )
        return list((await sessao.execute(consulta)).scalars())


async def chave_da_fonte(fabrica: FabricaSessoes, fonte_public_id: str) -> str:
    """A chave do objeto da fonte no armazenamento."""
    async with unidade_de_trabalho(fabrica) as sessao:
        consulta = select(Fonte.chave_objeto).where(Fonte.public_id == uuid.UUID(fonte_public_id))
        return (await sessao.execute(consulta)).scalar_one()


async def id_interno_da_fonte(fabrica: FabricaSessoes, fonte_public_id: str) -> int:
    """O `id` interno da fonte, que os participantes da exclusão recebem."""
    async with unidade_de_trabalho(fabrica) as sessao:
        consulta = select(Fonte.id).where(Fonte.public_id == uuid.UUID(fonte_public_id))
        return (await sessao.execute(consulta)).scalar_one()


async def contar_linhas_da_fonte(fabrica: FabricaSessoes, fonte_id: int) -> tuple[int, int]:
    """Quantas linhas de `fontes` e de `trechos` existem para o `id` interno."""
    from sqlalchemy import func

    from app.fontes.modelos import Trecho

    async with unidade_de_trabalho(fabrica) as sessao:
        fontes = (
            await sessao.execute(
                select(func.count()).select_from(Fonte).where(Fonte.id == fonte_id)
            )
        ).scalar_one()
        trechos = (
            await sessao.execute(
                select(func.count()).select_from(Trecho).where(Trecho.fonte_id == fonte_id)
            )
        ).scalar_one()
    return int(fontes), int(trechos)
