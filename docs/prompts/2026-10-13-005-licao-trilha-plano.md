# Plano, tarefas e rastreabilidade da spec 005-licao-trilha

**Data:** 2026-10-13
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** planejar (etapa 5); tarefas e rastreabilidade (etapas 6 e 7) depois do portão "Plano aprovado"
**Funcionalidade:** 005-licao-trilha

## Contexto fornecido

- `docs/skills/contexto-tecnico.md` (resumo das DTEC 001 a 047), `docs/skills/fluxo-sdd.md`, `docs/skills/registrar-prompt.md`
- `docs/constitution.md`, `docs/specs/005-licao-trilha/spec.md` (aprovada em 12/10/2026) e `checklists/requirements.md`
- `docs/arquitetura/esquema-inicial.dbml` (tabelas `licoes`, `revisoes`, `parametros_fsrs`, `cartoes`, `usuarios` e enums `estado_fsrs` e `nota_revisao`)
- Trechos pontuais: DTEC 012 em `docs/research.md`; obrigações para a 005 nos planos da 003 e da 004; RN-19, RN-20, RN-26 e RN-18 de `docs/base-specs/spec.md`; seções 9.2 e 9.7 de `docs/base-specs/design.md`
- Código-fonte da biblioteca `fsrs` (`fsrs/scheduler.py` no repositório oficial): o *fuzz* usa `from random import random` e só se aplica ao estado *Review*

## Prompts

### Prompt 1

```text
Prompt para a nova sessão (spec 005)

Vamos para a etapa 5 (planejar) da spec 005-licao-trilha, aprovada em 12/10/2026.
Siga docs/skills/fluxo-sdd.md e as guidelines à risca: produza plan.md, research.md (só
dúvidas técnicas novas), data-model.md, contracts/openapi.yaml e quickstart.md; depois da
minha aprovação do plano, tasks.md (etapa 6) e traceability.md com análise de consistência
(etapa 7). Não implemente código: a decisão de 13/10/2026 é documentar todas as specs do
MVP antes de implementar.

Economia de contexto: comece lendo SÓ docs/skills/contexto-tecnico.md (resumo das DTEC
001 a 047, convenções, códigos de erro, migrações e obrigações entre specs), a constituição,
a spec 005 e o checklist dela. Não leia os planos nem os research.md das specs 001 a 004
inteiros: abra uma seção específica só quando precisar de um detalhe que o guia não traz
ou antes de alterar algo já decidido. Para o modelo, use o .dbml com grep nas tabelas
licoes, revisoes, parametros_fsrs, cartoes e usuarios.

Não redefina nada do que o guia resume. Em particular:
- Stack aprovada e biblioteca fsrs (DTEC 012, FSRS soberano, RN-26). Tecnologia nova só
  com nova DTEC; a numeração continua na DTEC 048. Próxima migração: 0006.
- A 005 cria licoes e revisoes (revisoes.cartao_id ON DELETE SET NULL) e a coluna
  cartoes.dominado_em; parametros_fsrs já existe desde a 001. Atualize o .dbml se o plano
  mudar algo.
- O enum Erro.codigo é cumulativo (lista completa no guia).
- Cumpra as obrigações da tabela "Obrigações pendentes entre specs" do guia que são da 005
  (lição só com ativo, ordem de entrada_estudo_em, escritas disjuntas da DTEC 037,
  explicação ao errar com GET /cartoes/{id}/evidencias, reverificações da 003 e da 004).
- Deixe claro no plano o que a 005 entrega à 006 (evento de revisão, primeira revisão do
  dia, dominado_em), sem implementar XP.
- Responsável: qualquer membro da equipe pode implementar; nesta fase eu faço as
  aprovações.
- Exigências do PO que tocam a 005: EX-03 (explicação ao errar) e EX-05 (Q-002, em pauta
  com o PO; sem requisito de dificuldade até a resposta). Q-001 (trilha, UI-05) tem prazo
  em 14/10/2026: proponha opções no plano, sem decidir produto.

Pontos que o plano precisa resolver (alinhe comigo):
- Montagem da lição e limite de novos por dia sob concorrência e na virada das 4h
  (RF-001, RF-002, D-007, CS-003), inclusive lição aberta de dia anterior (D-005).
- Verso só depois da revelação e recusa de avaliação sem revelação (RF-003, CB-22).
- Reapresentação no passo curto dentro da lição e critério de término (RF-006, D-004).
- Revisão idempotente e conflito com mesmo identificador e conteúdo diferente (RF-008,
  CS-002); registro imutável com estado antes e depois e versão dos parâmetros (RF-007,
  RQ-004); reprodutibilidade do fuzz do FSRS (CS-001).
- Dominado (D-003, limiar de 21 dias em configuração versionada).
- Trilha (RF-010), lições extras (RF-012) e próximo vencimento sem cartões (RF-013).
- Teclado e desempenho da transição (RF-015, CS-004: 300 ms no p95).

Alinhe comigo em rodadas as decisões técnicas que não estiverem nas DTEC (perguntas
numeradas, opções e recomendação; consolidado antes de editar). Registre a sessão em
docs/prompts/ desde o início, faça commits atômicos separados na develop (decisões
transversais, esquema, artefatos da spec, registro) e, ao final de cada etapa, pare no
portão humano. Ao aprovar o plano, atualize docs/skills/contexto-tecnico.md (DTEC novas,
códigos de erro, migração e obrigações) no mesmo commit da aprovação. Ao terminar a 005,
gere o prompt da 006 para uma nova sessão.
O MVP tem apresentação prevista para 15/10/2026.
```

