# Tarefas (ponteiro)

**Atualizado em:** 12/10/2026 ([registro da sessão](../prompts/2026-10-12-alinhamento-produto-arquitetura.md))

As tarefas **não são planejadas para o produto inteiro**. Pelas guidelines e pelo Princípio VI da [constituição](../constitution.md), cada funcionalidade tem o seu `tasks.md`, organizado por história de usuário e gerado só depois de o `plan.md` dela ser aprovado (`docs/specs/NNN-nome-curto/tasks.md`, guia em [`../skills/fluxo-sdd.md`](../skills/fluxo-sdd.md)).

A versão de 07/10/2026 deste arquivo, com um plano em fases para trilhas e questões, está no histórico do git (commit `e32228a`). Ela não vale mais, porque questões e pontos por dificuldade saíram do produto (RN-07 e RN-11 da [base de especificação](spec.md)). Os critérios de validação daquela versão (isolamento, idempotência, ciclo de vida das fontes, contratos) continuam úteis como checklist ao escrever os testes de cada spec.

## Próximos passos do projeto

| Ordem | Passo | Situação |
|---|---|---|
| 1 | Esquema inicial do banco em DBML (`docs/arquitetura/esquema-inicial.dbml`), a partir das entidades da [base de especificação](spec.md#8-entidades-conceituais) | Pendente ([QA-21](../produto/pendencias.md#qa-21-esquema-inicial-do-banco)) |
| 2 | Specs das funcionalidades do MVP, na ordem do [backlog](../produto/backlog.md#ordem), conforme as guidelines | Pendente, após o passo 1 |
