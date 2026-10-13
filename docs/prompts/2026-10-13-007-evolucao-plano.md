# Plano, tarefas e rastreabilidade da spec 007-evolucao

**Data:** 2026-10-13
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** planejar (etapa 5); tarefas e rastreabilidade (etapas 6 e 7) depois do portão "Plano aprovado"
**Funcionalidade:** 007-evolucao

## Contexto fornecido

- `docs/skills/contexto-tecnico.md` (resumo das DTEC 001 a 063), `docs/skills/fluxo-sdd.md`, `docs/skills/registrar-prompt.md`
- `docs/constitution.md`, `docs/specs/007-evolucao/spec.md` (aprovada em 12/10/2026) e `checklists/requirements.md`
- `docs/produto/exigencias_po.md` e `docs/produto/pauta-po.md` (PO-01 e PO-02)
- Trechos pontuais: "Obrigações registradas para as próximas specs" do plano da 006; DTEC 061, 062 e 063; "Entidade DiaEstudo" e "Leituras que a 006 expõe a outras specs" do `data-model.md` da 006; "Leituras que a 005 expõe a outras specs" e DTEC 055 da 005; DTEC 057 em `docs/research.md`; seção 5.1 da arquitetura (domínio `evolucao`); RN-25 da base e seção 9.10 do `design.md`
- `docs/arquitetura/esquema-inicial.dbml` (tabelas `usuarios`, `materias`, `cartoes`, `revisoes`, `eventos_xp` e `dias_estudo`; enum `situacao_dia`)

## Prompts

### Prompt 1

```text
Prompt para a nova sessão (spec 007)

Vamos para a etapa 5 (planejar) da spec 007-evolucao, aprovada em 12/10/2026. É a última
spec do MVP. Siga docs/skills/fluxo-sdd.md e as guidelines à risca: produza plan.md,
research.md (só dúvidas técnicas novas), data-model.md, contracts/openapi.yaml e
quickstart.md; depois da minha aprovação do plano, tasks.md (etapa 6) e traceability.md
com análise de consistência (etapa 7). Não implemente código: a decisão de 13/10/2026 é
documentar todas as specs do MVP antes de implementar.

Economia de contexto: comece lendo SÓ docs/skills/contexto-tecnico.md (resumo das DTEC
001 a 063, convenções, códigos de erro, migrações e obrigações entre specs), a constituição,
a spec 007 e o checklist dela. Não leia os planos nem os research.md das specs 001 a 006
inteiros: abra uma seção específica só quando precisar de um detalhe que o guia não traz
ou antes de alterar algo já decidido. Da 006, as seções úteis são "Obrigações registradas
para as próximas specs" do plan.md, as DTEC 061 e 063 e "Leituras que a 006 expõe a outras
specs" do data-model.md. Da 005, "Leituras que a 005 expõe a outras specs" do data-model.md
e a DTEC 055. Para o modelo, use o .dbml com grep nas tabelas dias_estudo, eventos_xp,
revisoes, cartoes, materias e usuarios.

Não redefina nada do que o guia resume. Em particular:
- Stack aprovada; tecnologia nova só com nova DTEC; a numeração continua na DTEC 064.
  Próxima migração: 0008 (talvez nenhuma seja necessária; justifique).
- Domínio evolucao (arquitetura, seção 5.1). Dias e XP só por gamificacao/consultas.py
  (dias_no_intervalo, que inclui as datas ainda não liquidadas calculadas sem gravar, e
  xp_por_dia); nunca recalcular a sequência nem ler dias_estudo direto (obrigação da 006).
  Dominados, estabilidade e revisões pelas consultas de revisao e cartoes (obrigação da 005).
- Dia de estudo só por nucleo/dia_estudo.py (DTEC 048); leituras sem efeito colateral
  (DTEC 061).
- O enum Erro.codigo é cumulativo (lista completa no guia).
- Responsável: qualquer membro da equipe pode implementar; nesta fase eu faço as
  aprovações.
- Confira as exigências do PO (docs/produto/exigencias_po.md e pauta-po.md) mesmo que a
  spec diga que nenhuma a toca.

Pontos que o plano precisa resolver (alinhe comigo):
- RF-001: calendário de 26 semanas com as situações estudado, não estudado, neutro e "em
  andamento" (o dia corrente), mapeadas a partir de situacao_dia da 006 (pendente,
  estudado, nao_estudado, neutro, data_pulada); dias antes da criação da conta; total de
  dias estudados no período.
- RF-002: XP total, sequência atual e recorde idênticos aos do ResumoGamificacao da 006
  (reaproveitar a consulta, não recalcular).
- RF-003: dominados "atuais" (ativos ou suspensos com estabilidade >= limiar vigente) no
  total e por matéria, distintos de cartoes.dominado_em (bônus único da 006); relação com
  LIMIAR_DOMINADO_DIAS e VERSAO_REGRAS (revisao/regras.py), sem duplicar a regra.
- CS-002: 1 s no p95 com um ano de histórico fictício; índices e consultas agregadas.
- RQ-001: calendário navegável por teclado e legível por leitor de tela (cada dia anuncia
  data e situação), contraste 3:1 entre situações e marcação que não depende só de cor;
  RQ-002: 320 px sem rolagem horizontal da página.
- RF-005: estado vazio sem revisões, com acesso à trilha.

Alinhe comigo em rodadas as decisões técnicas que não estiverem nas DTEC (perguntas
numeradas, opções e recomendação; consolidado antes de editar). Registre a sessão em
docs/prompts/ desde o início, faça commits atômicos separados na develop (decisões
transversais, esquema, artefatos da spec, registro) e, ao final de cada etapa, pare no
portão humano. Ao aprovar o plano, atualize docs/skills/contexto-tecnico.md (DTEC novas,
códigos de erro, migração e obrigações) no mesmo commit da aprovação. Ao terminar a 007,
a documentação do MVP fica completa: atualize o "Estado atual" do AGENTS.md indicando que
a implementação pode começar e proponha a ordem de implementação das specs 001 a 007.
O MVP tem apresentação prevista para 15/10/2026.
```

## Saída aceita

Em andamento.

## Alterações humanas

Pendente de revisão.

## Verificação

Em andamento.

## Pendências

- Em andamento.
