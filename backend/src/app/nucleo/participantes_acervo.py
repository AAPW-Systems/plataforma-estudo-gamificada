"""Participantes da exclusão de fontes e matérias (DTEC 027).

A exclusão de uma fonte ou de uma matéria precisa contar e tratar cartões, evidências e
gerações, que pertencem a outros domínios (003, 004 e, depois, 014). Cada domínio registra aqui
um participante; o serviço de `fontes` ou de `materias` organiza a exclusão e soma as
contagens. Todas as operações rodam **na transação de quem chama** (a sessão recebida).

Prioridade: menor roda antes. Cartões e gerações vêm primeiro e `fontes` por último, porque as
FKs de cartões e de fontes para matérias usam `restrict` e os objetos saem antes das linhas.
Faixas: 100 a 799 para cartões, gerações e índices; 900 para `fontes`.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession


class ModoCartoes(StrEnum):
    """Escolha do estudante sobre os cartões gerados e aceitos de uma fonte (RN-14)."""

    MANTER = "manter"
    EXCLUIR = "excluir"


@dataclass(frozen=True, slots=True)
class ContagensAcervo:
    """Contagens padronizadas; o campo que um participante não conhece vale zero."""

    fontes: int = 0
    cartoes_ativos: int = 0
    cartoes_suspensos: int = 0  # emenda de 13/10/2026 da DTEC 027
    cartoes_aguardando_revisao: int = 0
    cartoes_gerados_aceitos: int = 0  # afetados pela escolha manter/excluir
    cartoes_referencia: int = 0  # criados pelo estudante; sempre mantidos (D-009)

    def __add__(self, outra: ContagensAcervo) -> ContagensAcervo:
        return ContagensAcervo(
            **{c.name: getattr(self, c.name) + getattr(outra, c.name) for c in fields(self)}
        )


class ParticipanteAcervo(Protocol):
    async def contar_por_materia(
        self, sessao: AsyncSession, usuario_id: int
    ) -> dict[int, ContagensAcervo]:
        """Contagens por `materia_id` (interno); matérias ausentes valem zero."""
        ...

    async def impacto_fonte(
        self, sessao: AsyncSession, usuario_id: int, fonte_id: int
    ) -> ContagensAcervo: ...

    async def ao_excluir_fonte(
        self, sessao: AsyncSession, usuario_id: int, fonte_id: int, modo: ModoCartoes
    ) -> None: ...

    async def ao_excluir_materia(
        self, sessao: AsyncSession, usuario_id: int, materia_id: int
    ) -> None: ...


@runtime_checkable
class ParticipanteComTravaDeMateria(Protocol):
    """Gancho opcional (emenda aditiva à DTEC 027): travar o que a exclusão da matéria vai afetar.

    A exclusão trava a matéria e as suas fontes (`FOR UPDATE`, em ordem de `id`) **antes** de
    contar o impacto (DTEC 031). `materias` não importa `fontes`, então quem é dono das linhas a
    travar (`fontes`, e depois cartões e gerações) as trava aqui. Participante sem o método é
    ignorado: o protocolo de quatro operações segue valendo para quem não precisa.
    """

    async def travar_para_exclusao_de_materia(
        self, sessao: AsyncSession, usuario_id: int, materia_id: int
    ) -> None: ...


class RegistroAcervo:
    def __init__(self) -> None:
        self._participantes: dict[str, tuple[int, ParticipanteAcervo]] = {}

    def registrar(self, prioridade: int, nome: str, participante: ParticipanteAcervo) -> None:
        existente = self._participantes.get(nome)
        if existente is not None and existente[1] is not participante:
            raise ValueError(f"o participante {nome!r} já registrado")
        if any(p == prioridade and n != nome for n, (p, _) in self._participantes.items()):
            raise ValueError(f"a prioridade {prioridade} já está em uso")
        self._participantes[nome] = (prioridade, participante)

    def remover(self, nome: str) -> None:
        """Desfaz um registro; existe para os testes, que registram participantes falsos."""
        self._participantes.pop(nome, None)

    def nomes(self) -> list[str]:
        return [nome for nome, _ in self._em_ordem()]

    def _em_ordem(self) -> list[tuple[str, ParticipanteAcervo]]:
        ordenados = sorted(self._participantes.items(), key=lambda item: item[1][0])
        return [(nome, participante) for nome, (_, participante) in ordenados]

    async def contar_por_materia(
        self, sessao: AsyncSession, usuario_id: int
    ) -> dict[int, ContagensAcervo]:
        total: dict[int, ContagensAcervo] = {}
        for _, participante in self._em_ordem():
            for materia_id, contagens in (
                await participante.contar_por_materia(sessao, usuario_id)
            ).items():
                total[materia_id] = total.get(materia_id, ContagensAcervo()) + contagens
        return total

    async def impacto_fonte(
        self, sessao: AsyncSession, usuario_id: int, fonte_id: int
    ) -> ContagensAcervo:
        total = ContagensAcervo()
        for _, participante in self._em_ordem():
            total = total + await participante.impacto_fonte(sessao, usuario_id, fonte_id)
        return total

    async def ao_excluir_fonte(
        self, sessao: AsyncSession, usuario_id: int, fonte_id: int, modo: ModoCartoes
    ) -> None:
        for _, participante in self._em_ordem():
            await participante.ao_excluir_fonte(sessao, usuario_id, fonte_id, modo)

    async def travar_materia(self, sessao: AsyncSession, usuario_id: int, materia_id: int) -> None:
        """Pede a cada participante que trave o que a exclusão da matéria vai afetar."""
        for _, participante in self._em_ordem():
            if isinstance(participante, ParticipanteComTravaDeMateria):
                await participante.travar_para_exclusao_de_materia(sessao, usuario_id, materia_id)

    async def ao_excluir_materia(
        self, sessao: AsyncSession, usuario_id: int, materia_id: int
    ) -> None:
        for _, participante in self._em_ordem():
            await participante.ao_excluir_materia(sessao, usuario_id, materia_id)


registro_acervo = RegistroAcervo()