### Resposta a esclarecimento 1

```text
Rodada 1 (7 perguntas: tabelas licoes_cartoes e apresentacoes com cascade; "começar ou
continuar" sob advisory lock e encerramento da lição de dia anterior só nos pontos de
entrada; limite de novos reconferido na primeira revisão; revelação no servidor e duração
medida no cliente com limites; idempotência pela chave e pela apresentação; semente do fuzz
por revisão com gerador por contexto; dominado_em, primeira_do_dia e tornou_dominado para a
006) -> pode seguir com as recomendações
```

### Resposta a esclarecimento 2

```text
Rodada 2 (7 perguntas: próximo cartão com passo curto vencido primeiro; elegibilidade pelo
estado do FSRS, com passo curto só depois de vencer; próxima apresentação na resposta da
avaliação e medição do p95; numero na conclusão, GET /trilha com cursor e extra por lição
concluída no dia; atalhos de teclado; Q-001 só com opções no plano; seis códigos de erro
novos) -> seguir
```

### Prompt 2

```text
plano aprovado
```

### Prompt 3

```text
tarefas aprovadas
```

## Saída aceita

Etapa 5 (planejar), até o portão "Plano aprovado":

| Artefato | Ação |
|---|---|
| `docs/research.md` | alterado: DTEC 048 (dia de estudo num único ponto), proposta |
| `docs/arquitetura/esquema-inicial.dbml` | alterado: `licoes`, `licoes_cartoes`, `apresentacoes`, `revisoes`, `cartoes` (`dominado_em`, índice `cartoes_id_usuario`) e FKs compostas |
| `docs/specs/005-licao-trilha/plan.md` | criado |
| `docs/specs/005-licao-trilha/research.md` | criado: DTEC 049 a 056 |
| `docs/specs/005-licao-trilha/data-model.md` | criado |
| `docs/specs/005-licao-trilha/contracts/openapi.yaml` | criado |
| `docs/specs/005-licao-trilha/quickstart.md` | criado |
| `docs/specs/005-licao-trilha/README.md` | alterado: ordem de leitura, status e histórico |
| `docs/prompts/2026-10-13-005-licao-trilha-plano.md` | criado (este registro) |

Portão "Plano aprovado" (13/10/2026): `plan.md`, `research.md` da spec, DTEC 048 em `docs/research.md`, README da spec, `docs/specs/README.md`, `.agents/AGENTS.md` e `docs/skills/contexto-tecnico.md` (DTEC 048 a 056, códigos de erro, migração `0007` como a próxima, obrigações) atualizados no commit da aprovação.

Etapas 6 e 7, até o portão "Tarefas aprovadas":

| Artefato | Ação |
|---|---|
| `docs/specs/005-licao-trilha/tasks.md` | criado: T001 a T049 |
| `docs/specs/005-licao-trilha/traceability.md` | criado, com a análise de consistência |
| `docs/specs/005-licao-trilha/README.md` | alterado: ordem de leitura, status e histórico |

Portão "Tarefas aprovadas" (13/10/2026): status de `tasks.md` e `traceability.md`, README da spec, `docs/specs/README.md`, estado atual do `.agents/AGENTS.md` e linha da 005 em `docs/skills/contexto-tecnico.md` atualizados no commit da aprovação.

Prompt gerado para a sessão da spec 006:

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

Ajustes feitos pelo agente sobre as recomendações aprovadas, explicitados ao autor no fim da etapa:

- `GET /trilha` não escreve: a lição aberta de dia anterior aparece como "Começar lição" e só é encerrada no `POST /licoes`, que a página da lição chama ao carregar (DTEC 050).
- A avaliação procura a chave de idempotência antes de verificar se a lição está aberta, para que o reenvio da avaliação que concluiu a lição devolva `200` (DTEC 052).
- `revisoes.apresentacao_public_id` guarda o valor sem FK, para sobreviver à exclusão do cartão (DTEC 049).
- Dia de estudo num módulo único do núcleo, compartilhado com a 004 e a 006 (DTEC 048, transversal).

## Alterações humanas

Pendente de revisão.

## Verificação

- `openapi-spec-validator` sobre `contracts/openapi.yaml`: OK.
- Links relativos e âncoras dos arquivos alterados conferidos por script: nenhum quebrado.
- Cobertura da matriz conferida por script: as 49 tarefas aparecem no `traceability.md` (a T035 faltava e foi incluída).
- Ponto de *fuzz* da biblioteca `fsrs` conferido no código-fonte oficial (`from random import random`, só no estado *Review*).
- Nenhum código implementado (decisão de 13/10/2026).

## Pendências

- Portões "Plano aprovado" e "Tarefas aprovadas": aprovados por Artur Lins em 13/10/2026.
- Plano da spec 006 em nova sessão, com o prompt acima.
- Implementação da 005 adiada até a documentação das specs do MVP ficar completa (decisão de 13/10/2026).
- `git push`: os commits desta sessão estão só no repositório local.
- Q-001 (trilha, UI-05): decisão da equipe até 14/10/2026, com as opções do plano.
- Q-002 (EX-05): resposta do PO.
