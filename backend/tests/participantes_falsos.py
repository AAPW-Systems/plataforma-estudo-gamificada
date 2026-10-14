"""Participante falso da exclusão de fontes e matérias (DTEC 027).

Devolve contagens configuráveis e registra cada chamada com o modo, para testar o mecanismo
da 002 antes de existirem as tabelas de cartões (003 e 004).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.participantes_acervo import ContagensAcervo, ModoCartoes


class ParticipanteFalso:
    def __init__(
        self,
        *,
        nome: str = "falso",
        por_materia: dict[int, ContagensAcervo] | None = None,
        impacto: ContagensAcervo | None = None,
        chamadas: list[tuple[str, str, object]] | None = None,
    ) -> None:
        self.nome = nome
        self.por_materia = por_materia or {}
        self.impacto = impacto or ContagensAcervo()
        self.chamadas = chamadas if chamadas is not None else []
        self.exclusoes_de_fonte: list[tuple[int, int, ModoCartoes]] = []
        self.exclusoes_de_materia: list[tuple[int, int]] = []

    async def contar_por_materia(
        self, sessao: AsyncSession, usuario_id: int
    ) -> dict[int, ContagensAcervo]:
        return dict(self.por_materia)

    async def impacto_fonte(
        self, sessao: AsyncSession, usuario_id: int, fonte_id: int
    ) -> ContagensAcervo:
        return self.impacto

    async def ao_excluir_fonte(
        self, sessao: AsyncSession, usuario_id: int, fonte_id: int, modo: ModoCartoes
    ) -> None:
        self.chamadas.append((self.nome, "fonte", sessao))
        self.exclusoes_de_fonte.append((usuario_id, fonte_id, modo))

    async def ao_excluir_materia(
        self, sessao: AsyncSession, usuario_id: int, materia_id: int
    ) -> None:
        self.chamadas.append((self.nome, "materia", sessao))
        self.exclusoes_de_materia.append((usuario_id, materia_id))
