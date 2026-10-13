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
- [ ] CHK006 Termos vagos possuem medida, condição ou referência. **Pendente:** O limite de novos por dia (RF-002) não define quando um cartão novo passa a contar: ao entrar numa lição ou ao ser revisado pela primeira vez. Isso importa quando a lição é interrompida ou encerrada no dia seguinte (D-005). Achado R6.
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

- Novo caso de borda: com menos cartões disponíveis que o tamanho da lição, a lição tem só os disponíveis (implícito na RN-19, "até o tamanho da lição") (CHK003).

### Abertos (dependem de decisão da equipe)

- R6: ver os itens desmarcados acima e o [registro da revisão](../../../prompts/2026-10-12-revisao-requisitos-specs-mvp.md).

### Observações

- Q-001 (composição visual da trilha, UI-05) e Q-002 (EX-05, com o PO) têm responsável e prazo e não bloqueiam o plano.
- D-004 altera o texto da RN-19 da base; atualizar a base na aprovação.

## Resultado da revisão

**Recomendação do agente:** aprovar para planejamento: sim, depois de responder R6.  
**Aprovada para planejamento:** pendente do revisor humano.  
**Pendências:** R6.
