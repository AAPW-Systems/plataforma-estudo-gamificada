"""O OpenAPI gerado contém o contrato de projeto da spec 001 (T037; RQ-005).

Cobertura incremental: as rotas que só chegam depois do ponto S1 (US3 e US4) estão em
`PENDENTES`, cada uma com a tarefa que a entrega. Quando a rota passa a existir, o teste
`test_pendentes_ainda_nao_existem` falha e obriga a tirá-la da lista, de modo que a
comparação completa passa a valer sem ninguém precisar lembrar.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from openapi_spec_validator import validate

from app.principal import criar_aplicacao
from tests.contrato import (
    carregar_contrato,
    nome_da_referencia,
    resolver,
    resumo_do_esquema,
    validar_corpo_erro,
)

pytestmark = pytest.mark.integration

# (método, caminho) -> tarefa que entrega a rota.
OPERACOES_PENDENTES = {
    ("patch", "/api/v1/perfil"): "T049",
    ("post", "/api/v1/perfil/senha"): "T056",
    ("post", "/api/v1/perfil/exclusao"): "T056",
}
ESQUEMAS_PENDENTES = {
    "PerfilAlteracao": "T049",
    "TrocaSenhaEntrada": "T056",
    "ExclusaoContaEntrada": "T056",
}
RAIZ_BACKEND = Path(__file__).parents[2]


@pytest.fixture(scope="module")
def gerado(configuracao: Any) -> dict[str, Any]:
    return criar_aplicacao(configuracao).openapi()


@pytest.fixture(scope="module")
def contrato() -> dict[str, Any]:
    return carregar_contrato()


def _operacoes(documento: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (metodo, caminho): operacao
        for caminho, item in documento["paths"].items()
        for metodo, operacao in item.items()
        if metodo in {"get", "post", "put", "patch", "delete"}
    }


def test_o_contrato_de_projeto_e_o_openapi_gerado_sao_documentos_validos(
    contrato: dict[str, Any], gerado: dict[str, Any]
) -> None:
    validate(contrato)
    validate(gerado)


def test_openapi_versionado_esta_atualizado(gerado: dict[str, Any]) -> None:
    versionado = json.loads((RAIZ_BACKEND / "openapi.json").read_text(encoding="utf-8"))
    assert versionado == json.loads(json.dumps(gerado)), (
        "rode `uv run python -m app.exportar_openapi` e `npm run gerar:api`"
    )


def test_pendentes_ainda_nao_existem(gerado: dict[str, Any]) -> None:
    operacoes = _operacoes(gerado)
    implementadas = [op for op in OPERACOES_PENDENTES if op in operacoes]
    assert not implementadas, f"tire de OPERACOES_PENDENTES (agora existem): {implementadas}"
    esquemas = [nome for nome in ESQUEMAS_PENDENTES if nome in gerado["components"]["schemas"]]
    assert not esquemas, f"tire de ESQUEMAS_PENDENTES (agora existem): {esquemas}"


def test_todas_as_operacoes_do_contrato_existem_exceto_as_pendentes(
    contrato: dict[str, Any], gerado: dict[str, Any]
) -> None:
    esperadas = set(_operacoes(contrato)) - set(OPERACOES_PENDENTES)
    existentes = set(_operacoes(gerado))
    assert esperadas <= existentes, f"faltam no OpenAPI gerado: {sorted(esperadas - existentes)}"
    assert len(esperadas) >= 7


def test_a_aplicacao_nao_expoe_rota_fora_do_contrato_nem_das_pendentes(
    contrato: dict[str, Any], gerado: dict[str, Any]
) -> None:
    extras = set(_operacoes(gerado)) - set(_operacoes(contrato))
    assert not extras, f"rota sem contrato de projeto: {sorted(extras)}"


def test_operacoes_tem_o_mesmo_id_respostas_e_corpos(
    contrato: dict[str, Any], gerado: dict[str, Any]
) -> None:
    operacoes_gerado = _operacoes(gerado)
    problemas: list[str] = []
    for chave, esperada in _operacoes(contrato).items():
        if chave in OPERACOES_PENDENTES:
            continue
        obtida = operacoes_gerado[chave]
        if obtida["operationId"] != esperada["operationId"]:
            problemas.append(f"{chave}: operationId {obtida['operationId']!r}")
        for codigo, resposta in esperada["responses"].items():
            if codigo not in obtida["responses"]:
                problemas.append(f"{chave}: falta a resposta {codigo}")
                continue
            esperado_json = resolver(contrato, resposta).get("content", {}).get("application/json")
            obtido_json = (
                resolver(gerado, obtida["responses"][codigo])
                .get("content", {})
                .get("application/json")
            )
            if esperado_json and (
                not obtido_json
                or nome_da_referencia(esperado_json["schema"])
                != nome_da_referencia(obtido_json["schema"])
            ):
                problemas.append(f"{chave} {codigo}: esquema da resposta diferente")
        corpo_esperado = esperada.get("requestBody")
        if corpo_esperado:
            corpo_obtido = obtida.get("requestBody") or {}
            esperado_ref = nome_da_referencia(
                corpo_esperado["content"]["application/json"]["schema"]
            )
            obtido_ref = nome_da_referencia(
                corpo_obtido.get("content", {}).get("application/json", {}).get("schema", {})
            )
            if esperado_ref != obtido_ref or not corpo_obtido.get("required"):
                problemas.append(
                    f"{chave}: corpo da requisição {obtido_ref!r}, esperado {esperado_ref!r}"
                )
    assert not problemas, "\n".join(problemas)


def test_esquemas_tem_campos_obrigatorios_tipos_e_limites_do_contrato(
    contrato: dict[str, Any], gerado: dict[str, Any]
) -> None:
    problemas: list[str] = []
    for nome, esperado in contrato["components"]["schemas"].items():
        if nome in ESQUEMAS_PENDENTES:
            continue
        if nome not in gerado["components"]["schemas"]:
            problemas.append(f"esquema ausente: {nome}")
            continue
        obtido = gerado["components"]["schemas"][nome]
        if set(esperado.get("required", [])) != set(obtido.get("required", [])):
            problemas.append(
                f"{nome}: obrigatórios {sorted(obtido.get('required', []))}, "
                f"esperado {sorted(esperado.get('required', []))}"
            )
        if "additionalProperties" in esperado and esperado["additionalProperties"] is False:
            if obtido.get("additionalProperties") is not False:
                problemas.append(f"{nome}: deveria recusar campos extras")
        propriedades_esperadas = esperado.get("properties", {})
        propriedades_obtidas = obtido.get("properties", {})
        if set(propriedades_esperadas) != set(propriedades_obtidas):
            tem_campos, quer_campos = sorted(propriedades_obtidas), sorted(propriedades_esperadas)
            problemas.append(f"{nome}: campos {tem_campos}, esperado {quer_campos}")
            continue
        for campo, definicao in propriedades_esperadas.items():
            quer = resumo_do_esquema(contrato, definicao)
            tem = resumo_do_esquema(gerado, propriedades_obtidas[campo])
            # Campo opcional: o Pydantic o publica como `X | null`; a API o omite e nunca envia
            # `null`, então o tipo extra `null` é um superconjunto aceitável.
            opcional = campo not in esperado.get("required", [])
            aceitos = quer["tipos"] | ({"null"} if opcional else set())
            if quer["tipos"] and not quer["tipos"] <= tem["tipos"] <= aceitos:
                problemas.append(f"{nome}.{campo}: tipos {tem['tipos']}, esperado {quer['tipos']}")
            if quer["enum"] and not quer["enum"] <= tem["enum"]:
                problemas.append(f"{nome}.{campo}: enum sem {sorted(quer['enum'] - tem['enum'])}")
            for restricao, valor in quer["restricoes"].items():
                obtida = tem["restricoes"].get(restricao)
                if obtida != valor:
                    problemas.append(f"{nome}.{campo}: {restricao}={obtida!r}, esperado {valor!r}")
    assert not problemas, "\n".join(problemas)


def test_codigos_de_erro_do_contrato_existem_no_codigo_da_aplicacao(
    contrato: dict[str, Any], gerado: dict[str, Any]
) -> None:
    esperado = set(contrato["components"]["schemas"]["Erro"]["properties"]["codigo"]["enum"])
    obtido = resumo_do_esquema(
        gerado, gerado["components"]["schemas"]["Erro"]["properties"]["codigo"]
    )
    assert esperado <= obtido["enum"], sorted(esperado - obtido["enum"])


def test_validador_de_corpo_de_erro_aceita_o_exemplo_do_contrato_e_recusa_o_invalido(
    contrato: dict[str, Any],
) -> None:
    exemplo = contrato["paths"]["/api/v1/auth/entrada"]["post"]["responses"]["401"]["content"][
        "application/json"
    ]["example"]
    validar_corpo_erro(exemplo, contrato)
    with pytest.raises(AssertionError):
        validar_corpo_erro({**exemplo, "codigo": "inventado"}, contrato)
    with pytest.raises(AssertionError):
        validar_corpo_erro({"codigo": "erro_interno", "mensagem": "x"}, contrato)
    with pytest.raises(AssertionError):
        validar_corpo_erro({**exemplo, "stack": "..."}, contrato)


def test_aplicacao_em_desenvolvimento_serve_o_openapi_e_producao_nao(
    configuracao: Any,
) -> None:
    desenvolvimento = criar_aplicacao(
        configuracao.model_copy(update={"app_ambiente": "desenvolvimento"})
    )
    teste = criar_aplicacao(configuracao)
    assert isinstance(desenvolvimento, FastAPI)
    assert desenvolvimento.openapi_url == "/api/openapi.json"
    assert teste.openapi_url is None
