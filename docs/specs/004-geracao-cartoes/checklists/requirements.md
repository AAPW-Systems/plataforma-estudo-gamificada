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
- [ ] CHK006 Termos vagos possuem medida, condição ou referência. **Pendente:** O limite de 20 gerações por dia (RF-019) não diz se gerações que falharam por erro técnico contam. Achado R3.
- [ ] CHK007 Questões abertas indicam responsável e prazo. **Pendente:** O Princípio V exige que o conjunto de avaliação seja revisado por uma pessoa responsável, que a spec não indica. Achado R5.

## Consistência

- [x] CHK008 Histórias, requisitos e critérios de sucesso não se contradizem.
- [x] CHK009 Prioridades refletem o valor e permitem entrega incremental.
- [x] CHK010 Suposições estão separadas de decisões confirmadas.

## Verificabilidade

- [x] CHK011 Cada história possui teste independente.
- [x] CHK012 Cenários de aceitação definem estado, ação e resultado.
- [ ] CHK013 Requisitos de qualidade podem ser verificados objetivamente. **Pendente:** "Não repetir, em conteúdo" (RF-013, EX-02) não tem critério de verificação objetivo. Achado R4.
- [x] CHK014 Ausência de informação e indisponibilidade possuem comportamento definido.

## Achados da revisão

### Corrigidos nesta revisão (sem mudança de decisão de produto)

- US2, cenário 2, passou a incluir os cartões aguardando revisão entre os que não podem ser repetidos, coerente com RF-013 e D-008 (CHK008).

### Abertos (dependem de decisão da equipe)

- R3, R4, R5: ver os itens desmarcados acima e o [registro da revisão](../../../prompts/2026-10-12-revisao-requisitos-specs-mvp.md).

### Observações

- O aviso de envio a provedor externo antes da primeira geração (RF-002) e o aviso de privacidade do cadastro ([001](../../001-conta-acesso/spec.md), D-007) são complementares e não se contradizem.

## Resultado da revisão

**Recomendação do agente:** aprovar para planejamento: sim, depois de responder R3 a R5.  
**Aprovada para planejamento:** pendente do revisor humano.  
**Pendências:** R3, R4, R5.
