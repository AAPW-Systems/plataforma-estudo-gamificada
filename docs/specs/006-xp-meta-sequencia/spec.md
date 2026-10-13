# Especificação: XP, meta diária e sequência

**Identificador:** 006-xp-meta-sequencia
**Estágio:** MVP
**Funcionalidade do backlog:** [F-09](../../produto/backlog.md#funcionalidades-candidatas) e [F-10](../../produto/backlog.md#funcionalidades-candidatas), parte do MVP (o congelamento da sequência é incremento posterior)
**Criada em:** 12/10/2026
**Status:** Aprovada para planejamento em 12/10/2026 por Artur Lins (equipe)
**Origem:** backlog, [princípio de gamificação](../../produto/visao.md#princípio-de-gamificação), [base de especificação](../../base-specs/spec.md) (HU-06, HU-17, RF-12, RF-24, RN-10, RN-15, RN-18, RN-21, RN-26, CB-13, CB-24, CB-25) e decisões da [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante individual que quer manter a constância.
**Situação:** o estudante começa animado e, depois de alguns dias, deixa de revisar.
**Problema observável:** sem um alvo diário e sem ver a própria constância, o estudo fica para depois, e a repetição espaçada perde o efeito.
**Resultado esperado:** cada cartão revisado rende XP, a meta do dia é clara e alcançável, e a sequência mostra quantos dias seguidos o estudante cumpriu a meta, sem puni-lo em dias sem cartões disponíveis.
**Alternativa atual:** força de vontade, sem nenhum retorno visível.

## Escopo

### Incluído

- XP pela primeira revisão de cada cartão no dia de estudo, independentemente da nota (RN-18).
- Bônus de XP quando um cartão se torna dominado pela primeira vez (RN-18).
- Meta diária em cartões distintos, meta efetiva, dia estudado e dia neutro (RN-21).
- Sequência atual e recorde (RN-21).
- Exibição de XP, progresso da meta e sequência na trilha e no fechamento da lição.

### Fora do escopo

- Congelamento da sequência: incremento posterior de F-10.
- Conquistas (F-11): fora dos estágios acadêmicos.
- Ranking, ligas e comparação entre estudantes.
- XP por nota, por dificuldade ou por tempo de estudo (contrariam o princípio de gamificação).
- Notificações e lembretes.
- Calendário e painel de evolução: [007-evolucao](../007-evolucao/spec.md).

## Cenários de usuário e testes

### História de usuário 1 Ganhar XP ao revisar P1

Como estudante, quero ganhar XP por cada cartão que reviso, para sentir que cada sessão conta.

**Motivo da prioridade:** é o retorno imediato da revisão e a base das outras recompensas.
**Teste independente:** revisar 5 cartões distintos, sendo um deles marcado Errei e reapresentado na mesma lição, e confirmar 50 de XP (e não 60); reenviar uma revisão e confirmar que o XP não muda.

**Cenários de aceitação**

1. **Dado** um cartão ainda não revisado no dia de estudo, **quando** o estudante o revisa com qualquer nota, **então** recebe 10 de XP, e o valor exibido vem da resposta do servidor.
2. **Dado** um cartão já revisado no dia, **quando** ele é reapresentado na mesma lição ou numa lição extra e revisado de novo, **então** não há novo XP.
3. **Dado** um cartão cuja estabilidade atinge o limiar de domínio pela primeira vez, **quando** a revisão é registrada, **então** o estudante recebe um bônus de 25 de XP, uma única vez por cartão.
4. **Dado** uma revisão reenviada com o mesmo identificador, **quando** o servidor a recebe, **então** o XP não é concedido de novo (CB-24).
5. **Dado** um cartão excluído depois de revisado, **quando** o estudante consulta o XP total, **então** o XP ganho com ele permanece.

### História de usuário 2 Cumprir a meta diária P1

Como estudante, quero ver quanto falta para cumprir a meta de hoje, para saber quando posso parar.

**Motivo da prioridade:** a meta transforma a lição num compromisso diário e define o dia estudado.
**Teste independente:** com meta de 20 e só 8 cartões disponíveis no dia, revisar os 8 e confirmar meta efetiva de 8, meta cumprida e dia estudado.

**Cenários de aceitação**

1. **Dado** meta de 20 e 30 cartões disponíveis, **quando** o estudante revisa 12 cartões distintos, **então** a trilha mostra 12 de 20, e o dia ainda não é estudado.
2. **Dado** meta de 20 e só 8 cartões disponíveis no dia, **quando** o estudante revisa os 8, **então** a meta efetiva é 8, a meta é cumprida e o dia passa a ser estudado.
3. **Dado** a meta cumprida, **quando** o estudante faz lições extras, **então** o progresso continua sendo exibido, mas não cria um dia estudado adicional.
4. **Dado** um cartão reapresentado na mesma lição, **quando** é revisado de novo, **então** não conta duas vezes para a meta.

### História de usuário 3 Manter a sequência sem punição injusta P2

Como estudante, quero que minha sequência conte os dias em que cumpri a meta e não seja quebrada em dias sem cartões disponíveis, para ser recompensado pela constância real (HU-17).

**Motivo da prioridade:** a sequência é o principal motivo de voltar no dia seguinte, mas depende do dia estudado da US2.
**Teste independente:** simular, com relógio controlado, a sequência de dias "estudado, estudado, neutro, estudado, não estudado, estudado" e confirmar a sequência atual de 1 e o recorde de 3.

**Cenários de aceitação**

1. **Dado** dias estudados consecutivos, **quando** o estudante cumpre a meta mais uma vez no dia seguinte, **então** a sequência atual aumenta em 1, e o recorde é atualizado se for superado.
2. **Dado** um dia sem nenhum cartão disponível, **quando** o dia de estudo vira, **então** o dia é neutro e não quebra nem aumenta a sequência (CB-13).
3. **Dado** um dia com cartões disponíveis em que a meta efetiva não foi cumprida, **quando** o dia de estudo vira, **então** a sequência atual volta a zero, e o recorde é mantido.
4. **Dado** uma revisão às 3h50 no fuso do estudante, **quando** ela é registrada, **então** conta para o dia de estudo anterior (o dia vira às 4h) (CB-25).
5. **Dado** a sequência atual, **quando** o dia de hoje ainda não foi estudado, **então** a trilha mostra a sequência até o último dia estudado e indica que hoje ainda falta cumprir a meta.

## Casos de borda

- Revisões enviadas de duas abas ao mesmo tempo: um único XP por cartão e uma única contagem para a meta (CB-24).
- Cartões aceitos ou criados no meio do dia: entram nos disponíveis e podem aumentar a meta efetiva até a meta configurada.
- Cartões excluídos ou suspensos no meio do dia: deixam de contar como disponíveis restantes; os já revisados continuam contando.
- Meta efetiva já cumprida: o dia continua estudado, mesmo que novos cartões fiquem disponíveis depois.
- Mudança da meta diária no meio do dia: vale para o dia corrente, mas um dia já marcado como estudado não deixa de sê-lo.
- Mudança de fuso: cada revisão pertence ao dia de estudo do seu instante, no fuso vigente. Datas puladas pela mudança são neutras; datas repetidas contam uma vez (CB-25, D-003).
- Mudança de horário de verão no fuso do estudante.
- Mudança dos valores de XP na configuração: não altera o XP já concedido.

## Requisitos funcionais

- **RF-001:** O sistema deverá conceder XP na primeira revisão de cada cartão no dia de estudo, independentemente da nota. Revisões seguintes do mesmo cartão no mesmo dia não concedem XP (deriva de RN-18 da base).
- **RF-002:** O sistema deverá conceder um bônus de XP quando a estabilidade de um cartão atingir o limiar de domínio pela primeira vez ([005](../005-licao-trilha/spec.md), D-003), uma única vez por cartão (deriva de RN-18 da base).
- **RF-003:** Todo XP deverá ser calculado no servidor, registrado como evento ligado à revisão que o originou, com a versão da regra de valores, e nunca removido, exceto na exclusão da conta pelo próprio estudante ([001](../001-conta-acesso/spec.md), D-003) (deriva de RN-18 da base).
- **RF-004:** O progresso da meta deverá contar cartões distintos revisados no dia de estudo (deriva de RN-21 da base).
- **RF-005:** A meta efetiva deverá ser o menor valor entre a meta diária e a soma dos cartões distintos já revisados no dia com os cartões ainda disponíveis (deriva de RN-21 da base).
- **RF-006:** O dia de estudo deverá ser marcado como estudado assim que os cartões distintos revisados atingirem a meta efetiva, com pelo menos uma revisão, e não deverá deixar de sê-lo depois.
- **RF-007:** Um dia de estudo sem revisões e sem nenhum cartão disponível na virada deverá ser neutro (deriva de RN-21 e CB-13 da base).
- **RF-008:** A sequência atual deverá ser o número de dias estudados consecutivos, desconsiderando os dias neutros. Um dia não neutro e não estudado zera a sequência atual. O recorde deverá guardar o maior valor já atingido (deriva de RN-21 da base).
- **RF-009:** Cada revisão deverá ser atribuída ao dia de estudo do seu instante, no fuso do estudante vigente nesse instante, com a virada às 4h (deriva de RN-15 e CB-25 da base).
- **RF-010:** A trilha deverá exibir o XP total, o progresso da meta (revisados sobre a meta efetiva) e a sequência atual. O fechamento da lição deverá exibir o XP ganho na lição e a sequência.
- **RF-011:** Nenhuma regra desta spec deverá alterar o agendamento calculado pelo FSRS (deriva de RN-26 da base).

## Entidades principais

- **Evento de XP:** quantidade, motivo (revisão ou cartão dominado), revisão de origem e versão da regra de valores.
- **Regra de valores:** versão dos valores de XP e do limiar de domínio, imutável depois de usada.
- **Dia de estudo:** data no fuso do estudante, com meta vigente, meta efetiva, cartões distintos revisados e situação (estudado, não estudado ou neutro).
- **Sequência:** valor atual, recorde e último dia estudado.

## Critérios de sucesso

- **CS-001:** Em 100% dos testes de reenvio e concorrência, o XP total é igual à soma dos eventos de XP, sem duplicidade.
- **CS-002:** Em testes com relógio controlado, cobrindo a virada das 4h, a mudança de fuso e o horário de verão, a sequência e os dias estudados coincidem com os valores calculados à mão para os mesmos dados.
- **CS-003:** Errar de propósito o mesmo cartão várias vezes no dia rende exatamente o mesmo XP que acertá-lo uma vez.

## Requisitos de qualidade

- **RQ-001:** A interface nunca exibe XP, meta ou sequência como confirmados antes da resposta do servidor (Princípio IV).
- **RQ-002:** A concessão de XP, a atualização da meta e da sequência ocorrem na mesma transação que registra a revisão.
- **RQ-003:** O ganho de XP e o cumprimento da meta são anunciados discretamente a tecnologias assistivas, sem sons automáticos nem animações que ignorem a preferência por movimento reduzido.
- **RQ-004:** Os valores de XP e o limiar de domínio ficam numa configuração versionada; mudá-los não altera o XP já concedido.

## Suposições e dependências

- **Dependência:** [005-licao-trilha](../005-licao-trilha/spec.md) (revisões, lição, cartões disponíveis e cartão dominado) e [001-conta-acesso](../001-conta-acesso/spec.md) (meta e fuso).

## Esclarecimentos

### Sessão de 12/10/2026 ([registro](../../prompts/2026-10-12-esclarecimento-specs-mvp.md))

- **E22:** Como a mudança de fuso afeta os dias de estudo? → Datas puladas pela mudança são neutras, e datas repetidas contam uma vez (D-003).

## Questões abertas

Nenhuma questão impede o planejamento. Os valores de QA-24 que tocam esta spec foram decididos em D-001.

## Decisões confirmadas

- **D-001:** 10 de XP pela primeira revisão de cada cartão no dia; bônus de 25 de XP pelo cartão dominado pela primeira vez; meta diária padrão de 20 cartões distintos ([001](../001-conta-acesso/spec.md), D-001). Valores numa regra versionada ([QA-24](../../produto/pendencias.md#qa-24-valores-da-gamificação)). — **Confirmada por:** Artur Lins (equipe) — **Data:** 12/10/2026
- **D-002:** XP e meta contam cartões distintos por dia, independentemente da nota (RN-18, RN-21), para que errar de propósito não renda pontos. — **Confirmada por:** Artur Lins (equipe), [registro](../../prompts/2026-10-12-esquema-inicial-banco.md) — **Data:** 12/10/2026
- **D-003:** Na mudança de fuso, cada revisão pertence ao dia de estudo do seu instante no fuso vigente; datas puladas pela mudança são neutras, e datas repetidas contam uma vez. — **Confirmada por:** Artur Lins (equipe), esclarecimento E22 — **Data:** 12/10/2026

## Exigências do PO

Nenhuma exigência (EX-01 a EX-05) toca esta funcionalidade. A proposta para EX-05 (PO-01) não altera XP nem meta.

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | Não se aplica: não há conteúdo gerado |
| II Proteção e isolamento | XP, meta e sequência pertencem ao estudante; nenhuma comparação entre estudantes |
| III Verificação humana | Valores decididos e registrados pela equipe (D-001) |
| IV Servidor autoritativo | RF-003, RQ-001, RQ-002; idempotência herdada de [005](../005-licao-trilha/spec.md) |
| V Qualidade verificável | CS-001 a CS-003 com relógio controlado |
| VI Entrega incremental | US1 demonstrável sozinha sobre as revisões de 005 |
| VII Rastreabilidade | Eventos de XP ligados à revisão de origem; IDs da base citados |
