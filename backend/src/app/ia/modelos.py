"""Persistência do domínio `ia` (spec 004, T004): consumo e ciência do aviso (DTEC 039 e 040)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base


class ConsumoIa(Base):
    """Uma linha por chamada ao provedor, com sucesso ou falha, nunca com conteúdo (RQ-003)."""

    __tablename__ = "consumo_ia"
    __table_args__ = (
        CheckConstraint("tokens_entrada IS NULL OR tokens_entrada >= 0", name="tokens_entrada"),
        CheckConstraint("tokens_saida IS NULL OR tokens_saida >= 0", name="tokens_saida"),
        CheckConstraint("latencia_ms >= 0", name="latencia_ms"),
        Index("consumo_ia_usuario_criado_em_idx", "usuario_id", "criado_em"),
        Index("consumo_ia_geracao_id_idx", "geracao_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    # Sem import do domínio `cartoes`: a FK é só pelo nome da tabela.
    geracao_id: Mapped[int | None] = mapped_column(ForeignKey("geracoes.id", ondelete="SET NULL"))
    operacao: Mapped[str] = mapped_column(String(40))
    provedor: Mapped[str] = mapped_column(String(20))
    modelo: Mapped[str] = mapped_column(String(100))
    versao_instrucoes: Mapped[str | None] = mapped_column(String(50))
    tokens_entrada: Mapped[int | None] = mapped_column(Integer)
    tokens_saida: Mapped[int | None] = mapped_column(Integer)
    latencia_ms: Mapped[int] = mapped_column(Integer)
    sucesso: Mapped[bool] = mapped_column(Boolean)
    custo_estimado: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CienciaAvisoIa(Base):
    """Ciência de uma versão do aviso do provedor (DTEC 039); o texto não é guardado."""

    __tablename__ = "ciencias_aviso_ia"

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), primary_key=True)
    versao_aviso: Mapped[str] = mapped_column(String(50), primary_key=True)
    confirmada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
