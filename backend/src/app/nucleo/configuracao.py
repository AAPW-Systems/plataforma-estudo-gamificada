"""Configuração da aplicação, validada ao iniciar (plano da 001, "Variáveis de ambiente").

A aplicação não sobe com valor ausente ou inválido: `obter_configuracao()` lança
`pydantic.ValidationError` e o processo termina antes de aceitar requisições.
"""

from __future__ import annotations

import ipaddress
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

TAMANHO_MINIMO_SEGREDO = 32

RedeConfiavel = ipaddress.IPv4Network | ipaddress.IPv6Network


def _separar_por_virgula(valor: object) -> object:
    if isinstance(valor, str):
        return [parte.strip() for parte in valor.split(",") if parte.strip()]
    return valor


class Configuracao(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", frozen=True, case_sensitive=False)

    app_ambiente: Literal["desenvolvimento", "teste", "producao"] = "desenvolvimento"

    postgres_user: str = Field(min_length=1)
    postgres_password: SecretStr
    postgres_db: str = Field(min_length=1)
    postgres_host: str = "db"
    postgres_port: int = Field(default=5432, ge=1, le=65535)

    segredo_aplicacao: SecretStr

    origens_permitidas: Annotated[list[str], NoDecode] = Field(min_length=1)
    proxies_confiaveis: Annotated[list[RedeConfiavel], NoDecode] = Field(default_factory=list)

    cookie_sessao_nome: str = Field(default="__Host-sessao", pattern=r"^[A-Za-z0-9_-]{1,64}$")
    cookie_csrf_nome: str = Field(default="__Host-csrf", pattern=r"^[A-Za-z0-9_-]{1,64}$")

    sessao_dias_inatividade: int = Field(default=14, ge=1, le=365)
    sessao_dias_maximo: int = Field(default=30, ge=1, le=365)

    limite_falhas_conta: int = Field(default=5, ge=1, le=1000)
    limite_falhas_ip: int = Field(default=20, ge=1, le=10000)
    janela_tentativas_min: int = Field(default=15, ge=1, le=1440)
    bloqueio_min: int = Field(default=15, ge=1, le=1440)
    limite_cadastros_ip_hora: int = Field(default=10, ge=1, le=10000)

    argon2_concorrencia: int = Field(default=4, ge=1, le=64)

    armazenamento_adaptador: Literal["local", "memoria"] = "local"
    armazenamento_diretorio: Path = Path("/dados/arquivos")

    # Acervo (spec 002, RQ-005): limites por ambiente, expostos em GET /acervo/uso.
    fonte_tamanho_max_bytes: int = Field(default=2_097_152, ge=1)
    pdf_max_paginas: int = Field(default=500, ge=1)
    cota_materias: int = Field(default=50, ge=1)
    cota_fontes_por_materia: int = Field(default=30, ge=1)
    cota_armazenamento_bytes: int = Field(default=104_857_600, ge=1)
    trecho_tamanho_alvo: int = Field(default=1200, ge=1)
    trecho_tamanho_maximo: int = Field(default=2000, ge=1)
    trecho_sobreposicao: int = Field(default=150, ge=0)
    # Subprocesso de validação (API) e de extração (worker), DTEC 024.
    validacao_arquivo_tempo_s: int = Field(default=10, ge=1)
    validacao_arquivo_memoria_mb: int = Field(default=256, ge=1)
    validacao_arquivo_concorrencia: int = Field(default=2, ge=1)
    extracao_tempo_s: int = Field(default=30, ge=1)
    extracao_memoria_mb: int = Field(default=512, ge=1)
    reconciliacao_margem_min: int = Field(default=60, ge=1)
    fila_segundos_travado: int = Field(default=60, ge=1)

    log_nivel: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("origens_permitidas", "proxies_confiaveis", mode="before")
    @classmethod
    def _lista(cls, valor: object) -> object:
        return _separar_por_virgula(valor)

    @field_validator("origens_permitidas")
    @classmethod
    def _origens_validas(cls, origens: list[str]) -> list[str]:
        for origem in origens:
            if not origem.startswith(("http://", "https://")) or origem.endswith("/"):
                raise ValueError(f"origem inválida: {origem!r} (use esquema://host[:porta])")
        return origens

    @field_validator("proxies_confiaveis", mode="before")
    @classmethod
    def _redes(cls, valor: object) -> object:
        if isinstance(valor, list):
            return [ipaddress.ip_network(str(item), strict=False) for item in valor]
        return valor

    @field_validator("segredo_aplicacao")
    @classmethod
    def _segredo_forte(cls, segredo: SecretStr) -> SecretStr:
        if len(segredo.get_secret_value().encode()) < TAMANHO_MINIMO_SEGREDO:
            raise ValueError(
                f"SEGREDO_APLICACAO precisa de pelo menos {TAMANHO_MINIMO_SEGREDO} bytes"
            )
        return segredo

    @model_validator(mode="after")
    def _coerencia(self) -> Configuracao:
        if self.sessao_dias_inatividade > self.sessao_dias_maximo:
            raise ValueError("SESSAO_DIAS_INATIVIDADE não pode passar de SESSAO_DIAS_MAXIMO")
        if self.trecho_sobreposicao >= self.trecho_tamanho_alvo:
            raise ValueError("TRECHO_SOBREPOSICAO precisa ser menor que TRECHO_TAMANHO_ALVO")
        if self.trecho_tamanho_alvo > self.trecho_tamanho_maximo:
            raise ValueError("TRECHO_TAMANHO_ALVO não pode passar de TRECHO_TAMANHO_MAXIMO")
        if self.cota_armazenamento_bytes < self.fonte_tamanho_max_bytes:
            raise ValueError("COTA_ARMAZENAMENTO_BYTES não pode ser menor que um arquivo")
        if self.app_ambiente == "producao":
            if not (
                self.cookie_sessao_nome.startswith("__Host-")
                and self.cookie_csrf_nome.startswith("__Host-")
            ):
                raise ValueError("em produção, os cookies exigem o prefixo __Host-")
            if self.armazenamento_adaptador == "memoria":
                raise ValueError("o armazenamento em memória é só para testes")
        return self

    @property
    def em_desenvolvimento(self) -> bool:
        return self.app_ambiente == "desenvolvimento"

    @property
    def segredo(self) -> bytes:
        return self.segredo_aplicacao.get_secret_value().encode()

    def conninfo(self, banco: str | None = None) -> str:
        """Conninfo libpq (psycopg e Procrastinate), com os valores escapados."""
        from psycopg.conninfo import make_conninfo

        return make_conninfo(
            host=self.postgres_host,
            port=self.postgres_port,
            dbname=banco or self.postgres_db,
            user=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
        )


@lru_cache(maxsize=1)
def obter_configuracao() -> Configuracao:
    return Configuracao()
