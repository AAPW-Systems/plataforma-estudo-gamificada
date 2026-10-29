"""Persistência dos cartões (spec 003, T003; data-model.md).

A 003 criou a tabela; a 004 (migração `0005`) acrescenta `geracao_id`, `motivo_recusa` e as
situações `aguardando_revisao` e `recusado` (DTEC 038). `dominado_em` (005) e `chave_imagem`
(011) chegam em migrações próprias.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Double,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base


class OrigemCartao(StrEnum):
    GERADO_VERIFICADO = "gerado_verificado"
    EDITADO = "editado"
    CRIADO = "criado"


class SituacaoCartao(StrEnum):
    ATIVO = "ativo"
    SUSPENSO = "suspenso"
    # Só cartões gerados (004): fora do estudo, da lista e das rotas da 003.
    AGUARDANDO_REVISAO = "aguardando_revisao"
    RECUSADO = "recusado"


class MotivoRecusa(StrEnum):
    """Motivo opcional da recusa de um cartão gerado (RF-020, D-007)."""

    INCORRETO = "incorreto"
    IRRELEVANTE = "irrelevante"
    REPETIDO = "repetido"
    MAL_ESCRITO = "mal_escrito"


class EstadoFsrs(StrEnum):
    """Espelha `fsrs.State` (RN-26): quem calcula o agendamento é só a biblioteca."""

    APRENDIZADO = "aprendizado"
    REVISAO = "revisao"
    REAPRENDIZADO = "reaprendizado"


def _valores(enumeracao: type[StrEnum]) -> list[str]:
    return [membro.value for membro in enumeracao]


class Cartao(Base):
    __tablename__ = "cartoes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["materia_id", "usuario_id"],
            ["materias.id", "materias.usuario_id"],
            name="cartoes_materia_id_fkey",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["fonte_id", "materia_id", "usuario_id"],
            ["fontes.id", "fontes.materia_id", "fontes.usuario_id"],
            name="cartoes_fonte_id_fkey",
            ondelete="RESTRICT",
        ),
        CheckConstraint("char_length(frente) BETWEEN 1 AND 4000", name="frente"),
        CheckConstraint("char_length(verso) BETWEEN 1 AND 8000", name="verso"),
        CheckConstraint(
            "explicacao IS NULL OR char_length(explicacao) BETWEEN 1 AND 4000", name="explicacao"
        ),
        CheckConstraint("dificuldade IS NULL OR dificuldade BETWEEN 1 AND 10", name="dificuldade"),
        CheckConstraint(
            "(referencia_titulo IS NULL) = (referencia_nome_arquivo IS NULL) "
            "AND (referencia_titulo IS NULL) = (referencia_enviada_em IS NULL)",
            name="copias_referencia",
        ),
        CheckConstraint(
            "fonte_id IS NULL OR referencia_titulo IS NOT NULL", name="fonte_com_copias"
        ),
        CheckConstraint(
            "referencia_titulo IS NULL OR origem = 'criado'", name="referencia_so_em_criado"
        ),
        CheckConstraint(
            "(entrada_estudo_em IS NOT NULL) = (situacao IN ('ativo', 'suspenso'))",
            name="entrada_estudo",
        ),
        Index("cartoes_devidos", "usuario_id", "situacao", "vencimento"),
        Index("cartoes_novos", "usuario_id", "situacao", "entrada_estudo_em"),
        Index("cartoes_materia", "materia_id", "usuario_id", "criado_em", "id"),
        Index("cartoes_fonte_id_idx", "fonte_id"),
        # Spec 004 (0005).
        CheckConstraint("origem <> 'criado' OR geracao_id IS NULL", name="geracao_so_em_gerado"),
        CheckConstraint(
            "situacao NOT IN ('aguardando_revisao', 'recusado') OR origem = 'gerado_verificado'",
            name="revisao_so_gerado",
        ),
        CheckConstraint("motivo_recusa IS NULL OR situacao = 'recusado'", name="motivo_recusa"),
        CheckConstraint(
            "origem <> 'gerado_verificado' OR explicacao IS NOT NULL", name="explicacao_gerado"
        ),
        Index("cartoes_geracao_id_idx", "geracao_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    public_id: Mapped[UUID] = mapped_column(unique=True, server_default=text("gen_random_uuid()"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    materia_id: Mapped[int] = mapped_column(BigInteger)
    frente: Mapped[str] = mapped_column(Text)
    verso: Mapped[str] = mapped_column(Text)
    explicacao: Mapped[str | None] = mapped_column(Text)
    origem: Mapped[OrigemCartao] = mapped_column(
        Enum(OrigemCartao, name="origem_cartao", values_callable=_valores)
    )
    situacao: Mapped[SituacaoCartao] = mapped_column(
        Enum(SituacaoCartao, name="situacao_cartao", values_callable=_valores)
    )
    entrada_estudo_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Referência do cartão manual a uma fonte (DTEC 035): as cópias sobrevivem à exclusão da
    # fonte, e `fonte_id` vira nulo ("Fonte apagada").
    fonte_id: Mapped[int | None] = mapped_column(BigInteger)
    referencia_titulo: Mapped[str | None] = mapped_column(String(120))
    referencia_nome_arquivo: Mapped[str | None] = mapped_column(String(255))
    referencia_enviada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Estado do FSRS (DTEC 037): gravado na criação e escrito depois só pela revisão (005).
    estado_fsrs: Mapped[EstadoFsrs] = mapped_column(
        Enum(EstadoFsrs, name="estado_fsrs", values_callable=_valores),
        server_default=EstadoFsrs.APRENDIZADO.value,
    )
    passo: Mapped[int | None] = mapped_column(SmallInteger)
    estabilidade: Mapped[float | None] = mapped_column(Double)
    dificuldade: Mapped[float | None] = mapped_column(Double)
    vencimento: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ultima_revisao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Geração de origem (004): nula nos criados e quando a geração some.
    geracao_id: Mapped[int | None] = mapped_column(ForeignKey("geracoes.id", ondelete="SET NULL"))
    motivo_recusa: Mapped[MotivoRecusa | None] = mapped_column(
        Enum(MotivoRecusa, name="motivo_recusa", values_callable=_valores)
    )
