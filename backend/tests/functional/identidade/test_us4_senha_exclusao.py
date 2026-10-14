"""US4: trocar a senha e excluir a conta, cenários 1 a 4 (T053; RF-014, RF-015, D-003, D-004).

O diálogo de exclusão (cenário 3, na interface) está em `DialogoExclusao.test.tsx`.
"""

from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select

from app.identidade.modelos import Sessao, Usuario
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.nucleo.relogio import RelogioControlavel
from tests.apoio_http import (
    COOKIE_CSRF,
    COOKIE_SESSAO,
    abrir_cliente,
    cadastrar,
    cookies_da_resposta,
    entrar,
    sair,
)
from tests.fabricas import dados_conta

pytestmark = pytest.mark.functional

NOVA_SENHA = "outra frase longa e incomum 2026"


# --- Cenário 1: troca de senha ------------------------------------------------------------


async def test_cenario1_troca_a_senha_e_encerra_so_as_outras_sessoes(
    aplicacao: FastAPI, cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    conta = dados_conta()
    assert (await cadastrar(cliente, conta)).status_code == 201
    async with (
        abrir_cliente(aplicacao, ip="198.51.100.71") as outro,
        abrir_cliente(aplicacao, ip="198.51.100.72") as terceiro,
    ):
        assert (await entrar(outro, conta)).status_code == 200
        assert (await entrar(terceiro, conta)).status_code == 200

        resposta = await cliente.post(
            "/api/v1/perfil/senha", json={"senhaAtual": conta.senha, "novaSenha": NOVA_SENHA}
        )

        assert resposta.status_code == 204, resposta.text
        assert resposta.content == b""
        assert (await cliente.get("/api/v1/perfil")).status_code == 200, "a sessão atual continua"
        assert (await outro.get("/api/v1/perfil")).status_code == 401
        assert (await terceiro.get("/api/v1/perfil")).status_code == 401
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        ativas = (
            await sessao.execute(
                select(func.count()).select_from(Sessao).where(Sessao.revogada_em.is_(None))
            )
        ).scalar_one()
    assert ativas == 1

    # A senha antiga não vale mais; a nova vale.
    await sair(cliente)
    assert (await entrar(cliente, conta)).status_code == 401
    assert (await entrar(cliente, {"email": conta.email, "senha": NOVA_SENHA})).status_code == 200


async def test_cenario1_a_nova_senha_fica_guardada_so_como_hash(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    conta = dados_conta()
    await cadastrar(cliente, conta)
    antes = None
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        antes = (await sessao.execute(select(Usuario.senha_hash))).scalar_one()
    await cliente.post(
        "/api/v1/perfil/senha", json={"senhaAtual": conta.senha, "novaSenha": NOVA_SENHA}
    )
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        depois = (await sessao.execute(select(Usuario.senha_hash))).scalar_one()
    assert depois != antes and depois.startswith("$argon2id$")
    assert NOVA_SENHA not in depois


async def test_cenario1_nova_senha_invalida_e_recusada_junto_do_campo_e_nada_muda(
    cliente: httpx.AsyncClient,
) -> None:
    conta = dados_conta()
    await cadastrar(cliente, conta)
    for nova in ("curta", "12345678", "        ", "x" * 129, "PASSWORD"):
        resposta = await cliente.post(
            "/api/v1/perfil/senha", json={"senhaAtual": conta.senha, "novaSenha": nova}
        )
        assert resposta.status_code == 422, (nova, resposta.text)
        assert resposta.json()["codigo"] == "dados_invalidos"
        assert [c["campo"] for c in resposta.json()["campos"]] == ["novaSenha"]
    await sair(cliente)
    assert (await entrar(cliente, conta)).status_code == 200, "a senha antiga segue valendo"


# --- Cenário 2: senha atual errada ---------------------------------------------------------


async def test_cenario2_senha_atual_errada_nao_muda_nada_e_conta_para_o_limite(
    cliente: httpx.AsyncClient,
) -> None:
    conta = dados_conta()
    await cadastrar(cliente, conta)
    for _ in range(5):
        resposta = await cliente.post(
            "/api/v1/perfil/senha", json={"senhaAtual": "errada-errada-1", "novaSenha": NOVA_SENHA}
        )
        assert resposta.status_code == 422
        assert resposta.json()["codigo"] == "senha_atual_incorreta"
        assert [c["campo"] for c in resposta.json()["campos"]] == ["senhaAtual"]

    # A sexta tentativa, mesmo com a senha certa, cai no bloqueio da conta (RQ-003).
    bloqueada = await cliente.post(
        "/api/v1/perfil/senha", json={"senhaAtual": conta.senha, "novaSenha": NOVA_SENHA}
    )
    assert bloqueada.status_code == 429
    assert bloqueada.json()["codigo"] == "muitas_tentativas"
    assert int(bloqueada.headers["Retry-After"]) >= 1
    # E a entrada da mesma conta também está bloqueada: o limite é um só.
    await sair(cliente)
    assert (await entrar(cliente, conta)).status_code == 429


async def test_cenario2_a_senha_certa_zera_as_falhas_da_senha_atual(
    cliente: httpx.AsyncClient, relogio: RelogioControlavel
) -> None:
    conta = dados_conta()
    await cadastrar(cliente, conta)
    for _ in range(4):
        await cliente.post(
            "/api/v1/perfil/senha", json={"senhaAtual": "errada-errada-1", "novaSenha": NOVA_SENHA}
        )
    assert (
        await cliente.post(
            "/api/v1/perfil/senha", json={"senhaAtual": conta.senha, "novaSenha": NOVA_SENHA}
        )
    ).status_code == 204
    for _ in range(4):
        resposta = await cliente.post(
            "/api/v1/perfil/senha",
            json={"senhaAtual": "errada-errada-1", "novaSenha": "mais uma frase 123"},
        )
        assert resposta.status_code == 422, "as falhas anteriores foram zeradas"
    relogio.avancar(minutes=16)
    assert (
        await cliente.post(
            "/api/v1/perfil/senha",
            json={"senhaAtual": NOVA_SENHA, "novaSenha": "mais uma frase 123"},
        )
    ).status_code == 204


async def test_troca_de_senha_exige_sessao(cliente: httpx.AsyncClient) -> None:
    await cliente.get("/api/v1/auth/csrf")
    resposta = await cliente.post(
        "/api/v1/perfil/senha", json={"senhaAtual": "qualquer coisa", "novaSenha": NOVA_SENHA}
    )
    assert resposta.status_code == 401


# --- Cenários 3 e 4: exclusão da conta -----------------------------------------------------


async def test_cenario4_exclusao_apaga_tudo_encerra_as_sessoes_e_libera_o_email(
    aplicacao: FastAPI, cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    conta = dados_conta()
    assert (await cadastrar(cliente, conta)).status_code == 201
    async with abrir_cliente(aplicacao, ip="198.51.100.73") as outro:
        assert (await entrar(outro, conta)).status_code == 200
        token_antigo = cliente.cookies[COOKIE_SESSAO]

        resposta = await cliente.post("/api/v1/perfil/exclusao", json={"senhaAtual": conta.senha})

        assert resposta.status_code == 204, resposta.text
        cookies = cookies_da_resposta(resposta)
        assert all("max-age=0" in valor.lower() for valor in cookies.values())
        assert COOKIE_SESSAO not in cliente.cookies and COOKIE_CSRF not in cliente.cookies
        assert (await outro.get("/api/v1/perfil")).status_code == 401, "todas as sessões terminam"
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        for entidade in (Usuario, Sessao):
            assert (
                await sessao.execute(select(func.count()).select_from(entidade))
            ).scalar_one() == 0

    # O cookie antigo não vale, a senha antiga não entra e o e-mail pode ser cadastrado de novo.
    cliente.cookies.set(COOKIE_SESSAO, token_antigo, domain="teste")
    assert (await cliente.get("/api/v1/perfil")).status_code == 401
    assert (await entrar(cliente, conta)).status_code == 401
    novo = await cadastrar(cliente, conta)
    assert novo.status_code == 201, novo.text
    assert novo.json()["email"] == conta.email


async def test_cenario4_exclusao_com_senha_errada_nao_apaga_nada(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    conta = dados_conta()
    await cadastrar(cliente, conta)
    resposta = await cliente.post("/api/v1/perfil/exclusao", json={"senhaAtual": "errada-errada-1"})
    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "senha_atual_incorreta"
    assert (await cliente.get("/api/v1/perfil")).status_code == 200
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        assert (await sessao.execute(select(func.count()).select_from(Usuario))).scalar_one() == 1


async def test_cenario4_a_exclusao_enfileira_a_remocao_dos_arquivos_na_mesma_transacao(
    cliente: httpx.AsyncClient, fabrica_sessoes: FabricaSessoes
) -> None:
    from sqlalchemy import text

    conta = dados_conta()
    perfil = await cadastrar(cliente, conta)
    assert perfil.status_code == 201
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        public_id = (await sessao.execute(select(Usuario.public_id))).scalar_one()
    assert (
        await cliente.post("/api/v1/perfil/exclusao", json={"senhaAtual": conta.senha})
    ).status_code == 204
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        jobs = (
            await sessao.execute(
                text(
                    "select task_name, args from procrastinate_jobs "
                    "where task_name like 'identidade.%'"
                )
            )
        ).all()
    assert [(j.task_name, j.args) for j in jobs] == [
        ("identidade.apagar_objetos_usuario", {"public_id": str(public_id)})
    ]


async def test_o_perfil_da_conta_excluida_nao_existe_mais_para_outra_conta(
    aplicacao: FastAPI, cliente: httpx.AsyncClient
) -> None:
    conta, outra = dados_conta(), dados_conta()
    await cadastrar(cliente, conta)
    async with abrir_cliente(aplicacao, ip="198.51.100.74") as cliente_outra:
        await cadastrar(cliente_outra, outra)
        await cliente.post("/api/v1/perfil/exclusao", json={"senhaAtual": conta.senha})
        assert (await cliente_outra.get("/api/v1/perfil")).json()["email"] == outra.email
