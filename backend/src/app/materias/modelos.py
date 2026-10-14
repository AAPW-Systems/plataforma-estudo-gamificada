"""Persistência das matérias (spec 002, T008)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base


class Materia(Base):
    __tablename__ = "materias"
    __table_args__ = (CheckConstraint("char_length(nome) BETWEEN 1 AND 60", name="nome"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    public_id: Mapped[UUID] = mapped_column(unique=True, server_default=text("gen_random_uuid()"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    nome: Mapped[str] = mapped_column(String(60))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# O nome é único por estudante sem diferenciar maiúsculas e minúsculas (RF-001); o par
# (id, usuario_id) é o alvo da FK composta que garante o mesmo dono nas fontes (RN-01).
Index("materias_nome_unico_por_usuario", Materia.usuario_id, func.lower(Materia.nome), unique=True)
Index("materias_id_usuario", Materia.id, Materia.usuario_id, unique=True)
