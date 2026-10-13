# Plano da spec 001-conta-acesso e estrutura base do repositório

**Data:** 2026-10-12
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** planejar
**Funcionalidade:** 001-conta-acesso

## Contexto fornecido

- `docs/skills/fluxo-sdd.md`, `docs/skills/padroes-implementacao.md`, `docs/skills/registrar-prompt.md`
- `docs/specs/001-conta-acesso/spec.md` (aprovada em 12/10/2026)
- `docs/arquitetura/README.md`, `docs/research.md` (DTEC 001 a 014), `docs/arquitetura/esquema-inicial.dbml`
- `docs/constitution.md`, `docs/base-specs/plan.md`
- Modelos de `docs/sdd_guidelines/modelos/` e o exemplo `docs/sdd_guidelines/exemplos/001-consulta-prazos/`
- Documentação do Procrastinate (conectores e conexão externa), consultada em 12/10/2026

## Prompts

### Prompt 1

```text
Vamos para a etapa 5 (planejar) da spec 001-conta-acesso, aprovada em 12/10/2026.
Siga docs/skills/fluxo-sdd.md e as guidelines: produza plan.md, research.md (só dúvidas
técnicas novas), data-model.md, contracts/openapi.yaml e quickstart.md, usando a stack
aprovada (docs/arquitetura/README.md e DTEC do docs/research.md) e o esquema inicial
(docs/arquitetura/esquema-inicial.dbml). Backend e frontend são projetos separados em
backend/ e frontend/. Este primeiro plano também define a estrutura base do repositório
(pastas, compose.yaml, Dockerfiles, ferramentas de qualidade), que as specs 002 a 007
vão reaproveitar. Alinhe comigo em rodadas as decisões técnicas que não estiverem nas DTEC.
O MVP tem apresentação prevista para 15/10/2026.
```

### Resposta a esclarecimento 1

```text
Rodada 1 do agente: Q1 driver do Postgres (psycopg 3 único, recomendado, porque o
Procrastinate não tem conector asyncpg); Q2 isolamento (filtro no repositório + teste que
percorre as rotas; RLS na referência); Q3 tentativas em tabela no Postgres; Q4 exclusão da
conta em transação + tarefa que apaga o prefixo usuarios/{public_id}/; Q5 TanStack Router +
TanStack Query + openapi-fetch; Q6 React Aria Components; Q7 Python 3.14, Node 24 LTS, pnpm;
Q8 GitHub Actions + pre-commit; Q9 lista SecLists 100k + lista curta pt-BR; e a lista de
decisões tomadas sem perguntar (prefixo /api/v1, camelCase, rotas, CSRF assinado, Argon2,
sessão, structlog, savepoints, Docker multi-stage, limites do OpenAPI, nome com 100 caracteres).

-> "Q7 - Python 3.14 + uv, node LTS, npm (particulamente prefiro o bun, mas como o trabalho é
em equipe é melhor manter o npm), as demais, pode seguir sua recomendação

sobre parte da arquitetura do backend, adicione para usar DTO, mapper, repository, além dos
controles de exceção"
```

### Resposta a esclarecimento 2

```text
Consolidado do agente (Q1 a Q9 com onde cada decisão é registrada; camadas do backend por
domínio: rotas, dtos, mapeadores, servicos, dominio, repositorios, modelos, excecoes;
hierarquia ErroAplicacao com handlers centrais; núcleo compartilhado). Confirma?
-> "ok"
```

### Prompt 2

```text
aprovo, faça os commits separados e siga
```

### Prompt 3 (13/10/2026)

```text
volte pro python 3.13, fora isso, aprovado. Não vamos implementar código agora, vamos logo gerar toda a documentação necessária de todas as specs do mvp, conforme as guidelines. se já tiver implementado tudo da spec001, gere um prompt para gerar a 002 em nova sessão
```

## Saída aceita

