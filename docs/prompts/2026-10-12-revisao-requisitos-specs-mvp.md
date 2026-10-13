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

### Resposta a esclarecimento 1

O agente apresentou seis achados que pediam decisão, cada um com recomendação: R1 (cartões manuais que citam uma fonte excluída), R2 (fonte com falha na cota), R3 (falhas técnicas no limite de gerações), R4 (critério para "Gerar mais" sem repetição), R5 (responsável pelo conjunto de avaliação) e R6 (quando um cartão novo conta no limite diário).

```text
R5 - cada pessoa da equipe poderá ficar responsável se for a ela a desenvolver a spec, não vamos ter tempo de discutir isso, pois dia 15 já temos que chegar com o mvp. Atualmente na parte da documentação eu (Artur Lins) e o Arthur Moura é que tem estado mais a frente. Após os specs estiverem prontos, já daremos sequência ao desenvolvimento
os demais ponto, pode seguir com sua recomendação
```

### Prompt 2

Enviado enquanto o agente aplicava as respostas.

```text
podemos apresentar dia 15, 20 ou 22 o mvp, mas a nossa equipe é uma das mais avançadas, então provavelmente vamos apresentar dia 15 ou 20
```

### Prompt 3

```text
aprovo as specs, fiz a revisão individual de cada uma delas
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

Depois das respostas (resposta a esclarecimento 1):

| Artefato | Ação |
|---|---|
| `docs/specs/002-materias-fontes/spec.md` | alterado: R1 (D-009, novo cenário 5 na US2) e R2 (D-010) |
| `docs/specs/003-cartoes-manuais/spec.md` | alterado: reflexo de R1 (D-006) |
| `docs/specs/004-geracao-cartoes/spec.md` | alterado: R3 (D-010), R4 (CS-007, D-011) e R5 (RQ-007, D-012) |
| `docs/specs/005-licao-trilha/spec.md` | alterado: R6 (D-007); prazo da Q-001 antecipado para 14/10/2026 |
| `docs/specs/002-*`, `003-*`, `004-*`, `005-*` `checklists/requirements.md` | alterados: itens resolvidos marcados, sem pendências bloqueantes |
| `docs/produto/backlog.md`, `docs/produto/pendencias.md`, `docs/base-specs/spec.md` | alterados: prazo do MVP passa a "apresentação em 15/10, 20/10 ou 22/10/2026, com meta da equipe em 15/10 e alternativa em 20/10", conforme as mensagens da pessoa |

Depois da aprovação (prompt 3):

| Artefato | Ação |
|---|---|
| `docs/specs/001-*` a `007-*` (`spec.md`, `README.md`, `checklists/requirements.md`) | alterados: status "Aprovada para planejamento", revisor humano registrado |
| `docs/specs/README.md` e `.agents/AGENTS.md` | alterados: specs 001 a 007 em "Spec aprovada"; próximo passo é o plano |
| `docs/base-specs/spec.md`, `docs/produto/visao.md`, `docs/produto/pendencias.md` | alterados: sincronizados com as specs aprovadas (RN-14, RN-18, RN-19, RN-20, RN-23, RN-26; limite de 20 novos por dia; QA-04, QA-23 e QA-24 respondidas), conforme a regra 12 |

## Alterações humanas

Artur Lins revisou individualmente cada spec de 001 a 007 e as aprovou para planejamento em 12/10/2026 (prompt 3). Os checklists marcados pelo agente foram conferidos por ele.

## Verificação

- Releitura integral das specs 001 a 005 na versão esclarecida; 006 e 007 conferidas nos trechos alterados.
- Links relativos e âncoras das specs e dos checklists conferidos por script (0 links quebrados).
- Os checklists foram marcados pelo agente; a aprovação para planejamento continua com o revisor humano.

## Pendências

- Decisões R1 a R6: respondidas em 12/10/2026.
- ~~Atualizar a [base de especificação](../base-specs/spec.md) quando as specs forem aprovadas: RN-19 (fim da lição, spec 005, D-004), RN-14 e RN-18 (exceção da exclusão da conta, spec 001, RF-015) e limite de novos por dia (20, spec 001, D-001; a visão ainda cita 10).~~ Feito em 12/10/2026.
- Plano das specs do MVP, começando pela 001 (etapa 5 do fluxo SDD).
