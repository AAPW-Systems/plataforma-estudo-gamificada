"""Fábrica do modelo do PydanticAI para o provedor configurado (DTEC 007 e 040).

Trocar de provedor muda só `IA_PROVEDOR` e a chave. `teste` usa o modelo simulado do PydanticAI,
sem rede; nos testes, o cliente recebe um `FunctionModel` de cenário no lugar deste.
"""

from __future__ import annotations

from typing import Literal

from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.groq import GroqProvider

from app.ia.configuracao import ConfiguracaoIa

type Finalidade = Literal["geracao", "verificador"]


def criar_modelo(configuracao: ConfiguracaoIa, finalidade: Finalidade) -> Model:
    nome = (
        configuracao.modelo_geracao if finalidade == "geracao" else configuracao.modelo_verificador
    )
    if configuracao.ia_provedor == "gemini":
        return GoogleModel(nome, provider=GoogleProvider(api_key=_chave(configuracao)))
    if configuracao.ia_provedor == "groq":
        return GroqModel(nome, provider=GroqProvider(api_key=_chave(configuracao)))
    return TestModel(model_name=nome)


def _chave(configuracao: ConfiguracaoIa) -> str:
    chave = configuracao.chave_api
    if chave is None:  # a validação da configuração já impede; aqui só para o tipo
        raise RuntimeError(f"IA_PROVEDOR={configuracao.ia_provedor} sem chave")
    return chave.get_secret_value()
