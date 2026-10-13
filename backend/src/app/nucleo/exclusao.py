"""Registro de exclusão de dados por domínio (DTEC 021).

Cada domínio com dados de estudante registra `apagar_dados_usuario(sessao, usuario_id)`
com uma ordem: dependentes antes das tabelas de que dependem (ordem menor roda antes). A
exclusão da conta chama `apagar_dados_usuario` na mesma transação e, por fim, apaga o
usuário. Um teste de catálogo (CS-004) detecta o domínio que esquecer de se registrar.

Ordens reservadas: 100 a 899 para os domínios das specs; 900 para `revisao`
(`parametros_fsrs`); 950 para `identidade` (sessões).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

type ApagarDadosUsuario = Callable[[AsyncSession, int], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class ParticipanteExclusao:
    ordem: int
    dominio: str
    apagar: ApagarDadosUsuario


class RegistroExclusao:
    def __init__(self) -> None:
        self._participantes: dict[str, ParticipanteExclusao] = {}

    def registrar(self, ordem: int, dominio: str, apagar: ApagarDadosUsuario) -> None:
        existente = self._participantes.get(dominio)
        if existente is not None and existente.apagar is not apagar:
            raise ValueError(f"o domínio {dominio!r} já registrou sua exclusão")
        if any(p.ordem == ordem and p.dominio != dominio for p in self._participantes.values()):
            raise ValueError(f"a ordem {ordem} já está em uso")
        self._participantes[dominio] = ParticipanteExclusao(ordem, dominio, apagar)

    def em_ordem(self) -> list[ParticipanteExclusao]:
        return sorted(self._participantes.values(), key=lambda p: p.ordem)

    async def apagar_dados_usuario(self, sessao: AsyncSession, usuario_id: int) -> None:
        for participante in self.em_ordem():
            await participante.apagar(sessao, usuario_id)


registro_exclusao = RegistroExclusao()
