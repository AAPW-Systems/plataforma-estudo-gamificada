"""Casos de uso das fontes (spec 002): envio, consulta, listagem e nova tentativa.

O envio segue o plano (DTEC 025, 028 e 032): matéria do estudante, título, arquivo temporário
com SHA-256, validação por conteúdo, pré-verificação sem trava, objeto gravado **antes** da
linha, e uma transação sob *advisory lock* que confere as cotas, insere a fonte e enfileira o
processamento. Qualquer erro depois da gravação apaga o objeto.
"""

from __future__ import annotations

import asyncio
import hashlib
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

import structlog
from procrastinate.exceptions import AlreadyEnqueued
from sqlalchemy.ext.asyncio import AsyncSession

from app.fontes import dominio, validacao
from app.fontes.dominio import EstadoFonte
from app.fontes.excecoes import (
    ArquivoMuitoGrande,
    ArquivoRecusado,
    CotaArmazenamentoExcedida,
    CotaFontesExcedida,
    FonteDuplicada,
    ReprocessamentoIndisponivel,
    TituloInvalido,
)
from app.fontes.modelos import Fonte
from app.fontes.repositorios import RepositorioFontes
from app.fontes.tarefas import processar_fonte
from app.fontes.validacao import ArquivoValidado, LimitesValidacao
from app.materias.repositorios import RepositorioMaterias
from app.nucleo.armazenamento import Armazenamento
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao
from app.nucleo.erros import ImpactoAlterado
from app.nucleo.fila import enfileirar as enfileirar
from app.nucleo.participantes_acervo import ContagensAcervo, ModoCartoes, RegistroAcervo
from app.nucleo.relogio import Relogio, RelogioSistema
from app.nucleo.texto import ValorInvalido

logger = structlog.get_logger(__name__)

TAMANHO_DO_BLOCO = 1024 * 1024


@dataclass(frozen=True, slots=True)
class FonteConsultada:
    fonte: Fonte
    materia_public_id: UUID


@dataclass(frozen=True, slots=True)
class ImpactoConsultado:
    titulo: str
    estado: EstadoFonte
    contagens: ContagensAcervo


@dataclass(frozen=True, slots=True)
class UsoDoAcervo:
    tamanho_maximo_bytes: int
    extensoes_aceitas: tuple[str, ...]
    paginas_maximas_pdf: int
    cota_materias: int
    total_materias: int
    cota_fontes_por_materia: int
    cota_armazenamento_bytes: int
    uso_armazenamento_bytes: int


def validar_titulo(valor: str) -> str:
    try:
        return dominio.validar_titulo(valor)
    except ValorInvalido as erro:
        raise TituloInvalido(erro.mensagem) from None


