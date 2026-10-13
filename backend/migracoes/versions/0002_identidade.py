"""Identidade e versões dos parâmetros FSRS (T021).

Revision ID: 0002
Revises: 0001
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQL fixo: a migração permanece imutável quando os modelos evoluírem.
    op.execute("""
        CREATE TYPE papel_usuario AS ENUM ('estudante', 'admin');
        CREATE TYPE tipo_tentativa_acesso AS ENUM
            ('falha_entrada', 'falha_senha_atual', 'cadastro');
        CREATE TYPE origem_parametros_fsrs AS ENUM ('padrao');
        CREATE TABLE usuarios (
            id bigint GENERATED ALWAYS AS IDENTITY CONSTRAINT usuarios_pkey PRIMARY KEY,
            public_id uuid NOT NULL DEFAULT gen_random_uuid()
                CONSTRAINT usuarios_public_id_key UNIQUE,
            nome varchar(100) NOT NULL,
            email varchar(254) NOT NULL,
            senha_hash varchar(255) NOT NULL,
            papel papel_usuario NOT NULL DEFAULT 'estudante',
            fuso varchar(64) NOT NULL DEFAULT 'America/Sao_Paulo',
            meta_diaria smallint NOT NULL DEFAULT 20,
            tamanho_licao smallint NOT NULL DEFAULT 10,
            limite_novos_dia smallint NOT NULL DEFAULT 20,
            criado_em timestamptz NOT NULL DEFAULT now(),
            atualizado_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT usuarios_nome_check CHECK (char_length(nome) BETWEEN 1 AND 100),
            CONSTRAINT usuarios_meta_diaria_check CHECK (meta_diaria BETWEEN 1 AND 200),
            CONSTRAINT usuarios_tamanho_licao_check CHECK (tamanho_licao BETWEEN 5 AND 50),
            CONSTRAINT usuarios_limite_novos_dia_check CHECK (limite_novos_dia BETWEEN 0 AND 100)
        );
        CREATE UNIQUE INDEX usuarios_email_unico ON usuarios (lower(email));
        CREATE TABLE sessoes (
            id bigint GENERATED ALWAYS AS IDENTITY CONSTRAINT sessoes_pkey PRIMARY KEY,
            usuario_id bigint NOT NULL CONSTRAINT sessoes_usuario_id_fkey
                REFERENCES usuarios(id) ON DELETE CASCADE,
            token_hash bytea NOT NULL CONSTRAINT sessoes_token_hash_key UNIQUE,
            criada_em timestamptz NOT NULL DEFAULT now(),
            ultimo_uso_em timestamptz NOT NULL DEFAULT now(),
            expira_em timestamptz NOT NULL,
            revogada_em timestamptz,
            ip inet,
            agente_usuario varchar(512)
        );
        CREATE INDEX sessoes_usuario_id_idx ON sessoes(usuario_id);
        CREATE TABLE tentativas_acesso (
            id bigint GENERATED ALWAYS AS IDENTITY CONSTRAINT tentativas_acesso_pkey PRIMARY KEY,
            tipo tipo_tentativa_acesso NOT NULL,
            chave_conta bytea,
            ip inet NOT NULL,
            criado_em timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX tentativas_acesso_chave_conta_criado_em_idx
            ON tentativas_acesso(chave_conta, criado_em);
        CREATE INDEX tentativas_acesso_ip_tipo_criado_em_idx
            ON tentativas_acesso(ip, tipo, criado_em);
        CREATE TABLE parametros_fsrs (
            id bigint GENERATED ALWAYS AS IDENTITY CONSTRAINT parametros_fsrs_pkey PRIMARY KEY,
            usuario_id bigint NOT NULL CONSTRAINT parametros_fsrs_usuario_id_fkey
                REFERENCES usuarios(id),
            versao integer NOT NULL,
            origem origem_parametros_fsrs NOT NULL DEFAULT 'padrao',
            pesos double precision[] NOT NULL,
            retencao_desejada numeric(3,2) NOT NULL DEFAULT 0.90,
            passos_aprendizado_s integer[] NOT NULL DEFAULT '{60,600}',
            passos_reaprendizado_s integer[] NOT NULL DEFAULT '{600}',
            intervalo_maximo_dias integer NOT NULL DEFAULT 36500,
            fuzzing boolean NOT NULL DEFAULT true,
            versao_biblioteca varchar(20) NOT NULL,
            criado_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT parametros_fsrs_usuario_id_versao_key UNIQUE (usuario_id, versao),
            CONSTRAINT parametros_fsrs_versao_check CHECK (versao >= 1),
            CONSTRAINT parametros_fsrs_pesos_check CHECK (cardinality(pesos) = 21),
            CONSTRAINT parametros_fsrs_retencao_desejada_check
                CHECK (retencao_desejada BETWEEN 0.70 AND 0.97)
        );
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE parametros_fsrs;
        DROP TABLE tentativas_acesso;
        DROP TABLE sessoes;
        DROP TABLE usuarios;
        DROP TYPE origem_parametros_fsrs;
        DROP TYPE tipo_tentativa_acesso;
        DROP TYPE papel_usuario;
    """)
