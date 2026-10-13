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

- Cenários da US1 estavam fora de ordem (1, 2, 7, 8, 3...) depois do esclarecimento; renumerados de 1 a 8 sem mudar o conteúdo (CHK012).
- RF-015 passa a dizer que a exclusão da conta é a única situação em que revisões, XP e sequência são removidos, exceção a RN-14 e RN-18 da base (CHK008). A base é atualizada quando a spec for aprovada.

### Abertos (dependem de decisão da equipe)

- Nenhum.

### Observações

- QA-33 (confirmação de e-mail no cadastro) é decisão de estágio posterior e não bloqueia o MVP.
- A suposição sobre os limites de nome e de tentativas de cadastro deve ser confirmada pelo revisor humano.

## Resultado da revisão

**Recomendação do agente:** aprovar para planejamento: sim.  
**Aprovada para planejamento:** pendente do revisor humano.  
**Pendências:** nenhuma bloqueante.
