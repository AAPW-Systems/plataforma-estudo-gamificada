# Checklist de qualidade dos requisitos

**Finalidade:** verificar se a especificação está pronta para planejamento  
**Funcionalidade:** [spec.md](../spec.md)  
**Revisor:** Claude Code (claude-opus-5-5), revisão preliminar do agente; revisor humano: pendente  
**Data:** 12/10/2026 ([registro](../../../prompts/2026-10-12-revisao-requisitos-specs-mvp.md))

Marcar um item significa que o revisor avaliou a qualidade do texto do requisito. Não significa que a implementação está pronta. Os itens foram marcados pelo agente e precisam ser conferidos pelo revisor humano, que é quem aprova a spec (portão humano).

## Completude

- [x] CHK001 O usuário, a situação e o resultado esperado estão definidos.
- [x] CHK002 O escopo incluído e o que ficou de fora estão explícitos.
- [x] CHK003 Fluxos alternativos, falhas e casos de borda estão cobertos.
- [x] CHK004 Entidades relevantes estão definidas sem antecipar a implementação.

## Clareza

- [x] CHK005 Cada requisito descreve comportamento observável.
- [x] CHK006 Termos vagos possuem medida, condição ou referência. Resolvido em 12/10/2026 (R3, D-010).
- [x] CHK007 Questões abertas indicam responsável e prazo. Resolvido em 12/10/2026 (R5, D-012 e RQ-007).

## Consistência

- [x] CHK008 Histórias, requisitos e critérios de sucesso não se contradizem.
- [x] CHK009 Prioridades refletem o valor e permitem entrega incremental.
- [x] CHK010 Suposições estão separadas de decisões confirmadas.

## Verificabilidade

- [x] CHK011 Cada história possui teste independente.
- [x] CHK012 Cenários de aceitação definem estado, ação e resultado.
- [x] CHK013 Requisitos de qualidade podem ser verificados objetivamente. Resolvido em 12/10/2026 (R4, D-011 e CS-007).
- [x] CHK014 Ausência de informação e indisponibilidade possuem comportamento definido.

## Achados da revisão

### Corrigidos nesta revisão (sem mudança de decisão de produto)

- US2, cenário 2, passou a incluir os cartões aguardando revisão entre os que não podem ser repetidos, coerente com RF-013 e D-008 (CHK008).

### Abertos (dependem de decisão da equipe)

- Nenhum. R3, R4, R5 respondidos por Artur Lins em 12/10/2026.

## Resultado da revisão

**Recomendação do agente:** aprovar para planejamento: sim.  
**Aprovada para planejamento:** pendente do revisor humano.  
**Pendências:** nenhuma bloqueante.
