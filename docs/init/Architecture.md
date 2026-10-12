# Architecture

Documento definitivo da stack e das decisões arquiteturais do projeto. Cada camada tem uma única ferramenta definida.

## 1. Visão geral

Aplicação web com backend em Python (FastAPI), frontend em React + TypeScript, banco PostgreSQL único (relacional + vetorial via pgvector) e camada de agentes de IA com RAG. Autenticação e autorização delegadas ao Keycloak. O acesso a LLMs passa por uma camada de abstração (LiteLLM), com provedores gratuitos no início e migração para provedor pago se necessário.

```
┌────────────┐   HTTPS / SSE    ┌──────────────────────┐      ┌────────────────────────┐
│  Frontend  │ ───────────────► │  Backend (FastAPI)   │ ───► │ PostgreSQL + pgvector  │
│ React + TS │ ◄─────────────── │  LangGraph / RAG     │      │ (relacional + vetorial)│
└─────┬──────┘                  └───┬──────────┬───────┘      └────────────────────────┘
      │ OIDC                        │          │
      ▼                             ▼          ▼
┌────────────┐              ┌────────────┐  ┌──────────────────┐
│  Keycloak  │ ◄── JWKS ─── │ Celery     │  │ LiteLLM          │
└────────────┘              │ + Redis    │  │ → Groq / Gemini  │
                            └────────────┘  └──────────────────┘
```

## 2. Backend

| Camada | Ferramenta |
|---|---|
| Linguagem | Python |
| Pacotes e dependências | uv |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x (async) |
| Driver do Postgres | asyncpg |
| Migrações | Alembic (`env.py` assíncrono) |
| Validação | Pydantic |
| Configuração | pydantic-settings |
| Autenticação | Keycloak |
| Validação de JWT | PyJWT (via JWKS) |
| Lint e formatação | Ruff |
| Tipagem estática | mypy |
| Testes | Pytest + pytest-asyncio |
| Testes de API | httpx (`AsyncClient`) |
| Banco nos testes | Testcontainers (Postgres com pgvector) |

### 2.1 Autenticação e autorização

- O frontend autentica no Keycloak via OIDC (Authorization Code + PKCE).
- O FastAPI valida o JWT em toda requisição: assinatura via JWKS, `iss`, `aud` e `exp`.
- As claims (usuário, tenant, roles) são propagadas para a camada de acesso a dados.
- Autorização por roles/escopos no Keycloak. Regras de dados aplicadas no backend e, para multi-tenant, via Row-Level Security no Postgres.

## 3. Banco de dados

**PostgreSQL** como banco único, cobrindo dados relacionais e vetoriais.

- Imagem Docker: `pgvector/pgvector`.
- Extensão **pgvector** com índice **HNSW** (operador `vector_cosine_ops`).
- **pgvector-python** para o tipo `Vector` no SQLAlchemy (`from pgvector.sqlalchemy import Vector`).
- Busca híbrida: pgvector (semântica) + `tsvector` (lexical), com fusão de rankings por RRF.
- A dimensão do embedding fixa o tamanho da coluna `vector(N)`. Definida em **1024** (ver seção 4.3).

### 3.1 Migrações com pgvector

- A extensão é criada na migração: `op.execute("CREATE EXTENSION IF NOT EXISTS vector")`.
- O autogenerate do Alembic não reconhece bem índices HNSW. Declará-los com `postgresql_using="hnsw"`, `postgresql_with` e `postgresql_ops`, e revisar sempre a migração gerada.

## 4. IA e RAG

### 4.1 Orquestração de agentes

- **LangGraph**, com checkpointer em Postgres (`langgraph-checkpoint-postgres`) para estado, persistência de conversas e human-in-the-loop.

### 4.2 Acesso a modelos de linguagem

- **LiteLLM** como camada única de acesso, mantendo o código independente do provedor. A troca de provedor é feita por configuração, sem alterar código.
- **Provedor inicial: Groq** (camada gratuita).
- **Provedor de migração: Gemini**, caso o Groq não comporte a carga.
- Provedores/roteadores gratuitos compatíveis com a API da OpenAI (OpenRouter, 9Router) podem ser plugados no LiteLLM apenas por `base_url` e chave, sem mudança de código. Uso restrito a desenvolvimento e experimentação, não como dependência do ambiente de entrega.
- O nome do modelo e o provedor ficam em variáveis de ambiente (pydantic-settings), nunca fixos no código.

### 4.3 Embeddings

- **Embeddings locais** com `BAAI/bge-m3` (multilíngue, bom desempenho em português), dimensão **1024**, executados nos workers Celery via `sentence-transformers`.
- Motivo: o Groq não oferece embeddings, o modelo local é gratuito e a dimensão do vetor não muda ao migrar o LLM de provedor.

