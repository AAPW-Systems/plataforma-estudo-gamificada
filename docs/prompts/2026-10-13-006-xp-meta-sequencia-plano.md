# Plano, tarefas e rastreabilidade da spec 006-xp-meta-sequencia

**Data:** 2026-10-13
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** planejar (etapa 5); tarefas e rastreabilidade (etapas 6 e 7) depois do portão "Plano aprovado"
**Funcionalidade:** 006-xp-meta-sequencia

## Contexto fornecido

- `docs/skills/contexto-tecnico.md` (resumo das DTEC 001 a 056), `docs/skills/fluxo-sdd.md`, `docs/skills/registrar-prompt.md`
- `docs/constitution.md`, `docs/specs/006-xp-meta-sequencia/spec.md` (aprovada em 12/10/2026) e `checklists/requirements.md`
- `docs/arquitetura/esquema-inicial.dbml` (tabelas `eventos_xp`, `dias_estudo`, `revisoes`, `licoes`, `usuarios`, `cartoes` e enum `tipo_evento_xp`)
- Trechos pontuais: "O que a 005 entrega à 006", "Complexidade e exceções" e "Obrigações registradas para as próximas specs" do plano da 005; DTEC 055 e 056 da 005; esquemas `Trilha`, `Fechamento` e `ResultadoAvaliacao` do contrato da 005; DTEC 048 em `docs/research.md`; preferências em `docs/specs/001-conta-acesso/data-model.md`; fluxos de suspensão, reativação e exclusão no plano da 003; seção 5.1 da arquitetura (domínio `gamificacao`)

## Prompts

### Prompt 1

```text
Prompt para a nova sessão (spec 006)

Vamos para a etapa 5 (planejar) da spec 006-xp-meta-sequencia, aprovada em 12/10/2026.
Siga docs/skills/fluxo-sdd.md e as guidelines à risca: produza plan.md, research.md (só
dúvidas técnicas novas), data-model.md, contracts/openapi.yaml e quickstart.md; depois da
minha aprovação do plano, tasks.md (etapa 6) e traceability.md com análise de consistência
(etapa 7). Não implemente código: a decisão de 13/10/2026 é documentar todas as specs do
MVP antes de implementar.

Economia de contexto: comece lendo SÓ docs/skills/contexto-tecnico.md (resumo das DTEC
001 a 056, convenções, códigos de erro, migrações e obrigações entre specs), a constituição,
a spec 006 e o checklist dela. Não leia os planos nem os research.md das specs 001 a 005
inteiros: abra uma seção específica só quando precisar de um detalhe que o guia não traz
ou antes de alterar algo já decidido. Da 005, as seções úteis são "O que a 005 entrega à
006" e "Obrigações registradas para as próximas specs" do plan.md, as DTEC 055 e 056 e o
esquema Fechamento do contrato. Para o modelo, use o .dbml com grep nas tabelas eventos_xp,
dias_estudo, revisoes, licoes e usuarios.

Não redefina nada do que o guia resume. Em particular:
- Stack aprovada; tecnologia nova só com nova DTEC; a numeração continua na DTEC 057.
  Próxima migração: 0007.
006" e "Obrigações registradas para as próximas specs" do plan.md, as DTEC 055 e 056 e o
esquema Fechamento do contrato. Para o modelo, use o .dbml com grep nas tabelas eventos_xp,
dias_estudo, revisoes, licoes e usuarios.

Não redefina nada do que o guia resume. Em particular:
- Stack aprovada; tecnologia nova só com nova DTEC; a numeração continua na DTEC 057.
  Próxima migração: 0007.
- Dia de estudo só por nucleo/dia_estudo.py (DTEC 048), inclusive na meta e na sequência.
- A 005 entrega: o evento RevisaoRegistrada em nucleo/eventos_revisao.py (mesma
  transação da revisão), revisoes.primeira_do_dia, revisoes.tornou_dominado,
  revisoes.versao_regras e cartoes.dominado_em. A 006 registra o ouvinte; não muda a
  lição nem o agendamento (RF-011, RN-26).
- Obrigações da tabela "Obrigações pendentes entre specs" que são da 006:
  eventos_xp.cartao_id com ON DELETE SET NULL (reverificar a US3-3 da 003); XP só com
  primeira_do_dia e bônus só com tornou_dominado; XP e sequência como campos aditivos do
  Fechamento e da trilha; "extra depois da meta" é classificação da 006.
- O enum Erro.codigo é cumulativo (lista completa no guia).
- Responsável: qualquer membro da equipe pode implementar; nesta fase eu faço as
  aprovações.
- Nenhuma exigência do PO toca a 006 (a spec registra isso); confira mesmo assim.

Pontos que o plano precisa resolver (alinhe comigo):
- Regra de valores versionada (RQ-004, D-001): relação com VERSAO_REGRAS e o limiar de
  dominado da 005 (revisao/regras.py), sem duplicar a regra.
- Concessão de XP idempotente e na mesma transação da revisão (RF-001 a RF-003, RQ-002,
  CS-001, CS-003), com o cache usuarios.xp_total.
- Meta efetiva (RF-005) e marcação de dia estudado que não se desfaz (RF-006), sob
  concorrência e com cartões ficando disponíveis ao longo do dia.
- Dia neutro (RF-007): "nenhum cartão disponível na virada" exige saber a disponibilidade
  na virada sem tarefa periódica por estudante, ou justificar uma; cálculo da sequência e
  do recorde (RF-008) sem depender de o estudante abrir o app.
- Mudança de fuso e horário de verão (RF-009, D-003, CS-002): datas puladas neutras e
  datas repetidas uma vez.
- Exibição na trilha e no fechamento (RF-010) e anúncio acessível (RQ-001, RQ-003).

Alinhe comigo em rodadas as decisões técnicas que não estiverem nas DTEC (perguntas
numeradas, opções e recomendação; consolidado antes de editar). Registre a sessão em
docs/prompts/ desde o início, faça commits atômicos separados na develop (decisões
transversais, esquema, artefatos da spec, registro) e, ao final de cada etapa, pare no
portão humano. Ao aprovar o plano, atualize docs/skills/contexto-tecnico.md (DTEC novas,
códigos de erro, migração e obrigações) no mesmo commit da aprovação. Ao terminar a 006,
gere o prompt da 007 para uma nova sessão.
O MVP tem apresentação prevista para 15/10/2026.
```

