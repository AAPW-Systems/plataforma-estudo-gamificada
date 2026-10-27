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

    # Spec 002 (matérias e fontes)
    MATERIA_NOME_EM_USO = "materia_nome_em_uso"
    COTA_MATERIAS_EXCEDIDA = "cota_materias_excedida"
    COTA_FONTES_EXCEDIDA = "cota_fontes_excedida"
    COTA_ARMAZENAMENTO_EXCEDIDA = "cota_armazenamento_excedida"
    FONTE_DUPLICADA = "fonte_duplicada"
    ARQUIVO_MUITO_GRANDE = "arquivo_muito_grande"
    FORMATO_NAO_ACEITO = "formato_nao_aceito"
    TIPO_DIVERGENTE = "tipo_divergente"
    ARQUIVO_VAZIO = "arquivo_vazio"
    ARQUIVO_CORROMPIDO = "arquivo_corrompido"
    PDF_PROTEGIDO = "pdf_protegido"
    PDF_PAGINAS_EXCEDIDAS = "pdf_paginas_excedidas"
    CODIFICACAO_INVALIDA = "codificacao_invalida"
    CONFIRMACAO_INVALIDA = "confirmacao_invalida"
    IMPACTO_ALTERADO = "impacto_alterado"
    REPROCESSAMENTO_INDISPONIVEL = "reprocessamento_indisponivel"

    # Spec 003 (cartões)
    CURSOR_INVALIDO = "cursor_invalido"
