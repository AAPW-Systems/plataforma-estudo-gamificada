"""Matérias, fontes e trechos (spec 002, T008).

Revision ID: 0003
Revises: 0002
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQL fixo: a migração permanece imutável quando os modelos evoluírem.
    op.execute("""
        CREATE TYPE estado_fonte AS ENUM ('pendente', 'processando', 'concluido', 'falhou');
        CREATE TYPE codigo_falha_fonte AS ENUM ('falha_tecnica', 'sem_texto', 'conteudo_invalido');

        CREATE TABLE materias (
            id bigint GENERATED ALWAYS AS IDENTITY CONSTRAINT materias_pkey PRIMARY KEY,
            public_id uuid NOT NULL DEFAULT gen_random_uuid()
                CONSTRAINT materias_public_id_key UNIQUE,
            usuario_id bigint NOT NULL CONSTRAINT materias_usuario_id_fkey
                REFERENCES usuarios(id),
            nome varchar(60) NOT NULL,
            criado_em timestamptz NOT NULL DEFAULT now(),
            atualizado_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT materias_nome_check CHECK (char_length(nome) BETWEEN 1 AND 60)
        );
        CREATE UNIQUE INDEX materias_nome_unico_por_usuario ON materias (usuario_id, lower(nome));
        CREATE UNIQUE INDEX materias_id_usuario ON materias (id, usuario_id);

        CREATE TABLE fontes (
            id bigint GENERATED ALWAYS AS IDENTITY CONSTRAINT fontes_pkey PRIMARY KEY,
            public_id uuid NOT NULL DEFAULT gen_random_uuid()
                CONSTRAINT fontes_public_id_key UNIQUE,
            usuario_id bigint NOT NULL CONSTRAINT fontes_usuario_id_fkey
                REFERENCES usuarios(id),
            materia_id bigint NOT NULL,
            titulo varchar(120) NOT NULL,
            nome_arquivo varchar(255) NOT NULL,
            chave_objeto varchar(512) NOT NULL CONSTRAINT fontes_chave_objeto_key UNIQUE,
            tipo_midia varchar(100) NOT NULL,
            tamanho_bytes integer NOT NULL,
            hash_sha256 bytea NOT NULL,
            estado estado_fonte NOT NULL DEFAULT 'pendente',
            codigo_falha codigo_falha_fonte,
            total_paginas integer,
            total_trechos integer,
            versao_extracao varchar(50),
            processada_em timestamptz,
            criado_em timestamptz NOT NULL DEFAULT now(),
            atualizado_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT fontes_materia_id_fkey FOREIGN KEY (materia_id, usuario_id)
                REFERENCES materias (id, usuario_id) ON DELETE RESTRICT,
            CONSTRAINT fontes_titulo_check CHECK (char_length(titulo) BETWEEN 1 AND 120),
            CONSTRAINT fontes_nome_arquivo_check
                CHECK (char_length(nome_arquivo) BETWEEN 1 AND 255),
            CONSTRAINT fontes_tipo_midia_check CHECK (
                tipo_midia IN ('application/pdf', 'text/plain', 'text/markdown')
            ),
            CONSTRAINT fontes_tamanho_bytes_check CHECK (tamanho_bytes >= 1),
            CONSTRAINT fontes_hash_sha256_check CHECK (octet_length(hash_sha256) = 32),
            CONSTRAINT fontes_total_paginas_check
                CHECK (total_paginas IS NULL OR total_paginas >= 1),
            CONSTRAINT fontes_total_trechos_check
                CHECK (total_trechos IS NULL OR total_trechos >= 0),
            CONSTRAINT fontes_codigo_falha_coerente_check
                CHECK ((estado = 'falhou') = (codigo_falha IS NOT NULL)),
            CONSTRAINT fontes_concluido_coerente_check
                CHECK ((estado = 'concluido') = (total_trechos IS NOT NULL)
                       AND (estado = 'concluido') = (versao_extracao IS NOT NULL))
        );
        CREATE INDEX fontes_materia_id_usuario_id_idx ON fontes (materia_id, usuario_id);
        CREATE UNIQUE INDEX fontes_conteudo_unico_por_materia ON fontes (materia_id, hash_sha256);
        CREATE INDEX fontes_usuario_id_idx ON fontes (usuario_id);

        CREATE TABLE trechos (
            id bigint GENERATED ALWAYS AS IDENTITY CONSTRAINT trechos_pkey PRIMARY KEY,
            public_id uuid NOT NULL DEFAULT gen_random_uuid()
                CONSTRAINT trechos_public_id_key UNIQUE,
            fonte_id bigint NOT NULL CONSTRAINT trechos_fonte_id_fkey
                REFERENCES fontes(id) ON DELETE CASCADE,
            ordem integer NOT NULL,
            texto text NOT NULL,
            pagina integer,
            inicio_caractere integer NOT NULL,
            fim_caractere integer NOT NULL,
            criado_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT trechos_fonte_id_ordem_key UNIQUE (fonte_id, ordem),
            CONSTRAINT trechos_ordem_check CHECK (ordem >= 0),
            CONSTRAINT trechos_texto_check CHECK (char_length(texto) >= 1),
            CONSTRAINT trechos_pagina_check CHECK (pagina IS NULL OR pagina >= 1),
            CONSTRAINT trechos_inicio_caractere_check CHECK (inicio_caractere >= 0),
            CONSTRAINT trechos_fim_caractere_check CHECK (
                fim_caractere > inicio_caractere
                AND fim_caractere - inicio_caractere = char_length(texto)
            )
        );
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE trechos;
        DROP TABLE fontes;
        DROP TABLE materias;
        DROP TYPE codigo_falha_fonte;
        DROP TYPE estado_fonte;
    """)
