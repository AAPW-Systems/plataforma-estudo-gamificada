"""Códigos de erro estáveis do contrato, cumulativos entre as specs."""

from __future__ import annotations

from enum import StrEnum


class CodigoErro(StrEnum):
    """Códigos estáveis do contrato. As specs acrescentam; nunca renomeiam nem removem."""

    REQUISICAO_MALFORMADA = "requisicao_malformada"
    DADOS_INVALIDOS = "dados_invalidos"
    EMAIL_EM_USO = "email_em_uso"
    CREDENCIAIS_INVALIDAS = "credenciais_invalidas"
    SENHA_ATUAL_INCORRETA = "senha_atual_incorreta"
    NAO_AUTENTICADO = "nao_autenticado"
    CSRF_INVALIDO = "csrf_invalido"
    ORIGEM_NAO_PERMITIDA = "origem_nao_permitida"
    RECURSO_NAO_ENCONTRADO = "recurso_nao_encontrado"
    MUITAS_TENTATIVAS = "muitas_tentativas"
    ERRO_INTERNO = "erro_interno"
