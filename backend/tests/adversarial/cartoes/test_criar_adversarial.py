"""Entradas maliciosas e concorrência na criação e na listagem de cartões (T013).

Payload no teto mais um, corpo acima de 64 KiB, campos extras (atribuição em massa), tipos
trocados, caracteres que quebram o armazenamento, parâmetros de listagem fora da faixa e a
corrida entre a criação com referência e a exclusão da fonte (DTEC 035 e 031).
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from procrastinate import App

from app.nucleo.participantes_acervo import registro_acervo
from tests import fabricas_arquivos as fab
from tests.apoio_acervo import (
    criar_conta,
    criar_materia,
    enviar,
    id_interno_da_materia,
)
from tests.apoio_cartoes import cartoes_da_materia, criar_cartao
from tests.conftest import executar_jobs
from tests.fabricas_arquivos import ArquivoGerado
from tests.participantes_falsos import ParticipanteDeCartoesFalso

pytestmark = pytest.mark.adversarial


@pytest.fixture(scope="module")
def resumo() -> ArquivoGerado:
    return {a.nome: a for a in fab.validos()}["resumo.txt"]


@pytest.fixture
async def estudante(acervo: FastAPI, cliente_real: httpx.AsyncClient) -> httpx.AsyncClient:
    await criar_conta(cliente_real)
    return cliente_real


@pytest.fixture
async def biologia(estudante: httpx.AsyncClient) -> dict[str, Any]:
    return await criar_materia(estudante, "Biologia")


async def _total(estudante: httpx.AsyncClient, materia_id: str) -> int:
    corpo = (await estudante.get(f"/api/v1/materias/{materia_id}/cartoes")).json()
    total: int = corpo["total"]
    return total


# --- Teto absoluto do DTO ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("campo", "teto"), [("frente", 4000), ("verso", 8000), ("explicacao", 4000)]
)
async def test_payload_no_teto_mais_um_e_recusado_pelo_dto(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], campo: str, teto: int
) -> None:
    """Acima do teto absoluto, o DTO barra antes do domínio (DTEC 036), sem criar nada."""
    resposta = await criar_cartao(estudante, biologia["id"], **{campo: "a" * (teto + 1)})
    assert resposta.status_code == 422
    erro = resposta.json()
    assert erro["codigo"] == "dados_invalidos"
    assert [c["campo"] for c in erro["campos"]] == [campo]
    assert "a" * 50 not in resposta.text, "a resposta não ecoa o texto enviado"
    assert await _total(estudante, biologia["id"]) == 0


async def test_corpo_acima_de_64_kib_vira_413_sem_criar_nada(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    resposta = await estudante.post(
        f"/api/v1/materias/{biologia['id']}/cartoes",
        json={"frente": "f", "verso": "v", "explicacao": "e" * (64 * 1024 + 10)},
    )
    assert resposta.status_code == 413
    assert await _total(estudante, biologia["id"]) == 0


async def test_corpo_gigante_sem_content_length_tambem_vira_413(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    async def em_blocos() -> Any:
        yield b'{"frente": "f", "verso": "v", "explicacao": "'
        for _ in range(40):
            yield b"e" * 4096
        yield b'"}'

    pedido = estudante.build_request(
        "POST",
        f"/api/v1/materias/{biologia['id']}/cartoes",
        content=em_blocos(),
        headers={"Content-Type": "application/json"},
    )
    assert "content-length" not in pedido.headers
    resposta = await estudante.send(pedido)
    assert resposta.status_code == 413
    assert await _total(estudante, biologia["id"]) == 0


# --- Campos extras e atribuição em massa ---------------------------------------------------------


@pytest.mark.parametrize(
    "extra",
    [
        {"origem": "gerado_verificado"},
        {"origem": "editado"},
        {"verificado": True},
        {"situacao": "suspenso"},
        {"usuarioId": 1},
        {"materiaId": str(uuid.uuid4())},
        {"id": str(uuid.uuid4())},
        {"vencimento": "2030-01-01T00:00:00Z"},
        {"estabilidade": 99.0},
        {"entradaEstudoEm": "2020-01-01T00:00:00Z"},
        {"referencia": {"titulo": "Falsa"}},
        {"geracaoId": 1},
    ],
    ids=lambda e: next(iter(e)),
)
async def test_campo_extra_e_recusado_e_nao_forja_origem_nem_agendamento(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], extra: dict[str, Any]
) -> None:
    """`extra="forbid"`: nem selo de verificado nem estado do FSRS vêm do cliente (Princípio IV)."""
    resposta = await criar_cartao(estudante, biologia["id"], **extra)
    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "dados_invalidos"
    assert await _total(estudante, biologia["id"]) == 0


@pytest.mark.parametrize(
    "corpo",
    [
        {},
        {"frente": "f"},
        {"verso": "v"},
        {"frente": None, "verso": "v"},
        {"frente": "f", "verso": None},
        {"frente": 123, "verso": "v"},
        {"frente": ["f"], "verso": "v"},
        {"frente": {"a": 1}, "verso": "v"},
        {"frente": True, "verso": "v"},
        {"frente": "f", "verso": "v", "explicacao": 5},
        {"frente": "f", "verso": "v", "explicacao": ["x"]},
    ],
    ids=lambda c: "-".join(f"{k}={type(v).__name__}" for k, v in c.items()) or "vazio",
)
async def test_tipos_trocados_ou_campos_ausentes_sao_422(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], corpo: dict[str, Any]
) -> None:
    resposta = await estudante.post(f"/api/v1/materias/{biologia['id']}/cartoes", json=corpo)
    assert resposta.status_code == 422 and resposta.json()["codigo"] == "dados_invalidos"
    assert await _total(estudante, biologia["id"]) == 0


@pytest.mark.parametrize("bruto", [b"", b"{", b"[]", b"null", b"\xff\xfe", b"frente=f&verso=v"])
async def test_corpo_que_nao_e_um_objeto_json_nao_cria_nada(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], bruto: bytes
) -> None:
    resposta = await estudante.post(
        f"/api/v1/materias/{biologia['id']}/cartoes",
        content=bruto,
        headers={"Content-Type": "application/json"},
    )
    assert resposta.status_code in {400, 422}
    assert resposta.json()["codigo"] in {"requisicao_malformada", "dados_invalidos"}
    assert await _total(estudante, biologia["id"]) == 0


@pytest.mark.parametrize("fonte_id", ["nao-e-uuid", "", 123, [], {}, True, "0" * 64, "' OR 1=1 --"])
async def test_fonte_id_que_nao_e_uuid_e_422_no_campo(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], fonte_id: Any
) -> None:
    resposta = await criar_cartao(estudante, biologia["id"], fonteId=fonte_id)
    assert resposta.status_code == 422
    assert [c["campo"] for c in resposta.json()["campos"]] == ["fonteId"]
    assert await _total(estudante, biologia["id"]) == 0


# --- Caracteres que quebrariam o armazenamento ---------------------------------------------------


async def test_nul_e_controles_sao_removidos_e_nao_viram_500(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    """O JSON aceita `\\u0000`; o PostgreSQL não: a normalização tira os controles."""
    bruto = b'{"frente": "a\\u0000b\\u0007c", "verso": "v\\u001bw", "explicacao": "\\u0000"}'
    resposta = await estudante.post(
        f"/api/v1/materias/{biologia['id']}/cartoes",
        content=bruto,
        headers={"Content-Type": "application/json"},
    )
    assert resposta.status_code == 201, resposta.text
    cartao = resposta.json()
    assert (cartao["frente"], cartao["verso"], cartao["explicacao"]) == ("abc", "vw", None)


@pytest.mark.parametrize("campo", ["frente", "verso", "explicacao"])
async def test_substituto_isolado_e_recusado_com_422_e_nao_vira_500(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], campo: str
) -> None:
    """`\\ud800` não é texto válido (não codifica em UTF-8): o DTO o recusa no campo."""
    corpo = {"frente": "f", "verso": "v", "explicacao": "e", campo: "a\\ud800b"}
    bruto = ('{"frente": "%s", "verso": "%s", "explicacao": "%s"}' % tuple(corpo.values())).encode()  # noqa: UP031
    resposta = await estudante.post(
        f"/api/v1/materias/{biologia['id']}/cartoes",
        content=bruto,
        headers={"Content-Type": "application/json"},
    )
    assert resposta.status_code == 422, resposta.text
    assert [c["campo"] for c in resposta.json()["campos"]] == [campo]
    assert await _total(estudante, biologia["id"]) == 0


@pytest.mark.parametrize("campo", ["frente", "verso"])
@pytest.mark.parametrize("so", ["\\u0000", "\\ud800", "\\u200b", "\\u202e", "\\u0007\\u0000"])
async def test_texto_so_de_caracteres_invisiveis_ou_proibidos_vale_como_vazio(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], campo: str, so: str
) -> None:
    outro = "verso" if campo == "frente" else "frente"
    bruto = ('{"%s": "%s", "%s": "ok"}' % (campo, so, outro)).encode()  # noqa: UP031
    resposta = await estudante.post(
        f"/api/v1/materias/{biologia['id']}/cartoes",
        content=bruto,
        headers={"Content-Type": "application/json"},
    )
    assert resposta.status_code == 422
    assert [c["campo"] for c in resposta.json()["campos"]] == [campo]


async def test_bidirecional_e_largura_zero_no_meio_do_texto_voltam_literais(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    texto = "início ‮direita-para-esquerda‬ e​ largura⁠ zero fim"
    resposta = await criar_cartao(estudante, biologia["id"], frente=texto, verso=texto)
    assert resposta.status_code == 201
    assert resposta.json()["frente"] == texto == resposta.json()["verso"]


# --- Parâmetros da listagem ----------------------------------------------------------------------


@pytest.mark.parametrize("limite", ["0", "101", "-1", "abc", "1.5", "", "999999999999"])
async def test_limite_fora_de_1_a_100_e_422(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], limite: str
) -> None:
    resposta = await estudante.get(f"/api/v1/materias/{biologia['id']}/cartoes?limite={limite}")
    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "dados_invalidos"
    assert [c["campo"] for c in resposta.json()["campos"]] == ["limite"]


@pytest.mark.parametrize("limite", [1, 100])
async def test_limites_da_faixa_sao_aceitos(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], limite: int
) -> None:
    resposta = await estudante.get(f"/api/v1/materias/{biologia['id']}/cartoes?limite={limite}")
    assert resposta.status_code == 200


@pytest.mark.parametrize(
    "cursor",
    ["lixo", "!!!", "a" * 43, "../../etc/passwd", "%00", "' OR 1=1 --", "💥", " ", "A" * 100],
)
async def test_cursor_adulterado_ou_inventado_e_422_cursor_invalido(
    estudante: httpx.AsyncClient, biologia: dict[str, Any], cursor: str
) -> None:
    await criar_cartao(estudante, biologia["id"], frente="Existe")
    resposta = await estudante.get(
        f"/api/v1/materias/{biologia['id']}/cartoes", params={"cursor": cursor}
    )
    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "cursor_invalido"
    assert "Existe" not in resposta.text


async def test_cursor_acima_de_512_caracteres_e_recusado_antes_de_decodificar(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    resposta = await estudante.get(
        f"/api/v1/materias/{biologia['id']}/cartoes", params={"cursor": "A" * 513}
    )
    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "dados_invalidos"


async def test_cursor_adulterado_no_meio_da_paginacao_nao_pula_nem_repete(
    estudante: httpx.AsyncClient, biologia: dict[str, Any]
) -> None:
    for numero in range(6):
        await criar_cartao(estudante, biologia["id"], frente=f"Pergunta {numero}")
    pagina = (await estudante.get(f"/api/v1/materias/{biologia['id']}/cartoes?limite=2")).json()
    cursor = pagina["proximoCursor"]
    adulterado = cursor[:-2] + ("AA" if not cursor.endswith("AA") else "BB")
    resposta = await estudante.get(
        f"/api/v1/materias/{biologia['id']}/cartoes", params={"cursor": adulterado}
    )
    assert resposta.status_code == 422 and resposta.json()["codigo"] == "cursor_invalido"
    # O cursor verdadeiro continua valendo.
    segunda = await estudante.get(
        f"/api/v1/materias/{biologia['id']}/cartoes", params={"cursor": cursor, "limite": 2}
    )
    assert segunda.status_code == 200
    assert {c["frente"] for c in segunda.json()["itens"]}.isdisjoint(
        {c["frente"] for c in pagina["itens"]}
    )


# --- Concorrência: criação com referência × exclusão da fonte ------------------------------------


@pytest.fixture
def exclusao_lenta() -> Any:
    """Participante falso que alarga a janela da exclusão da fonte (a trava já foi tomada)."""
    participante = ParticipanteDeCartoesFalso(atraso_s=0.6)
    registro_acervo.registrar(150, "lento", participante)
    try:
        yield participante
    finally:
        registro_acervo.remover("lento")


async def test_criar_com_referencia_durante_a_exclusao_da_fonte_nunca_cita_fonte_inexistente(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    biologia: dict[str, Any],
    fila: App,
    resumo: ArquivoGerado,
    exclusao_lenta: ParticipanteDeCartoesFalso,
) -> None:
    """A criação espera a exclusão e então recebe `422`, nunca `500` nem cartão com fonte morta.

    Duas defesas, cada uma suficiente: a fonte lida com `FOR SHARE` (a criação espera ali) e a
    conversão da violação da FK composta em `422 fonteId`. Sem as duas, a criação terminaria em
    erro interno depois de a exclusão confirmar.
    """
    fonte = (await enviar(estudante, biologia["id"], resumo)).json()
    await executar_jobs(fila)
    visto = (await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")).json()

    exclusao = asyncio.create_task(
        estudante.post(
            f"/api/v1/fontes/{fonte['id']}/exclusao",
            json={"modoCartoes": "manter", "impactoConfirmado": visto["contagens"]},
        )
    )
    await asyncio.sleep(0.2)  # a exclusão já travou a fonte e está na janela lenta
    criacao = await criar_cartao(estudante, biologia["id"], fonteId=fonte["id"])
    resposta_exclusao = await exclusao

    assert resposta_exclusao.status_code == 204
    assert criacao.status_code == 422, criacao.text
    assert criacao.json()["campos"] == [
        {"campo": "fonteId", "mensagem": "Escolha uma fonte desta matéria."}
    ]
    interno = await id_interno_da_materia(acervo.state.fabrica_sessoes, biologia["id"])
    assert await cartoes_da_materia(acervo.state.fabrica_sessoes, interno) == []


async def test_corrida_sem_atraso_termina_sempre_coerente_sem_erro_interno(
    acervo: FastAPI,
    estudante: httpx.AsyncClient,
    fila: App,
    resumo: ArquivoGerado,
) -> None:
    """Várias rodadas: ou o cartão nasce antes e fica com "Fonte apagada", ou recebe 422."""
    nasceram = recusadas = 0
    for rodada in range(8):
        materia = await criar_materia(estudante, f"Matéria {rodada}")
        arquivo = (f"corrida-{rodada}.txt", f"conteúdo único {rodada} ".encode() * 30)
        fonte = (await enviar(estudante, materia["id"], arquivo)).json()
        await executar_jobs(fila)
        visto = (await estudante.get(f"/api/v1/fontes/{fonte['id']}/impacto-exclusao")).json()

        criacao, exclusao = await asyncio.gather(
            criar_cartao(estudante, materia["id"], fonteId=fonte["id"]),
            estudante.post(
                f"/api/v1/fontes/{fonte['id']}/exclusao",
                json={"modoCartoes": "manter", "impactoConfirmado": visto["contagens"]},
            ),
        )

        assert criacao.status_code in {201, 422}, criacao.text
        assert exclusao.status_code in {204, 409}, exclusao.text  # 409: o impacto mudou
        cartoes = (await estudante.get(f"/api/v1/materias/{materia['id']}/cartoes")).json()
        if criacao.status_code == 201:
            nasceram += 1
            (cartao,) = cartoes["itens"]
            if exclusao.status_code == 204:
                assert cartao["referencia"]["fonteApagada"] is True
                assert cartao["referencia"]["fonteId"] is None
            else:
                assert cartao["referencia"]["fonteId"] == fonte["id"]
        else:
            recusadas += 1
            assert cartoes["itens"] == []
    assert nasceram + recusadas == 8
