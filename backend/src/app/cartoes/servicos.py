"""Casos de uso dos cartões. Cada um controla a própria transação (DTEC 018)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

import structlog

from app.cartoes import cursor as cursor_opaco
from app.cartoes import dominio
from app.cartoes.cursor import CursorInvalido, PosicaoCursor
from app.cartoes.dominio import LimitesTexto, TextoInvalido
from app.cartoes.excecoes import (
    CursorDeListaInvalido,
    FonteDeReferenciaInvalida,
    TextoCartaoInvalido,
)
from app.cartoes.repositorios import CopiaReferencia, LinhaCartao, RepositorioCartoes
from app.materias.repositorios import RepositorioMaterias
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao
from app.nucleo.relogio import Relogio

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class PaginaCartoes:
    itens: list[LinhaCartao]
    proximo_cursor: str | None
    total: int


class ServicoCartoes:
    def __init__(
        self, fabrica: FabricaSessoes, configuracao: Configuracao, relogio: Relogio
    ) -> None:
        self._fabrica = fabrica
        self._configuracao = configuracao
        self._relogio = relogio

    def limites(self) -> LimitesTexto:
        """Os limites vigentes no ambiente (D-004); a interface os lê em `/cartoes/limites`."""
        return LimitesTexto(
            frente=self._configuracao.cartao_frente_max,
            verso=self._configuracao.cartao_verso_max,
            explicacao=self._configuracao.cartao_explicacao_max,
        )

    async def criar(
        self,
        *,
        usuario_id: int,
        usuario_public_id: UUID,
        materia_public_id: UUID,
        frente: str,
        verso: str,
        explicacao: str | None,
        fonte_public_id: UUID | None,
    ) -> LinhaCartao:
        """Cria um cartão manual: ativo, "Criado por você" e como cartão novo do FSRS (US1)."""
        try:
            texto = dominio.validar_limites(frente, verso, explicacao, self.limites())
        except TextoInvalido as erro:
            raise TextoCartaoInvalido(erro.campos) from None
        agora = self._relogio.agora()
        async with unidade_de_trabalho(self._fabrica) as sessao:
            materia = await RepositorioMaterias(sessao).buscar(usuario_id, materia_public_id)
            repositorio = RepositorioCartoes(sessao)
            fonte = None
            if fonte_public_id is not None:
                fonte = await repositorio.buscar_fonte_para_referencia(
                    usuario_id, materia.id, fonte_public_id
                )
                if fonte is None:
                    raise FonteDeReferenciaInvalida()
            cartao = await repositorio.criar(
                usuario_id=usuario_id,
                materia_id=materia.id,
                texto=texto,
                estado=dominio.estado_inicial(agora),
                agora=agora,
                referencia=CopiaReferencia.da_fonte(fonte) if fonte is not None else None,
            )
            linha = LinhaCartao(cartao, materia.public_id, fonte.public_id if fonte else None)
        logger.info(
            "cartao_criado",
            cartao_public_id=str(cartao.public_id),
            usuario_public_id=str(usuario_public_id),
            materia_public_id=str(materia.public_id),
            com_referencia=fonte is not None,
        )
        return linha

    async def listar(
        self, usuario_id: int, materia_public_id: UUID, *, cursor: str | None, limite: int
    ) -> PaginaCartoes:
        """Uma página dos cartões ativos e suspensos da matéria, do mais recente ao mais antigo."""
        async with unidade_de_trabalho(self._fabrica) as sessao:
            materia = await RepositorioMaterias(sessao).buscar(usuario_id, materia_public_id)
            resumo = cursor_opaco.resumo_dos_filtros(usuario_id, materia.public_id)
            posicao: PosicaoCursor | None = None
            if cursor:
                try:
                    posicao = cursor_opaco.decodificar(
                        cursor, resumo=resumo, segredo=self._configuracao.segredo
                    )
                except CursorInvalido:
                    raise CursorDeListaInvalido() from None
            repositorio = RepositorioCartoes(sessao)
            itens, ha_mais = await repositorio.listar(
                usuario_id, materia.id, posicao=posicao, limite=limite
            )
            total = await repositorio.contar(usuario_id, materia.id)
        proximo = None
        if ha_mais:
            ultimo = itens[-1].cartao
            proximo = cursor_opaco.codificar(
                PosicaoCursor(ultimo.criado_em, ultimo.id),
                resumo=resumo,
                segredo=self._configuracao.segredo,
            )
        return PaginaCartoes(itens, proximo, total)

    async def consultar(self, usuario_id: int, public_id: UUID) -> LinhaCartao:
        async with unidade_de_trabalho(self._fabrica) as sessao:
            return await RepositorioCartoes(sessao).buscar(usuario_id, public_id)

    async def editar(
        self,
        *,
        usuario_id: int,
        usuario_public_id: UUID | str,
        public_id: UUID,
        alteracoes: Mapping[str, str | None],
    ) -> LinhaCartao:
        """Edita frente, verso ou explicação sem tocar no agendamento (US2; RF-005, RF-006).

        Sem mudança efetiva depois da normalização, nada é gravado: nem `atualizado_em` nem a
        origem mudam (US2-3). Vale a última gravação entre duas abas (DTEC 037).
        """
        async with unidade_de_trabalho(self._fabrica) as sessao:
            repositorio = RepositorioCartoes(sessao)
            linha = await repositorio.buscar(usuario_id, public_id, para_atualizar=True)
            cartao = linha.cartao
            atual = dominio.TextoCartao(cartao.frente, cartao.verso, cartao.explicacao)
            try:
                novo = dominio.validar_edicao(atual, alteracoes, self.limites())
            except TextoInvalido as erro:
                raise TextoCartaoInvalido(erro.campos) from None
            mudou = dominio.houve_mudanca(atual, novo)
            if mudou:
                origem = dominio.origem_apos_edicao(cartao.origem, mudou=True)
                origem_mudou = origem is not cartao.origem
                await repositorio.editar(cartao, novo, origem, self._relogio.agora())
        if not mudou:
            logger.info(
                "cartao_edicao_sem_mudanca",
                cartao_public_id=str(cartao.public_id),
                usuario_public_id=str(usuario_public_id),
            )
        else:
            logger.info(
                "cartao_editado",
                cartao_public_id=str(cartao.public_id),
                usuario_public_id=str(usuario_public_id),
                origem_mudou=origem_mudou,
            )
        return linha

    async def suspender(
        self, *, usuario_id: int, usuario_public_id: UUID | str, public_id: UUID
    ) -> LinhaCartao:
        """Tira o cartão das lições sem tocar no agendamento (US3-1; RF-007). Idempotente."""
        return await self._mudar_situacao(
            usuario_id, usuario_public_id, public_id, dominio.SituacaoCartao.SUSPENSO
        )

    async def reativar(
        self, *, usuario_id: int, usuario_public_id: UUID | str, public_id: UUID
    ) -> LinhaCartao:
        """Devolve o cartão às lições com o vencimento de antes (US3-2; RF-007). Idempotente."""
        return await self._mudar_situacao(
            usuario_id, usuario_public_id, public_id, dominio.SituacaoCartao.ATIVO
        )

    async def _mudar_situacao(
        self,
        usuario_id: int,
        usuario_public_id: UUID | str,
        public_id: UUID,
        destino: dominio.SituacaoCartao,
    ) -> LinhaCartao:
        # A linha travada serializa pedidos repetidos: só o primeiro escreve; os outros a
        # encontram já na situação pedida e respondem `200` sem escrita.
        async with unidade_de_trabalho(self._fabrica) as sessao:
            repositorio = RepositorioCartoes(sessao)
            linha = await repositorio.buscar(usuario_id, public_id, para_atualizar=True)
            mudou = linha.cartao.situacao is not destino
            if mudou:
                await repositorio.alterar_situacao(linha.cartao, destino, self._relogio.agora())
        if mudou:
            evento = (
                "cartao_suspenso"
                if destino is dominio.SituacaoCartao.SUSPENSO
                else "cartao_reativado"
            )
            logger.info(
                evento,
                cartao_public_id=str(public_id),
                usuario_public_id=str(usuario_public_id),
            )
        else:
            logger.info(
                "cartao_situacao_sem_mudanca",
                cartao_public_id=str(public_id),
                usuario_public_id=str(usuario_public_id),
                situacao=destino.value,
            )
        return linha

    async def excluir(
        self, *, usuario_id: int, usuario_public_id: UUID | str, public_id: UUID
    ) -> None:
        """Exclusão definitiva, confirmada antes na interface (US3-3; RF-008, RN-14)."""
        async with unidade_de_trabalho(self._fabrica) as sessao:
            await RepositorioCartoes(sessao).excluir(usuario_id, public_id)
        logger.info(
            "cartao_excluido",
            cartao_public_id=str(public_id),
            usuario_public_id=str(usuario_public_id),
        )