### Resposta a esclarecimento 1

```text
Rodada 1 com sete decisões, cada uma com opções e recomendação: (1) regra de valores de XP
versionada em gamificacao/regras.py, com histórico imutável e versão smallint, e o limiar de
dominado só em revisao/regras.py, ligados pela revisão de origem; (2) XP por INSERT simples com
índice único (revisao_id, tipo) e cache xp_total na mesma transação; (3) provedor de
disponibilidade registrado por revisao em nucleo/disponibilidade.py, para evitar o ciclo entre
domínios; (4) liquidação preguiçosa e exata dos dias passados, com ganchos antes e depois das
ações que retiram disponibilidade, sem tarefa periódica; (5) leitura literal de "disponível na
virada"; (6) datas puladas = datas que nunca foram o dia corrente, data vivida em parte segue a
regra normal, data liquidada não muda; (7) ResumoGamificacao como campo aditivo de Trilha,
Fechamento e ResultadoAvaliacao, aria-live discreto -> "siga com as recomendações"
```

### Prompt 2

```text
continue
```

### Prompt 3

```text
plano aprovado, siga para tarefas e rastreabilidade
```

## Saída aceita

### Etapa 5 (planejar)

| Artefato | Ação |
|---|---|
| `docs/research.md` | alterado: DTEC 057 (disponibilidade de cartões e ganchos de alteração no núcleo), transversal, proposta |
| `docs/arquitetura/esquema-inicial.dbml` | alterado: enum `situacao_dia`; `eventos_xp` (`versao_regra smallint`, índice `(revisao_id, tipo)`, FKs compostas); `dias_estudo` (situação, meta diária, `data_pulada`, `liquidado_em`); `usuarios.dias_liquidados_ate`; índice `revisoes_id_usuario` |
| `docs/specs/006-xp-meta-sequencia/research.md` | criado: DTEC 058 a 063 |
| `docs/specs/006-xp-meta-sequencia/plan.md` | criado |
| `docs/specs/006-xp-meta-sequencia/data-model.md` | criado |
| `docs/specs/006-xp-meta-sequencia/contracts/openapi.yaml` | criado: superconjunto dos caminhos afetados da 005 |
| `docs/specs/006-xp-meta-sequencia/quickstart.md` | criado |
| `docs/specs/006-xp-meta-sequencia/README.md` | alterado: ordem de leitura e histórico |

## Alterações humanas

Pendente de revisão.

## Verificação

- `openapi-spec-validator` sobre `contracts/openapi.yaml` da 006: OK.
- Script de comparação entre os contratos: o da 006 é superconjunto do da 005 nos caminhos e esquemas comuns (nenhum campo, código de resposta ou valor de enum removido).
- Links relativos e âncoras dos arquivos alterados conferidos por script: nenhum quebrado.
- Exigências do PO conferidas: nenhuma toca a 006.
- Nenhum código implementado (decisão de 13/10/2026).

## Pendências

- Portão "Plano aprovado": aprovado por Artur Lins em 13/10/2026; `contexto-tecnico.md` atualizado no mesmo commit.
- Portão "Tarefas aprovadas": aguardando Artur Lins.
