"""Configuração do provedor de IA, validada ao iniciar (DTEC 007, 039 e 040).

Só este domínio lê o provedor e as chaves (teste de arquitetura). A aplicação não sobe com o
provedor real sem a chave, nem com o provedor simulado (`teste`) em produção.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, get_args

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Provedor = Literal["gemini", "groq", "teste"]
PROVEDORES: tuple[Provedor, ...] = get_args(Provedor)


@dataclass(frozen=True, slots=True)
class AvisoProvedor:
    """Texto do aviso de envio ao provedor (DTEC 039). Mudar o texto exige mudar a versão."""

    versao: str
    paragrafos: tuple[str, ...]


_RECOMENDACAO = (
    "Não peça cartões de fontes com dados pessoais ou informações confidenciais, suas ou de "
    "outras pessoas."
)
_FINALIDADE = (
    "Para gerar cartões, enviamos ao {nome} só os trechos da fonte que você pediu. Nada de "
    "outras fontes, matérias ou da sua conta vai junto."
)

AVISOS: dict[Provedor, AvisoProvedor] = {
    "gemini": AvisoProvedor(
        versao="gemini-v1",
        paragrafos=(
            "A geração de cartões usa o Gemini, um serviço de IA externo do Google.",
            _FINALIDADE.format(nome="Gemini"),
            "Na camada gratuita, o Google pode usar o conteúdo enviado para melhorar os produtos "
            "dele, inclusive com leitura por pessoas.",
            _RECOMENDACAO,
        ),
    ),
    "groq": AvisoProvedor(
        versao="groq-v1",
        paragrafos=(
            "A geração de cartões usa o Groq, um serviço de IA externo.",
            _FINALIDADE.format(nome="Groq"),
            "O Groq processa o conteúdo enviado nos servidores dele, conforme a política de uso de "
            "dados do serviço.",
            _RECOMENDACAO,
        ),
    ),
    "teste": AvisoProvedor(
        versao="teste-v1",
        paragrafos=(
            "Ambiente de desenvolvimento: a geração usa um provedor simulado, sem rede.",
            _FINALIDADE.format(nome="provedor simulado"),
            _RECOMENDACAO,
        ),
    ),
}

# Modelos padrão por provedor (IA_MODELO_* vazios). O modelo efetivamente usado fica gravado em
# cada geração e no relatório de avaliação (RQ-006).
MODELOS_PADRAO: dict[Provedor, tuple[str, str]] = {
    "gemini": ("gemini-2.5-flash", "gemini-2.5-flash"),
    "groq": ("llama-3.3-70b-versatile", "llama-3.3-70b-versatile"),
    "teste": ("simulado", "simulado"),
}

_CHAVES: dict[Provedor, str] = {"gemini": "GEMINI_API_KEY", "groq": "GROQ_API_KEY"}


class ConfiguracaoIa(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", frozen=True, case_sensitive=False)

    app_ambiente: Literal["desenvolvimento", "teste", "producao"] = "desenvolvimento"
    ia_provedor: Provedor = "teste"
    ia_modelo_geracao: str = ""
    ia_modelo_verificador: str = ""
    gemini_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None
    ia_timeout_segundos: int = Field(default=60, ge=1, le=600)
    ia_orcamento_tokens_dia: int = Field(default=300_000, ge=1)

    @model_validator(mode="after")
    def _coerencia(self) -> ConfiguracaoIa:
        if self.ia_provedor == "teste" and self.app_ambiente == "producao":
            raise ValueError("IA_PROVEDOR=teste é só para testes e desenvolvimento")
        if self.ia_provedor != "teste":
            chave = self.chave_api
            if chave is None or not chave.get_secret_value().strip():
                raise ValueError(
                    f"IA_PROVEDOR={self.ia_provedor} exige {_CHAVES[self.ia_provedor]} no .env"
                )
        return self

    @property
    def chave_api(self) -> SecretStr | None:
        if self.ia_provedor == "gemini":
            return self.gemini_api_key
        if self.ia_provedor == "groq":
            return self.groq_api_key
        return None

    @property
    def modelo_geracao(self) -> str:
        return self.ia_modelo_geracao.strip() or MODELOS_PADRAO[self.ia_provedor][0]

    @property
    def modelo_verificador(self) -> str:
        return self.ia_modelo_verificador.strip() or MODELOS_PADRAO[self.ia_provedor][1]

    @property
    def aviso(self) -> AvisoProvedor:
        return AVISOS[self.ia_provedor]


@lru_cache(maxsize=1)
def obter_configuracao_ia() -> ConfiguracaoIa:
    return ConfiguracaoIa()
