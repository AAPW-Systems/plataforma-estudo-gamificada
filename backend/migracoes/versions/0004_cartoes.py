"""Cartões criados pelo estudante (spec 003, T003).

Revision ID: 0004
Revises: 0003
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQL fixo: a migração permanece imutável quando os modelos evoluírem. A 004 acrescenta
    # `aguardando_revisao` e `recusado` a `situacao_cartao`, e as colunas `geracao_id` (004),
    # `dominado_em` (005) e `chave_imagem` (011) chegam em migrações próprias.
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS unaccent;

        CREATE TYPE origem_cartao AS ENUM ('gerado_verificado', 'editado', 'criado');
        CREATE TYPE situacao_cartao AS ENUM ('ativo', 'suspenso');
        CREATE TYPE estado_fsrs AS ENUM ('aprendizado', 'revisao', 'reaprendizado');

        CREATE UNIQUE INDEX fontes_id_materia_usuario ON fontes (id, materia_id, usuario_id);

        CREATE TABLE cartoes (
            id bigint GENERATED ALWAYS AS IDENTITY CONSTRAINT cartoes_pkey PRIMARY KEY,
            public_id uuid NOT NULL DEFAULT gen_random_uuid()
                CONSTRAINT cartoes_public_id_key UNIQUE,
            usuario_id bigint NOT NULL CONSTRAINT cartoes_usuario_id_fkey
                REFERENCES usuarios(id),
            materia_id bigint NOT NULL,
            frente text NOT NULL,
            verso text NOT NULL,
            explicacao text,
            origem origem_cartao NOT NULL,
            situacao situacao_cartao NOT NULL,
            entrada_estudo_em timestamptz,
            fonte_id bigint,
            referencia_titulo varchar(120),
            referencia_nome_arquivo varchar(255),
            referencia_enviada_em timestamptz,
            estado_fsrs estado_fsrs NOT NULL DEFAULT 'aprendizado',
            passo smallint,
            estabilidade double precision,
            dificuldade double precision,
            vencimento timestamptz NOT NULL DEFAULT now(),
            ultima_revisao timestamptz,
            criado_em timestamptz NOT NULL DEFAULT now(),
            atualizado_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT cartoes_materia_id_fkey FOREIGN KEY (materia_id, usuario_id)
                REFERENCES materias (id, usuario_id) ON DELETE RESTRICT,
            CONSTRAINT cartoes_fonte_id_fkey FOREIGN KEY (fonte_id, materia_id, usuario_id)
                REFERENCES fontes (id, materia_id, usuario_id) ON DELETE RESTRICT,
            CONSTRAINT cartoes_frente_check CHECK (char_length(frente) BETWEEN 1 AND 4000),
            CONSTRAINT cartoes_verso_check CHECK (char_length(verso) BETWEEN 1 AND 8000),
            CONSTRAINT cartoes_explicacao_check
                CHECK (explicacao IS NULL OR char_length(explicacao) BETWEEN 1 AND 4000),
            CONSTRAINT cartoes_dificuldade_check
                CHECK (dificuldade IS NULL OR dificuldade BETWEEN 1 AND 10),
            CONSTRAINT cartoes_copias_referencia_check CHECK (
                (referencia_titulo IS NULL) = (referencia_nome_arquivo IS NULL)
                AND (referencia_titulo IS NULL) = (referencia_enviada_em IS NULL)
            ),
            CONSTRAINT cartoes_fonte_com_copias_check
                CHECK (fonte_id IS NULL OR referencia_titulo IS NOT NULL),
            CONSTRAINT cartoes_referencia_so_em_criado_check
                CHECK (referencia_titulo IS NULL OR origem = 'criado'),
            CONSTRAINT cartoes_entrada_estudo_check CHECK (
                (entrada_estudo_em IS NOT NULL) = (situacao IN ('ativo', 'suspenso'))
            )
        );
        CREATE INDEX cartoes_devidos ON cartoes (usuario_id, situacao, vencimento);
        CREATE INDEX cartoes_novos ON cartoes (usuario_id, situacao, entrada_estudo_em);
        CREATE INDEX cartoes_materia ON cartoes (materia_id, usuario_id, criado_em, id);
        CREATE INDEX cartoes_fonte_id_idx ON cartoes (fonte_id);
    """)


def downgrade() -> None:
    # A extensão fica: outras partes do banco podem usá-la.
    op.execute("""
        DROP TABLE cartoes;
        DROP INDEX fontes_id_materia_usuario;
        DROP TYPE estado_fsrs;
        DROP TYPE situacao_cartao;
        DROP TYPE origem_cartao;
    """)
