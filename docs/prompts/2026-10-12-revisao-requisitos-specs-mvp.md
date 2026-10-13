# Revisão dos requisitos das specs do MVP

**Data:** 2026-10-12
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** revisar
**Funcionalidade:** 001 a 007 (specs do MVP)

## Contexto fornecido

- Specs 001 a 007 depois do [esclarecimento](2026-10-12-esclarecimento-specs-mvp.md)
- Modelo do checklist ([`modelos/checklists/requirements.md`](../sdd_guidelines/modelos/checklists/requirements.md)) e prompt "Revisar a especificação" das guidelines ([`prompts_para_agente.md`](../sdd_guidelines/atividades/prompts_para_agente.md))

## Prompts

### Prompt 1

O agente perguntou se fazia os commits do esclarecimento e se começava a revisão pelo checklist de requisitos, como revisão preliminar do agente, deixando a aprovação para o revisor humano.

```text
sim
```

## Saída aceita

| Artefato | Ação |
|---|---|
| `docs/specs/001-*/checklists/requirements.md` a `007-*/checklists/requirements.md` | criados: revisão preliminar do agente, item a item |
| `docs/specs/001-conta-acesso/spec.md` | alterado: cenários da US1 renumerados; exceção da exclusão da conta explícita em RF-015 |
| `docs/specs/002-materias-fontes/spec.md` | alterado: título da US3 cobre a renomeação de fontes |
| `docs/specs/004-geracao-cartoes/spec.md` | alterado: US2, cenário 2, inclui os cartões aguardando revisão |
| `docs/specs/005-licao-trilha/spec.md` | alterado: caso de borda da lição com menos cartões disponíveis que o tamanho |
| `docs/specs/006-xp-meta-sequencia/spec.md` | alterado: RF-003 cita a exceção da exclusão da conta |
| `docs/specs/001-*/README.md` a `007-*/README.md` | alterados: ordem de leitura e histórico |

As correções acima são mecânicas ou de consistência e não mudam decisões de produto. Os achados que pedem decisão (R1 a R6) foram levados à pessoa.

## Alterações humanas

Pendente de revisão.

## Verificação

- Releitura integral das specs 001 a 005 na versão esclarecida; 006 e 007 conferidas nos trechos alterados.
- Links relativos e âncoras das specs e dos checklists conferidos por script (0 links quebrados).
- Os checklists foram marcados pelo agente; a aprovação para planejamento continua com o revisor humano.

## Pendências

- Decisões R1 a R6, levadas à pessoa nesta sessão.
- Conferência dos checklists pelo revisor humano e aprovação das specs (portão humano).
