"""Casos de uso dos cartões. Cada um controla a própria transação (DTEC 018)."""

from __future__ import annotations

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
