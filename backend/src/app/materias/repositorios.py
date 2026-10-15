"""Consultas das matérias. Todo método de recurso de estudante recebe `usuario_id` (DTEC 019)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.materias.excecoes import MateriaNomeEmUso
from app.materias.modelos import Materia
from app.nucleo.dono import buscar_do_dono

INDICE_NOME = "materias_nome_unico_por_usuario"


class RepositorioMaterias:
    def __init__(self, sessao: AsyncSession) -> None:
        self._sessao = sessao

    async def travar_acervo(self, usuario_id: int) -> None:
        """`pg_advisory_xact_lock` do acervo do estudante, até o fim da transação (DTEC 032).

        Serializa só as operações de cota do mesmo estudante (criar matéria, enviar fonte), num
        espaço de chaves próprio, sem disputar a linha do usuário com a 001.
        """
        await self._sessao.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:chave, 0))"),
            {"chave": f"acervo:{usuario_id}"},
        )

    async def contar(self, usuario_id: int) -> int:
        consulta = select(func.count()).select_from(Materia).where(Materia.usuario_id == usuario_id)
        return int((await self._sessao.execute(consulta)).scalar_one())

    async def criar(self, usuario_id: int, nome: str, agora: datetime) -> Materia:
        """Insere a matéria; a corrida entre dois nomes iguais é resolvida pelo índice único."""
        materia = Materia(usuario_id=usuario_id, nome=nome, criado_em=agora, atualizado_em=agora)
        try:
            # Savepoint: a violação desfaz só a inserção e a transação segue utilizável.
            async with self._sessao.begin_nested():
                self._sessao.add(materia)
                await self._sessao.flush()
        except IntegrityError as erro:
            if getattr(getattr(erro.orig, "diag", None), "constraint_name", None) == INDICE_NOME:
                raise MateriaNomeEmUso() from erro
            raise
        return materia

    async def renomear(self, materia: Materia, nome: str, agora: datetime) -> None:
        """Troca o nome; o índice único decide a corrida entre dois nomes iguais (RF-001)."""
        try:
            # Savepoint: a violação desfaz só a alteração e a transação segue utilizável.
            async with self._sessao.begin_nested():
                materia.nome = nome
                materia.atualizado_em = agora
                await self._sessao.flush()
        except IntegrityError as erro:
            if getattr(getattr(erro.orig, "diag", None), "constraint_name", None) == INDICE_NOME:
                raise MateriaNomeEmUso() from erro
            raise

    async def apagar(self, usuario_id: int, materia_id: int) -> None:
        """Apaga a matéria; quem a chama já apagou as fontes e os cartões (FKs `restrict`)."""
        await self._sessao.execute(
            delete(Materia).where(Materia.id == materia_id, Materia.usuario_id == usuario_id)
        )

    async def listar(self, usuario_id: int) -> list[Materia]:
        """Ordenadas por nome, sem diferenciar maiúsculas e minúsculas (sem paginação)."""
        consulta = (
            select(Materia)
            .where(Materia.usuario_id == usuario_id)
            .order_by(func.lower(Materia.nome), Materia.id)
        )
        return list((await self._sessao.execute(consulta)).scalars())

    async def buscar(
        self, usuario_id: int, public_id: UUID, *, para_atualizar: bool = False
    ) -> Materia:
        """A matéria do estudante, ou `404` idêntico ao de inexistente (DTEC 019)."""
        return await buscar_do_dono(
            self._sessao, Materia, public_id, usuario_id, para_atualizar=para_atualizar
        )
