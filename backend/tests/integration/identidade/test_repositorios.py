"""Repositórios da identidade contra o PostgreSQL real (T034; DTEC 019, 020 e 023).

Os testes de concorrência usam `fabrica_real` (conexões e transações reais), porque os
savepoints de uma única conexão não exercitam travas nem a corrida pelo índice único.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.identidade.excecoes import EmailEmUso
from app.identidade.modelos import Sessao, TentativaAcesso, Usuario
from app.identidade.repositorios import (
    RepositorioSessoes,
    RepositorioTentativas,
    RepositorioUsuarios,
)
from app.nucleo.banco import FabricaSessoes, unidade_de_trabalho
from app.revisao.repositorios import RepositorioParametrosFsrs

pytestmark = pytest.mark.integration

AGORA = datetime(2026, 10, 13, 12, 0, tzinfo=UTC)
HASH = "$argon2id$v=19$m=65536,t=3,p=4$c2Fs$aGFzaA"  # formato PHC fictício


async def _criar_usuario(fabrica: FabricaSessoes, email: str = "ana@exemplo.com") -> int:
    async with unidade_de_trabalho(fabrica) as sessao:
        usuario = await RepositorioUsuarios(sessao).criar(
            nome="Ana", email=email, senha_hash=HASH, fuso="America/Recife", agora=AGORA
        )
        return usuario.id


# --- Usuários ----------------------------------------------------------------------------


async def test_criar_usuario_aplica_padroes_de_d001(fabrica_sessoes: FabricaSessoes) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        usuario = await RepositorioUsuarios(sessao).criar(
            nome="Ana", email="ana@exemplo.com", senha_hash=HASH, fuso="America/Recife", agora=AGORA
        )
        assert usuario.id > 0 and usuario.public_id is not None
        assert usuario.papel == "estudante"
        assert (usuario.meta_diaria, usuario.tamanho_licao, usuario.limite_novos_dia) == (
            20,
            10,
            20,
        )
        assert usuario.criado_em == AGORA == usuario.atualizado_em
        assert usuario.fuso == "America/Recife"


async def test_buscar_por_email_ignora_a_caixa(fabrica_sessoes: FabricaSessoes) -> None:
    await _criar_usuario(fabrica_sessoes, "ana@exemplo.com")
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        repositorio = RepositorioUsuarios(sessao)
        assert (await repositorio.buscar_por_email("ana@exemplo.com")) is not None
        assert (await repositorio.buscar_por_email("ANA@Exemplo.com")) is not None
        assert (await repositorio.buscar_por_email("bia@exemplo.com")) is None


async def test_email_repetido_com_outra_caixa_vira_email_em_uso(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    await _criar_usuario(fabrica_sessoes, "ana@exemplo.com")
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        with pytest.raises(EmailEmUso) as erro:
            await RepositorioUsuarios(sessao).criar(
                nome="Outra",
                email="ANA@EXEMPLO.COM",
                senha_hash=HASH,
                fuso="America/Recife",
                agora=AGORA,
            )
        assert erro.value.status == 409
        # A sessão continua utilizável depois do conflito (a violação foi num savepoint).
        total = (await sessao.execute(select(func.count()).select_from(Usuario))).scalar_one()
        assert total == 1


async def test_buscar_por_id_e_atualizar_hash(fabrica_sessoes: FabricaSessoes) -> None:
    usuario_id = await _criar_usuario(fabrica_sessoes)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        repositorio = RepositorioUsuarios(sessao)
        await repositorio.atualizar_senha_hash(usuario_id, "novo-hash", AGORA + timedelta(hours=1))
        usuario = await repositorio.buscar_por_id(usuario_id)
        assert usuario is not None
        assert usuario.senha_hash == "novo-hash"
        assert usuario.atualizado_em == AGORA + timedelta(hours=1)
        assert await repositorio.buscar_por_id(usuario_id + 999) is None


async def test_corrida_de_cadastros_com_o_mesmo_email_cria_uma_conta(
    fabrica_real: FabricaSessoes,
) -> None:
    async def tentar(i: int) -> str:
        try:
            async with unidade_de_trabalho(fabrica_real) as sessao:
                await RepositorioUsuarios(sessao).criar(
                    nome=f"Concorrente {i}",
                    email="corrida@exemplo.com" if i % 2 else "CORRIDA@exemplo.com",
                    senha_hash=HASH,
                    fuso="America/Recife",
                    agora=AGORA,
                )
        except EmailEmUso:
            return "em_uso"
        return "criada"

    resultados = await asyncio.gather(*(tentar(i) for i in range(8)))
    assert resultados.count("criada") == 1
    assert resultados.count("em_uso") == 7
    async with unidade_de_trabalho(fabrica_real) as sessao:
        assert (await sessao.execute(select(func.count()).select_from(Usuario))).scalar_one() == 1


# --- Sessões -----------------------------------------------------------------------------


async def test_ciclo_da_sessao(fabrica_sessoes: FabricaSessoes) -> None:
    usuario_id = await _criar_usuario(fabrica_sessoes)
    token_hash = b"\x01" * 32
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        repositorio = RepositorioSessoes(sessao)
        criada = await repositorio.criar(
            usuario_id=usuario_id,
            token_hash=token_hash,
            agora=AGORA,
            expira_em=AGORA + timedelta(days=30),
            ip="203.0.113.7",
            agente_usuario="Navegador de teste/1.0 " + "x" * 600,
        )
        assert criada.revogada_em is None
        assert len(criada.agente_usuario or "") == 512, "o agente é truncado"

        achada = await repositorio.buscar_por_hash(token_hash)
        assert achada is not None
        sessao_achada, usuario = achada
        assert sessao_achada.id == criada.id and usuario.id == usuario_id
        assert await repositorio.buscar_por_hash(b"\x02" * 32) is None

        await repositorio.renovar_uso(criada.id, AGORA + timedelta(minutes=5))
        await repositorio.revogar(criada.id, AGORA + timedelta(minutes=6))
        achada = await repositorio.buscar_por_hash(token_hash)
        assert achada is not None
        assert achada[0].ultimo_uso_em == AGORA + timedelta(minutes=5)
        assert achada[0].revogada_em == AGORA + timedelta(minutes=6)


async def test_revogar_outras_preserva_a_atual_e_so_da_mesma_conta(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    ana = await _criar_usuario(fabrica_sessoes, "ana@exemplo.com")
    bia = await _criar_usuario(fabrica_sessoes, "bia@exemplo.com")
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        repositorio = RepositorioSessoes(sessao)
        ids = {}
        for nome, dono, byte in (("a1", ana, 1), ("a2", ana, 2), ("a3", ana, 3), ("b1", bia, 4)):
            ids[nome] = (
                await repositorio.criar(
                    usuario_id=dono,
                    token_hash=bytes([byte]) * 32,
                    agora=AGORA,
                    expira_em=AGORA + timedelta(days=30),
                    ip=None,
                    agente_usuario=None,
                )
            ).id
        revogadas = await repositorio.revogar_outras(ana, ids["a1"], AGORA)
        assert revogadas == 2
        estado = {
            linha.id: linha.revogada_em
            for linha in (await sessao.execute(select(Sessao))).scalars()
        }
        assert estado[ids["a1"]] is None
        assert estado[ids["a2"]] == AGORA and estado[ids["a3"]] == AGORA
        assert estado[ids["b1"]] is None, "sessões de outra conta nunca são tocadas"


# --- Tentativas de acesso ----------------------------------------------------------------


async def test_registra_e_conta_falhas_por_conta_e_por_endereco(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    chave_a, chave_b = b"a" * 32, b"b" * 32
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        tentativas = RepositorioTentativas(sessao)
        await tentativas.registrar("falha_entrada", chave_a, "203.0.113.7", AGORA)
        await tentativas.registrar(
            "falha_senha_atual", chave_a, "203.0.113.8", AGORA + timedelta(minutes=1)
        )
        await tentativas.registrar(
            "falha_entrada", chave_b, "203.0.113.7", AGORA + timedelta(minutes=2)
        )
        await tentativas.registrar("cadastro", None, "203.0.113.7", AGORA + timedelta(minutes=3))

        desde = AGORA - timedelta(minutes=1)
        assert len(await tentativas.instantes_falhas_conta(chave_a, desde)) == 2
        assert len(await tentativas.instantes_falhas_conta(chave_b, desde)) == 1
        assert len(await tentativas.instantes_falhas_ip("203.0.113.7", desde)) == 2, (
            "o cadastro não conta como falha"
        )
        assert len(await tentativas.instantes_cadastros_ip("203.0.113.7", desde)) == 1
        assert await tentativas.instantes_falhas_conta(chave_a, AGORA + timedelta(minutes=30)) == []


async def test_entrada_bem_sucedida_apaga_so_as_falhas_da_conta(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    chave_a, chave_b = b"a" * 32, b"b" * 32
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        tentativas = RepositorioTentativas(sessao)
        for chave in (chave_a, chave_a, chave_b):
            await tentativas.registrar("falha_entrada", chave, "203.0.113.7", AGORA)
        await tentativas.apagar_falhas_conta(chave_a)
        desde = AGORA - timedelta(minutes=1)
        assert await tentativas.instantes_falhas_conta(chave_a, desde) == []
        assert len(await tentativas.instantes_falhas_conta(chave_b, desde)) == 1
        assert len(await tentativas.instantes_falhas_ip("203.0.113.7", desde)) == 1, (
            "as falhas do endereço permanecem (DTEC 020)"
        )


async def test_tentativa_nunca_guarda_email_em_claro(fabrica_sessoes: FabricaSessoes) -> None:
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        await RepositorioTentativas(sessao).registrar(
            "falha_entrada", b"\x00" * 32, "2001:db8::1", AGORA
        )
        linha = (await sessao.execute(select(TentativaAcesso))).scalar_one()
        assert linha.chave_conta == b"\x00" * 32
        assert "@" not in repr(linha.chave_conta)


async def test_apagar_expiradas_remove_tentativas_antigas_e_sessoes_invalidas(
    fabrica_sessoes: FabricaSessoes,
) -> None:
    """Base da tarefa `limpar_registros_expirados` (T056): o repositório já apaga."""
    usuario_id = await _criar_usuario(fabrica_sessoes)
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        tentativas = RepositorioTentativas(sessao)
        await tentativas.registrar(
            "falha_entrada", b"a" * 32, "203.0.113.7", AGORA - timedelta(hours=25)
        )
        await tentativas.registrar(
            "falha_entrada", b"a" * 32, "203.0.113.7", AGORA - timedelta(hours=23)
        )
        assert await tentativas.apagar_anteriores_a(AGORA - timedelta(hours=24)) == 1

        repositorio = RepositorioSessoes(sessao)
        velha = await repositorio.criar(
            usuario_id=usuario_id,
            token_hash=b"\x0a" * 32,
            agora=AGORA - timedelta(days=60),
            expira_em=AGORA - timedelta(days=31),
            ip=None,
            agente_usuario=None,
        )
        revogada = await repositorio.criar(
            usuario_id=usuario_id,
            token_hash=b"\x0b" * 32,
            agora=AGORA - timedelta(days=40),
            expira_em=AGORA + timedelta(days=10),
            ip=None,
            agente_usuario=None,
        )
        await repositorio.revogar(revogada.id, AGORA - timedelta(days=35))
        viva = await repositorio.criar(
            usuario_id=usuario_id,
            token_hash=b"\x0c" * 32,
            agora=AGORA,
            expira_em=AGORA + timedelta(days=30),
            ip=None,
            agente_usuario=None,
        )
        assert await repositorio.apagar_invalidas_antes_de(AGORA - timedelta(days=30), 14) == 2
        restantes = {s.id for s in (await sessao.execute(select(Sessao))).scalars()}
        assert restantes == {viva.id}
        assert velha.id not in restantes


# --- Trava por chave (advisory lock da transação) ----------------------------------------


async def test_trava_por_chave_exclui_transacoes_concorrentes(fabrica_real: FabricaSessoes) -> None:
    """A segunda transação só passa da trava depois que a primeira termina (DTEC 020)."""
    ordem: list[str] = []
    liberar_primeira = asyncio.Event()
    primeira_travou = asyncio.Event()

    async def primeira() -> None:
        async with unidade_de_trabalho(fabrica_real) as sessao:
            await RepositorioTentativas(sessao).travar("acesso:conta:abc")
            primeira_travou.set()
            ordem.append("primeira_dentro")
            await liberar_primeira.wait()
            ordem.append("primeira_fim")

    async def segunda() -> None:
        await primeira_travou.wait()
        async with unidade_de_trabalho(fabrica_real) as sessao:
            await RepositorioTentativas(sessao).travar("acesso:conta:abc")
            ordem.append("segunda_dentro")

    t1, t2 = asyncio.create_task(primeira()), asyncio.create_task(segunda())
    await primeira_travou.wait()
    await asyncio.sleep(0.3)
    assert ordem == ["primeira_dentro"], "a segunda deve esperar a trava"
    liberar_primeira.set()
    await asyncio.gather(t1, t2)
    assert ordem == ["primeira_dentro", "primeira_fim", "segunda_dentro"]


async def test_chaves_diferentes_nao_se_bloqueiam(fabrica_real: FabricaSessoes) -> None:
    async with unidade_de_trabalho(fabrica_real) as a, unidade_de_trabalho(fabrica_real) as b:
        await RepositorioTentativas(a).travar("acesso:conta:um")
        await asyncio.wait_for(RepositorioTentativas(b).travar("acesso:conta:dois"), timeout=2)


async def test_travar_varias_chaves_em_ordem_evita_impasse(fabrica_real: FabricaSessoes) -> None:
    async def trabalhar(chaves: tuple[str, ...]) -> None:
        async with unidade_de_trabalho(fabrica_real) as sessao:
            await RepositorioTentativas(sessao).travar(*chaves)
            await asyncio.sleep(0.05)

    await asyncio.wait_for(
        asyncio.gather(
            *(
                trabalhar(
                    ("acesso:conta:x", "acesso:ip:y")
                    if i % 2
                    else ("acesso:ip:y", "acesso:conta:x")
                )
                for i in range(10)
            )
        ),
        timeout=15,
    )


# --- Parâmetros do FSRS ------------------------------------------------------------------


async def test_parametros_fsrs_versao_vigente_e_a_maior(fabrica_sessoes: FabricaSessoes) -> None:
    usuario_id = await _criar_usuario(fabrica_sessoes)
    pesos = [float(i) / 10 for i in range(21)]
    async with unidade_de_trabalho(fabrica_sessoes) as sessao:
        repositorio = RepositorioParametrosFsrs(sessao)
        assert await repositorio.buscar_vigente(usuario_id) is None
        for versao, retencao in ((1, "0.90"), (2, "0.85")):
            await repositorio.criar(
                usuario_id=usuario_id,
                versao=versao,
                pesos=pesos,
                retencao_desejada=Decimal(retencao),
                passos_aprendizado_s=[60, 600],
                passos_reaprendizado_s=[600],
                intervalo_maximo_dias=36500,
                fuzzing=True,
                versao_biblioteca="6.3.2",
                agora=AGORA,
            )
        vigente = await repositorio.buscar_vigente(usuario_id)
        assert vigente is not None
        assert vigente.versao == 2 and str(vigente.retencao_desejada) == "0.85"
        assert vigente.pesos == pesos