class ServicoFontes:
    def __init__(
        self,
        fabrica: FabricaSessoes,
        configuracao: Configuracao,
        armazenamento: Armazenamento,
        registro_acervo: RegistroAcervo,
        relogio: Relogio | None = None,
    ) -> None:
        self._fabrica = fabrica
        self._configuracao = configuracao
        self._armazenamento = armazenamento
        self._registro = registro_acervo
        self._relogio = relogio or RelogioSistema()
        # Aberturas simultâneas de PDF na API (DTEC 024): as demais esperam a vez.
        self._semaforo = asyncio.Semaphore(configuracao.validacao_arquivo_concorrencia)

    @property
    def _limites(self) -> LimitesValidacao:
        c = self._configuracao
        return LimitesValidacao(
            tamanho_max_bytes=c.fonte_tamanho_max_bytes,
            max_paginas=c.pdf_max_paginas,
            tempo_s=c.validacao_arquivo_tempo_s,
            memoria_mb=c.validacao_arquivo_memoria_mb,
        )

    # --- Envio ----------------------------------------------------------------------------------

    async def enviar(
        self,
        *,
        usuario_id: int,
        usuario_public_id: UUID,
        materia_id: UUID,
        nome_enviado: str,
        origem: BinaryIO,
        titulo: str | None,
    ) -> FonteConsultada:
        # A matéria é do estudante? Antes de tocar no arquivo: quem não é dono não gasta trabalho.
        async with unidade_de_trabalho(self._fabrica) as sessao:
            materia = await RepositorioMaterias(sessao).buscar(usuario_id, materia_id)
            materia_interno, materia_publico = materia.id, materia.public_id
        titulo_final = (
            validar_titulo(titulo)
            if titulo is not None
            else dominio.titulo_padrao(dominio.nome_exibido(nome_enviado))
        )
        diretorio = Path(await asyncio.to_thread(tempfile.mkdtemp))
        chave: str | None = None
        try:
            try:
                caminho = diretorio / "recebido"
                hash_sha256, tamanho = await asyncio.to_thread(
                    _copiar_calculando_hash, origem, caminho, self._limites.tamanho_max_bytes
                )
                validado = await validacao.validar_arquivo(
                    nome_enviado, caminho, tamanho, self._limites, semaforo=self._semaforo
                )
                await self._preverificar(usuario_id, materia_interno, hash_sha256, tamanho)
                chave = f"usuarios/{usuario_public_id}/fontes/{uuid.uuid4()}"
                await self._armazenamento.gravar(chave, caminho)
                fonte = await self._inserir(
                    usuario_id=usuario_id,
                    materia_id=materia_interno,
                    titulo=titulo_final,
                    nome_enviado=nome_enviado,
                    chave=chave,
                    hash_sha256=hash_sha256,
                    tamanho=tamanho,
                    validado=validado,
                )
            except (ArquivoRecusado, ArquivoMuitoGrande, FonteDuplicada) as recusa:
                logger.info("fonte_recusada", codigo=str(recusa.codigo))
                raise
        except BaseException:
            if chave is not None:
                await self._compensar(chave)
            raise
        finally:
            await asyncio.to_thread(shutil.rmtree, diretorio, True)
        logger.info(
            "fonte_recebida",
            fonte_public_id=str(fonte.public_id),
            usuario_public_id=str(usuario_public_id),
            tipo=fonte.tipo_midia,
            tamanho_bytes=fonte.tamanho_bytes,
        )
        return FonteConsultada(fonte, materia_publico)

    async def _preverificar(
        self, usuario_id: int, materia_id: int, hash_sha256: bytes, tamanho: int
    ) -> None:
        """Falha cedo, antes de gravar o objeto, quando a recusa já é certa (sem trava)."""
        async with unidade_de_trabalho(self._fabrica) as sessao:
            await self._conferir(sessao, usuario_id, materia_id, hash_sha256, tamanho)

    async def _conferir(
        self,
        sessao: AsyncSession,
        usuario_id: int,
        materia_id: int,
        hash_sha256: bytes,
        tamanho: int,
    ) -> None:
        repositorio = RepositorioFontes(sessao)
        existente = await repositorio.titulo_do_conteudo(materia_id, usuario_id, hash_sha256)
        if existente is not None:
            raise FonteDuplicada(existente)
        c = self._configuracao
        if await repositorio.contar_da_materia(materia_id, usuario_id) >= c.cota_fontes_por_materia:
            raise CotaFontesExcedida(c.cota_fontes_por_materia)
        if await repositorio.somar_tamanho(usuario_id) + tamanho > c.cota_armazenamento_bytes:
            raise CotaArmazenamentoExcedida(c.cota_armazenamento_bytes)

    async def _inserir(
        self,
        *,
        usuario_id: int,
        materia_id: int,
        titulo: str,
        nome_enviado: str,
        chave: str,
        hash_sha256: bytes,
        tamanho: int,
        validado: ArquivoValidado,
    ) -> Fonte:
        agora = self._relogio.agora()
        async with unidade_de_trabalho(self._fabrica) as sessao:
            await RepositorioMaterias(sessao).travar_acervo(usuario_id)
            await self._conferir(sessao, usuario_id, materia_id, hash_sha256, tamanho)
            fonte = await RepositorioFontes(sessao).inserir(
                Fonte(
                    usuario_id=usuario_id,
                    materia_id=materia_id,
                    titulo=titulo,
                    nome_arquivo=dominio.nome_exibido(nome_enviado),
                    chave_objeto=chave,
                    tipo_midia=validado.tipo_midia,
                    tamanho_bytes=tamanho,
                    hash_sha256=hash_sha256,
                    estado=EstadoFonte.PENDENTE.value,
                    total_paginas=validado.total_paginas,
                    criado_em=agora,
                    atualizado_em=agora,
                )
            )
            # Na mesma transação: sem a linha, não há job; sem o job, não há linha (DTEC 030).
            await enfileirar(
                sessao,
                processar_fonte,
                queueing_lock=f"fonte:{fonte.id}",
                lock=f"fonte:{fonte.id}",
                fonte_id=fonte.id,
            )
        return fonte

    async def _compensar(self, chave: str) -> None:
        """Apaga o objeto gravado quando a linha não chegou a existir (DTEC 025)."""
        try:
            await asyncio.shield(self._armazenamento.apagar(chave))
            logger.warning("objeto_compensado")
        except Exception:
            # A reconciliação diária remove o que sobrar; só o tipo vai ao log.
            logger.exception("objeto_compensado_falhou")

    # --- Consultas ------------------------------------------------------------------------------

    async def listar(self, usuario_id: int, materia_id: UUID) -> list[FonteConsultada]:
        async with unidade_de_trabalho(self._fabrica) as sessao:
            materia = await RepositorioMaterias(sessao).buscar(usuario_id, materia_id)
            fontes = await RepositorioFontes(sessao).listar_da_materia(usuario_id, materia.id)
            publico = materia.public_id
        return [FonteConsultada(f, publico) for f in fontes]

    async def consultar(self, usuario_id: int, fonte_id: UUID) -> FonteConsultada:
        async with unidade_de_trabalho(self._fabrica) as sessao:
            repositorio = RepositorioFontes(sessao)
            fonte = await repositorio.buscar(usuario_id, fonte_id)
            return FonteConsultada(fonte, await repositorio.materia_publica(fonte))

    async def uso_do_acervo(self, usuario_id: int) -> UsoDoAcervo:
        c = self._configuracao
        async with unidade_de_trabalho(self._fabrica) as sessao:
            total_materias = await RepositorioMaterias(sessao).contar(usuario_id)
            uso = await RepositorioFontes(sessao).somar_tamanho(usuario_id)
        return UsoDoAcervo(
            tamanho_maximo_bytes=c.fonte_tamanho_max_bytes,
            extensoes_aceitas=validacao.EXTENSOES_ACEITAS,
            paginas_maximas_pdf=c.pdf_max_paginas,
            cota_materias=c.cota_materias,
            total_materias=total_materias,
            cota_fontes_por_materia=c.cota_fontes_por_materia,
            cota_armazenamento_bytes=c.cota_armazenamento_bytes,
            uso_armazenamento_bytes=uso,
        )

    # --- Nova tentativa -------------------------------------------------------------------------

    async def reprocessar(self, usuario_id: int, fonte_id: UUID) -> FonteConsultada:
        """`falhou` com `falha_tecnica` volta a `pendente` e é enfileirada de novo (US1-6)."""
        async with unidade_de_trabalho(self._fabrica) as sessao:
            repositorio = RepositorioFontes(sessao)
            fonte = await repositorio.buscar(usuario_id, fonte_id, para_atualizar=True)
            estado = EstadoFonte(fonte.estado)
            codigo = dominio.CodigoFalha(fonte.codigo_falha) if fonte.codigo_falha else None
            if not dominio.transicao_permitida(estado, EstadoFonte.PENDENTE, codigo_atual=codigo):
                raise ReprocessamentoIndisponivel()
            fonte.estado = EstadoFonte.PENDENTE.value
            fonte.codigo_falha = None
            fonte.atualizado_em = self._relogio.agora()
            await sessao.flush()
            try:
                # Savepoint: um job já na fila (AlreadyEnqueued) é sucesso e não aborta a transação.
                async with sessao.begin_nested():
                    await enfileirar(
                        sessao,
                        processar_fonte,
                        queueing_lock=f"fonte:{fonte.id}",
                        lock=f"fonte:{fonte.id}",
                        fonte_id=fonte.id,
                    )
            except AlreadyEnqueued:
                logger.info("reprocessamento_ja_enfileirado")
            publico = await repositorio.materia_publica(fonte)
        return FonteConsultada(fonte, publico)

    # --- Exclusão (DTEC 031) --------------------------------------------------------------------

    async def impacto_exclusao(self, usuario_id: int, fonte_id: UUID) -> ImpactoConsultado:
        """O que a exclusão afeta, para o diálogo. Só consulta: nada é gravado nem chamado."""
        async with unidade_de_trabalho(self._fabrica) as sessao:
            fonte = await RepositorioFontes(sessao).buscar(usuario_id, fonte_id)
            contagens = await self._registro.impacto_fonte(sessao, usuario_id, fonte.id)
            return ImpactoConsultado(fonte.titulo, EstadoFonte(fonte.estado), contagens)

    async def excluir(
        self,
        *,
        usuario_id: int,
        usuario_public_id: UUID,
        fonte_id: UUID,
        modo: ModoCartoes,
        impacto_confirmado: ContagensAcervo,
    ) -> None:
        """Exclui a fonte numa transação: trava, confere o impacto, apaga o objeto e as linhas.

        Ordem (DTEC 031 e 025): `FOR UPDATE` na fonte; recálculo do impacto, que recusa com
        `impacto_alterado` se difere do que o estudante viu; objeto **antes** das linhas;
        participantes (cartões e gerações) com o modo escolhido; trechos e fonte. Qualquer
        falha desfaz as linhas, e a exclusão pode ser repetida. A exclusão não espera o worker:
        a transação B dele encontra a fonte apagada e termina sem gravar nada (CB-16).
        """
        async with unidade_de_trabalho(self._fabrica) as sessao:
            repositorio = RepositorioFontes(sessao)
            fonte = await repositorio.buscar(usuario_id, fonte_id, para_atualizar=True)
            atual = await self._registro.impacto_fonte(sessao, usuario_id, fonte.id)
            if not dominio.impacto_confere(impacto_confirmado, atual):
                raise ImpactoAlterado()
            await self._armazenamento.apagar(fonte.chave_objeto)
            await self._registro.ao_excluir_fonte(sessao, usuario_id, fonte.id, modo)
            await repositorio.apagar(fonte.id)
            public_id = str(fonte.public_id)
        logger.info(
            "fonte_excluida",
            fonte_public_id=public_id,
            usuario_public_id=str(usuario_public_id),
            modo=modo.value,
            cartoes_gerados_aceitos=atual.cartoes_gerados_aceitos,
            cartoes_aguardando_revisao=atual.cartoes_aguardando_revisao,
            cartoes_referencia=atual.cartoes_referencia,
        )


def _copiar_calculando_hash(origem: BinaryIO, destino: Path, limite: int) -> tuple[bytes, int]:
    """Copia em blocos para o arquivo temporário, calculando o SHA-256 e o tamanho.

    Para ao passar de `limite` bytes (413), sem ler o resto.
    """
    resumo = hashlib.sha256()
    tamanho = 0
    origem.seek(0)
    with destino.open("wb") as saida:
        while bloco := origem.read(TAMANHO_DO_BLOCO):
            tamanho += len(bloco)
            if tamanho > limite:
                raise ArquivoMuitoGrande(limite)
            resumo.update(bloco)
            saida.write(bloco)
    return resumo.digest(), tamanho
