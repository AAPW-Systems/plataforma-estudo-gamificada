"""Consultas das fontes e dos trechos. Todo método de recurso de estudante recebe `usuario_id`."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.fontes.divisao import TrechoDividido
from app.fontes.excecoes import FonteDuplicada
from app.fontes.modelos import Fonte, Trecho
from app.materias.modelos import Materia
from app.nucleo.dono import buscar_do_dono
from app.nucleo.erros import RecursoNaoEncontrado

INDICE_CONTEUDO = "fontes_conteudo_unico_por_materia"
RESTRICAO_MATERIA = "fontes_materia_id_fkey"
LOTE_DE_TRECHOS = 500


class RepositorioFontes:
    def __init__(self, sessao: AsyncSession) -> None:
        self._sessao = sessao

    # --- Cotas e duplicatas ---------------------------------------------------------------------

    async def somar_tamanho(self, usuario_id: int) -> int:
        """Soma dos tamanhos de **todas** as fontes do estudante, inclusive as com `falhou`."""
        consulta = select(func.coalesce(func.sum(Fonte.tamanho_bytes), 0)).where(
            Fonte.usuario_id == usuario_id
        )
        return int((await self._sessao.execute(consulta)).scalar_one())

    async def contar_da_materia(self, materia_id: int, usuario_id: int) -> int:
        consulta = (
            select(func.count())
            .select_from(Fonte)
            .where(Fonte.materia_id == materia_id, Fonte.usuario_id == usuario_id)
        )
        return int((await self._sessao.execute(consulta)).scalar_one())

    async def titulo_do_conteudo(
        self, materia_id: int, usuario_id: int, hash_sha256: bytes
    ) -> str | None:
        consulta = select(Fonte.titulo).where(
            Fonte.materia_id == materia_id,
            Fonte.usuario_id == usuario_id,
            Fonte.hash_sha256 == hash_sha256,
        )
        return (await self._sessao.execute(consulta)).scalar_one_or_none()

    # --- Escrita --------------------------------------------------------------------------------

    async def inserir(self, fonte: Fonte) -> Fonte:
        """Insere a fonte; o índice único decide a corrida de duas cópias do mesmo conteúdo."""
        try:
            # Savepoint: a violação desfaz só a inserção e a transação segue utilizável.
            async with self._sessao.begin_nested():
                self._sessao.add(fonte)
                await self._sessao.flush()
        except IntegrityError as erro:
            restricao = getattr(getattr(erro.orig, "diag", None), "constraint_name", None)
            if restricao == INDICE_CONTEUDO:
                raise FonteDuplicada() from erro
            if restricao == RESTRICAO_MATERIA:
                # A matéria foi excluída entre a conferência e a inserção (DTEC 032).
                raise RecursoNaoEncontrado() from erro
            raise
        return fonte

    async def apagar_trechos(self, fonte_id: int) -> None:
        await self._sessao.execute(delete(Trecho).where(Trecho.fonte_id == fonte_id))

    async def inserir_trechos(self, fonte_id: int, trechos: Sequence[TrechoDividido]) -> None:
        """Insere em lotes (DTEC 029); a ordem do texto vira `ordem`, contígua a partir de 0."""
        for inicio in range(0, len(trechos), LOTE_DE_TRECHOS):
            lote = trechos[inicio : inicio + LOTE_DE_TRECHOS]
            await self._sessao.execute(
                insert(Trecho),
                [
                    {
                        "fonte_id": fonte_id,
                        "ordem": t.ordem,
                        "texto": t.texto,
                        "pagina": t.pagina,
                        "inicio_caractere": t.inicio,
                        "fim_caractere": t.fim,
                    }
                    for t in lote
                ],
            )

    async def contar_trechos(self, fonte_id: int) -> int:
        consulta = select(func.count()).select_from(Trecho).where(Trecho.fonte_id == fonte_id)
        return int((await self._sessao.execute(consulta)).scalar_one())

    # --- Leitura --------------------------------------------------------------------------------

    async def listar_da_materia(self, usuario_id: int, materia_id: int) -> list[Fonte]:
        """Da mais recente para a mais antiga (sem paginação: a cota é de 30 por matéria)."""
        consulta = (
            select(Fonte)
            .where(Fonte.usuario_id == usuario_id, Fonte.materia_id == materia_id)
            .order_by(Fonte.criado_em.desc(), Fonte.id.desc())
        )
        return list((await self._sessao.execute(consulta)).scalars())

    async def buscar(
        self, usuario_id: int, public_id: UUID, *, para_atualizar: bool = False
    ) -> Fonte:
        """A fonte do estudante, ou `404` idêntico ao de inexistente (DTEC 019)."""
        return await buscar_do_dono(
            self._sessao, Fonte, public_id, usuario_id, para_atualizar=para_atualizar
        )

    async def bloquear_por_id(self, fonte_id: int) -> Fonte | None:
        """Para o worker: trava a fonte pelo id interno (`FOR UPDATE`), se ainda existir."""
        consulta = select(Fonte).where(Fonte.id == fonte_id).with_for_update()
        return (await self._sessao.execute(consulta)).scalar_one_or_none()

    async def materia_publica(self, fonte: Fonte) -> UUID:
        consulta = select(Materia.public_id).where(Materia.id == fonte.materia_id)
        return (await self._sessao.execute(consulta)).scalar_one()
