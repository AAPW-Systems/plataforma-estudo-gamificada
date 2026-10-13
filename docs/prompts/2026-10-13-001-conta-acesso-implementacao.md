# Implementação da spec 001 e estrutura base do repositório

**Data:** 2026-10-13
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** implementar
**Funcionalidade:** 001-conta-acesso

## Contexto fornecido

- `.agents/AGENTS.md`, `docs/skills/contexto-tecnico.md`, `docs/skills/padroes-implementacao.md`
- `docs/specs/001-conta-acesso/` (spec, plano, pesquisa, modelo de dados, contrato, quickstart, tarefas e rastreabilidade)

## Prompts

### Prompt 1

```text
nessa sessão iremos iniciar o setup do desenvolvimento do projeto: criar as pastas de backend, frontend, o docker compose, o exemplo da .env, seguido pela implementação da  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\docs\\specs\\001-conta-acesso"
```

### Resposta a esclarecimento 1

```text
[agente: a decisão de 13/10/2026 impede código antes de documentar todo o MVP (falta o plano da 007); rever a decisão? O Docker Desktop não está ativo] -> vou rodar a spec 007 em paralelo, inicie a implementação conforme solicitado, o docker já está ativo
```

### Prompt 2

```text
siga, resolvido
```

### Prompt 3

```text
quando for seguro parar, pare, terei que usar um modelo menor
```

## Saída aceita

Sessão interrompida a pedido, depois da T019 (Fase 1 completa e parte da Fase 2).

| Artefato | Ação |
|---|---|
| `.editorconfig`, `.gitattributes`, `.gitignore` | criados / alterado (T001) |
| `backend/pyproject.toml`, `backend/uv.lock`, `backend/.python-version` | criados (T002) |
| `frontend/` (package.json, lock, tsconfig, ESLint, Prettier, Vite, Vitest, index.html, `src/main.tsx`, `src/rotas/`, `routeTree.gen.ts`) | criados (T003) |
| `backend/Dockerfile`, `backend/.dockerignore` | criados (T004) |
| `frontend/Dockerfile`, `frontend/Caddyfile`, `frontend/.dockerignore` | criados (T005) |
| `compose.yaml`, `.env.example` | criados (T006); banco sem porta publicada no host |
| `.github/workflows/ci.yml` | criado (T007) |
| `.pre-commit-config.yaml` | criado (T008) |
| `backend/src/app/nucleo/` (`configuracao`, `dtos`, `erros`, `cookies`, `logs`, `middlewares`, `rede`, `banco`, `fila`, `relogio`, `exclusao`, `armazenamento/`), `backend/src/app/worker.py`, `backend/src/app/modelos.py` | criados (T009 a T014, T016, T018, T019) |
| `backend/alembic.ini`, `backend/migracoes/` (env, `0001_procrastinate`, SQL fixado do Procrastinate 3.10.0) | criados (T015) |
| `backend/tests/` (`conftest.py`, `fabricas.py`, unitários do núcleo, integração da fila e do armazenamento) | criados (T009 a T012, T016 a T019) |
| `docs/specs/001-conta-acesso/tasks.md` | alterado: T001 a T005 e T009 a T019 marcadas |
| `.agents/AGENTS.md`, `docs/skills/contexto-tecnico.md` | alterados: decisão de 13/10 revista |

## Alterações humanas

Pendente de revisão.

## Verificação

- `uv sync --locked` em Python 3.13 (T002); `npm ci && npm run build`, `typecheck`, `lint` e `format:check` (T003).
- Imagens `dev` da API e `dev`/`prod` do frontend construídas; a `prod` do frontend respondeu `200` na raiz e numa rota do SPA (T004 e T005). A imagem `prod` da API ainda não foi construída.
- `docker compose config` válido (T006). `alembic upgrade head`, `downgrade base` e `upgrade head` no contêiner, com contagem de funções, tipos e tabelas do Procrastinate (18, 7, 4 → 0, 0, 0 → 18, 7, 4) (T015).
- Suíte do backend no contêiner (`docker compose run --rm --no-deps api uv run --frozen pytest`): 85 testes passando antes da T018; depois, 38 do contrato de armazenamento e 4 do registro de exclusão passando. Ruff (lint e formato) e `mypy --strict` limpos.
- **Não verificado:** T007 (a integração contínua nunca rodou: nada foi enviado ao remoto), T008 (pre-commit não instalado) e T006 com `docker compose up` completo (depende da T022 e da T027). Essas três seguem sem checkbox.

### Decisões de implementação desta sessão

- TypeScript 5.9 (não 7): `openapi-typescript` 7.13 e `typescript-eslint` 8 ainda não aceitam versões novas como peer. ESLint 9 pelo mesmo motivo (`eslint-plugin-jsx-a11y`).
- PostgreSQL 17 (`pgvector/pgvector:pg17-trixie`), conforme o `research.md`; Caddy 2.11 na imagem `prod` do frontend (arquitetura, seção 5.2). Todas as imagens base fixadas por digest.
- Uvicorn com `--no-proxy-headers`: o `X-Forwarded-For` só é resolvido por `nucleo/rede.py` (DTEC 020); o proxy do Vite tem IP fixo `172.28.0.10` na rede do Compose.
- Corpo acima de 64 KiB responde `413` com o código existente `requisicao_malformada`; corpo ausente ou que não é objeto JSON responde `400`.
- `Cache-Control: no-store` em toda a `/api/`, não só em `/auth` e `/perfil` (superconjunto do plano, alinhado ao `contexto-tecnico.md`).
- Esquema do Procrastinate copiado para `migracoes/sql/` (imutável), em vez de lido do pacote.

## Pendências

- **Próxima tarefa: T020** (sessão, CSRF e Argon2 em `app/nucleo/seguranca/`), seguida de T021 (modelos e migração `0002`), T022 (`principal.py`, saúde e exportação do OpenAPI; acrescentar aí o cliente HTTP do `conftest`), T023 a T027 e a US1 e a US2 (até a T045, ponto S1 da divisão).
- O cliente `httpx` do `conftest` (parte da T016) depende de `criar_aplicacao` (T022): usar `base_url="https://teste"`, porque os cookies `__Host-` são `Secure`.
- `nucleo/fila.py` tem `MODULOS_TAREFAS` vazio; a T056 acrescenta `app.identidade.tarefas`.
- Contrato: o `contracts/openapi.yaml` da 001 não declara a resposta `413` das rotas com corpo; registrar na fase final (T065) ou numa emenda.
- Nenhum push feito. Antes do push: `git pull --rebase` (protocolo da divisão da implementação) e suíte completa.
