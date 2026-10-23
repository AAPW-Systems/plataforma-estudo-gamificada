# 003-cartoes-manuais: cartões criados e gerenciados pelo estudante

| Campo | Valor |
|---|---|
| Funcionalidade do backlog | F-04 (parte manual) |
| Estágio | **MVP** |
| Status | Implementando |
| Depende de | [001](../001-conta-acesso/README.md), [002](../002-materias-fontes/README.md) |

## Ordem de leitura

1. [`spec.md`](spec.md): o quê e por quê. Aprovada para planejamento em 12/10/2026.
2. [`checklists/requirements.md`](checklists/requirements.md): revisão do agente, conferida e aprovada por Artur Lins.
3. [`plan.md`](plan.md): como. Aprovado em 13/10/2026 por Artur Lins.
4. [`research.md`](research.md): DTEC 035 a 038, específicas desta spec. As transversais deste planejamento (DTEC 033, DTEC 034 e a emenda da DTEC 027) estão em [`../../research.md`](../../research.md).
5. [`data-model.md`](data-model.md): entidade, estados, restrições e validações.
6. [`contracts/openapi.yaml`](contracts/openapi.yaml): contrato da API.
7. [`quickstart.md`](quickstart.md): validação local.

8. [`tasks.md`](tasks.md): tarefas T001 a T045, por história. Aprovadas em 13/10/2026.
9. [`traceability.md`](traceability.md): requisito ↔ cenário ↔ teste ↔ tarefa e análise de consistência. Aprovada em 13/10/2026, junto com as tarefas.

## Histórico

| Data | Mudança |
|---|---|
| 12/10/2026 | Spec criada em rascunho ([registro](../../prompts/2026-10-12-specs-funcionalidades.md)) |
| 12/10/2026 | Esclarecimento (E11 a E13) incorporado à spec; próxima etapa: revisão pelo checklist de requisitos ([registro](../../prompts/2026-10-12-esclarecimento-specs-mvp.md)) |
| 12/10/2026 | Revisão preliminar pelo checklist de requisitos ([registro](../../prompts/2026-10-12-revisao-requisitos-specs-mvp.md)) |
| 12/10/2026 | Spec aprovada para planejamento por Artur Lins, depois da revisão individual ([registro](../../prompts/2026-10-12-revisao-requisitos-specs-mvp.md)) |
| 13/10/2026 | Plano, pesquisa, modelo de dados, contrato e quickstart escritos; decisões técnicas alinhadas em rodada com Artur Lins ([registro](../../prompts/2026-10-13-003-cartoes-manuais-plano.md)) |
| 13/10/2026 | Plano aprovado por Artur Lins, com as DTEC 033 a 038 e a emenda da DTEC 027 ([registro](../../prompts/2026-10-13-003-cartoes-manuais-plano.md)) |
| 13/10/2026 | Tarefas (T001 a T045) e rastreabilidade escritas; aguardando o portão "Tarefas aprovadas" ([registro](../../prompts/2026-10-13-003-cartoes-manuais-plano.md)) |
| 13/10/2026 | Tarefas e rastreabilidade aprovadas por Artur Lins; implementação adiada até a documentação das specs do MVP ficar completa ([registro](../../prompts/2026-10-13-003-cartoes-manuais-plano.md)) |
| 13/10/2026 | Propagação do plano da 004 ([DTEC 045](../004-geracao-cartoes/research.md#decisão-dtec-045-revisão-dos-cartões-gerados)): nos cartões gerados, `verificado` e "Fonte apagada" passam a ser derivados também da fonte da geração, e o esquema `Cartao` ganha o campo `geracao`. A mudança no mapeador e no repositório da 003 é feita por uma tarefa da 004, sem alterar as tarefas aprovadas da 003 ([registro](../../prompts/2026-10-13-004-geracao-cartoes-plano.md)) |
| 23/10/2026 | Implementação iniciada na `develop`: T001 a T003 (limites, regra de lint e migração `0004_cartoes`) com evidência; T004 em diante pendentes ([registro](../../prompts/2026-10-23-003-cartoes-manuais-implementacao.md)) |
