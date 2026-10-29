"""Geração de cartões pela IA e revisão dos gerados (spec 004, T004; data-model.md).

Revision ID: 0005
Revises: 0004
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # O PostgreSQL não usa um valor de enum novo antes do commit da transação que o criou: os
    # valores entram num bloco autocommit, antes dos CHECKs que os citam. `IF NOT EXISTS` porque
    # a descida não os remove (o PostgreSQL não remove valores de enum).
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE situacao_cartao ADD VALUE IF NOT EXISTS 'aguardando_revisao'")
        op.execute("ALTER TYPE situacao_cartao ADD VALUE IF NOT EXISTS 'recusado'")

    # SQL fixo: a migração permanece imutável quando os modelos evoluírem.
    op.execute("""
        CREATE TYPE estado_geracao AS ENUM ('pendente', 'processando', 'concluida', 'falhou');
        CREATE TYPE codigo_falha_geracao AS ENUM (
            'provedor_indisponivel', 'limite_provedor', 'resposta_invalida',
            'orcamento_esgotado', 'fonte_excluida'
        );
        CREATE TYPE motivo_recusa AS ENUM ('incorreto', 'irrelevante', 'repetido', 'mal_escrito');
        CREATE TYPE motivo_descarte AS ENUM (
            'estrutura_invalida', 'sem_evidencia', 'citacao_nao_encontrada',
            'cobertura_insuficiente', 'reprovado_verificador', 'repetido', 'excedente'
        );

        CREATE TABLE geracoes (
            id bigint GENERATED ALWAYS AS IDENTITY CONSTRAINT geracoes_pkey PRIMARY KEY,
            public_id uuid NOT NULL DEFAULT gen_random_uuid()
                CONSTRAINT geracoes_public_id_key UNIQUE,
            usuario_id bigint NOT NULL CONSTRAINT geracoes_usuario_id_fkey
                REFERENCES usuarios(id),
            materia_id bigint NOT NULL,
            fonte_id bigint,
            chave_idempotencia uuid NOT NULL,
            estado estado_geracao NOT NULL DEFAULT 'pendente',
            codigo_falha codigo_falha_geracao,
            provedor varchar(20),
            modelo varchar(100),
            versao_instrucoes varchar(50),
            quantidade_gerada integer NOT NULL DEFAULT 0,
            quantidade_aprovada integer NOT NULL DEFAULT 0,
            pontos_contraditorios integer NOT NULL DEFAULT 0,
            criado_em timestamptz NOT NULL DEFAULT now(),
            iniciada_em timestamptz,
            concluida_em timestamptz,
            CONSTRAINT geracoes_materia_id_fkey FOREIGN KEY (materia_id, usuario_id)
                REFERENCES materias (id, usuario_id) ON DELETE CASCADE,
            -- A geração sobrevive à fonte (consumo e histórico), presa à mesma matéria e dono.
            CONSTRAINT geracoes_fonte_id_fkey FOREIGN KEY (fonte_id, materia_id, usuario_id)
                REFERENCES fontes (id, materia_id, usuario_id) ON DELETE SET NULL (fonte_id),
            CONSTRAINT geracoes_codigo_falha_check
                CHECK ((codigo_falha IS NOT NULL) = (estado = 'falhou')),
            CONSTRAINT geracoes_concluida_em_check
                CHECK ((concluida_em IS NOT NULL) = (estado IN ('concluida', 'falhou'))),
            CONSTRAINT geracoes_quantidade_gerada_check CHECK (quantidade_gerada >= 0),
            CONSTRAINT geracoes_quantidade_aprovada_check CHECK (
                quantidade_aprovada BETWEEN 0 AND 10 AND quantidade_aprovada <= quantidade_gerada
            ),
            CONSTRAINT geracoes_pontos_contraditorios_check CHECK (pontos_contraditorios >= 0)
        );
        CREATE UNIQUE INDEX geracoes_usuario_chave_unica
            ON geracoes (usuario_id, chave_idempotencia);
        CREATE UNIQUE INDEX geracoes_fonte_em_andamento
            ON geracoes (fonte_id) WHERE estado IN ('pendente', 'processando');
        CREATE INDEX geracoes_usuario_criado_em_idx ON geracoes (usuario_id, criado_em);
        CREATE INDEX geracoes_materia_usuario_idx ON geracoes (materia_id, usuario_id);

        CREATE TABLE geracoes_trechos (
            geracao_id bigint NOT NULL CONSTRAINT geracoes_trechos_geracao_id_fkey
                REFERENCES geracoes(id) ON DELETE CASCADE,
            trecho_id bigint NOT NULL CONSTRAINT geracoes_trechos_trecho_id_fkey
                REFERENCES trechos(id) ON DELETE CASCADE,
            CONSTRAINT geracoes_trechos_pkey PRIMARY KEY (geracao_id, trecho_id)
        );
        CREATE INDEX geracoes_trechos_trecho_id_idx ON geracoes_trechos (trecho_id);

        ALTER TABLE cartoes
            ADD COLUMN geracao_id bigint CONSTRAINT cartoes_geracao_id_fkey
                REFERENCES geracoes(id) ON DELETE SET NULL,
            ADD COLUMN motivo_recusa motivo_recusa,
            ADD CONSTRAINT cartoes_geracao_so_em_gerado_check
                CHECK (origem <> 'criado' OR geracao_id IS NULL),
            ADD CONSTRAINT cartoes_revisao_so_gerado_check CHECK (
                situacao NOT IN ('aguardando_revisao', 'recusado')
                OR origem = 'gerado_verificado'
            ),
            ADD CONSTRAINT cartoes_motivo_recusa_check
                CHECK (motivo_recusa IS NULL OR situacao = 'recusado'),
            ADD CONSTRAINT cartoes_explicacao_gerado_check
                CHECK (origem <> 'gerado_verificado' OR explicacao IS NOT NULL);
        CREATE INDEX cartoes_geracao_id_idx ON cartoes (geracao_id);

        CREATE TABLE evidencias_cartoes (
            id bigint GENERATED ALWAYS AS IDENTITY CONSTRAINT evidencias_cartoes_pkey PRIMARY KEY,
            cartao_id bigint NOT NULL CONSTRAINT evidencias_cartoes_cartao_id_fkey
                REFERENCES cartoes(id) ON DELETE CASCADE,
            trecho_id bigint CONSTRAINT evidencias_cartoes_trecho_id_fkey
                REFERENCES trechos(id) ON DELETE SET NULL,
            fonte_titulo varchar(120) NOT NULL,
            fonte_nome_arquivo varchar(255) NOT NULL,
            fonte_enviada_em timestamptz NOT NULL,
            pagina integer,
            citacao_inicio integer NOT NULL,
            citacao_fim integer NOT NULL,
            CONSTRAINT evidencias_cartoes_pagina_check CHECK (pagina IS NULL OR pagina >= 1),
            -- O limite superior (o tamanho do trecho) é conferido na publicação.
            CONSTRAINT evidencias_cartoes_citacao_check
                CHECK (citacao_inicio >= 0 AND citacao_inicio < citacao_fim)
        );
        CREATE UNIQUE INDEX evidencias_cartoes_cartao_trecho_unica
            ON evidencias_cartoes (cartao_id, trecho_id);
        CREATE INDEX evidencias_cartoes_trecho_id_idx ON evidencias_cartoes (trecho_id);

        CREATE TABLE cartoes_descartados (
            id bigint GENERATED ALWAYS AS IDENTITY CONSTRAINT cartoes_descartados_pkey PRIMARY KEY,
            geracao_id bigint NOT NULL CONSTRAINT cartoes_descartados_geracao_id_fkey
                REFERENCES geracoes(id) ON DELETE CASCADE,
            usuario_id bigint NOT NULL CONSTRAINT cartoes_descartados_usuario_id_fkey
                REFERENCES usuarios(id),
            motivo motivo_descarte NOT NULL,
            detalhe varchar(100),
            frente text,
            verso text,
            explicacao text,
            criado_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT cartoes_descartados_frente_check
                CHECK (frente IS NULL OR char_length(frente) <= 4000),
            CONSTRAINT cartoes_descartados_verso_check
                CHECK (verso IS NULL OR char_length(verso) <= 8000),
            CONSTRAINT cartoes_descartados_explicacao_check
                CHECK (explicacao IS NULL OR char_length(explicacao) <= 4000)
        );
        CREATE INDEX cartoes_descartados_geracao_id_idx ON cartoes_descartados (geracao_id);
        CREATE INDEX cartoes_descartados_usuario_id_idx ON cartoes_descartados (usuario_id);

        CREATE TABLE consumo_ia (
            id bigint GENERATED ALWAYS AS IDENTITY CONSTRAINT consumo_ia_pkey PRIMARY KEY,
            usuario_id bigint NOT NULL CONSTRAINT consumo_ia_usuario_id_fkey
                REFERENCES usuarios(id),
            geracao_id bigint CONSTRAINT consumo_ia_geracao_id_fkey
                REFERENCES geracoes(id) ON DELETE SET NULL,
            operacao varchar(40) NOT NULL,
            provedor varchar(20) NOT NULL,
            modelo varchar(100) NOT NULL,
            versao_instrucoes varchar(50),
            tokens_entrada integer,
            tokens_saida integer,
            latencia_ms integer NOT NULL,
            sucesso boolean NOT NULL,
            custo_estimado numeric(12, 6),
            criado_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT consumo_ia_tokens_entrada_check
                CHECK (tokens_entrada IS NULL OR tokens_entrada >= 0),
            CONSTRAINT consumo_ia_tokens_saida_check
                CHECK (tokens_saida IS NULL OR tokens_saida >= 0),
            CONSTRAINT consumo_ia_latencia_ms_check CHECK (latencia_ms >= 0)
        );
        CREATE INDEX consumo_ia_usuario_criado_em_idx ON consumo_ia (usuario_id, criado_em);
        CREATE INDEX consumo_ia_geracao_id_idx ON consumo_ia (geracao_id);

        CREATE TABLE ciencias_aviso_ia (
            usuario_id bigint NOT NULL CONSTRAINT ciencias_aviso_ia_usuario_id_fkey
                REFERENCES usuarios(id),
            versao_aviso varchar(50) NOT NULL,
            confirmada_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ciencias_aviso_ia_pkey PRIMARY KEY (usuario_id, versao_aviso)
        );
    """)


def downgrade() -> None:
    # Descer apagaria a única marca de um cartão ainda não aceito ou já recusado: recusa.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM cartoes WHERE situacao IN ('aguardando_revisao', 'recusado')
            ) THEN
                RAISE EXCEPTION
                    'descida da 0005 recusada: há cartões gerados aguardando revisão ou recusados';
            END IF;
        END
        $$;

        DROP TABLE ciencias_aviso_ia;
        DROP TABLE consumo_ia;
        DROP TABLE cartoes_descartados;
        DROP TABLE evidencias_cartoes;
        DROP INDEX cartoes_geracao_id_idx;
        ALTER TABLE cartoes
            DROP CONSTRAINT cartoes_explicacao_gerado_check,
            DROP CONSTRAINT cartoes_motivo_recusa_check,
            DROP CONSTRAINT cartoes_revisao_so_gerado_check,
            DROP CONSTRAINT cartoes_geracao_so_em_gerado_check,
            DROP COLUMN motivo_recusa,
            DROP COLUMN geracao_id;
        DROP TABLE geracoes_trechos;
        DROP TABLE geracoes;
        DROP TYPE motivo_descarte;
        DROP TYPE motivo_recusa;
        DROP TYPE codigo_falha_geracao;
        DROP TYPE estado_geracao;
    """)
