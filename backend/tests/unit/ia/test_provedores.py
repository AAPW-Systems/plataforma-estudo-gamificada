"""T008 (spec 004, DTEC 007): o provedor configurado gera o modelo certo, sem rede."""

from __future__ import annotations

import pytest
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.models.test import TestModel

from app.ia.configuracao import ConfiguracaoIa
from app.ia.provedores import criar_modelo

pytestmark = pytest.mark.unit


def _config(provedor: str, **extra: str) -> ConfiguracaoIa:
    return ConfiguracaoIa(app_ambiente="desenvolvimento", ia_provedor=provedor, **extra)  # type: ignore[arg-type]


def test_gemini() -> None:
    config = _config(
        "gemini",
        gemini_api_key="chave-ficticia",
        ia_modelo_geracao="gemini-a",
        ia_modelo_verificador="gemini-b",
    )
    geracao = criar_modelo(config, "geracao")
    verificador = criar_modelo(config, "verificador")
    assert isinstance(geracao, GoogleModel) and isinstance(verificador, GoogleModel)
    assert (geracao.model_name, verificador.model_name) == ("gemini-a", "gemini-b")


def test_groq() -> None:
    config = _config("groq", groq_api_key="chave-ficticia", ia_modelo_geracao="groq-a")
    modelo = criar_modelo(config, "geracao")
    assert isinstance(modelo, GroqModel)
    assert modelo.model_name == "groq-a"
    assert criar_modelo(config, "verificador").model_name == "llama-3.3-70b-versatile"


def test_teste_usa_o_modelo_simulado() -> None:
    modelo = criar_modelo(_config("teste"), "geracao")
    assert isinstance(modelo, TestModel)
