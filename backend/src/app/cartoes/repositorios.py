"""Consultas dos cartões. Todo método de recurso de estudante recebe `usuario_id` (DTEC 019)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import ColumnElement, Select, bindparam, delete, func, or_, select, tuple_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.cartoes.cursor import PosicaoCursor
from app.cartoes.dominio import EstadoInicial, TextoCartao
from app.cartoes.excecoes import FonteDeReferenciaInvalida
from app.cartoes.modelos import Cartao, OrigemCartao, SituacaoCartao
from app.fontes.modelos import Fonte
from app.materias.modelos import Materia
from app.nucleo.erros import RecursoNaoEncontrado

# Aguardando revisão e recusado (004) ficam fora de toda rota e lista da 003 (DTEC 038).
SITUACOES_VISIVEIS = (SituacaoCartao.ATIVO, SituacaoCartao.SUSPENSO)


@dataclass(frozen=True, slots=True)
class FiltrosCartoes:
    """Filtros da lista (US4; RF-010). `busca` já vem normalizada pelo domínio, ou é `None`."""

    busca: str | None = None
    situacao: SituacaoCartao | None = None
    origem: OrigemCartao | None = None


def escapar_like(termo: str) -> str:
    """`\\`, `%` e `_` viram literais no `LIKE ... ESCAPE '\\'` (DTEC 033)."""
    return termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _sem_acento_minusculo(
    expressao: ColumnElement[str] | InstrumentedAttribute[str],
) -> ColumnElement[str]:
    # Primeiro `unaccent`, depois `lower`: "É" vira "E" antes da minúscula, mesmo que a colação
    # do banco converta só ASCII (DTEC 033).
    return func.lower(func.unaccent(expressao))


def filtro_busca(termo: str) -> ColumnElement[bool]:
    """Ponto único da busca: frente ou verso contém o termo, sem caixa nem acento (DTEC 033).

    O termo vai sempre como parâmetro, nunca concatenado ao SQL.
    """
    padrao = _sem_acento_minusculo(bindparam("termo_busca", "%" + escapar_like(termo) + "%"))
    return or_(
        _sem_acento_minusculo(Cartao.frente).like(padrao, escape="\\"),
        _sem_acento_minusculo(Cartao.verso).like(padrao, escape="\\"),
    )


_FK_MATERIA = "cartoes_materia_id_fkey"
_FK_FONTE = "cartoes_fonte_id_fkey"


@dataclass(frozen=True, slots=True)
class CopiaReferencia:
    """A descrição da origem copiada da fonte, que sobrevive à exclusão e à renomeação dela."""

    fonte_id: int
    titulo: str
    nome_arquivo: str
    enviada_em: datetime

    @classmethod
    def da_fonte(cls, fonte: Fonte) -> CopiaReferencia:
        return cls(fonte.id, fonte.titulo, fonte.nome_arquivo, fonte.criado_em)


@dataclass(frozen=True, slots=True)
class LinhaCartao:
    """Um cartão com os identificadores públicos que a resposta precisa."""

    cartao: Cartao
    materia_public_id: UUID
    fonte_public_id: UUID | None


def _restricao(erro: IntegrityError) -> str | None:
    nome = getattr(getattr(erro.orig, "diag", None), "constraint_name", None)
    return nome if isinstance(nome, str) else None


class RepositorioCartoes:
    def __init__(self, sessao: AsyncSession) -> None:
        self._sessao = sessao

    async def buscar_fonte_para_referencia(
        self, usuario_id: int, materia_id: int, public_id: UUID
    ) -> Fonte | None:
        """A fonte do estudante **e da matéria**, travada com `FOR SHARE` até o fim da transação.

        A exclusão da fonte trava com `FOR UPDATE` (DTEC 031): uma criação nunca cita uma fonte
        que está sendo apagada, e quem só cita a mesma fonte não espera ninguém.
        """
        consulta = (
            select(Fonte)
            .where(
                Fonte.public_id == public_id,
                Fonte.usuario_id == usuario_id,
                Fonte.materia_id == materia_id,
            )
            .with_for_update(read=True)
        )
        return (await self._sessao.execute(consulta)).scalar_one_or_none()

    async def criar(
        self,
        *,
        usuario_id: int,
        materia_id: int,
        texto: TextoCartao,
        estado: EstadoInicial,
        agora: datetime,
        referencia: CopiaReferencia | None = None,
    ) -> Cartao:
        """Insere o cartão manual: ativo, de origem `criado` e com o estado de um cartão novo."""
        cartao = Cartao(
            usuario_id=usuario_id,
            materia_id=materia_id,
            frente=texto.frente,
            verso=texto.verso,
            explicacao=texto.explicacao,
            origem=OrigemCartao.CRIADO,
            situacao=SituacaoCartao.ATIVO,
            entrada_estudo_em=agora,
            fonte_id=referencia.fonte_id if referencia else None,
            referencia_titulo=referencia.titulo if referencia else None,
            referencia_nome_arquivo=referencia.nome_arquivo if referencia else None,
            referencia_enviada_em=referencia.enviada_em if referencia else None,
            estado_fsrs=estado.estado_fsrs,
            passo=estado.passo,
            estabilidade=estado.estabilidade,
            dificuldade=estado.dificuldade,
            vencimento=estado.vencimento,
            ultima_revisao=estado.ultima_revisao,
            criado_em=agora,
            atualizado_em=agora,
        )
        try:
            # Savepoint: a violação desfaz só a inserção e a transação segue utilizável.
            async with self._sessao.begin_nested():
                self._sessao.add(cartao)
                await self._sessao.flush()
        except IntegrityError as erro:
            # A matéria (ou a fonte) foi excluída entre a conferência e a inserção, ou o dono não
            # confere: para o estudante, o que ele citou não existe mais.
            restricao = _restricao(erro)
            if restricao == _FK_MATERIA:
                raise RecursoNaoEncontrado() from erro
            if restricao == _FK_FONTE:
                raise FonteDeReferenciaInvalida() from erro
            raise
        return cartao

    @staticmethod
    def _com_identificadores() -> Select[Cartao, UUID, UUID]:
        return (
            select(Cartao, Materia.public_id, Fonte.public_id)
            .join(Materia, Materia.id == Cartao.materia_id)
            .outerjoin(Fonte, Fonte.id == Cartao.fonte_id)
        )

    async def buscar(
        self, usuario_id: int, public_id: UUID, *, para_atualizar: bool = False
    ) -> LinhaCartao:
        """O cartão do estudante numa situação visível, ou `404` idêntico ao de inexistente.

        Cartão de outro estudante, inexistente, aguardando revisão ou recusado (004) dão a mesma
        resposta (DTEC 019 e 038). `para_atualizar` trava só a linha do cartão (`FOR UPDATE OF`).
        """
        consulta = self._com_identificadores().where(
            Cartao.public_id == public_id,
            Cartao.usuario_id == usuario_id,
            Cartao.situacao.in_(SITUACOES_VISIVEIS),
        )
        if para_atualizar:
            consulta = consulta.with_for_update(of=Cartao)
        linha = (await self._sessao.execute(consulta)).one_or_none()
        if linha is None:
            raise RecursoNaoEncontrado()
        cartao, materia_public_id, fonte_public_id = linha
        return LinhaCartao(cartao, materia_public_id, fonte_public_id)

    async def editar(
        self, cartao: Cartao, texto: TextoCartao, origem: OrigemCartao, agora: datetime
    ) -> None:
        """Um único `UPDATE` só do conteúdo, da origem e de `atualizado_em` (DTEC 037).

        As colunas do FSRS nunca aparecem aqui: a revisão (005) as escreve, e as duas escritas
        não se cruzam, mesmo em paralelo (CS-002).
        """
        await self._sessao.execute(
            update(Cartao)
            .where(Cartao.id == cartao.id, Cartao.usuario_id == cartao.usuario_id)
            .values(
                frente=texto.frente,
                verso=texto.verso,
                explicacao=texto.explicacao,
                origem=origem,
                atualizado_em=agora,
            )
        )

    async def alterar_situacao(
        self, cartao: Cartao, situacao: SituacaoCartao, agora: datetime
    ) -> None:
        """Só `situacao` e `atualizado_em`: suspender e reativar preservam o FSRS (RF-007)."""
        await self._sessao.execute(
            update(Cartao)
            .where(Cartao.id == cartao.id, Cartao.usuario_id == cartao.usuario_id)
            .values(situacao=situacao, atualizado_em=agora)
        )

    async def excluir(self, usuario_id: int, public_id: UUID) -> UUID:
        """Remove o cartão visível do estudante, ou `404` idêntico ao de inexistente (RN-14).

        Num pedido repetido em paralelo, o segundo espera a linha e não a encontra mais.
        """
        excluido = (
            await self._sessao.execute(
                delete(Cartao)
                .where(
                    Cartao.public_id == public_id,
                    Cartao.usuario_id == usuario_id,
                    Cartao.situacao.in_(SITUACOES_VISIVEIS),
                )
                .returning(Cartao.public_id)
            )
        ).scalar_one_or_none()
        if excluido is None:
            raise RecursoNaoEncontrado()
        return excluido

    @staticmethod
    def _filtro(
        usuario_id: int, materia_id: int, filtros: FiltrosCartoes | None = None
    ) -> tuple[ColumnElement[bool], ...]:
        condicoes: list[ColumnElement[bool]] = [
            Cartao.usuario_id == usuario_id,
            Cartao.materia_id == materia_id,
            Cartao.situacao.in_(SITUACOES_VISIVEIS),
        ]
        if filtros is not None:
            if filtros.situacao is not None:
                condicoes.append(Cartao.situacao == filtros.situacao)
            if filtros.origem is not None:
                condicoes.append(Cartao.origem == filtros.origem)
            if filtros.busca:
                condicoes.append(filtro_busca(filtros.busca))
        return tuple(condicoes)

    async def contar(
        self, usuario_id: int, materia_id: int, *, filtros: FiltrosCartoes | None = None
    ) -> int:
        """Todos os cartões que atendem aos filtros, não só os da página (DTEC 034)."""
        consulta = (
            select(func.count())
            .select_from(Cartao)
            .where(*self._filtro(usuario_id, materia_id, filtros))
        )
        return int((await self._sessao.execute(consulta)).scalar_one())

    async def listar(
        self,
        usuario_id: int,
        materia_id: int,
        *,
        filtros: FiltrosCartoes | None = None,
        posicao: PosicaoCursor | None = None,
        limite: int = 50,
    ) -> tuple[list[LinhaCartao], bool]:
        """Uma página do mais recente ao mais antigo (`criado_em` e `id` decrescentes).

        A ordem é total, e a página seguinte começa estritamente antes de `posicao` (*keyset*,
        DTEC 034): criação e exclusão entre as páginas não repetem nem pulam itens. Lê um item a
        mais para saber se há próxima página.
        """
        consulta = (
            self._com_identificadores()
            .where(*self._filtro(usuario_id, materia_id, filtros))
            .order_by(Cartao.criado_em.desc(), Cartao.id.desc())
            .limit(limite + 1)
        )
        if posicao is not None:
            consulta = consulta.where(
                tuple_(Cartao.criado_em, Cartao.id) < tuple_(posicao.criado_em, posicao.id)
            )
        linhas = [
            LinhaCartao(cartao, materia_public_id, fonte_public_id)
            for cartao, materia_public_id, fonte_public_id in await self._sessao.execute(consulta)
        ]
        return linhas[:limite], len(linhas) > limite
