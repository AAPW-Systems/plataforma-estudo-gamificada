"""Persistência da geração (spec 004, T004; data-model.md, migração `0005`)."""

from datetime import datetime
from enum import StrEnum
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
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base


class EstadoGeracao(StrEnum):
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    CONCLUIDA = "concluida"
    FALHOU = "falhou"


class CodigoFalhaGeracao(StrEnum):
    """Motivo técnico da falha (DTEC 043); a mensagem vem do catálogo da aplicação."""

    PROVEDOR_INDISPONIVEL = "provedor_indisponivel"
    LIMITE_PROVEDOR = "limite_provedor"
    RESPOSTA_INVALIDA = "resposta_invalida"
    ORCAMENTO_ESGOTADO = "orcamento_esgotado"
    FONTE_EXCLUIDA = "fonte_excluida"


class MotivoDescarte(StrEnum):
    """Portão que reprovou a saída do modelo (DTEC 042), na ordem em que são aplicados."""

    ESTRUTURA_INVALIDA = "estrutura_invalida"
    SEM_EVIDENCIA = "sem_evidencia"
    CITACAO_NAO_ENCONTRADA = "citacao_nao_encontrada"
    COBERTURA_INSUFICIENTE = "cobertura_insuficiente"
    REPROVADO_VERIFICADOR = "reprovado_verificador"
    REPETIDO = "repetido"
    EXCEDENTE = "excedente"


def _valores(enumeracao: type[StrEnum]) -> list[str]:
    return [membro.value for membro in enumeracao]


class Geracao(Base):
    __tablename__ = "geracoes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["materia_id", "usuario_id"],
            ["materias.id", "materias.usuario_id"],
            name="geracoes_materia_id_fkey",
            ondelete="CASCADE",
        ),
        # A geração sobrevive à fonte, presa à mesma matéria e dono (DTEC 046).
        ForeignKeyConstraint(
            ["fonte_id", "materia_id", "usuario_id"],
            ["fontes.id", "fontes.materia_id", "fontes.usuario_id"],
            name="geracoes_fonte_id_fkey",
            ondelete="SET NULL (fonte_id)",
        ),
        CheckConstraint("(codigo_falha IS NOT NULL) = (estado = 'falhou')", name="codigo_falha"),
        CheckConstraint(
            "(concluida_em IS NOT NULL) = (estado IN ('concluida', 'falhou'))",
            name="concluida_em",
        ),
        CheckConstraint("quantidade_gerada >= 0", name="quantidade_gerada"),
        CheckConstraint(
            "quantidade_aprovada BETWEEN 0 AND 10 AND quantidade_aprovada <= quantidade_gerada",
            name="quantidade_aprovada",
        ),
        CheckConstraint("pontos_contraditorios >= 0", name="pontos_contraditorios"),
        Index("geracoes_usuario_chave_unica", "usuario_id", "chave_idempotencia", unique=True),
        Index(
            "geracoes_fonte_em_andamento",
            "fonte_id",
            unique=True,
            postgresql_where=text("estado IN ('pendente', 'processando')"),
        ),
        Index("geracoes_usuario_criado_em_idx", "usuario_id", "criado_em"),
        Index("geracoes_materia_usuario_idx", "materia_id", "usuario_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    public_id: Mapped[UUID] = mapped_column(unique=True, server_default=text("gen_random_uuid()"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    materia_id: Mapped[int] = mapped_column(BigInteger)
    fonte_id: Mapped[int | None] = mapped_column(BigInteger)
    chave_idempotencia: Mapped[UUID]
    estado: Mapped[EstadoGeracao] = mapped_column(
        Enum(EstadoGeracao, name="estado_geracao", values_callable=_valores),
        server_default=EstadoGeracao.PENDENTE.value,
    )
    codigo_falha: Mapped[CodigoFalhaGeracao | None] = mapped_column(
        Enum(CodigoFalhaGeracao, name="codigo_falha_geracao", values_callable=_valores)
    )
    # Rastreabilidade (RF-017, RQ-006): gravados ao iniciar.
    provedor: Mapped[str | None] = mapped_column(String(20))
    modelo: Mapped[str | None] = mapped_column(String(100))
    versao_instrucoes: Mapped[str | None] = mapped_column(String(50))
    quantidade_gerada: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    quantidade_aprovada: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    pontos_contraditorios: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    iniciada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    concluida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GeracaoTrecho(Base):
    """Trecho enviado ao modelo (RF-017); coberto quando a geração está `concluida` (DTEC 041)."""

    __tablename__ = "geracoes_trechos"
    __table_args__ = (Index("geracoes_trechos_trecho_id_idx", "trecho_id"),)

    geracao_id: Mapped[int] = mapped_column(
        ForeignKey("geracoes.id", ondelete="CASCADE"), primary_key=True
    )
    trecho_id: Mapped[int] = mapped_column(
        ForeignKey("trechos.id", ondelete="CASCADE"), primary_key=True
    )


class Evidencia(Base):
    """Trecho que sustenta o cartão gerado, com a descrição da origem copiada (RN-05)."""

    __tablename__ = "evidencias_cartoes"
    __table_args__ = (
        CheckConstraint("pagina IS NULL OR pagina >= 1", name="pagina"),
        CheckConstraint("citacao_inicio >= 0 AND citacao_inicio < citacao_fim", name="citacao"),
        Index("evidencias_cartoes_cartao_trecho_unica", "cartao_id", "trecho_id", unique=True),
        Index("evidencias_cartoes_trecho_id_idx", "trecho_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    cartao_id: Mapped[int] = mapped_column(ForeignKey("cartoes.id", ondelete="CASCADE"))
    trecho_id: Mapped[int | None] = mapped_column(ForeignKey("trechos.id", ondelete="SET NULL"))
    fonte_titulo: Mapped[str] = mapped_column(String(120))
    fonte_nome_arquivo: Mapped[str] = mapped_column(String(255))
    fonte_enviada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    pagina: Mapped[int | None] = mapped_column(Integer)
    # Posição da citação no texto do trecho, em code points, só para o destaque (sem copiar).
    citacao_inicio: Mapped[int] = mapped_column(Integer)
    citacao_fim: Mapped[int] = mapped_column(Integer)


class CartaoDescartado(Base):
    """Saída do modelo reprovada, só para análise (RF-007, DTEC 046); nunca sai por rota."""

    __tablename__ = "cartoes_descartados"
    __table_args__ = (
        CheckConstraint("frente IS NULL OR char_length(frente) <= 4000", name="frente"),
        CheckConstraint("verso IS NULL OR char_length(verso) <= 8000", name="verso"),
        CheckConstraint("explicacao IS NULL OR char_length(explicacao) <= 4000", name="explicacao"),
        Index("cartoes_descartados_geracao_id_idx", "geracao_id"),
        Index("cartoes_descartados_usuario_id_idx", "usuario_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    geracao_id: Mapped[int] = mapped_column(ForeignKey("geracoes.id", ondelete="CASCADE"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    motivo: Mapped[MotivoDescarte] = mapped_column(
        Enum(MotivoDescarte, name="motivo_descarte", values_callable=_valores)
    )
    detalhe: Mapped[str | None] = mapped_column(String(100))
    frente: Mapped[str | None] = mapped_column(Text)
    verso: Mapped[str | None] = mapped_column(Text)
    explicacao: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
