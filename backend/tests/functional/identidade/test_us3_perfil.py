"""US3: ajustar perfil e preferências, cenários 1 a 4 (T047; RF-008, RF-009, RF-010, CB-29).

O cenário 1 inclui, na interface, a explicação da retenção (`FormularioPerfil.test.tsx`).
"""

from __future__ import annotations

from decimal import Decimal

import httpx
import pytest
from sqlalchemy import func, select

from app.identidade.modelos import Sessao, Usuario
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.relogio import RelogioControlavel
from app.revisao.modelos import ParametrosFsrs
from tests.apoio_http import cadastrar
from tests.fabricas import dados_conta

pytestmark = pytest.mark.functional


async def _versoes(fabrica: FabricaSessoes) -> list[ParametrosFsrs]:
    async with unidade_de_trabalho(fabrica) as sessao:
        linhas = (
            await sessao.execute(select(ParametrosFsrs).order_by(ParametrosFsrs.versao))
        ).scalars()
        return list(linhas)


async def _conta(cliente: httpx.AsyncClient) -> dict[str, object]:
    resposta = await cadastrar(cliente, dados_conta(fuso="America/Recife"))
    assert resposta.status_code == 201
    perfil: dict[str, object] = resposta.json()
    return perfil


# --- Cenário 1: consulta ------------------------------------------------------------------


async def test_cenario1_o_perfil_mostra_nome_email_fuso_e_preferencias(
    cliente: httpx.AsyncClient,
) -> None:
    perfil = await _conta(cliente)
    consultado = (await cliente.get("/api/v1/perfil")).json()
    assert consultado == perfil
    assert {
        "nome",
        "email",
        "fuso",
        "metaDiaria",
        "tamanhoLicao",
        "limiteNovosDia",
        "retencaoDesejada",
    } <= set(consultado)


# --- Cenário 2: limites -------------------------------------------------------------------


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("metaDiaria", 1),
        ("metaDiaria", 200),
        ("tamanhoLicao", 5),
        ("tamanhoLicao", 50),
        ("limiteNovosDia", 0),
        ("limiteNovosDia", 100),
        ("nome", "Outro Nome"),
        ("fuso", "America/Manaus"),
    ],
)
async def test_cenario2_valor_valido_e_salvo_e_devolvido(
    cliente: httpx.AsyncClient, campo: str, valor: object
) -> None:
    await _conta(cliente)
    resposta = await cliente.patch("/api/v1/perfil", json={campo: valor})
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()[campo] == valor
    assert (await cliente.get("/api/v1/perfil")).json()[campo] == valor


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("metaDiaria", 0),
        ("metaDiaria", 201),
        ("tamanhoLicao", 4),
        ("tamanhoLicao", 51),
        ("limiteNovosDia", -1),
        ("limiteNovosDia", 101),
        ("retencaoDesejada", 0.69),
        ("retencaoDesejada", 0.98),
        ("nome", "   "),
        ("fuso", "Marte/Phobos"),
    ],
)
async def test_cenario2_valor_fora_dos_limites_nao_altera_nada_e_o_erro_vem_por_campo(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes, campo: str, valor: object
) -> None:
    antes = await _conta(cliente)
    resposta = await cliente.patch("/api/v1/perfil", json={campo: valor})
    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "dados_invalidos"
    assert [c["campo"] for c in resposta.json()["campos"]] == [campo]
    assert (await cliente.get("/api/v1/perfil")).json() == antes
    assert len(await _versoes(fabrica_sessoes)) == 1


