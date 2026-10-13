# Retomada da implementação da spec 001 a partir da T027

**Data:** 2026-10-13
**Autor:** pessoa responsável por esta sessão (a confirmar)
**Agente e modelo:** Claude Code / claude-sonnet-5-5
**Etapa SDD:** implementar
**Funcionalidade:** 001-conta-acesso

## Contexto fornecido

Documentos e estado descritos no prompt literal abaixo. Esta sessão rodou num contêiner de nuvem (Linux), e não na máquina Windows descrita no prompt: o clone inicial estava atrás do remoto e foi atualizado por `git pull --ff-only origin develop` (sem commits locais a preservar).

## Prompts

### Prompt 1

```text
Continue a implementação da spec 001 (docs/specs/001-conta-acesso) na branch develop, a partir da T027. A sessão anterior foi pausada com segurança a pedido do usuário.

Leia antes, nesta ordem: .agents/AGENTS.md; docs/skills/contexto-tecnico.md e docs/skills/padroes-implementacao.md; docs/specs/001-conta-acesso/tasks.md, plan.md, data-model.md, research.md (DTEC 019 a 023) e contracts/openapi.yaml; docs/specs/divisao-implementacao-mvp.md (escopo: Onda 0, T001 a T045 da 001, até S1); os registros docs/prompts/2026-10-13-001-conta-acesso-implementacao.md, docs/prompts/2026-10-13-001-conta-acesso-implementacao-2.md e docs/prompts/2026-10-13-001-conta-acesso-implementacao-3.md. Para o frontend, leia também docs/skills/padroes-interface.md e docs/base-specs/design.md (seções 5 a 9.1). Crie um novo registro de prompts para sua sessão (regra 7) com este prompt literal e adicione-o ao índice docs/prompts/README.md.

Estado: T001 a T005 e T009 a T026 estão concluídas e com [x] no tasks.md. T006 a T008 e T027 seguem sem [x] por falta de verificação; T028 a T045 não foram iniciadas. S1 não foi alcançado. Os commits até cdb9e13 (T026) foram publicados na develop. Há commits de documentação posteriores apenas locais: confira git status e git log e preserve-os. O último git pull --rebase origin develop passou; antes do push, 216 testes do backend e 18 do frontend passaram nos contêineres. O backend usa uv, Python 3.13, FastAPI, SQLAlchemy 2 assíncrono, psycopg 3, Alembic e Procrastinate; o frontend usa React, Vite, TanStack Router/Query, TypeScript 5.9, React Aria, MSW e openapi-fetch nas versões fixadas.

Faça, em ordem, T027 (verificar docker compose up -d --build --wait, /health/ready com 200 e o CI remoto na develop), depois US1 e US2 (T028 a T045), com testes antes do código dentro de cada história. A T027 está apenas parcialmente verificada: docker compose up -d --wait passou, com db/api/web saudáveis, migrate exit 0 e worker ativo; a tentativa com --build foi interrompida durante o chown da imagem web. O CI remoto continua desconhecido: uma consulta pelo conector GitHub retornou 404, o que não comprova seu resultado. Não marque T027 ou T007 sem evidência do CI. T006 pode ser marcada após verificação própria do Compose; T008 depende da verificação do pre-commit. Pare na T045 (ponto S1) e avise Arthur Moura para começar a base da 002 somente após verificar S1.

Regras: um commit atômico por tarefa citando o ID (Conventional Commits, descrição em português); [x] no tasks.md só com teste ou demonstração executados (regra 6); nunca na main; nunca reescrever histórico publicado; sem segredos nem dados pessoais reais (contas @exemplo.com); use só a stack aprovada. Preserve o .env local ignorado e não imprima seus valores. Em outro ambiente, copie .env.example para .env e preencha POSTGRES_PASSWORD e SEGREDO_APLICACAO (mínimo 32 bytes). Rode a suíte no contêiner com docker compose up -d --wait db e docker compose run --rm --no-deps api uv run --frozen pytest. Antes de cada push: git pull --rebase origin develop e suíte completa. Não faça push com testes falhando.

Ambiente desta máquina: repositório em F:\Cesmac\Sistemas inteligentes\sistema\plataforma-estudo-gamificada; Git em C:\Program Files\Git\cmd\git.exe; Docker em C:\Program Files\Docker\Docker\resources\bin\docker.exe. Para build ou pull de imagens, acrescente o diretório bin do Docker ao PATH do processo para localizar docker-credential-desktop. Docker Desktop está iniciado. Respeite as autorizações do sandbox.

Atenção especial à segurança: T031, T032, T034 e T035 exigem advisory lock antes da contagem na mesma transação, testes de rajada com fabrica_real em vez de savepoints e teste de tempo da CS-003 estável. T041 deve percorrer as rotas e detectar ausência de casos de isolamento (DTEC 019). Leia os módulos existentes de sessão, CSRF, Argon2 e proteção antes de integrar.

Registre no tasks.md e no novo registro as divergências do plano: T037 terá cobertura incremental do contrato porque algumas rotas só chegam depois de S1; T041 não pode declarar cobertas as rotas de perfil, senha e exclusão previstas para T049/T056. A resposta 413 ainda falta no contrato (pendência T065). O OpenAPI gerado ainda contém só saúde; regenere os tipos após criar as rotas de identidade em T036/T037. A consulta de perfil do frontend usa temporariamente retorno unknown e deve passar ao cliente tipado na T037; o tratamento global de 401 chega na T044. app/nucleo/fila.py mantém MODULOS_TAREFAS vazio até T056. Não reinicie T021 a T026: o ponto de retomada é T027.
```

## Saída aceita

Em andamento. Atualizado ao longo da sessão.

## Alterações humanas

Pendente de revisão.

## Verificação

- O clone da sessão estava em `52e9f17`, atrás de `origin/develop` (`bbb19e2`); `git pull --ff-only origin develop` avançou sem conflito (a árvore estava limpa e `52e9f17` já era ancestral do remoto).
- Contêiner de nuvem Linux sem daemon do Docker ativo: `dockerd` iniciado na sessão. O primeiro pull da imagem do banco falhou com `429 Too Many Requests` do Docker Hub e passou na nova tentativa.
- `.env` criado a partir do `.env.example`, com `POSTGRES_PASSWORD` e `SEGREDO_APLICACAO` aleatórios gerados sem exibição (arquivo ignorado pelo git).

## Pendências

- T027 a T045 (ver tasks.md).
