# Esclarecimento das specs do MVP

**Data:** 2026-10-12
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** esclarecer
**Funcionalidade:** 001 a 007 (specs do MVP), em duas rodadas

## Contexto fornecido

- Specs em rascunho de [`docs/specs/`](../specs/README.md), criadas na [sessão anterior](2026-10-12-specs-funcionalidades.md)
- Prompt de esclarecimento das guidelines ([`prompts_para_agente.md`](../sdd_guidelines/atividades/prompts_para_agente.md), "Esclarecer sem ampliar o escopo"): no máximo cinco dúvidas por spec, ordenadas por impacto, sem detalhes que cabem no plano técnico

## Prompts

### Prompt 1

```text
inicie os esclarecimentos
```

### Resposta a esclarecimento 1

O agente fez 13 perguntas (E1 a E13), cada uma com recomendação: E1 a E5 para a spec 001 (exclusão da conta, troca de senha, cadastro com e-mail já existente, duração da sessão, aviso de privacidade), E6 a E10 para a 002 (arquivo idêntico, renomear título, texto mínimo, arquivo original, meta de 60 s) e E11 a E13 para a 003 (formatação, limites de texto, busca e filtro).

```text
E3 - B
os demais, sua recomendação
```

### Resposta a esclarecimento 2

O agente apresentou o consolidado. Para a E3 (opção B: confirmação de e-mail já no MVP), descreveu as consequências: cadastro neutro, envio de e-mail no MVP com nova DTEC e a pergunta E3-bis (trazer a recuperação de senha para o MVP).

```text
entendi errado o 001, não precisa de confirmação de conta por e-mail no mvp nem recuperação de conta. basta que faça uma verificação no banco de dados se o email já está em uso. deixe como pendência discutir com a equipe se isso entrará no escopo da versão final acadêmica ou se entraria na referência pós-acadêmica
```

### Resposta a esclarecimento 3

Segunda rodada: o agente fez 12 perguntas, cada uma com recomendação: E14 a E18 para a spec 004 (limite diário de gerações, meta de qualidade, motivo da recusa, nova geração com cartões aguardando revisão, meta de 2 minutos), E19 a E21 para a 005 (fim da lição com passo curto pendente, lição aberta de um dia anterior, duração da revisão e meta de 300 ms), E22 para a 006 (mudança de fuso) e E23 a E25 para a 007 (período do calendário, gráficos, meta de 1 segundo).

```text
aprovo todas as sugestões
```

## Saída aceita

| Artefato | Ação |
|---|---|
| `docs/specs/001-conta-acesso/spec.md` | alterado: seção "Esclarecimentos" (E1 a E5), US4 (troca de senha e exclusão da conta), RF-012 a RF-015, CS-004, D-003 a D-007; Q-001 a Q-003 resolvidas |
| `docs/specs/002-materias-fontes/spec.md` | alterado: esclarecimentos E6 a E10, novos cenários, RF-014 a RF-016, D-004 a D-008; Q-001 e Q-002 resolvidas |
| `docs/specs/003-cartoes-manuais/spec.md` | alterado: esclarecimentos E11 a E13, US4 (busca e filtro), RF-010 e RF-011, D-003 a D-005; Q-001 resolvida |
| `docs/specs/004-geracao-cartoes/spec.md` | alterado: esclarecimentos E14 a E18, RF-019 e RF-020, D-005 a D-009; Q-001 a Q-003 resolvidas |
| `docs/specs/005-licao-trilha/spec.md` | alterado: esclarecimentos E19 a E21, fim da lição com passo curto pendente (altera a RN-19 da base), D-004 a D-006 |
| `docs/specs/006-xp-meta-sequencia/spec.md` | alterado: esclarecimento E22, D-003 |
| `docs/specs/007-evolucao/spec.md` | alterado: esclarecimentos E23 a E25, D-002 a D-004; Q-001 e Q-002 resolvidas |
| `docs/specs/008-recuperacao-senha/spec.md` | alterado: Q-002 movida para QA-33 |
| `docs/specs/001-*/README.md` a `007-*/README.md` | alterados: histórico |
| `docs/produto/pendencias.md` | alterado: nova QA-33 (confirmação de e-mail no cadastro: final acadêmico ou referência pós-acadêmica) |
| `docs/prompts/2026-10-12-esclarecimento-specs-mvp.md` e `docs/prompts/README.md` | criado e alterado |

Na E3, a resposta final da pessoa substituiu a opção B: o cadastro verifica no banco se o e-mail já está em uso e informa o estudante; não há confirmação de conta por e-mail nem recuperação de senha no MVP. A spec 008 continua no final acadêmico, como no backlog.

## Alterações humanas

Pendente de revisão.

## Verificação

- Links relativos e âncoras dos arquivos alterados conferidos por script (0 links quebrados).
- O checklist de requisitos (`checklists/requirements.md`) das specs 001 a 007 **não** foi executado: é a próxima etapa, feita por um revisor da equipe.

## Pendências

- QA-33: a equipe decide se a confirmação de e-mail no cadastro entra no final acadêmico ou na referência pós-acadêmica.
- Revisão das specs 001 a 007 pelo checklist de requisitos e aprovação pela equipe (portão humano).
- Ao aprovar a spec 005, atualizar a RN-19 da [base de especificação](../base-specs/spec.md) com a D-004 (fim da lição com passo curto pendente).
- Continuam abertas na spec 005: Q-001 (composição visual da trilha, UI-05, até 16/10/2026) e Q-002 (EX-05, com o PO).
