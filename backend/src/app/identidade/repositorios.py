"""Consultas da identidade (T034).

Todo método que lê ou altera dado de um estudante recebe o `usuario_id` (DTEC 019). As exceções
são as buscas pela credencial (hash do token da sessão, e-mail da entrada), que existem
justamente para descobrir quem é o dono, e a limpeza periódica de registros expirados.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any, Literal, cast

from sqlalchemy import CursorResult, delete, func, or_, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.identidade.dominio import AlteracaoPerfil
from app.identidade.excecoes import EmailEmUso
from app.identidade.modelos import Sessao, TentativaAcesso, Usuario

type TipoTentativa = Literal["falha_entrada", "falha_senha_atual", "cadastro"]

_INDICE_EMAIL = "usuarios_email_unico"
_TIPOS_DE_FALHA = ("falha_entrada", "falha_senha_atual")


def _linhas_afetadas(resultado: object) -> int:
    return cast("CursorResult[Any]", resultado).rowcount


class RepositorioUsuarios:
    def __init__(self, sessao: AsyncSession) -> None:
        self._sessao = sessao

    async def criar(
        self, *, nome: str, email: str, senha_hash: str, fuso: str, agora: datetime
    ) -> Usuario:
        """Insere a conta; a corrida entre dois cadastros é resolvida pelo índice único."""
        usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=senha_hash,
            fuso=fuso,
            criado_em=agora,
            atualizado_em=agora,
        )
        try:
            # Savepoint: a violação desfaz só a inserção e a transação segue utilizável.
            async with self._sessao.begin_nested():
                self._sessao.add(usuario)
                await self._sessao.flush()
        except IntegrityError as erro:
            if getattr(getattr(erro.orig, "diag", None), "constraint_name", None) == _INDICE_EMAIL:
                raise EmailEmUso() from erro
            raise
        return usuario

    async def buscar_por_email(self, email: str) -> Usuario | None:
        consulta = (
            select(Usuario)
            .where(func.lower(Usuario.email) == func.lower(email))
            .execution_options(populate_existing=True)
        )
        return (await self._sessao.execute(consulta)).scalar_one_or_none()

    async def buscar_por_id(self, usuario_id: int) -> Usuario | None:
        consulta = (
            select(Usuario)
            .where(Usuario.id == usuario_id)
            .execution_options(populate_existing=True)
        )
        return (await self._sessao.execute(consulta)).scalar_one_or_none()

    async def travar_por_id(self, usuario_id: int) -> Usuario | None:
        """`SELECT ... FOR UPDATE`: serializa alterações do perfil e a exclusão da conta."""
        consulta = (
            select(Usuario)
            .where(Usuario.id == usuario_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return (await self._sessao.execute(consulta)).scalar_one_or_none()

    async def aplicar_alteracao(
        self, usuario: Usuario, alteracao: AlteracaoPerfil, agora: datetime
    ) -> None:
        """Grava só os campos presentes da alteração, no usuário já travado por quem chama."""
        for campo in ("nome", "fuso", "meta_diaria", "tamanho_licao", "limite_novos_dia"):
            valor = getattr(alteracao, campo)
            if valor is not None:
                setattr(usuario, campo, valor)
        usuario.atualizado_em = agora
        await self._sessao.flush()

    async def atualizar_senha_hash(self, usuario_id: int, senha_hash: str, agora: datetime) -> None:
        await self._sessao.execute(
            update(Usuario)
            .where(Usuario.id == usuario_id)
            .values(senha_hash=senha_hash, atualizado_em=agora)
        )


class RepositorioSessoes:
    def __init__(self, sessao: AsyncSession) -> None:
        self._sessao = sessao

    async def criar(
        self,
        *,
        usuario_id: int,
        token_hash: bytes,
        agora: datetime,
        expira_em: datetime,
        ip: str | None,
        agente_usuario: str | None,
    ) -> Sessao:
        sessao = Sessao(
            usuario_id=usuario_id,
            token_hash=token_hash,
            criada_em=agora,
            ultimo_uso_em=agora,
            expira_em=expira_em,
            ip=ip,
            agente_usuario=agente_usuario[:512] if agente_usuario is not None else None,
        )
        self._sessao.add(sessao)
        await self._sessao.flush()
        return sessao

    async def buscar_por_hash(self, token_hash: bytes) -> tuple[Sessao, Usuario] | None:
        """A sessão e o dono, válida ou não: a validade é decidida por `dominio`/`sessoes`."""
        consulta = (
            select(Sessao, Usuario)
            .join(Usuario, Usuario.id == Sessao.usuario_id)
            .where(Sessao.token_hash == token_hash)
            .execution_options(populate_existing=True)
        )
        linha = (await self._sessao.execute(consulta)).one_or_none()
        return None if linha is None else (linha[0], linha[1])

    async def renovar_uso(self, sessao_id: int, agora: datetime) -> None:
        await self._sessao.execute(
            update(Sessao).where(Sessao.id == sessao_id).values(ultimo_uso_em=agora)
        )

    async def revogar(self, sessao_id: int, agora: datetime) -> None:
        """Mantém a primeira revogação: uma sessão já revogada não muda."""
        await self._sessao.execute(
            update(Sessao)
            .where(Sessao.id == sessao_id, Sessao.revogada_em.is_(None))
            .values(revogada_em=agora)
        )

    async def revogar_outras(self, usuario_id: int, manter_sessao_id: int, agora: datetime) -> int:
        resultado = await self._sessao.execute(
            update(Sessao)
            .where(
                Sessao.usuario_id == usuario_id,
                Sessao.id != manter_sessao_id,
                Sessao.revogada_em.is_(None),
            )
            .values(revogada_em=agora)
        )
        return _linhas_afetadas(resultado)

    async def apagar_invalidas_antes_de(self, limite: datetime, dias_inatividade: int) -> int:
        """Apaga as sessões inválidas desde antes de `limite` (revogadas, expiradas ou inativas)."""
        sem_uso_desde = limite - timedelta(days=dias_inatividade)
        resultado = await self._sessao.execute(
            delete(Sessao).where(
                or_(
                    Sessao.revogada_em < limite,
                    Sessao.expira_em < limite,
                    Sessao.ultimo_uso_em < sem_uso_desde,
                )
            )
        )
        return _linhas_afetadas(resultado)


class RepositorioTentativas:
    def __init__(self, sessao: AsyncSession) -> None:
        self._sessao = sessao

    async def travar(self, *chaves: str) -> None:
        """`pg_advisory_xact_lock` por chave, até o fim da transação (DTEC 020 e 023).

        Chame antes de contar: a contagem e o registro da tentativa têm de acontecer na mesma
        transação, sob a trava, para que uma rajada paralela não ultrapasse o limite. Várias
        chaves são travadas em ordem alfabética, o que evita impasse entre transações.
        """
        for chave in sorted(set(chaves)):
            await self._sessao.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:chave, 0))"), {"chave": chave}
            )

    async def registrar(
        self, tipo: TipoTentativa, chave_conta: bytes | None, ip: str, agora: datetime
    ) -> None:
        self._sessao.add(
            TentativaAcesso(tipo=tipo, chave_conta=chave_conta, ip=ip, criado_em=agora)
        )
        await self._sessao.flush()

    async def instantes_falhas_conta(self, chave_conta: bytes, desde: datetime) -> list[datetime]:
        return await self._instantes(
            TentativaAcesso.chave_conta == chave_conta,
            TentativaAcesso.tipo.in_(_TIPOS_DE_FALHA),
            desde,
        )

    async def instantes_falhas_ip(self, ip: str, desde: datetime) -> list[datetime]:
        return await self._instantes(
            TentativaAcesso.ip == ip, TentativaAcesso.tipo.in_(_TIPOS_DE_FALHA), desde
        )

    async def instantes_cadastros_ip(self, ip: str, desde: datetime) -> list[datetime]:
        return await self._instantes(
            TentativaAcesso.ip == ip, TentativaAcesso.tipo == "cadastro", desde
        )

    async def apagar_falhas_conta(self, chave_conta: bytes) -> None:
        """Entrada bem-sucedida: zera as falhas da conta, mas não as do endereço (DTEC 020)."""
        await self._sessao.execute(
            delete(TentativaAcesso).where(
                TentativaAcesso.chave_conta == chave_conta,
                TentativaAcesso.tipo.in_(_TIPOS_DE_FALHA),
            )
        )

    async def apagar_anteriores_a(self, limite: datetime) -> int:
        resultado = await self._sessao.execute(
            delete(TentativaAcesso).where(TentativaAcesso.criado_em < limite)
        )
        return _linhas_afetadas(resultado)

    async def _instantes(self, *filtros: Any) -> list[datetime]:
        *condicoes, desde = filtros
        consulta = (
            select(TentativaAcesso.criado_em)
            .where(*condicoes, TentativaAcesso.criado_em > desde)
            .order_by(TentativaAcesso.criado_em)
        )
        instantes: Sequence[datetime] = (await self._sessao.execute(consulta)).scalars().all()
        return list(instantes)
