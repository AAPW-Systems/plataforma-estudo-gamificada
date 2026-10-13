# Checklist de qualidade dos requisitos

**Finalidade:** verificar se a especificação está pronta para planejamento  
**Funcionalidade:** [spec.md](../spec.md)  
**Revisor:** Claude Code (claude-opus-5-5), revisão preliminar do agente; revisor humano: pendente  
**Data:** 12/10/2026 ([registro](../../../prompts/2026-10-12-revisao-requisitos-specs-mvp.md))

Marcar um item significa que o revisor avaliou a qualidade do texto do requisito. Não significa que a implementação está pronta. Os itens foram marcados pelo agente e precisam ser conferidos pelo revisor humano, que é quem aprova a spec (portão humano).

## Completude

- [x] CHK001 O usuário, a situação e o resultado esperado estão definidos.
- [x] CHK002 O escopo incluído e o que ficou de fora estão explícitos.
- [ ] CHK003 Fluxos alternativos, falhas e casos de borda estão cobertos. **Pendente:** Não está definido se "Excluir os cartões junto" apaga também os cartões criados pelo estudante que só citam a fonte como referência ([003](../../003-cartoes-manuais/spec.md), RF-002). Achado R1.
- [x] CHK004 Entidades relevantes estão definidas sem antecipar a implementação.

## Clareza

- [x] CHK005 Cada requisito descreve comportamento observável.
- [x] CHK006 Termos vagos possuem medida, condição ou referência.
- [x] CHK007 Questões abertas indicam responsável e prazo.

## Consistência

- [x] CHK008 Histórias, requisitos e critérios de sucesso não se contradizem.
- [x] CHK009 Prioridades refletem o valor e permitem entrega incremental.
- [x] CHK010 Suposições estão separadas de decisões confirmadas.

## Verificabilidade

- [x] CHK011 Cada história possui teste independente.
- [x] CHK012 Cenários de aceitação definem estado, ação e resultado.
- [x] CHK013 Requisitos de qualidade podem ser verificados objetivamente.
- [ ] CHK014 Ausência de informação e indisponibilidade possuem comportamento definido. **Pendente:** Não está definido se uma fonte com `falhou` ocupa a cota (30 fontes por matéria e 100 MB). Achado R2.

## Achados da revisão

### Corrigidos nesta revisão (sem mudança de decisão de produto)

- O título da US3 passou a cobrir também a renomeação de fontes (cenário 5), incluída no esclarecimento (CHK008).

### Abertos (dependem de decisão da equipe)

- R1, R2: ver os itens desmarcados acima e o [registro da revisão](../../../prompts/2026-10-12-revisao-requisitos-specs-mvp.md).

## Resultado da revisão

**Recomendação do agente:** aprovar para planejamento: sim, depois de responder R1 e R2.  
**Aprovada para planejamento:** pendente do revisor humano.  
**Pendências:** R1, R2.
