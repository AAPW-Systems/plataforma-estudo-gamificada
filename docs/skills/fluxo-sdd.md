# Guia: fluxo SDD de uma funcionalidade

Resumo operacional das guidelines em [`../sdd_guidelines/`](../sdd_guidelines/00_COMECE_AQUI.md). Em caso de divergência, **as guidelines prevalecem**.

## Antes de começar

1. Leia a [constituição](../constitution.md), a [visão](../produto/visao.md) e o [backlog](../produto/backlog.md).
2. Confirme com a equipe qual funcionalidade `F-xx` será especificada.
3. Crie a pasta seguindo [`../specs/README.md`](../specs/README.md).

## Etapas e portões de revisão

Cada etapa termina em um **portão humano**. O agente não avança para a etapa seguinte sem a confirmação explícita de uma pessoa da equipe.

| # | Etapa | Entrada | Saída | Modelo | Portão |
|---|---|---|---|---|---|
| 1 | Especificar | descrição da jornada, itens do init citados no backlog | `spec.md` | [`modelos/spec.md`](../sdd_guidelines/modelos/spec.md) | — |
| 2 | Esclarecer | `spec.md` | no máximo 5 perguntas de alto impacto | [prompt](../sdd_guidelines/atividades/prompts_para_agente.md) | PO responde |
| 3 | Revisar requisitos | `spec.md` | `checklists/requirements.md` | [`modelos/checklists/requirements.md`](../sdd_guidelines/modelos/checklists/requirements.md) | **Spec aprovada** |
| 4 | Pesquisar | dúvidas técnicas | `research.md` | [`modelos/research.md`](../sdd_guidelines/modelos/research.md) | — |
| 5 | Planejar | spec aprovada, constituição | `plan.md`, `data-model.md`, `contracts/`, `quickstart.md` | [`modelos/`](../sdd_guidelines/modelos/) | **Plano aprovado** |
| 6 | Criar tarefas | todos os artefatos acima | `tasks.md` | [`modelos/tasks.md`](../sdd_guidelines/modelos/tasks.md) | — |
| 7 | Rastrear e analisar | spec, plano, tarefas | `traceability.md` e análise de consistência | [exemplo](../sdd_guidelines/exemplos/001-consulta-prazos/traceability.md) | **Tarefas aprovadas** |
| 8 | Implementar | tarefas de uma história por vez | código, testes, tarefas marcadas | — | Testes passam |
| 9 | Convergir | implementação e artefatos | lacunas viram novas tarefas | — | Critérios com evidência |

## Regras que o agente deve seguir

- **A spec não escolhe tecnologia.** Framework, banco e bibliotecas pertencem ao plano e ao `research.md`.
- **Não invente respostas.** Toda dúvida de produto vira `Q-xxx` na spec, com responsável e prazo. Toda dúvida técnica vira uma decisão `DTEC` no `research.md`.
- **Não enfraqueça requisitos no plano.** Se o plano não conseguir atender, registre a incompatibilidade e volte ao PO.
- **Tarefas por história, não por camada.** Use o formato `T001 [P] [US1] ação em caminho/exato`. Use `[P]` só quando o trabalho for realmente paralelo.
- **Checkbox só depois da verificação.** Código escrito não significa comportamento aprovado.
- **Arquivos não aplicáveis** são omitidos, ou marcados como "não aplicável" com a justificativa. Nada de seção vazia.
- **Mudanças após a aprovação** seguem o modelo ancorado: atualize a spec, registre a mudança e propague para plano, tarefas, testes e contratos. Não reescreva o histórico.
- **IDs são estáveis.** Não renumere RF, CS, RQ, US ou T existentes. Ao remover um item, marque-o como removido.
- **Reaproveite o init.** Os itens listados na coluna "Origem no init" do backlog devem ser revisados e citados (ex.: "deriva de RN-06 do init").

## Antes da entrega

Use o [`checklist_entrega.md`](../sdd_guidelines/atividades/checklist_entrega.md) e atualize a coluna "Spec" do [backlog](../produto/backlog.md).
