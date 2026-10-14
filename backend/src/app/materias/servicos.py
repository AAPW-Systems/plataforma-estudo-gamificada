"""Casos de uso das matérias. Cada um controla a própria transação (DTEC 018)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import structlog

from app.materias import dominio
from app.materias.excecoes import CotaMateriasExcedida, NomeInvalido
from app.materias.modelos import Materia
from app.materias.repositorios import RepositorioMaterias
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao
from app.nucleo.participantes_acervo import ContagensAcervo, RegistroAcervo
from app.nucleo.relogio import Relogio
from app.nucleo.texto import ValorInvalido

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class MateriaConsultada:
    materia: Materia
    contagens: ContagensAcervo


def validar_nome(valor: str) -> str:
    try:
        return dominio.validar_nome(valor)
    except ValorInvalido as erro:
        raise NomeInvalido(erro.mensagem) from None


class ServicoMaterias:
    def __init__(
        self,
        fabrica: FabricaSessoes,
        configuracao: Configuracao,
        registro_acervo: RegistroAcervo,
        relogio: Relogio,
    ) -> None:
        self._fabrica = fabrica
        self._configuracao = configuracao
        self._registro = registro_acervo
        self._relogio = relogio

    async def criar(self, usuario_id: int, nome: str) -> MateriaConsultada:
        """Cria a matéria sob o *advisory lock* do acervo: a cota não passa numa rajada."""
        nome_valido = validar_nome(nome)
        async with unidade_de_trabalho(self._fabrica) as sessao:
            repositorio = RepositorioMaterias(sessao)
            await repositorio.travar_acervo(usuario_id)
            if await repositorio.contar(usuario_id) >= self._configuracao.cota_materias:
                raise CotaMateriasExcedida(self._configuracao.cota_materias)
            materia = await repositorio.criar(usuario_id, nome_valido, self._relogio.agora())
        logger.info("materia_criada", materia_public_id=str(materia.public_id))
        return MateriaConsultada(materia, ContagensAcervo())

    async def listar(self, usuario_id: int) -> list[MateriaConsultada]:
        async with unidade_de_trabalho(self._fabrica) as sessao:
            materias = await RepositorioMaterias(sessao).listar(usuario_id)
            contagens = await self._registro.contar_por_materia(sessao, usuario_id)
        return [MateriaConsultada(m, contagens.get(m.id, ContagensAcervo())) for m in materias]

    async def consultar(self, usuario_id: int, public_id: UUID) -> MateriaConsultada:
        async with unidade_de_trabalho(self._fabrica) as sessao:
            materia = await RepositorioMaterias(sessao).buscar(usuario_id, public_id)
            contagens = await self._registro.contar_por_materia(sessao, usuario_id)
        return MateriaConsultada(materia, contagens.get(materia.id, ContagensAcervo()))