### 4.4 Ingestão de documentos

- Parsing: **Docling**.
- Chunking: `langchain-text-splitters` (`RecursiveCharacterTextSplitter`), com overlap.

### 4.5 Processamento assíncrono

- **Celery + Redis**. Ingestão, chunking e geração de embeddings rodam fora do ciclo da requisição.

### 4.6 Streaming

- Respostas de agentes via **SSE**, com `sse-starlette` no FastAPI.

### 4.7 Autorização no retrieval

- `tenant_id` / `owner_id` / ACL armazenados nos metadados dos chunks.
- Filtro aplicado **no retrieval**, nunca depois da recuperação.
- Row-Level Security do Postgres também na tabela de embeddings.

## 5. Observabilidade e avaliação

| Finalidade | Ferramenta |
|---|---|
| Tracing de LLM e agentes | Langfuse (self-hosted) |
| Tracing e métricas gerais | OpenTelemetry |
| Avaliação de RAG | Ragas (integrado ao Pytest) |
| Validação de saída dos agentes | Pydantic |

- Mitigação de prompt injection obrigatória quando os documentos indexados vierem de terceiros.

## 6. Frontend

| Camada | Ferramenta |
|---|---|
| Linguagem | TypeScript (modo `strict`) |
| Build | Vite |
| Framework | React |
| Estilo | Tailwind CSS |
| Autenticação no cliente | react-oidc-context |
| Streaming de agentes | Vercel AI SDK (`ai`, `@ai-sdk/react`) |

### 6.1 Validação

- **Zod** para schemas e inferência de tipos.
- **React Hook Form** + `@hookform/resolvers` para formulários.

### 6.2 Contrato com o backend

- **openapi-typescript** gera os tipos a partir do OpenAPI exposto pelo FastAPI, mantendo front e back sincronizados.

### 6.3 Testes

| Tipo | Ferramenta |
|---|---|
| Unitários e de componentes | Vitest |
| Testes de componentes por comportamento | React Testing Library + `user-event` + `jest-dom` |
| Mock de API | MSW (Mock Service Worker) |
| End-to-end | Playwright |

- No E2E, o login no Keycloak é automatizado uma única vez e o `storageState` autenticado do Playwright é reaproveitado entre os testes.
- Nos testes unitários, o provedor de autenticação é mockado.

### 6.4 Qualidade estática

- **ESLint** (`typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`).
- **Prettier** + `prettier-plugin-tailwindcss`.

## 7. Privacidade, LGPD e auditoria

- **Trilha de auditoria**: registrar quais chunks e documentos embasaram cada resposta (consulta, chunks recuperados, versão do documento, modelo, usuário, timestamp).
- **Retenção e exclusão**: política de retenção definida e exclusão dos embeddings junto com o documento de origem. Dado pessoal vetorizado continua sendo dado pessoal para fins de LGPD.
- **Minimização e transferência**: avaliar o que é enviado ao provedor de LLM (Groq, Gemini) e documentar base legal e papel do provedor como operador. Camadas gratuitas de provedores costumam permitir uso do conteúdo para melhoria dos modelos, o que deve ser verificado nos termos antes de enviar dados pessoais.
- **Isolamento**: filtros por tenant/owner no retrieval e RLS no banco (seção 4.7).
- **Logs**: não registrar conteúdo sensível de prompts e respostas em logs e traces sem controle de acesso e prazo de retenção.

## 8. Resumo da stack

```
Backend:       Python + uv + FastAPI + SQLAlchemy 2 (async) + asyncpg + Alembic + Pydantic
Banco:         PostgreSQL + pgvector (HNSW, cosine) + pgvector-python
Agentes:       LangGraph (checkpointer Postgres)
LLM:           LiteLLM → Groq (inicial) → Gemini (migração)
Embeddings:    BAAI/bge-m3 local (1024 dim) via sentence-transformers
Ingestão:      Docling + langchain-text-splitters
Filas:         Celery + Redis
Streaming:     SSE (sse-starlette)
Auth:          Keycloak (OIDC, JWT via JWKS com PyJWT)
Observab.:     Langfuse + OpenTelemetry
Avaliação:     Ragas
Qualidade BE:  Ruff + mypy + Pytest + pytest-asyncio + httpx + Testcontainers

Frontend:      TypeScript + React + Vite + Tailwind CSS
Auth cliente:  react-oidc-context
Streaming:     Vercel AI SDK
Validação:     Zod + React Hook Form
Contrato:      openapi-typescript
Testes FE:     Vitest + React Testing Library + MSW
E2E:           Playwright
Qualidade FE:  ESLint + Prettier + prettier-plugin-tailwindcss
```
