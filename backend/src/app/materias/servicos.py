"""Casos de uso das matérias. Cada um controla a própria transação (DTEC 018)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import structlog

from app.materias import dominio
from app.materias.excecoes import ConfirmacaoInvalida, CotaMateriasExcedida, NomeInvalido
from app.materias.modelos import Materia
from app.materias.repositorios import RepositorioMaterias
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao
from app.nucleo.erros import ImpactoAlterado
from app.nucleo.participantes_acervo import ContagensAcervo, RegistroAcervo
from app.nucleo.relogio import Relogio
from app.nucleo.texto import ValorInvalido

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class MateriaConsultada:
    materia: Materia
    contagens: ContagensAcervo


@dataclass(frozen=True, slots=True)
class ImpactoConsultado:
    nome: str
    impacto: dominio.ImpactoMateria


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

    # --- Organizar (US3) ------------------------------------------------------------------------

    async def renomear(self, usuario_id: int, public_id: UUID, nome: str) -> MateriaConsultada:
        """Renomeia a matéria; o nome continua único por estudante, sem diferenciar caixa."""
        nome_valido = validar_nome(nome)
        async with unidade_de_trabalho(self._fabrica) as sessao:
            repositorio = RepositorioMaterias(sessao)
            materia = await repositorio.buscar(usuario_id, public_id, para_atualizar=True)
            await repositorio.renomear(materia, nome_valido, self._relogio.agora())
            contagens = await self._registro.contar_por_materia(sessao, usuario_id)
        logger.info("materia_renomeada", materia_public_id=str(materia.public_id))
        return MateriaConsultada(materia, contagens.get(materia.id, ContagensAcervo()))

    async def impacto_exclusao(self, usuario_id: int, public_id: UUID) -> ImpactoConsultado:
        """O que a exclusão apaga, para o diálogo. Só consulta: nada é gravado nem chamado."""
        async with unidade_de_trabalho(self._fabrica) as sessao:
            materia = await RepositorioMaterias(sessao).buscar(usuario_id, public_id)
            contagens = await self._registro.contar_por_materia(sessao, usuario_id)
            return ImpactoConsultado(
                materia.nome,
                dominio.impacto_da_materia(contagens.get(materia.id, ContagensAcervo())),
            )

    async def excluir(
        self,
        *,
        usuario_id: int,
        public_id: UUID,
        nome_confirmacao: str,
        impacto_confirmado: dominio.ImpactoMateria,
    ) -> None:
        """Exclui a matéria em cascata, numa transação (DTEC 031, 027 e 025).

        Ordem: `FOR UPDATE` na matéria; nome digitado (`422 confirmacao_invalida`); trava das
        fontes por `id` (e do que os participantes de cartões precisarem); recálculo do impacto,
        que recusa com `impacto_alterado` se difere do que o estudante viu; participantes por
        prioridade (cartões e gerações primeiro; `fontes` por último, com os objetos **antes**
        das linhas); a matéria. Qualquer falha desfaz as linhas, e a exclusão pode ser repetida.
        A exclusão não espera o worker: a transação B dele encontra a fonte apagada e termina
        sem gravar nada (CB-16).
        """
        async with unidade_de_trabalho(self._fabrica) as sessao:
            repositorio = RepositorioMaterias(sessao)
            materia = await repositorio.buscar(usuario_id, public_id, para_atualizar=True)
            if not dominio.confirmacao_confere(nome_confirmacao, materia.nome):
                raise ConfirmacaoInvalida()
            await self._registro.travar_materia(sessao, usuario_id, materia.id)
            contagens = await self._registro.contar_por_materia(sessao, usuario_id)
            atual = dominio.impacto_da_materia(contagens.get(materia.id, ContagensAcervo()))
            if atual != impacto_confirmado:
                raise ImpactoAlterado()
            await self._registro.ao_excluir_materia(sessao, usuario_id, materia.id)
            await repositorio.apagar(usuario_id, materia.id)
            materia_public_id = str(materia.public_id)
        logger.info(
            "materia_excluida",
            materia_public_id=materia_public_id,
            fontes=atual.fontes,
            cartoes_ativos=atual.cartoes_ativos,
            cartoes_aguardando_revisao=atual.cartoes_aguardando_revisao,
        )