async def test_cenario2_alteracao_e_tudo_ou_nada_com_varios_campos_invalidos(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    antes = await _conta(cliente)
    resposta = await cliente.patch(
        "/api/v1/perfil",
        json={
            "nome": "Nome Valido",
            "metaDiaria": 0,
            "tamanhoLicao": 999,
            "retencaoDesejada": 0.5,
            "fuso": "UTC",
        },
    )
    assert resposta.status_code == 422
    assert {c["campo"] for c in resposta.json()["campos"]} == {
        "metaDiaria",
        "tamanhoLicao",
        "retencaoDesejada",
    }
    # Nem o nome nem o fuso válidos foram salvos.
    assert (await cliente.get("/api/v1/perfil")).json() == antes
    assert len(await _versoes(fabrica_sessoes)) == 1


async def test_cenario2_so_os_campos_enviados_mudam(cliente: httpx.AsyncClient) -> None:
    antes = await _conta(cliente)
    depois = (await cliente.patch("/api/v1/perfil", json={"metaDiaria": 35})).json()
    assert depois["metaDiaria"] == 35
    assert {k: v for k, v in depois.items() if k != "metaDiaria"} == {
        k: v for k, v in antes.items() if k != "metaDiaria"
    }


# --- Cenário 3: retenção e versões --------------------------------------------------------


async def test_cenario3_nova_retencao_cria_a_versao_n_mais_1_e_a_anterior_fica_intacta(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes, relogio: RelogioControlavel
) -> None:
    await _conta(cliente)
    (v1,) = await _versoes(fabrica_sessoes)
    relogio.avancar(hours=2)

    resposta = await cliente.patch("/api/v1/perfil", json={"retencaoDesejada": 0.85})

    assert resposta.status_code == 200
    assert resposta.json()["retencaoDesejada"] == 0.85
    versoes = await _versoes(fabrica_sessoes)
    assert [v.versao for v in versoes] == [1, 2]
    anterior, nova = versoes
    assert str(anterior.retencao_desejada) == "0.90", "a versão 1 nunca é alterada"
    assert anterior.id == v1.id and anterior.criado_em == v1.criado_em
    assert anterior.pesos == v1.pesos
    assert str(nova.retencao_desejada) == "0.85"
    assert nova.criado_em == relogio.agora()
    # Os demais parâmetros são copiados da versão vigente.
    for campo in (
        "pesos",
        "passos_aprendizado_s",
        "passos_reaprendizado_s",
        "intervalo_maximo_dias",
        "fuzzing",
        "versao_biblioteca",
        "origem",
    ):
        assert getattr(nova, campo) == getattr(anterior, campo), campo
    assert nova.usuario_id == anterior.usuario_id


async def test_cenario3_o_mesmo_valor_nao_cria_versao(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    await _conta(cliente)
    for valor in (0.9, 0.90, 0.9):
        assert (
            await cliente.patch("/api/v1/perfil", json={"retencaoDesejada": valor})
        ).status_code == 200
    assert len(await _versoes(fabrica_sessoes)) == 1
    await cliente.patch("/api/v1/perfil", json={"retencaoDesejada": 0.8})
    await cliente.patch("/api/v1/perfil", json={"retencaoDesejada": 0.8})
    assert [v.versao for v in await _versoes(fabrica_sessoes)] == [1, 2]


async def test_cenario3_varias_trocas_geram_versoes_sequenciais(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    await _conta(cliente)
    for valor in (0.8, 0.95, 0.7, 0.97, 0.9):
        assert (
            await cliente.patch("/api/v1/perfil", json={"retencaoDesejada": valor})
        ).status_code == 200
    versoes = await _versoes(fabrica_sessoes)
    assert [v.versao for v in versoes] == [1, 2, 3, 4, 5, 6]
    assert [str(v.retencao_desejada) for v in versoes] == [
        "0.90",
        "0.80",
        "0.95",
        "0.70",
        "0.97",
        "0.90",
    ]
    assert (await cliente.get("/api/v1/perfil")).json()["retencaoDesejada"] == 0.9


async def test_cenario3_alterar_outras_preferencias_nao_cria_versao_do_fsrs(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    await _conta(cliente)
    await cliente.patch(
        "/api/v1/perfil", json={"metaDiaria": 40, "tamanhoLicao": 12, "limiteNovosDia": 5}
    )
    assert len(await _versoes(fabrica_sessoes)) == 1


async def test_cenario3_a_versao_nova_e_a_vigente_para_quem_agenda(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    from app.revisao.repositorios import RepositorioParametrosFsrs

    await _conta(cliente)
    await cliente.patch("/api/v1/perfil", json={"retencaoDesejada": 0.75})
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario_id = (await sessao.execute(select(Usuario.id))).scalar_one()
        vigente = await RepositorioParametrosFsrs(sessao).buscar_vigente(usuario_id)
    assert vigente is not None and vigente.versao == 2
    assert vigente.retencao_desejada == Decimal("0.75")


# --- Cenário 4: fuso ----------------------------------------------------------------------


async def test_cenario4_fuso_novo_nao_mexe_em_dados_anteriores(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    antes = await _conta(cliente)
    versoes_antes = await _versoes(fabrica_sessoes)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        sessoes_antes = (await sessao.execute(select(Sessao.id, Sessao.criada_em))).all()

    resposta = await cliente.patch("/api/v1/perfil", json={"fuso": "Asia/Tokyo"})

    assert resposta.status_code == 200
    depois = resposta.json()
    assert depois["fuso"] == "Asia/Tokyo"
    assert {k: v for k, v in depois.items() if k != "fuso"} == {
        k: v for k, v in antes.items() if k != "fuso"
    }
    versoes_depois = await _versoes(fabrica_sessoes)
    assert [(v.id, v.versao, v.criado_em) for v in versoes_depois] == [
        (v.id, v.versao, v.criado_em) for v in versoes_antes
    ]
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        assert (await sessao.execute(select(Sessao.id, Sessao.criada_em))).all() == sessoes_antes
        assert (await sessao.execute(select(func.count()).select_from(Usuario))).scalar_one() == 1


async def test_a_alteracao_atualiza_atualizado_em_e_a_sessao_continua_valida(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes, relogio: RelogioControlavel
) -> None:
    await _conta(cliente)
    relogio.avancar(minutes=5)
    assert (await cliente.patch("/api/v1/perfil", json={"nome": "Nome Novo"})).status_code == 200
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario = (await sessao.execute(select(Usuario))).scalar_one()
    assert usuario.atualizado_em == relogio.agora() and usuario.criado_em < usuario.atualizado_em
    assert (await cliente.get("/api/v1/perfil")).status_code == 200


async def test_alteracao_sem_sessao_e_recusada(cliente: httpx.AsyncClient) -> None:
    await cliente.get("/api/v1/auth/csrf")
    resposta = await cliente.patch("/api/v1/perfil", json={"metaDiaria": 30})
    assert resposta.status_code == 401
