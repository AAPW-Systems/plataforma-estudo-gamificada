"""Persistência das fontes e dos trechos (spec 002, T008)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base


class Fonte(Base):
    __tablename__ = "fontes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["materia_id", "usuario_id"],
            ["materias.id", "materias.usuario_id"],
            name="fontes_materia_id_fkey",
            ondelete="RESTRICT",
        ),
        CheckConstraint("char_length(titulo) BETWEEN 1 AND 120", name="titulo"),
        CheckConstraint("char_length(nome_arquivo) BETWEEN 1 AND 255", name="nome_arquivo"),
        CheckConstraint(
            "tipo_midia IN ('application/pdf', 'text/plain', 'text/markdown')", name="tipo_midia"
        ),
        CheckConstraint("tamanho_bytes >= 1", name="tamanho_bytes"),
        CheckConstraint("octet_length(hash_sha256) = 32", name="hash_sha256"),
        CheckConstraint("total_paginas IS NULL OR total_paginas >= 1", name="total_paginas"),
        CheckConstraint("total_trechos IS NULL OR total_trechos >= 0", name="total_trechos"),
        CheckConstraint(
            "(estado = 'falhou') = (codigo_falha IS NOT NULL)", name="codigo_falha_coerente"
        ),
        CheckConstraint(
            "(estado = 'concluido') = (total_trechos IS NOT NULL) "
            "AND (estado = 'concluido') = (versao_extracao IS NOT NULL)",
            name="concluido_coerente",
        ),
        Index("fontes_materia_id_usuario_id_idx", "materia_id", "usuario_id"),
        Index("fontes_conteudo_unico_por_materia", "materia_id", "hash_sha256", unique=True),
        Index("fontes_usuario_id_idx", "usuario_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    public_id: Mapped[UUID] = mapped_column(unique=True, server_default=text("gen_random_uuid()"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    materia_id: Mapped[int] = mapped_column(BigInteger)
    titulo: Mapped[str] = mapped_column(String(120))
    nome_arquivo: Mapped[str] = mapped_column(String(255))
    chave_objeto: Mapped[str] = mapped_column(String(512), unique=True)
    tipo_midia: Mapped[str] = mapped_column(String(100))
    tamanho_bytes: Mapped[int] = mapped_column(Integer)
    hash_sha256: Mapped[bytes] = mapped_column(LargeBinary)
    estado: Mapped[str] = mapped_column(
        Enum("pendente", "processando", "concluido", "falhou", name="estado_fonte"),
        server_default="pendente",
    )
    codigo_falha: Mapped[str | None] = mapped_column(
        Enum("falha_tecnica", "sem_texto", "conteudo_invalido", name="codigo_falha_fonte")
    )
    total_paginas: Mapped[int | None] = mapped_column(Integer)
    total_trechos: Mapped[int | None] = mapped_column(Integer)
    versao_extracao: Mapped[str | None] = mapped_column(String(50))
    processada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Trecho(Base):
    __tablename__ = "trechos"
    __table_args__ = (
        UniqueConstraint("fonte_id", "ordem"),
        CheckConstraint("ordem >= 0", name="ordem"),
        CheckConstraint("char_length(texto) >= 1", name="texto"),
        CheckConstraint("pagina IS NULL OR pagina >= 1", name="pagina"),
        CheckConstraint("inicio_caractere >= 0", name="inicio_caractere"),
        CheckConstraint(
            "fim_caractere > inicio_caractere "
            "AND fim_caractere - inicio_caractere = char_length(texto)",
            name="fim_caractere",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    public_id: Mapped[UUID] = mapped_column(unique=True, server_default=text("gen_random_uuid()"))
    fonte_id: Mapped[int] = mapped_column(ForeignKey("fontes.id", ondelete="CASCADE"))
    ordem: Mapped[int] = mapped_column(Integer)
    texto: Mapped[str] = mapped_column(Text)
    pagina: Mapped[int | None] = mapped_column(Integer)
    inicio_caractere: Mapped[int] = mapped_column(Integer)
    fim_caractere: Mapped[int] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
