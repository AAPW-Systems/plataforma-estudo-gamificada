# Tarefas da funcionalidade

**Entrada:** `spec.md`, `plan.md` e artefatos de apoio revisados  
**Formato:** `[ID] [P?] [US?] ação com caminho exato e resultado verificável`

- `[P]` indica que a tarefa pode ser executada em paralelo porque não altera os mesmos arquivos nem depende de outra tarefa pendente.
- `[US1]` relaciona a tarefa a uma história de usuário.
- Marque `[x]` somente quando o resultado e sua verificação estiverem concluídos.

## Fase 1 Preparação

- [ ] T001 Criar [estrutura] em `[caminho]`
- [ ] T002 [P] Configurar [ferramenta] em `[arquivo]`

## Fase 2 Base compartilhada

- [ ] T003 Implementar [componente necessário a todas as histórias] em `[arquivo]`
- [ ] T004 [P] Criar testes de [contrato ou regra] em `[arquivo]`

## Fase 3 História de usuário 1

**Objetivo:** [resultado da história]  
**Teste independente:** [procedimento]

- [ ] T005 [P] [US1] Criar teste para [cenário] em `[arquivo]`
- [ ] T006 [US1] Implementar [comportamento] em `[arquivo]`
- [ ] T007 [US1] Integrar [componentes] em `[arquivo]`
- [ ] T008 [US1] Executar [teste ou demonstração] e registrar o resultado em `[arquivo]`

## Fase 4 História de usuário 2

**Objetivo:**  
**Teste independente:**

- [ ] T009 [P] [US2] Criar teste para [cenário] em `[arquivo]`
- [ ] T010 [US2] Implementar [comportamento] em `[arquivo]`

## Fase final Qualidade transversal

- [ ] T011 Executar testes relacionados aos critérios de aceitação
- [ ] T012 Revisar logs, segredos, acessibilidade e mensagens de erro
- [ ] T013 Atualizar `quickstart.md` com comandos realmente verificados
- [ ] T014 Conferir rastreabilidade entre requisitos, testes e tarefas

## Dependências

- T003 bloqueia [tarefas].
- US1 pode ser implementada e demonstrada antes de US2.

## Estratégia de incremento

1. Concluir a preparação e a base compartilhada.
2. Entregar a história P1 com teste independente.
3. Adicionar as histórias seguintes sem quebrar a P1.
4. Executar a verificação final e atualizar os artefatos afetados.
