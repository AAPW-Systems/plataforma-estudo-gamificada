"""Participante falso da exclusão de fontes e matérias (DTEC 027).

Devolve contagens configuráveis e registra cada chamada com o modo, para testar o mecanismo
da 002 antes de existirem as tabelas de cartões (003 e 004).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import text
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
        atraso_s: float = 0.0,
        observar_fontes: bool = False,
    ) -> None:
        self.nome = nome
        self.observar_fontes = observar_fontes
        # Alarga a janela da contagem, para as corridas dos testes adversariais.
        self.atraso_s = atraso_s
        self.por_materia = por_materia or {}
        self.impacto = impacto or ContagensAcervo()
        self.chamadas = chamadas if chamadas is not None else []
        self.exclusoes_de_fonte: list[tuple[int, int, ModoCartoes]] = []
        self.exclusoes_de_materia: list[tuple[int, int]] = []
        # Quantas fontes da matéria ainda existiam quando este participante foi chamado: prova a
        # ordem (cartões antes de `fontes`, DTEC 027).
        self.fontes_vistas_ao_excluir_materia: list[int] = []

    async def contar_por_materia(
        self, sessao: AsyncSession, usuario_id: int
    ) -> dict[int, ContagensAcervo]:
        if self.atraso_s:
            await asyncio.sleep(self.atraso_s)
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
        if self.observar_fontes:  # só com banco de verdade; os testes unitários usam sessão falsa
            total = await sessao.execute(
                text("SELECT count(*) FROM fontes WHERE materia_id = :m"), {"m": materia_id}
            )
            self.fontes_vistas_ao_excluir_materia.append(int(total.scalar_one()))


@dataclass
class CartoesDaFonte:
    """Cartões de uma fonte no participante falso (DTEC 027, contagens da US2)."""

    aceitos: int = 0
    aguardando: int = 0
    referencia: int = 0


class ParticipanteDeCartoesFalso:
    """Faz o papel dos cartões (003 e 004) com estado em memória, para testar a US2 da 002.

    - `aguardando revisão` é sempre apagado;
    - `gerados e aceitos` seguem o modo (`excluir` apaga, `manter` conserva);
    - `referência` (criados pelo estudante) nunca muda (D-009).

    `atraso_s` alarga a janela da consulta de impacto, para as corridas dos testes
    adversariais (duas exclusões paralelas); `aoContar` permite mudar as contagens entre a
    consulta e a confirmação.
    """

    def __init__(self, *, atraso_s: float = 0.0) -> None:
        self.por_fonte: dict[int, CartoesDaFonte] = {}
        self.atraso_s = atraso_s
        self.modos: list[ModoCartoes] = []
        self.apagados: list[dict[str, int]] = []
        self.consultas = 0

    def definir(self, fonte_id: int, *, aceitos: int, aguardando: int, referencia: int) -> None:
        self.por_fonte[fonte_id] = CartoesDaFonte(aceitos, aguardando, referencia)

    async def contar_por_materia(
        self, sessao: AsyncSession, usuario_id: int
    ) -> dict[int, ContagensAcervo]:
        return {}

    async def impacto_fonte(
        self, sessao: AsyncSession, usuario_id: int, fonte_id: int
    ) -> ContagensAcervo:
        self.consultas += 1
        if self.atraso_s:
            await asyncio.sleep(self.atraso_s)
        c = self.por_fonte.get(fonte_id, CartoesDaFonte())
        return ContagensAcervo(
            cartoes_gerados_aceitos=c.aceitos,
            cartoes_aguardando_revisao=c.aguardando,
            cartoes_referencia=c.referencia,
        )

    async def ao_excluir_fonte(
        self, sessao: AsyncSession, usuario_id: int, fonte_id: int, modo: ModoCartoes
    ) -> None:
        self.modos.append(modo)
        c = self.por_fonte.setdefault(fonte_id, CartoesDaFonte())
        self.apagados.append(
            {
                "aguardando": c.aguardando,
                "aceitos": c.aceitos if modo is ModoCartoes.EXCLUIR else 0,
                "referencia": 0,
            }
        )
        c.aguardando = 0
        if modo is ModoCartoes.EXCLUIR:
            c.aceitos = 0

    async def ao_excluir_materia(
        self, sessao: AsyncSession, usuario_id: int, materia_id: int
    ) -> None:
        return None
