"""Casos de uso da identidade: cadastro, entrada, saída e autenticação (T035).

Cada caso de uso controla as próprias transações. Os limites de tentativas seguem a DTEC 020:
o *advisory lock* é obtido antes da contagem, na mesma transação que registra a tentativa,
e fica até o fim dela. Assim, uma rajada paralela não passa do limite.
"""

from __future__ import annotations

import math
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.identidade import dominio, preferencias
from app.identidade.excecoes import CredenciaisInvalidas, SenhaAtualIncorreta, ValorInvalido
from app.identidade.modelos import Usuario
from app.identidade.repositorios import (
    RepositorioSessoes,
    RepositorioTentativas,
    RepositorioUsuarios,
)
from app.identidade.tarefas import apagar_objetos_usuario
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao
from app.nucleo.erros import EntradaInvalida, ErroCampo, LimiteExcedido, NaoAutenticado
from app.nucleo.exclusao import registro_exclusao
from app.nucleo.fila import enfileirar
from app.nucleo.relogio import Relogio
from app.nucleo.seguranca.senhas import ServicoSenhas
from app.nucleo.seguranca.sessoes import (
    calcular_expiracao,
    deve_renovar_uso,
    gerar_token,
    hash_token,
    sessao_valida,
    token_bem_formado,
)
from app.revisao.servicos import alterar_retencao, criar_parametros_iniciais, retencao_vigente

logger = structlog.get_logger(__name__)

JANELA_CADASTROS = timedelta(hours=1)

# Senha de mentira, aleatória a cada subida, para as entradas que não podem ser verificadas
# de verdade (longas demais ou que não codificam): gastam o mesmo custo e nunca autenticam.
_SENHA_DESCARTADA = secrets.token_urlsafe(64)


@dataclass(frozen=True, slots=True)
class ContextoRequisicao:
    ip: str
    agente_usuario: str | None


@dataclass(frozen=True, slots=True)
class PerfilConsultado:
    usuario: Usuario
    retencao_desejada: Decimal


@dataclass(frozen=True, slots=True)
class SessaoIniciada:
    perfil: PerfilConsultado
    token: str


@dataclass(frozen=True, slots=True)
class UsuarioAutenticado:
    usuario: Usuario
    sessao_id: int
    token_hash: bytes


def _chave_de_trava_conta(chave_conta: bytes) -> str:
    return f"acesso:conta:{chave_conta.hex()}"


def _chave_de_trava_ip(ip: str) -> str:
    return f"acesso:ip:{ip}"


def _segundos_ate(instante: datetime, agora: datetime) -> int:
    return max(1, math.ceil((instante - agora).total_seconds()))


