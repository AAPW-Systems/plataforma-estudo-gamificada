"""Exceções do domínio `identidade`, convertidas no corpo `Erro` pelos handlers centrais."""

from __future__ import annotations

from app.nucleo.codigos import CodigoErro
from app.nucleo.erros import Conflito, EntradaInvalida, ErroCampo, NaoAutenticado

MENSAGEM_EMAIL_EM_USO = "Este e-mail já está em uso."


class ValorInvalido(ValueError):
    """Regra de domínio violada por um valor; a mensagem já é para o estudante."""

    def __init__(self, mensagem: str) -> None:
        self.mensagem = mensagem
        super().__init__(mensagem)


class EmailEmUso(Conflito):
    """409 do cadastro (D-005): o único caso em que a API revela que o e-mail tem conta."""

    codigo_padrao = CodigoErro.EMAIL_EM_USO
    mensagem_padrao = MENSAGEM_EMAIL_EM_USO

    def __init__(self) -> None:
        super().__init__(campos=[ErroCampo("email", MENSAGEM_EMAIL_EM_USO)])


class CredenciaisInvalidas(NaoAutenticado):
    """401 da entrada: a mesma resposta para e-mail inexistente e senha errada (RF-004)."""

    codigo_padrao = CodigoErro.CREDENCIAIS_INVALIDAS
    mensagem_padrao = "E-mail ou senha incorretos."


class SenhaAtualIncorreta(EntradaInvalida):
    """422 da troca de senha e da exclusão da conta (US4); conta para o limite da conta."""

    codigo_padrao = CodigoErro.SENHA_ATUAL_INCORRETA
    mensagem_padrao = "A senha atual está incorreta."

    def __init__(self) -> None:
        super().__init__(campos=[ErroCampo("senhaAtual", self.mensagem_padrao)])
