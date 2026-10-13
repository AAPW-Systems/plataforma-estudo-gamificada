# Especificação: evolução mínima

**Identificador:** 007-evolucao
**Estágio:** MVP
**Funcionalidade do backlog:** [F-12](../../produto/backlog.md#funcionalidades-candidatas), parte do MVP (o painel completo do final acadêmico está em [013-evolucao-completa](../013-evolucao-completa/spec.md))
**Criada em:** 12/10/2026
**Status:** Aprovada para planejamento em 12/10/2026 por Artur Lins (equipe)
**Origem:** backlog, [base de especificação](../../base-specs/spec.md) (HU-08, RF-15, RN-25) e decisões da [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante individual que estuda há alguns dias ou semanas.
**Situação:** o estudante quer saber se está avançando.
**Problema observável:** a trilha mostra o dia a dia, mas não a constância ao longo das semanas nem quanto já foi consolidado.
**Resultado esperado:** uma tela de evolução mostra os dias estudados num calendário, o XP total, a sequência atual e o recorde, e os cartões dominados no total e por matéria.
**Alternativa atual:** nenhuma; o estudante só tem a própria impressão.

## Escopo

### Incluído

- Calendário dos dias de estudo das últimas 26 semanas, com cada dia marcado como estudado, não estudado ou neutro (D-002).
- XP total.
- Sequência atual e recorde.
- Cartões dominados no total e por matéria.
- Estado vazio para quem ainda não estudou.

### Fora do escopo

- Tempo dedicado, filtros, períodos e indicadores completos por matéria: final acadêmico, em [013-evolucao-completa](../013-evolucao-completa/spec.md).
- Domínio por matéria (dominados sobre ativos): final acadêmico, em [012-filtro-dominio-materia](../012-filtro-dominio-materia/spec.md).
- Exibição da dificuldade dos cartões (EX-05): em pauta com o PO (PO-01).
- Exportação de dados e comparação com outros estudantes.

## Cenários de usuário e testes

### História de usuário 1 Ver minha evolução P1

Como estudante, quero ver meus dias estudados, meu XP, minha sequência e meus cartões dominados, para acompanhar minha evolução (HU-08).

**Motivo da prioridade:** é a única história desta spec; fecha a capacidade de gamificação do MVP.
**Teste independente:** com dados fictícios de 30 dias (estudados, não estudados e neutros), 2 matérias e cartões dominados, abrir a evolução e conferir cada valor com o calculado à mão.

**Cenários de aceitação**

1. **Dado** um histórico de estudos, **quando** o estudante abre a evolução, **então** vê o calendário das últimas 26 semanas, com cada dia identificado como estudado, não estudado ou neutro sem depender só de cor, e o total de dias estudados no período.
2. **Dado** o mesmo histórico, **quando** o estudante abre a evolução, **então** vê o XP total, a sequência atual, a sequência recorde e os cartões dominados no total e em cada matéria, todos com o valor em texto.
3. **Dado** um estudante sem nenhuma revisão, **quando** ele abre a evolução, **então** vê um estado vazio que explica que a evolução começa na primeira lição, com o acesso à trilha, sem números fictícios.
4. **Dado** um cartão dominado que foi excluído, **quando** o estudante abre a evolução, **então** ele não conta nos cartões dominados, mas o XP que ele rendeu permanece no total.

## Casos de borda

- Dias anteriores à criação da conta: não aparecem como não estudados.
- Dia de hoje ainda não encerrado: aparece como "em andamento", nunca como não estudado.
- Cartão dominado que perdeu estabilidade depois de um Errei: deixa de contar como dominado no momento, sem perder o bônus já concedido.
- Cartões suspensos dominados: contam como dominados.
- Matéria excluída: deixa de aparecer na lista por matéria; o XP permanece no total.
- Mudança de fuso: o calendário usa as datas já atribuídas a cada dia de estudo.

## Requisitos funcionais

- **RF-001:** O sistema deverá exibir o calendário dos dias de estudo das últimas 26 semanas, com a situação de cada dia (estudado, não estudado, neutro ou em andamento) e o total de dias estudados no período (deriva de RN-25 da base).
- **RF-002:** O sistema deverá exibir o XP total, a sequência atual e a sequência recorde, iguais aos valores calculados em [006](../006-xp-meta-sequencia/spec.md) (deriva de RN-25 da base).
- **RF-003:** O sistema deverá exibir a quantidade atual de cartões dominados (ativos ou suspensos, com estabilidade no limiar de domínio) no total e em cada matéria (deriva de RN-25 da base).
- **RF-004:** Todos os valores deverão ser calculados no servidor e exibidos também em texto. No MVP, só o calendário é gráfico; os demais valores são números em destaque (D-003).
- **RF-005:** Sem nenhuma revisão, a tela deverá exibir um estado vazio com o acesso à trilha.

## Entidades principais

- **Resumo da evolução:** visão calculada a partir dos dias de estudo, dos eventos de XP, da sequência e do estado de agendamento dos cartões. Não cria dados novos.

## Critérios de sucesso

- **CS-001:** Para o conjunto fictício de 30 dias, todos os valores exibidos coincidem com os calculados à mão.
- **CS-002:** A tela de evolução carrega em até 1 segundo no percentil 95 no ambiente local, com um ano de histórico fictício.

## Requisitos de qualidade

- **RQ-001:** O calendário é navegável por teclado e legível por leitores de tela (cada dia anuncia a data e a situação), com contraste mínimo de 3:1 entre as situações e marcação que não depende só de cor.
- **RQ-002:** A tela funciona a partir de 320 px sem rolagem horizontal da página.
- **RQ-003:** Os dados respeitam o isolamento entre estudantes.

## Suposições e dependências

- **Dependência:** [006-xp-meta-sequencia](../006-xp-meta-sequencia/spec.md) (dias de estudo, XP e sequência) e [005-licao-trilha](../005-licao-trilha/spec.md) (cartão dominado).
- **Suposição:** se o prazo do MVP apertar, esta spec é o primeiro corte e se reduz a XP e sequência, que já aparecem na trilha ([backlog](../../produto/backlog.md#ordem)).

## Esclarecimentos

### Sessão de 12/10/2026 ([registro](../../prompts/2026-10-12-esclarecimento-specs-mvp.md))

- **E23:** Qual o período do calendário? → As últimas 26 semanas (D-002).
- **E24:** Quais indicadores usam gráfico? → No MVP, só o calendário (D-003).
- **E25:** A meta de 1 segundo para carregar a evolução está confirmada? → Sim (D-004).

## Questões abertas

- **Q-001:** ~~Calendário de 26 semanas ou desde a criação da conta?~~ Resolvida em 12/10/2026 (D-002).
- **Q-002:** ~~Quais indicadores usam gráfico?~~ Resolvida em 12/10/2026 (D-003).

Nenhuma questão aberta impede o planejamento.

## Decisões confirmadas

- **D-001:** O mínimo do MVP é dias estudados, XP, sequência e cartões dominados (RN-25 da base). — **Confirmada por:** equipe, no [backlog](../../produto/backlog.md#capacidades) — **Data:** 12/10/2026
- **D-002:** O calendário do MVP cobre as últimas 26 semanas; períodos e filtros ficam em [013](../013-evolucao-completa/spec.md). — **Confirmada por:** Artur Lins (equipe), esclarecimento E23 — **Data:** 12/10/2026
- **D-003:** No MVP, só o calendário é gráfico; os demais indicadores são números em destaque ([UI-04](../../base-specs/design.md#12-pendências-de-design)). — **Confirmada por:** Artur Lins (equipe), esclarecimento E24 — **Data:** 12/10/2026
- **D-004:** Meta de até 1 segundo no percentil 95 para carregar a evolução, no ambiente local, com um ano de histórico fictício (CS-002). — **Confirmada por:** Artur Lins (equipe), esclarecimento E25 — **Data:** 12/10/2026

## Exigências do PO

Nenhuma exigência toca esta parte. A exibição da dificuldade (EX-05, PO-01), se aprovada, entra em [013](../013-evolucao-completa/spec.md).

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | Não se aplica |
| II Proteção e isolamento | RQ-003 |
| III Verificação humana | Q-001 e Q-002 ficam com a equipe |
| IV Servidor autoritativo | RF-004 |
| V Qualidade verificável | CS-001 com dados fictícios calculados à mão; RQ-001 |
| VI Entrega incremental | História única, demonstrável sobre 005 e 006 |
| VII Rastreabilidade | IDs da base citados; sessão registrada |
