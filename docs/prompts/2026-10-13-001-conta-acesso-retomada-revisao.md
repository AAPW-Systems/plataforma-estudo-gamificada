# Revisão do prompt de retomada da spec 001

**Data:** 2026-10-13
**Autor:**
**Agente e modelo:** Codex / GPT-6
**Etapa SDD:** implementar
**Funcionalidade:** 001-conta-acesso

## Contexto fornecido

O exemplo fornecido pela pessoa é apenas modelo de redação e não deve ser executado. Prompt de retomada vigente em 2026-10-13-001-conta-acesso-retomada-2.md.

## Prompts

### Prompt 1

```text
eu quero que o prompt fique no padrão desse exemplo aqui:

Continue a implementação da spec 001 (docs/specs/001-conta-acesso) na branch `develop`, a partir da T021.

Leia antes, nesta ordem: .agents/AGENTS.md; docs/skills/contexto-tecnico.md e docs/skills/padroes-implementacao.md; docs/specs/001-conta-acesso/tasks.md, plan.md, data-model.md, research.md (DTEC 019 a 023) e contracts/openapi.yaml; docs/specs/divisao-implementacao-mvp.md (escopo: Onda 0, T001 a T045 da 001, até o ponto S1); e o registro docs/prompts/2026-10-13-001-conta-acesso-implementacao.md (andamento, decisões e pendências). Crie um novo registro de prompts para esta sessão (regra 7) com este prompt literal e adicione-o ao índice docs/prompts/README.md.

Estado: T001 a T005 e T009 a T020 estão concluídas e com [x] no tasks.md. T006, T007 e T008 estão sem [x] porque falta verificação (docker compose up completo, CI rodando no remoto, pre-commit). Backend em backend/ (uv, Python 3.13, FastAPI, SQLAlchemy 2 assíncrono, psycopg 3, Alembic, Procrastinate); frontend em frontend/ (React, Vite, TanStack, TypeScript 5.9, ESLint 9). Já existem em backend/src/app/nucleo/: configuracao, dtos, erros, cookies, logs, middlewares, rede, banco, fila, relogio, exclusao, armazenamento/ e seguranca/ (sessoes, csrf, senhas, protecao); app/worker.py; app/modelos.py (registro vazio de modelos); migracoes/ com a 0001_procrastinate; tests/conftest.py e tests/fabricas.py.

Faça, em ordem, T021 (modelos de identidade e revisao/ParametrosFsrs e migração 0002_identidade, com sobe-e-desce testado) e T022 (app/principal.py com criar_aplicacao, ligando os middlewares na ordem correlação → cabeçalhos → limite de corpo → proteção CSRF → erros inesperados, mais saúde e exportar_openapi; acrescentar ao conftest o cliente httpx com base_url https://teste, porque os cookies __Host- são Secure). Em seguida T023 a T027 e a US1 e a US2 (T028 a T045). Pare na T045 (ponto S1 da divisão) e avise para o Arthur Moura começar a 002.

Regras: um commit atômico por tarefa citando o ID (Conventional Commits, descrição em português); testes antes do código dentro de cada história; [x] no tasks.md só com teste executado (regra 6); nunca na main; nunca reescrever histórico publicado; sem segredos nem dados pessoais reais (contas @exemplo.com); use só a stack aprovada. Rode a suíte no contêiner: `cp .env.example .env`, preencha POSTGRES_PASSWORD e SEGREDO_APLICACAO (mín. 32 bytes), `docker compose up -d --wait db` e `docker compose run --rm --no-deps api uv run --frozen pytest`. Antes de cada push: `git pull --rebase` e suíte completa.

Atenção especial (segurança): T031, T032, T034 e T035 (advisory lock antes da contagem na mesma transação; testes de rajada com fabrica_real, não savepoints; teste de tempo da CS-003 estável) e T041 (teste que percorre as rotas, DTEC 019). Registre no tasks.md/registro qualquer divergência do plano.

O registro docs/prompts/2026-10-13-001-conta-acesso-implementacao.md já traz as decisões desta sessão e as pendências (por exemplo, a resposta 413 que o contrato ainda não declara, para a T065).


lembre que isso é apenas o exemplo de como montar e não deve ser executado
```

## Saída aceita

O prompt vigente da T027 foi reescrito no formato direto do exemplo, preservando o estado real da implementação.

## Alterações humanas

Pendente de revisão.

## Verificação

Leitura do prompt revisado, conferência do ponto de retomada T027, referências e git diff --check.

## Pendências

T027 a T045 permanecem pendentes; este pedido não autoriza executá-las.