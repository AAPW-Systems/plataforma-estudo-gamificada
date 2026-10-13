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
- [x] CHK014 Ausência de informação e indisponibilidade possuem comportamento definido.

## Achados da revisão

### Corrigidos nesta revisão (sem mudança de decisão de produto)

- Nenhum.

### Abertos (dependem de decisão da equipe)

- Nenhum.

### Observações

- Esta spec conta como dominados os cartões ativos e suspensos; o domínio por matéria do final acadêmico ([012](../../012-filtro-dominio-materia/spec.md)) usa só os ativos. As duas definições estão explícitas em cada spec e medem coisas diferentes; manter os rótulos distintos na interface ("cartões dominados" e "domínio da matéria").

## Resultado da revisão

**Recomendação do agente:** aprovar para planejamento: sim.  
**Aprovada para planejamento:** pendente do revisor humano.  
**Pendências:** nenhuma bloqueante.
