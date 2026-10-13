"""Versões dos parâmetros FSRS (RF-010, D-001)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Double,
    Enum,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base


class ParametrosFsrs(Base):
    __tablename__ = "parametros_fsrs"
    __table_args__ = (
        UniqueConstraint("usuario_id", "versao"),
        CheckConstraint("versao >= 1", name="versao"),
        CheckConstraint("cardinality(pesos) = 21", name="pesos"),
        CheckConstraint("retencao_desejada BETWEEN 0.70 AND 0.97", name="retencao_desejada"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    versao: Mapped[int] = mapped_column(Integer)
    origem: Mapped[str] = mapped_column(
        Enum("padrao", name="origem_parametros_fsrs"), server_default="padrao"
    )
    pesos: Mapped[list[float]] = mapped_column(ARRAY(Double))
    retencao_desejada: Mapped[Decimal] = mapped_column(Numeric(3, 2), server_default="0.90")
    passos_aprendizado_s: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), server_default=text("'{60,600}'")
    )
    passos_reaprendizado_s: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), server_default=text("'{600}'")
    )
    intervalo_maximo_dias: Mapped[int] = mapped_column(Integer, server_default="36500")
    fuzzing: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    versao_biblioteca: Mapped[str] = mapped_column(String(20))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
