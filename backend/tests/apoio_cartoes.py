"""Apoio aos testes da spec 003: semear estudante, matéria, fonte e cartões direto no banco.

Os cartões vêm de `tests/fabricas_cartoes.py` (nada real, regra 10). Os atalhos HTTP usam o
cliente com cookies e CSRF de `tests/apoio_http.py`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cartoes.modelos import Cartao
from app.fontes.modelos import Fonte
from app.identidade.modelos import Usuario
from app.identidade.repositorios import RepositorioUsuarios
from app.materias.modelos import Materia
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho

AGORA = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


async def semear_estudante(
    sessao: AsyncSession, *, email: str | None = None, materia: str = "Biologia"
) -> tuple[Usuario, Materia]:
    """Um estudante fictício (`@exemplo.com`) com uma matéria."""
    usuario = await RepositorioUsuarios(sessao).criar(
        nome="Estudante Teste",
        email=email or f"cartoes.{uuid.uuid4().hex[:8]}@exemplo.com",
        senha_hash="hash-ficticio",
        fuso="America/Recife",
        agora=AGORA,
    )
    nova = Materia(usuario_id=usuario.id, nome=materia, criado_em=AGORA, atualizado_em=AGORA)
    sessao.add(nova)
    await sessao.flush()
    return usuario, nova


async def semear_materia(sessao: AsyncSession, usuario_id: int, nome: str) -> Materia:
    materia = Materia(usuario_id=usuario_id, nome=nome, criado_em=AGORA, atualizado_em=AGORA)
    sessao.add(materia)
    await sessao.flush()
    return materia


async def semear_fonte(
    sessao: AsyncSession,
    usuario_id: int,
    materia_id: int,
    *,
    titulo: str = "Citologia",
    nome_arquivo: str = "citologia.pdf",
    estado: str = "concluido",
) -> Fonte:
    """Uma fonte sem objeto no armazenamento (basta para a referência dos cartões)."""
    concluida = estado == "concluido"
    fonte = Fonte(
        usuario_id=usuario_id,
        materia_id=materia_id,
        titulo=titulo,
        nome_arquivo=nome_arquivo,
        chave_objeto=f"usuarios/teste/fontes/{uuid.uuid4()}",
        tipo_midia="application/pdf",
        tamanho_bytes=100,
        hash_sha256=uuid.uuid4().bytes * 2,
        estado=estado,
        codigo_falha="sem_texto" if estado == "falhou" else None,
        total_trechos=3 if concluida else None,
        versao_extracao="v2" if concluida else None,
        criado_em=datetime(2026, 10, 1, 9, 30, tzinfo=UTC),
    )
    sessao.add(fonte)
    await sessao.flush()
    return fonte


async def cartoes_da_materia(fabrica: FabricaSessoes, materia_id: int) -> list[Cartao]:
    """Todos os cartões da matéria, do mais antigo ao mais recente, lidos numa transação nova."""
    async with unidade_de_trabalho(fabrica) as sessao:
        consulta = select(Cartao).where(Cartao.materia_id == materia_id).order_by(Cartao.id)
        return list((await sessao.execute(consulta)).scalars())


# --- HTTP -------------------------------------------------------------------------------------


async def criar_cartao(cliente: httpx.AsyncClient, materia_id: str, **corpo: Any) -> httpx.Response:
    """`POST /materias/{id}/cartoes` com frente e verso padrão, que o `corpo` sobrescreve."""
    padrao = {"frente": "Qual organela produz ATP?", "verso": "Mitocôndria"}
    return await cliente.post(f"/api/v1/materias/{materia_id}/cartoes", json={**padrao, **corpo})


def ajustar_limites_cartoes(aplicacao: Any, **alteracoes: Any) -> None:
    """Troca limites da configuração do serviço de cartões de uma aplicação já criada."""
    nova = aplicacao.state.configuracao.model_copy(update=alteracoes)
    aplicacao.state.cartoes._configuracao = nova
    aplicacao.state.configuracao = nova


async def semear_na_materia(
    fabrica: FabricaSessoes, materia_public_id: str, itens: Any
) -> list[str]:
    """Insere cartões da fábrica (`CartaoFicticio`) na matéria de quem a criou pela API.

    Serve para o que a API da 003 não cria: cartões `gerado_verificado` (só a 004 os cria) e
    cartões já revisados, em estados do FSRS diferentes do novo.
    """
    from tests.fabricas_cartoes import inserir

    async with unidade_de_trabalho(fabrica) as sessao:
        materia = (
            await sessao.execute(
                select(Materia).where(Materia.public_id == uuid.UUID(materia_public_id))
            )
        ).scalar_one()
        cartoes = await inserir(
            sessao,
            usuario_id=materia.usuario_id,
            materia_id=materia.id,
            itens=list(itens),
            agora=AGORA,
        )
        return [str(c.public_id) for c in cartoes]


async def estado_fsrs(fabrica: FabricaSessoes, cartao_public_id: str) -> tuple[Any, ...]:
    """As seis colunas do FSRS do cartão, para conferir que não mudaram (CS-002)."""
    async with unidade_de_trabalho(fabrica) as sessao:
        cartao = (
            await sessao.execute(
                select(Cartao).where(Cartao.public_id == uuid.UUID(cartao_public_id))
            )
        ).scalar_one()
        return (
            cartao.estado_fsrs,
            cartao.passo,
            cartao.estabilidade,
            cartao.dificuldade,
            cartao.vencimento,
            cartao.ultima_revisao,
        )
