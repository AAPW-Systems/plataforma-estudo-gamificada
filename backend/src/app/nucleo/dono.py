"""Busca de um recurso de estudante pelo identificador público e pelo dono (DTEC 019, T043).

Todo recurso de estudante exposto por rota é buscado com o dono **na própria consulta**:
`WHERE public_id = :id AND usuario_id = :dono`. Quem não é o dono recebe exatamente a resposta
de um identificador inexistente (`404 recurso_nao_encontrado`, mesmo corpo e mesmos cabeçalhos),
de modo que a API nunca confirma a existência de um recurso alheio (RF-007, CS-002).

As specs 002 em diante usam esta função nos seus repositórios, em vez de escrever a consulta
à mão. O teste `tests/security/test_isolamento_rotas.py` exige um caso de duas contas para
toda rota com identificador no caminho.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.erros import RecursoNaoEncontrado


class ModeloDeEstudante(Protocol):
    """Entidade com identificador público e dono (as colunas `public_id` e `usuario_id`)."""

    public_id: UUID
    usuario_id: int


async def buscar_do_dono[Modelo: ModeloDeEstudante](
    sessao: AsyncSession,
    modelo: type[Modelo],
    public_id: UUID,
    usuario_id: int,
    *,
    para_atualizar: bool = False,
) -> Modelo:
    """O recurso do estudante, ou `RecursoNaoEncontrado` se não existir ou for de outro dono.

    `para_atualizar` trava a linha (`FOR UPDATE`) para quem vai alterá-la ou excluí-la.
    """
    consulta = select(modelo).filter_by(public_id=public_id, usuario_id=usuario_id)
    if para_atualizar:
        consulta = consulta.with_for_update()
    recurso = (await sessao.execute(consulta)).scalar_one_or_none()
    if recurso is None:
        raise RecursoNaoEncontrado()
    return recurso