| Artefato | Ação |
|---|---|
| `docs/specs/001-conta-acesso/plan.md` | criado (inclui a estrutura base do repositório) |
| `docs/specs/001-conta-acesso/research.md` | criado (DTEC 019 a 023) |
| `docs/specs/001-conta-acesso/data-model.md` | criado |
| `docs/specs/001-conta-acesso/contracts/openapi.yaml` | criado |
| `docs/specs/001-conta-acesso/quickstart.md` | criado |
| `docs/specs/001-conta-acesso/README.md` | alterado (status "Planejando", ordem de leitura, histórico) |
| `docs/research.md` | alterado (emenda da DTEC 002: psycopg 3; DTEC 015 a 018; índice) |
| `docs/arquitetura/README.md` | alterado (stack, camadas, chaves por usuário, tentativas) |
| `docs/arquitetura/esquema-inicial.dbml` | alterado (tabela `tentativas_acesso`, enum `tipo_tentativa_acesso`, `nome` com 100 caracteres) |
| `docs/arquitetura/referencia-pos-academica.md` | alterado (psycopg 3) |
| `docs/skills/padroes-implementacao.md` | alterado (camadas DTO, mapeador, repositório; hierarquia de exceções; camelCase) |
| `docs/produto/pendencias.md` | alterado (QA-30: integração contínua proposta na DTEC 017) |
| `docs/specs/README.md` | alterado (001 em "Planejando") |
| `.agents/AGENTS.md` | alterado ("Estado atual") |
| `docs/prompts/README.md` | alterado (índice) |
| `docs/prompts/2026-10-12-001-conta-acesso-plano.md` | criado (este registro) |
| `docs/specs/001-conta-acesso/plan.md`, `research.md`, `README.md`, `docs/research.md`, `docs/produto/pendencias.md`, `docs/specs/README.md`, `.agents/AGENTS.md` | alterados depois do prompt 2 (registro da aprovação do plano) |
| `docs/specs/001-conta-acesso/tasks.md` | criado (etapa 6, T001 a T065) |
| `docs/specs/001-conta-acesso/traceability.md` | criado (etapa 7, com análise de consistência) |
| `docs/specs/001-conta-acesso/plan.md`, `tasks.md`, `traceability.md`, `quickstart.md`, `README.md`, `docs/specs/README.md`, `.agents/AGENTS.md` | alterados depois do prompt 3 (Python 3.13; aprovação das tarefas; implementação adiada) |

## Alterações humanas

- Plano aprovado por Artur Lins em 12/10/2026 sem alterações (prompt 2), com a emenda da DTEC 002 e as DTEC 015 a 023.
- Tarefas e rastreabilidade aprovadas por Artur Lins em 13/10/2026 (prompt 3), com uma alteração: Python 3.13 no lugar do 3.14.

## Verificação

- Links relativos e âncoras de todos os arquivos Markdown alterados conferidos por script: nenhum quebrado.
- `contracts/openapi.yaml` validado com `openapi-spec-validator` (OpenAPI 3.1): OK.
- Conector do Procrastinate conferido na documentação oficial (sem conector asyncpg; conexão externa só com psycopg 3, `SyncPsycopgConnector` ou `SQLAlchemyPsycopg2Connector`), base da emenda da DTEC 002.
- Commits do prompt 2: `e4f6777` (decisões transversais), `aa51e5b` (esquema), `1fb863d` (artefatos da 001), `5aabfd6` (registro).
- Tarefas conferidas por script: 65 tarefas, todas citadas na rastreabilidade, e todo ID citado na rastreabilidade existe em `tasks.md`.
- Nenhum código foi escrito nem executado: as versões exatas das dependências e a compatibilidade com Python 3.13 serão verificadas na tarefa de estrutura base (T002).

## Pendências

- Plano, tarefas e rastreabilidade da 002 a 007, em sessões próprias (prompt da 002 entregue ao usuário na resposta ao prompt 3). A implementação da 001 só começa depois disso (prompt 3).
- QA-30: proteção da `main` no GitHub e decisões de processo (revisão obrigatória, documentação pela `develop`) continuam com a equipe.
- Lista curta de senhas comuns em português (DTEC 022): revisão pela equipe antes do merge.
- Specs 002 e 004: os planos devem adotar o formato de chave `usuarios/{public_id}/...` e tarefas que terminam sem efeito quando o registro não existe mais (DTEC 021).
- O índice de `docs/prompts/README.md` não lista a sessão `2026-10-12-revisao-requisitos-specs-mvp.md`, anterior a esta; registro encerrado não foi alterado.
