"""Persistência da identidade (spec 001, T021)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Identity,
    Index,
    LargeBinary,
    SmallInteger,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint("char_length(nome) BETWEEN 1 AND 100", name="nome"),
        CheckConstraint("meta_diaria BETWEEN 1 AND 200", name="meta_diaria"),
        CheckConstraint("tamanho_licao BETWEEN 5 AND 50", name="tamanho_licao"),
        CheckConstraint("limite_novos_dia BETWEEN 0 AND 100", name="limite_novos_dia"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    public_id: Mapped[UUID] = mapped_column(unique=True, server_default=text("gen_random_uuid()"))
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254))
    senha_hash: Mapped[str] = mapped_column(String(255))
    papel: Mapped[str] = mapped_column(
        Enum("estudante", "admin", name="papel_usuario"), server_default="estudante"
    )
    fuso: Mapped[str] = mapped_column(String(64), server_default="America/Sao_Paulo")
    meta_diaria: Mapped[int] = mapped_column(SmallInteger, server_default="20")
    tamanho_licao: Mapped[int] = mapped_column(SmallInteger, server_default="10")
    limite_novos_dia: Mapped[int] = mapped_column(SmallInteger, server_default="20")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


Index("usuarios_email_unico", func.lower(Usuario.email), unique=True)


class Sessao(Base):
    __tablename__ = "sessoes"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ultimo_uso_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revogada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip: Mapped[str | None] = mapped_column(INET)
    agente_usuario: Mapped[str | None] = mapped_column(String(512))


class TentativaAcesso(Base):
    __tablename__ = "tentativas_acesso"
    __table_args__ = (
        Index("tentativas_acesso_chave_conta_criado_em_idx", "chave_conta", "criado_em"),
        Index("tentativas_acesso_ip_tipo_criado_em_idx", "ip", "tipo", "criado_em"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    tipo: Mapped[str] = mapped_column(
        Enum("falha_entrada", "falha_senha_atual", "cadastro", name="tipo_tentativa_acesso")
    )
    chave_conta: Mapped[bytes | None] = mapped_column(LargeBinary)
    ip: Mapped[str] = mapped_column(INET)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