class ServicoIdentidade:
    def __init__(
        self,
        *,
        fabrica: FabricaSessoes,
        configuracao: Configuracao,
        relogio: Relogio,
        senhas: ServicoSenhas,
        senhas_comuns: frozenset[str],
    ) -> None:
        self._fabrica = fabrica
        self._configuracao = configuracao
        self._relogio = relogio
        self._senhas = senhas
        self._senhas_comuns = senhas_comuns

    # --- Cadastro ------------------------------------------------------------------------

    async def cadastrar(
        self, *, nome: str, email: str, senha: str, fuso: str | None, contexto: ContextoRequisicao
    ) -> SessaoIniciada:
        validado = dominio.validar_cadastro(
            nome=nome, email=email, senha=senha, fuso=fuso, senhas_comuns=self._senhas_comuns
        )
        await self._registrar_tentativa_de_cadastro(contexto.ip)
        senha_hash = await self._senhas.gerar_hash(validado.senha)

        agora = self._relogio.agora()
        async with unidade_de_trabalho(self._fabrica) as sessao:
            usuario = await RepositorioUsuarios(sessao).criar(
                nome=validado.nome,
                email=validado.email,
                senha_hash=senha_hash,
                fuso=validado.fuso,
                agora=agora,
            )
            retencao = preferencias.RETENCAO_DESEJADA.padrao
            await criar_parametros_iniciais(sessao, usuario.id, agora, retencao)
            token = await self._abrir_sessao(sessao, usuario.id, contexto, agora)
        logger.info("conta_criada", usuario_public_id=str(usuario.public_id))
        return SessaoIniciada(PerfilConsultado(usuario, retencao), token)

    async def _registrar_tentativa_de_cadastro(self, ip: str) -> None:
        """Limite de cadastros por endereço (RQ-003): conta e registra sob a mesma trava."""
        agora = self._relogio.agora()
        async with unidade_de_trabalho(self._fabrica) as sessao:
            tentativas = RepositorioTentativas(sessao)
            await tentativas.travar(f"acesso:cadastro:{ip}")
            anteriores = await tentativas.instantes_cadastros_ip(ip, agora - JANELA_CADASTROS)
            liberado_em = dominio.liberado_cadastro_em(
                anteriores,
                agora=agora,
                limite=self._configuracao.limite_cadastros_ip_hora,
                janela=JANELA_CADASTROS,
            )
            if liberado_em is not None:
                segundos = _segundos_ate(liberado_em, agora)
                logger.warning("bloqueio_aplicado", tipo="cadastro", segundos=segundos)
                raise LimiteExcedido(segundos)
            await tentativas.registrar("cadastro", None, ip, agora)

    # --- Entrada -------------------------------------------------------------------------

    async def entrar(
        self, *, email: str, senha: str, contexto: ContextoRequisicao
    ) -> SessaoIniciada:
        email_normalizado = dominio.normalizar_email_de_entrada(email)
        chave = dominio.chave_da_conta(self._configuracao.segredo, email_normalizado)
        ip = contexto.ip
        verificavel = len(senha) <= preferencias.SENHA_MAXIMA and dominio.senha_codificavel(senha)

        agora = self._relogio.agora()
        iniciada: SessaoIniciada | None = None
        async with unidade_de_trabalho(self._fabrica) as sessao:
            tentativas = RepositorioTentativas(sessao)
            await tentativas.travar(_chave_de_trava_conta(chave), _chave_de_trava_ip(ip))
            await self._recusar_se_bloqueado(tentativas, chave, ip, agora)

            usuarios = RepositorioUsuarios(sessao)
            usuario = await usuarios.buscar_por_email(email_normalizado)
            if usuario is None or not verificavel:
                # Mesmo custo de uma verificação real, para o tempo não revelar a conta (CS-003).
                await self._senhas.verificar_ficticia(senha if verificavel else _SENHA_DESCARTADA)
                autenticado = False
            else:
                autenticado = await self._senhas.verificar(usuario.senha_hash, senha)

            if not autenticado or usuario is None:
                await tentativas.registrar("falha_entrada", chave, ip, agora)
            else:
                await tentativas.apagar_falhas_conta(chave)
                if self._senhas.precisa_novo_hash(usuario.senha_hash):
                    novo_hash = await self._senhas.gerar_hash(senha)
                    await usuarios.atualizar_senha_hash(usuario.id, novo_hash, agora)
                token = await self._abrir_sessao(sessao, usuario.id, contexto, agora)
                retencao = await retencao_vigente(sessao, usuario.id)
                iniciada = SessaoIniciada(PerfilConsultado(usuario, retencao), token)

        if iniciada is None:
            # Depois do commit: a falha fica registrada mesmo com a resposta de erro.
            logger.warning("entrada_recusada")
            raise CredenciaisInvalidas()
        return iniciada

    async def _recusar_se_bloqueado(
        self, tentativas: RepositorioTentativas, chave: bytes, ip: str, agora: datetime
    ) -> None:
        configuracao = self._configuracao
        janela = timedelta(minutes=configuracao.janela_tentativas_min)
        bloqueio = timedelta(minutes=configuracao.bloqueio_min)
        desde = agora - (janela + bloqueio)
        fins = [
            dominio.bloqueado_ate(
                await tentativas.instantes_falhas_conta(chave, desde),
                limite=configuracao.limite_falhas_conta,
                janela=janela,
                bloqueio=bloqueio,
            ),
            dominio.bloqueado_ate(
                await tentativas.instantes_falhas_ip(ip, desde),
                limite=configuracao.limite_falhas_ip,
                janela=janela,
                bloqueio=bloqueio,
            ),
        ]
        ativos = [fim for fim in fins if fim is not None and fim > agora]
        if ativos:
            segundos = _segundos_ate(max(ativos), agora)
            logger.warning("bloqueio_aplicado", tipo="entrada", segundos=segundos)
            raise LimiteExcedido(segundos)

    # --- Sessão --------------------------------------------------------------------------

    async def _abrir_sessao(
        self, sessao: AsyncSession, usuario_id: int, contexto: ContextoRequisicao, agora: datetime
    ) -> str:
        token = gerar_token()
        await RepositorioSessoes(sessao).criar(
            usuario_id=usuario_id,
            token_hash=hash_token(token),
            agora=agora,
            expira_em=calcular_expiracao(agora, self._configuracao.sessao_dias_maximo),
            ip=contexto.ip,
            agente_usuario=contexto.agente_usuario,
        )
        return token

    async def sair(self, token: str | None) -> None:
        """Revoga a sessão no servidor. Sem sessão válida, não faz nada (idempotente)."""
        if not token_bem_formado(token):
            return
        agora = self._relogio.agora()
        async with unidade_de_trabalho(self._fabrica) as sessao:
            repositorio = RepositorioSessoes(sessao)
            achada = await repositorio.buscar_por_hash(hash_token(token))
            if achada is None or achada[0].revogada_em is not None:
                return
            await repositorio.revogar(achada[0].id, agora)
            usuario = achada[1]
        logger.info("sessao_revogada", usuario_public_id=str(usuario.public_id))

    async def autenticar(self, token: str | None) -> UsuarioAutenticado:
        """Resolve a sessão do cookie; qualquer falha é a mesma `NaoAutenticado` (RF-006)."""
        if not token_bem_formado(token):
            raise NaoAutenticado()
        agora = self._relogio.agora()
        digest = hash_token(token)
        async with unidade_de_trabalho(self._fabrica) as sessao:
            repositorio = RepositorioSessoes(sessao)
            achada = await repositorio.buscar_por_hash(digest)
            if achada is None:
                raise NaoAutenticado()
            sessao_achada, usuario = achada
            if not sessao_valida(
                agora=agora,
                expira_em=sessao_achada.expira_em,
                ultimo_uso_em=sessao_achada.ultimo_uso_em,
                revogada_em=sessao_achada.revogada_em,
                dias_inatividade=self._configuracao.sessao_dias_inatividade,
            ):
                raise NaoAutenticado()
            if deve_renovar_uso(sessao_achada.ultimo_uso_em, agora):
                await repositorio.renovar_uso(sessao_achada.id, agora)
        return UsuarioAutenticado(usuario, sessao_achada.id, digest)

    # --- Perfil --------------------------------------------------------------------------

    async def consultar_perfil(self, usuario_id: int) -> PerfilConsultado:
        async with unidade_de_trabalho(self._fabrica) as sessao:
            usuario = await RepositorioUsuarios(sessao).buscar_por_id(usuario_id)
            if usuario is None:
                raise NaoAutenticado()
            return PerfilConsultado(usuario, await retencao_vigente(sessao, usuario_id))

    async def alterar_perfil(
        self, usuario_id: int, enviados: Mapping[str, Any]
    ) -> PerfilConsultado:
        """Altera nome, fuso e preferências, tudo ou nada (RF-008, RF-010).

        A validação acontece antes de qualquer escrita. A linha do usuário é travada
        (`FOR UPDATE`) durante a escrita, o que serializa alterações concorrentes e, com elas,
        as novas versões dos parâmetros do FSRS.
        """
        alteracao = dominio.validar_alteracao_perfil(enviados)
        agora = self._relogio.agora()
        async with unidade_de_trabalho(self._fabrica) as sessao:
            usuarios = RepositorioUsuarios(sessao)
            usuario = await usuarios.travar_por_id(usuario_id)
            if usuario is None:
                raise NaoAutenticado()
            await usuarios.aplicar_alteracao(usuario, alteracao, agora)
            if alteracao.retencao_desejada is not None:
                retencao = await alterar_retencao(
                    sessao, usuario_id, alteracao.retencao_desejada, agora
                )
            else:
                retencao = await retencao_vigente(sessao, usuario_id)
        return PerfilConsultado(usuario, retencao)

    # --- Troca de senha e exclusão da conta (US4) ------------------------------------------

    async def _senha_atual_confere(
        self,
        usuario: Usuario,
        senha_atual: str,
        tentativas: RepositorioTentativas,
        chave: bytes,
        ip: str,
        agora: datetime,
    ) -> bool:
        """Verifica a senha atual; uma falha é registrada e conta para o limite da conta."""
        verificavel = len(senha_atual) <= preferencias.SENHA_MAXIMA and dominio.senha_codificavel(
            senha_atual
        )
        if verificavel:
            confere = await self._senhas.verificar(usuario.senha_hash, senha_atual)
        else:
            await self._senhas.verificar_ficticia(_SENHA_DESCARTADA)
            confere = False
        if not confere:
            await tentativas.registrar("falha_senha_atual", chave, ip, agora)
        return confere

    async def trocar_senha(
        self,
        *,
        atual: UsuarioAutenticado,
        senha_atual: str,
        nova_senha: str,
        contexto: ContextoRequisicao,
    ) -> None:
        """Troca a senha e encerra as outras sessões (RF-014, D-004).

        Limite da conta, depois senha atual (a falha conta como `falha_senha_atual`), depois a
        validação da nova senha. Tudo sob a trava da conta, como a entrada.
        """
        agora = self._relogio.agora()
        erro: SenhaAtualIncorreta | None = None
        async with unidade_de_trabalho(self._fabrica) as sessao:
            tentativas = RepositorioTentativas(sessao)
            usuarios = RepositorioUsuarios(sessao)
            usuario = await usuarios.buscar_por_id(atual.usuario.id)
            if usuario is None:
                raise NaoAutenticado()
            chave = dominio.chave_da_conta(self._configuracao.segredo, usuario.email)
            await tentativas.travar(_chave_de_trava_conta(chave), _chave_de_trava_ip(contexto.ip))
            await self._recusar_se_bloqueado(tentativas, chave, contexto.ip, agora)
            # Relê o usuário sob a trava: uma troca concorrente já pode ter mudado o hash.
            usuario = await usuarios.buscar_por_id(atual.usuario.id)
            if usuario is None:
                raise NaoAutenticado()

            if not await self._senha_atual_confere(
                usuario, senha_atual, tentativas, chave, contexto.ip, agora
            ):
                erro = SenhaAtualIncorreta()
            else:
                try:
                    nova = dominio.validar_senha(nova_senha, self._senhas_comuns)
                except ValorInvalido as invalido:
                    raise EntradaInvalida(
                        campos=[ErroCampo("novaSenha", invalido.mensagem)]
                    ) from None
                novo_hash = await self._senhas.gerar_hash(nova)
                await usuarios.atualizar_senha_hash(usuario.id, novo_hash, agora)
                await RepositorioSessoes(sessao).revogar_outras(usuario.id, atual.sessao_id, agora)
                await tentativas.apagar_falhas_conta(chave)

        if erro is not None:
            logger.warning("senha_atual_recusada", operacao="troca_de_senha")
            raise erro
        logger.info("senha_trocada", usuario_public_id=str(usuario.public_id))

    async def excluir_conta(
        self, *, atual: UsuarioAutenticado, senha_atual: str, contexto: ContextoRequisicao
    ) -> None:
        """Apaga a conta e enfileira a remoção dos objetos, numa só transação (RF-015, DTEC 021).

        A linha do usuário é travada (`FOR UPDATE`): um segundo pedido em paralelo espera, não
        encontra mais o usuário e recebe `401`. Há um único efeito.
        """
        agora = self._relogio.agora()
        erro: SenhaAtualIncorreta | None = None
        public_id: str | None = None
        async with unidade_de_trabalho(self._fabrica) as sessao:
            tentativas = RepositorioTentativas(sessao)
            usuarios = RepositorioUsuarios(sessao)
            usuario = await usuarios.buscar_por_id(atual.usuario.id)
            if usuario is None:
                raise NaoAutenticado()
            chave = dominio.chave_da_conta(self._configuracao.segredo, usuario.email)
            await tentativas.travar(_chave_de_trava_conta(chave), _chave_de_trava_ip(contexto.ip))
            await self._recusar_se_bloqueado(tentativas, chave, contexto.ip, agora)
            usuario = await usuarios.travar_por_id(atual.usuario.id)
            if usuario is None:
                raise NaoAutenticado()

            if not await self._senha_atual_confere(
                usuario, senha_atual, tentativas, chave, contexto.ip, agora
            ):
                erro = SenhaAtualIncorreta()
            else:
                public_id = str(usuario.public_id)
                await registro_exclusao.apagar_dados_usuario(sessao, usuario.id)
                await tentativas.apagar_falhas_conta(chave)
                await enfileirar(
                    sessao,
                    apagar_objetos_usuario,
                    queueing_lock=f"apagar-objetos-{public_id}",
                    public_id=public_id,
                )

        if erro is not None:
            logger.warning("senha_atual_recusada", operacao="exclusao_da_conta")
            raise erro
        logger.info("conta_excluida", usuario_public_id=public_id)
