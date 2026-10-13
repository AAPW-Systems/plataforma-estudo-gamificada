# Continuação da implementação da spec 001 até S1

**Data:** 2026-10-13
**Autor:** pessoa responsável por esta sessão (a confirmar)
**Agente e modelo:** Codex / GPT-6
**Etapa SDD:** implementar
**Funcionalidade:** 001-conta-acesso

## Contexto fornecido

- IDE com `backend/src/app/nucleo/erros.py` ativo; abas `dtos.py`, `cookies.py`, `configuracao.py` e `__init__.py`.
- Documentos indicados no prompt e repositório local na branch `develop`.

## Prompts

### Prompt 1

```text
Continue a implementação da spec 001 (docs/specs/001-conta-acesso) na branch `develop`, a partir da T021.

Leia antes, nesta ordem: .agents/AGENTS.md; docs/skills/contexto-tecnico.md e docs/skills/padroes-implementacao.md; docs/specs/001-conta-acesso/tasks.md, plan.md, data-model.md, research.md (DTEC 019 a 023) e contracts/openapi.yaml; docs/specs/divisao-implementacao-mvp.md (escopo: Onda 0, T001 a T045 da 001, até o ponto S1); e o registro docs/prompts/2026-10-13-001-conta-acesso-implementacao.md (andamento, decisões e pendências). Crie um novo registro de prompts para esta sessão (regra 7) com este prompt literal e adicione-o ao índice docs/prompts/README.md.

Estado: T001 a T005 e T009 a T020 estão concluídas e com [x] no tasks.md. T006, T007 e T008 estão sem [x] porque falta verificação (docker compose up completo, CI rodando no remoto, pre-commit). Backend em backend/ (uv, Python 3.13, FastAPI, SQLAlchemy 2 assíncrono, psycopg 3, Alembic, Procrastinate); frontend em frontend/ (React, Vite, TanStack, TypeScript 5.9, ESLint 9). Já existem em backend/src/app/nucleo/: configuracao, dtos, erros, cookies, logs, middlewares, rede, banco, fila, relogio, exclusao, armazenamento/ e seguranca/ (sessoes, csrf, senhas, protecao); app/worker.py; app/modelos.py (registro vazio de modelos); migracoes/ com a 0001_procrastinate; tests/conftest.py e tests/fabricas.py.

Faça, em ordem, T021 (modelos de identidade e revisao/ParametrosFsrs e migração 0002_identidade, com sobe-e-desce testado) e T022 (app/principal.py com criar_aplicacao, ligando os middlewares na ordem correlação → cabeçalhos → limite de corpo → proteção CSRF → erros inesperados, mais saúde e exportar_openapi; acrescentar ao conftest o cliente httpx com base_url https://teste, porque os cookies __Host- são Secure). Em seguida T023 a T027 e a US1 e a US2 (T028 a T045). Pare na T045 (ponto S1 da divisão) e avise para o Arthur Moura começar a 002.

Regras: um commit atômico por tarefa citando o ID (Conventional Commits, descrição em português); testes antes do código dentro de cada história; [x] no tasks.md só com teste executado (regra 6); nunca na main; nunca reescrever histórico publicado; sem segredos nem dados pessoais reais (contas @exemplo.com); use só a stack aprovada. Rode a suíte no contêiner: `cp .env.example .env`, preencha POSTGRES_PASSWORD e SEGREDO_APLICACAO (mín. 32 bytes), `docker compose up -d --wait db` e `docker compose run --rm --no-deps api uv run --frozen pytest`. Antes de cada push: `git pull --rebase` e suíte completa.

Atenção especial (segurança): T031, T032, T034 e T035 (advisory lock antes da contagem na mesma transação; testes de rajada com fabrica_real, não savepoints; teste de tempo da CS-003 estável) e T041 (teste que percorre as rotas, DTEC 019). Registre no tasks.md/registro qualquer divergência do plano.

O registro docs/prompts/2026-10-13-001-conta-acesso-implementacao.md já traz as decisões desta sessão e as pendências (por exemplo, a resposta 413 que o contrato ainda não declara, para a T065).
```

## Saída aceita

| Artefato | Ação |
|---|---|
| `backend/src/app/identidade/modelos.py`, `backend/src/app/revisao/modelos.py` | Entidades da T021 criadas |
| `backend/src/app/modelos.py` | Registro das entidades |
| `backend/migracoes/versions/0002_identidade.py` | Migração criada, com ID `0002`, seguindo o ID `0001` existente |
| `backend/tests/integration/test_migracoes.py` | 13 casos: sobe/desce, identity, limites, unicidade e equivalência ORM/esquema |
| `docs/specs/001-conta-acesso/tasks.md` | T021 marcada após execução |
| `backend/src/app/principal.py`, `saude/`, `exportar_openapi.py`, `backend/openapi.json` | Aplicação, saúde e exportação do contrato (T022) |
| `backend/tests/conftest.py`, `tests/integration/test_saude.py` | Cliente HTTPS com cookies/CSRF e seis testes da T022 |

## Alterações humanas

Pendente de revisão.

## Verificação

- Branch `develop`, árvore inicialmente limpa.
- Git e Docker instalados fora do PATH; uso dos executáveis pelos caminhos absolutos.
- Docker inicialmente sem daemon; inicialização do Docker Desktop solicitada.
- Docker Desktop iniciado; `.env` local ignorado criado com valores aleatórios, sem exibição; `docker compose up -d --wait db` passou.
- T021: suíte completa no contêiner: **201 passed** (8,07 s); Ruff completo passou.
- T021: mypy passou (47 arquivos).
- T022: teste antes do código falhou pela ausência de `app.principal`; após implementar, suíte completa **207 passed** (8,86 s), mypy passou (54 arquivos), exportação OpenAPI executada.
- T023: detector AST de importações absolutas/relativas e oito casos de violação deliberada; **216 passed** (9,62 s), Ruff e mypy passaram (55 arquivos).
- Primeira execução identificou o vínculo incorreto ao nome do arquivo da revisão anterior; corrigido para o ID real `0001` e repetida a suíte com sucesso.
- A migração cria apenas o valor `padrao` de `origem_parametros_fsrs`; `otimizado` fica fora do MVP conforme o plano. Modelos importam a Base compartilhada e tipos da biblioteca padrão: exceção estrutural necessária à tabela de camadas, sem importar comportamento de domínio.

## Pendências

- Implementar e verificar T021 a T045, respeitando S1.
- T041 menciona rotas implementadas só em T049/T056; registrar a cobertura incremental sem antecipar US3/US4.
- Resposta 413 ausente no contrato: pendência herdada para T065.
