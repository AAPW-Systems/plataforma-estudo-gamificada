"""Fábrica de cartões fictícios da spec 003 (plano, "Dados de teste"; regra 10).

Os textos vêm de um corpus fictício pequeno, sem dados pessoais, e a sequência é determinística:
`gerar(n)` devolve sempre os mesmos `n` cartões, em um ciclo de 12 receitas que cobre:

- as três origens (``criado``, ``editado`` e ``gerado_verificado``, esta última inserida direto,
  como a RF-006 e a US4 pedem, porque só a 004 cria cartões gerados de verdade);
- ativos e suspensos, nos três estados do FSRS (novo, revisão e reaprendizado), para o CS-002 e o
  CS-003;
- referência a uma fonte (só em ``criado``, DTEC 035);
- acentos, cedilha, variação de maiúsculas, curingas do ``LIKE`` (``%``, ``_`` e ``\\``), marcação
  e script (RQ-001), quebras de linha e emoji.

Linha de comando (também usada no quickstart)::

    python -m tests.fabricas_cartoes --email ana.teste@exemplo.com --materia Biologia \\
        --quantidade 120

Só roda com ``APP_AMBIENTE=desenvolvimento`` e só para contas do domínio ``exemplo.com``.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cartoes.modelos import Cartao, EstadoFsrs, OrigemCartao, SituacaoCartao
from app.fontes.modelos import Fonte
from app.identidade.modelos import Usuario
from app.materias.modelos import Materia
from app.nucleo.banco import criar_engine, criar_fabrica, unidade_de_trabalho
from app.nucleo.configuracao import Configuracao, obter_configuracao

DOMINIO_PERMITIDO = "exemplo.com"
QUANTIDADE_MAXIMA = 5000

_ATIVO, _SUSPENSO = SituacaoCartao.ATIVO, SituacaoCartao.SUSPENSO
_CRIADO, _EDITADO, _GERADO = (
    OrigemCartao.CRIADO,
    OrigemCartao.EDITADO,
    OrigemCartao.GERADO_VERIFICADO,
)
_NOVO, _REVISAO, _REAPRENDIZADO = (
    EstadoFsrs.APRENDIZADO,
    EstadoFsrs.REVISAO,
    EstadoFsrs.REAPRENDIZADO,
)


@dataclass(frozen=True, slots=True)
class CartaoFicticio:
    """Um cartão a inserir. Os instantes do FSRS são deslocamentos a partir de `agora`."""

    frente: str
    verso: str
    explicacao: str | None = None
    origem: OrigemCartao = OrigemCartao.CRIADO
    situacao: SituacaoCartao = SituacaoCartao.ATIVO
    estado_fsrs: EstadoFsrs = EstadoFsrs.APRENDIZADO
    passo: int | None = 0
    estabilidade: float | None = None
    dificuldade: float | None = None
    # Nulo no cartão novo: o vencimento é o instante da criação (DTEC 037).
    vencimento_em: timedelta | None = None
    ultima_revisao_em: timedelta | None = None
    com_referencia: bool = False


@dataclass(frozen=True, slots=True)
class ReferenciaFonte:
    """Descrição da origem copiada para o cartão que cita uma fonte (DTEC 035)."""

    fonte_id: int
    titulo: str
    nome_arquivo: str
    enviada_em: datetime


# --- Corpus fictício -----------------------------------------------------------------------------

_PARES = (
    ("Qual organela produz ATP?", "Mitocôndria", "A respiração celular ocorre nas cristas."),
    ("O que guarda o material genético?", "O núcleo.", None),
    ("Qual é a função dos ribossomos?", "Montar as proteínas.", "Eles leem o RNA mensageiro."),
    ("O que é fotossíntese?", "A conversão de luz em energia química.", None),
    ("Onde ocorre a fotossíntese?", "Nos cloroplastos.", "Existem nas células vegetais."),
    ("O que é osmose?", "A passagem de água por uma membrana semipermeável.", None),
    (
        "Qual a função das enzimas?",
        "Acelerar reações químicas.",
        "Cada enzima age em um substrato.",
    ),
    ("O que é uma população?", "Indivíduos da mesma espécie em um mesmo local.", None),
    (
        "O que liga produtores e consumidores?",
        "A cadeia alimentar.",
        "Os decompositores fecham o ciclo.",
    ),
    ("Como o DNA é copiado?", "Por replicação semiconservativa.", None),
    (
        "O que é mitose?",
        "A divisão que gera duas células idênticas.",
        "Tem prófase, metáfase, anáfase e telófase.",
    ),
    ("O que é um ecossistema?", "Seres vivos e o ambiente em que interagem.", None),
)

_CAIXA = (
    ("O que é a célula?", "A unidade básica da vida."),
    ("Defina CÉLULA.", "A menor unidade estrutural e funcional dos seres vivos."),
    ("Célula: qual a função da membrana?", "Controlar o que entra e sai."),
    ("Por que a célula precisa de energia?", "Para manter as reações e o transporte."),
    ("Qual a AÇÃO da insulina na CÉLULA?", "Facilita a entrada de glicose."),
    ("Qual é a ação do cloroplasto?", "Realizar a fotossíntese na célula vegetal."),
)

_CURINGAS = (
    ("Quanto é 100% de 50?", "50. O % e o _ são só texto aqui, como a barra \\ em C:\\pasta."),
    ("Como se chama a variável nome_do_aluno?", "snake_case: palavras ligadas por _."),
    ("O que significa o padrão 50%_?", "Nada especial: é o texto literal 50%_."),
)

_MARCACAO = (
    ("<script>alert(1)</script>", "Isto é só texto: nada é executado."),
    ("<img src=x onerror=alert(1)>", "Também é texto puro, exibido literalmente."),
    ("**negrito** e [link](javascript:alert(1))", "Sem formatação no MVP (D-003)."),
    ("Use <b>tags</b> & entidades &amp; &lt;", "O que se vê é o que foi digitado."),
)

_QUEBRAS = (
    (
        "Liste as fases da mitose:\n1. Prófase\n2. Metáfase\n3. Anáfase",
        "Prófase, metáfase, anáfase e telófase.\nNessa ordem.",
    ),
    (
        "Cite três organelas:\n- núcleo\n- ribossomo\n- lisossomo",
        "Há muitas outras:\nretículo, golgi, vacúolo.",
    ),
)

_EMOJI = (
    ("🧬 O que é o DNA?", "O ácido desoxirribonucleico. 🔬"),
    ("🌱 Do que a planta precisa para crescer?", "Luz, água e CO₂. ☀️"),
)


def texto_com_tamanho(tamanho: int) -> str:
    """Texto normalizado com exatamente `tamanho` code points, sem espaços nas extremidades."""
    if tamanho < 1:
        raise ValueError("o tamanho precisa ser de pelo menos 1")
    texto = ("ação " * (tamanho // 4 + 1))[:tamanho]
    return texto[:-1] + "x" if texto.endswith(" ") else texto


# --- Receitas ------------------------------------------------------------------------------------

# (origem, situação, estado do FSRS, tema). Suspensos: 4 de 12.
_RECEITAS = (
    (_CRIADO, _ATIVO, _NOVO, "normal"),
    (_CRIADO, _ATIVO, _REVISAO, "caixa"),
    (_CRIADO, _SUSPENSO, _NOVO, "normal"),
    (_EDITADO, _ATIVO, _REAPRENDIZADO, "normal"),
    (_GERADO, _ATIVO, _REVISAO, "caixa"),
    (_CRIADO, _ATIVO, _NOVO, "curinga"),
    (_CRIADO, _ATIVO, _REVISAO, "marcacao"),
    (_CRIADO, _SUSPENSO, _REVISAO, "normal"),
    (_GERADO, _SUSPENSO, _NOVO, "quebra"),
    (_CRIADO, _ATIVO, _NOVO, "emoji"),
    (_CRIADO, _ATIVO, _NOVO, "referencia"),
    (_EDITADO, _SUSPENSO, _REVISAO, "caixa"),
)


def _estado_do_fsrs(estado: EstadoFsrs, indice: int) -> dict[str, object]:
    """Colunas do FSRS coerentes com o `Card` da biblioteca (DTEC 037)."""
    if estado is EstadoFsrs.APRENDIZADO:  # cartão novo: o estado de `fsrs.Card()`
        return {"passo": 0, "estabilidade": None, "dificuldade": None}
    variacao = (indice % 7) / 10
    if estado is EstadoFsrs.REVISAO:
        return {
            "passo": None,
            "estabilidade": 8.0 + indice % 40,
            "dificuldade": 4.0 + variacao,
            "vencimento_em": timedelta(days=1 + indice % 9),
            "ultima_revisao_em": -timedelta(days=2 + indice % 5),
        }
    return {  # reaprendizado: vencido há pouco, depois de um "Errei"
        "passo": 0,
        "estabilidade": 1.5 + variacao,
        "dificuldade": 6.0 + variacao,
        "vencimento_em": -timedelta(minutes=30),
        "ultima_revisao_em": -timedelta(hours=1),
    }


def _textos(tema: str, indice: int) -> tuple[str, str, str | None]:
    rodada = indice // len(_RECEITAS)
    if tema == "caixa":
        frente, verso = _CAIXA[(indice + rodada) % len(_CAIXA)]
        return frente, verso, None
    if tema == "curinga":
        frente, verso = _CURINGAS[rodada % len(_CURINGAS)]
        return frente, verso, None
    if tema == "marcacao":
        frente, verso = _MARCACAO[rodada % len(_MARCACAO)]
        return frente, verso, "Texto de estudante é sempre texto."
    if tema == "quebra":
        frente, verso = _QUEBRAS[rodada % len(_QUEBRAS)]
        return frente, verso, None
    if tema == "emoji":
        frente, verso = _EMOJI[rodada % len(_EMOJI)]
        return frente, verso, None
    return _PARES[(indice + rodada) % len(_PARES)]


def gerar(quantidade: int) -> list[CartaoFicticio]:
    """Os `quantidade` primeiros cartões da sequência fixa (de 0 a 5.000)."""
    if not 0 <= quantidade <= QUANTIDADE_MAXIMA:
        raise ValueError(f"quantidade deve estar entre 0 e {QUANTIDADE_MAXIMA}")
    cartoes: list[CartaoFicticio] = []
    for indice in range(quantidade):
        origem, situacao, estado, tema = _RECEITAS[indice % len(_RECEITAS)]
        frente, verso, explicacao = _textos(tema, indice)
        cartoes.append(
            CartaoFicticio(
                frente=frente,
                verso=verso,
                explicacao=explicacao,
                origem=origem,
                situacao=situacao,
                estado_fsrs=estado,
                com_referencia=tema == "referencia",
                **_estado_do_fsrs(estado, indice),  # type: ignore[arg-type]
            )
        )
    return cartoes


EXPLICACAO_GERADO = "Explicação fictícia de um cartão gerado."


def _explicacao(item: CartaoFicticio) -> str | None:
    """Desde a 0005 (spec 004), o banco exige explicação no gerado (RF-008 da 004)."""
    if item.origem is _GERADO and item.explicacao is None:
        return EXPLICACAO_GERADO
    return item.explicacao


def cartao_ficticio(**alteracoes: object) -> CartaoFicticio:
    """Um cartão novo, ativo e criado pelo estudante, com as alterações pedidas."""
    return replace(CartaoFicticio("Qual organela produz ATP?", "Mitocôndria"), **alteracoes)  # type: ignore[arg-type]


def cartao_no_limite(frente: int, verso: int, explicacao: int) -> CartaoFicticio:
    """Textos com exatamente o tamanho dos limites vigentes (borda aceita)."""
    return cartao_ficticio(
        frente=texto_com_tamanho(frente),
        verso=texto_com_tamanho(verso),
        explicacao=texto_com_tamanho(explicacao),
    )


def cartao_acima_do_limite(campo: str, frente: int, verso: int, explicacao: int) -> CartaoFicticio:
    """Como `cartao_no_limite`, com um caractere a mais em `campo` (borda recusada)."""
    base = cartao_no_limite(frente, verso, explicacao)
    limites = {"frente": frente, "verso": verso, "explicacao": explicacao}
    alteracao: dict[str, Any] = {campo: texto_com_tamanho(limites[campo] + 1)}
    return replace(base, **alteracao)


# --- Inserção ------------------------------------------------------------------------------------


async def inserir(
    sessao: AsyncSession,
    *,
    usuario_id: int,
    materia_id: int,
    itens: Sequence[CartaoFicticio],
    agora: datetime,
    fonte: ReferenciaFonte | None = None,
) -> list[Cartao]:
    """Insere os cartões direto no banco, do mais antigo ao mais recente (um segundo entre eles).

    A fábrica passa pelos `CHECK` e pelas FKs de verdade: não há atalho de validação.
    """
    cartoes: list[Cartao] = []
    total = len(itens)
    for posicao, item in enumerate(itens):
        criado_em = agora - timedelta(seconds=total - posicao)
        referencia = fonte if item.com_referencia and fonte is not None else None
        cartoes.append(
            Cartao(
                usuario_id=usuario_id,
                materia_id=materia_id,
                frente=item.frente,
                verso=item.verso,
                explicacao=_explicacao(item),
                origem=item.origem,
                situacao=item.situacao,
                entrada_estudo_em=criado_em,
                fonte_id=referencia.fonte_id if referencia else None,
                referencia_titulo=referencia.titulo if referencia else None,
                referencia_nome_arquivo=referencia.nome_arquivo if referencia else None,
                referencia_enviada_em=referencia.enviada_em if referencia else None,
                estado_fsrs=item.estado_fsrs,
                passo=item.passo,
                estabilidade=item.estabilidade,
                dificuldade=item.dificuldade,
                vencimento=criado_em if item.vencimento_em is None else agora + item.vencimento_em,
                ultima_revisao=(
                    None if item.ultima_revisao_em is None else agora + item.ultima_revisao_em
                ),
                criado_em=criado_em,
                atualizado_em=criado_em,
            )
        )
    sessao.add_all(cartoes)
    await sessao.flush()
    return cartoes


# --- Linha de comando ----------------------------------------------------------------------------


def email_de_exemplo(email: str) -> bool:
    """Verdadeiro só para `algo@exemplo.com`, sem diferenciar a caixa (regra 10)."""
    local, separador, dominio = email.partition("@")
    return bool(local) and separador == "@" and dominio.lower() == DOMINIO_PERMITIDO


def _quantidade(valor: str) -> int:
    try:
        quantidade = int(valor)
    except ValueError:
        raise argparse.ArgumentTypeError(f"quantidade inválida: {valor!r}") from None
    if not 1 <= quantidade <= QUANTIDADE_MAXIMA:
        raise argparse.ArgumentTypeError(f"quantidade deve estar entre 1 e {QUANTIDADE_MAXIMA}")
    return quantidade


def _analisador() -> argparse.ArgumentParser:
    analisador = argparse.ArgumentParser(
        prog="python -m tests.fabricas_cartoes",
        description="Cria cartões fictícios numa matéria de uma conta @exemplo.com.",
    )
    analisador.add_argument("--email", required=True, help="conta fictícia do domínio exemplo.com")
    analisador.add_argument("--materia", required=True, help="nome da matéria da conta")
    analisador.add_argument("--quantidade", type=_quantidade, default=120)
    return analisador


def _validar(argv: Sequence[str] | None, configuracao: Configuracao) -> argparse.Namespace | int:
    """Lê os argumentos e aplica as recusas da regra 10, antes de abrir qualquer conexão."""
    argumentos = _analisador().parse_args(argv)
    if configuracao.app_ambiente != "desenvolvimento":
        sys.stderr.write("A fábrica só roda com APP_AMBIENTE=desenvolvimento.\n")
        return 2
    if not email_de_exemplo(argumentos.email):
        sys.stderr.write(
            f"Use uma conta do domínio {DOMINIO_PERMITIDO} (dados fictícios, regra 10).\n"
        )
        return 2
    return argumentos


async def _semear(argumentos: argparse.Namespace, configuracao: Configuracao) -> int:
    engine = criar_engine(configuracao)
    try:
        fabrica = criar_fabrica(engine)
        async with unidade_de_trabalho(fabrica) as sessao:
            usuario = (
                await sessao.execute(
                    select(Usuario).where(func.lower(Usuario.email) == argumentos.email.lower())
                )
            ).scalar_one_or_none()
            if usuario is None:
                sys.stderr.write(f"Não há conta com o e-mail {argumentos.email}.\n")
                return 1
            materia = (
                await sessao.execute(
                    select(Materia).where(
                        Materia.usuario_id == usuario.id,
                        func.lower(Materia.nome) == argumentos.materia.lower(),
                    )
                )
            ).scalar_one_or_none()
            if materia is None:
                sys.stderr.write(f"A conta não tem a matéria {argumentos.materia!r}.\n")
                return 1
            fonte = (
                await sessao.execute(
                    select(Fonte)
                    .where(Fonte.usuario_id == usuario.id, Fonte.materia_id == materia.id)
                    .order_by(Fonte.id)
                    .limit(1)
                )
            ).scalar_one_or_none()
            referencia = (
                ReferenciaFonte(fonte.id, fonte.titulo, fonte.nome_arquivo, fonte.criado_em)
                if fonte is not None
                else None
            )
            criados = await inserir(
                sessao,
                usuario_id=usuario.id,
                materia_id=materia.id,
                itens=gerar(argumentos.quantidade),
                agora=datetime.now(UTC),
                fonte=referencia,
            )
        sys.stdout.write(f"{len(criados)} cartões criados na matéria {materia.nome!r}.\n")
        return 0
    finally:
        await engine.dispose()


async def executar(
    argv: Sequence[str] | None = None, configuracao: Configuracao | None = None
) -> int:
    """Versão assíncrona de `principal`, para quem já tem um laço de eventos (os testes)."""
    configuracao = configuracao or obter_configuracao()
    argumentos = _validar(argv, configuracao)
    if isinstance(argumentos, int):
        return argumentos
    return await _semear(argumentos, configuracao)


def principal(argv: Sequence[str] | None = None, configuracao: Configuracao | None = None) -> int:
    configuracao = configuracao or obter_configuracao()
    argumentos = _validar(argv, configuracao)
    if isinstance(argumentos, int):
        return argumentos
    return asyncio.run(_semear(argumentos, configuracao))


if __name__ == "__main__":
    raise SystemExit(principal())
