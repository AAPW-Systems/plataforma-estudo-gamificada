# 004-geracao-cartoes: geração de cartões pela IA e revisão dos gerados

| Campo | Valor |
|---|---|
| Funcionalidade do backlog | F-04 (parte de IA do MVP); EX-02 e EX-03 |
| Estágio | **MVP** |
| Status | Implementando |
| Depende de | [002](../002-materias-fontes/README.md), [003](../003-cartoes-manuais/README.md) |

## Ordem de leitura

1. [`spec.md`](spec.md): o quê e por quê. Aprovada para planejamento em 12/10/2026.
2. [`checklists/requirements.md`](checklists/requirements.md): revisão do agente, conferida e aprovada por Artur Lins.
3. [`plan.md`](plan.md): como. Aprovado em 13/10/2026 por Artur Lins.
4. [`research.md`](research.md): DTEC 041 a 047, específicas desta spec. As transversais deste planejamento (DTEC 039 e DTEC 040) estão em [`../../research.md`](../../research.md).
5. [`data-model.md`](data-model.md): entidades, estados, restrições e validações.
6. [`contracts/openapi.yaml`](contracts/openapi.yaml): contrato da API.
7. [`quickstart.md`](quickstart.md): validação local, demonstração e runbook.

8. [`tasks.md`](tasks.md): tarefas T001 a T059, por história. Aprovadas em 13/10/2026.
9. [`traceability.md`](traceability.md): requisito ↔ cenário ↔ teste ↔ tarefa e análise de consistência. Aprovada em 13/10/2026, junto com as tarefas.

## Histórico

| Data | Mudança |
|---|---|
| 12/10/2026 | Spec criada em rascunho ([registro](../../prompts/2026-10-12-specs-funcionalidades.md)) |
| 12/10/2026 | Esclarecimento (E14 a E18) incorporado à spec; próxima etapa: revisão pelo checklist de requisitos ([registro](../../prompts/2026-10-12-esclarecimento-specs-mvp.md)) |
| 12/10/2026 | Revisão preliminar pelo checklist de requisitos ([registro](../../prompts/2026-10-12-revisao-requisitos-specs-mvp.md)) |
| 12/10/2026 | Spec aprovada para planejamento por Artur Lins, depois da revisão individual ([registro](../../prompts/2026-10-12-revisao-requisitos-specs-mvp.md)) |
| 13/10/2026 | Plano, pesquisa, modelo de dados, contrato e quickstart escritos; decisões técnicas alinhadas em rodadas com Artur Lins ([registro](../../prompts/2026-10-13-004-geracao-cartoes-plano.md)) |
| 13/10/2026 | Plano aprovado por Artur Lins, com as DTEC 039 a 047 ([registro](../../prompts/2026-10-13-004-geracao-cartoes-plano.md)) |
| 13/10/2026 | Tarefas (T001 a T059) e rastreabilidade escritas; aguardando o portão "Tarefas aprovadas" ([registro](../../prompts/2026-10-13-004-geracao-cartoes-plano.md)) |
| 13/10/2026 | Tarefas e rastreabilidade aprovadas por Artur Lins; implementação adiada até a documentação das specs do MVP ficar completa ([registro](../../prompts/2026-10-13-004-geracao-cartoes-plano.md)) |
| 29/10/2026 | Implementação da base (Fases 1 e 2) na `develop`: T001 a T010 concluídas com evidência; T011 aguarda a verificação no Docker Desktop por Artur Lins e o CI; responsável pela implementação e revisor do conjunto de avaliação: Artur Lins ([registro](../../prompts/2026-10-29-004-geracao-cartoes-implementacao.md)) |
