# Especificação: lição com repetição espaçada e trilha de progressão

**Identificador:** 005-licao-trilha
**Estágio:** MVP
**Funcionalidade do backlog:** [F-05](../../produto/backlog.md#funcionalidades-candidatas) e [F-07](../../produto/backlog.md#funcionalidades-candidatas), parte do MVP (o filtro por matéria e o domínio por matéria, do final acadêmico, estão em [012-filtro-dominio-materia](../012-filtro-dominio-materia/spec.md); o tira-dúvidas, em [015-tira-duvidas-cartao](../015-tira-duvidas-cartao/spec.md))
**Criada em:** 12/10/2026
**Status:** Rascunho
**Origem:** backlog, [exigências do PO](../../produto/exigencias_po.md) EX-03 e EX-05, [base de especificação](../../base-specs/spec.md) (HU-04, HU-06, HU-07, HU-16, RF-08, RF-21, RF-23, RN-10, RN-15, RN-16, RN-17, RN-19, RN-20, RN-26, CB-13, CB-22, CB-24, CB-25, CB-27, CB-28, CB-30) e decisões da [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante individual com cartões ativos em várias matérias.
**Situação:** o estudante tem dezenas de cartões e pouco tempo por dia.
**Problema observável:** sem um agendamento, ele revisa o que já sabe e esquece o que não revisou. Sem ver o progresso, perde a vontade de voltar.
**Resultado esperado:** o estudante abre a trilha, começa a lição do dia, revela cada resposta, se autoavalia com quatro botões e vê a explicação quando erra. O algoritmo de repetição espaçada decide quando cada cartão volta, e cada lição concluída acende um nó da trilha.
**Alternativa atual:** reler o material ou revisar cartões em ordem fixa, sem saber o que está perto de ser esquecido.

## Escopo

### Incluído

- Trilha unificada: cada nó é uma lição; nós alcançados, nó atual e próximos passos (RN-19).
- Montagem da lição pelo servidor: cartões devidos primeiro, depois os novos, até o tamanho da lição, respeitando o limite de novos por dia (RN-19, RN-20).
- Apresentação: frente, "Revelar resposta", verso e autoavaliação com Errei, Difícil, Bom e Fácil (RN-17).
- Agendamento calculado exclusivamente pelo FSRS, inclusive os passos curtos que trazem o cartão de volta na mesma lição (RN-26).
- Explicação curta e acesso à evidência ao marcar Errei (RN-16, EX-03).
- Fechamento da lição e lições extras enquanto houver cartões disponíveis.
- Dia sem cartões disponíveis: nenhuma lição e o próximo vencimento exibido (CB-13, CB-30).
- Envio idempotente das revisões (RN-10).
- Definição de "cartão dominado" (D-003), usada aqui no fechamento e em [006](../006-xp-meta-sequencia/spec.md) e [007](../007-evolucao/spec.md).

### Fora do escopo

- Filtro da lição por matéria e domínio por matéria: final acadêmico, em [012-filtro-dominio-materia](../012-filtro-dominio-materia/spec.md).
- Tira-dúvidas durante a lição: final acadêmico, em [015-tira-duvidas-cartao](../015-tira-duvidas-cartao/spec.md).
- Desfazer revisão e reiniciar o aprendizado de um cartão: incrementos posteriores de F-05.
- Revisão antecipada de cartões que ainda não venceram (RN-26).
- Otimização dos parâmetros pelo histórico do estudante (RN-26).
- Seleção de cartões por dificuldade (EX-05): em pauta com o PO (Q-002).
- Cálculo de XP, meta e sequência: [006-xp-meta-sequencia](../006-xp-meta-sequencia/spec.md).

## Cenários de usuário e testes

### História de usuário 1 Fazer a lição do dia P1

Como estudante, quero fazer uma lição curta com os cartões que o algoritmo escolheu para hoje, para revisar no momento certo o que estou perto de esquecer (HU-07).

**Motivo da prioridade:** é o centro do produto. Sem lição, nenhuma outra parte da gamificação faz sentido.
**Teste independente:** com cartões manuais fictícios (12 novos, 3 devidos), lição de 10 e limite de 20 novos, iniciar a lição, revisar todos os cartões e conferir a ordem (devidos antes dos novos), o novo vencimento de cada cartão, a reapresentação de um cartão marcado Errei e a conclusão da lição.

**Cenários de aceitação**

1. **Dado** 3 cartões devidos e 12 novos, com lição de 10, **quando** o estudante começa a lição, **então** ela tem 10 cartões distintos: os 3 devidos (mais atrasados primeiro) e 7 novos na ordem de entrada.
2. **Dado** um cartão na tela, **quando** o estudante ainda não revelou a resposta, **então** os botões de autoavaliação não estão disponíveis, e o verso não foi enviado ao navegador.
3. **Dado** o verso revelado, **quando** o estudante escolhe Bom, **então** o servidor calcula o próximo vencimento pelo FSRS, registra a revisão e apresenta o próximo cartão.
4. **Dado** um cartão novo marcado Errei, **quando** o FSRS agenda um passo curto (minutos), **então** o cartão volta na mesma lição quando o passo vence, sinalizado como "revendo", sem contar como novo cartão na posição da lição.
5. **Dado** que todos os cartões previstos foram revisados ao menos uma vez e nenhum passo curto já vencido aguarda reapresentação, **quando** o último é avaliado, **então** a lição é concluída, o nó da trilha acende e o fechamento mostra as revisões feitas e os cartões que se tornaram dominados.
6. **Dado** que todos os cartões previstos já foram revisados e só restam cartões com passo curto ainda não vencido, **quando** o último cartão é avaliado, **então** a lição é concluída, o nó acende, e o fechamento informa que esses cartões voltam na próxima lição, no instante calculado pelo FSRS, sem apresentá-los antes do vencimento (D-004).

### História de usuário 2 Entender o erro P1

Como estudante, quero ver uma explicação curta quando erro um cartão, para entender o porquê e não só decorar a resposta (HU-16, EX-03).

**Motivo da prioridade:** é exigência do PO e parte do fluxo principal da lição.
**Teste independente:** marcar Errei num cartão gerado e confirmar a exibição da explicação e do acesso à evidência; repetir com um cartão manual sem explicação.

**Cenários de aceitação**

1. **Dado** um cartão com explicação, **quando** o estudante marca Errei, **então** a explicação aparece com o acesso à evidência (recolhida por padrão), antes de seguir para o próximo cartão.
2. **Dado** um cartão manual sem explicação, **quando** o estudante marca Errei, **então** a lição segue sem a área de explicação e sem mensagem de erro.
3. **Dado** a explicação exibida, **quando** ela aparece, **então** nenhuma nova chamada à IA é feita (RN-16).

### História de usuário 3 Ver a trilha e saber o próximo passo P1

Como estudante, quero ver na trilha as lições que já concluí e o que vem a seguir, para enxergar meu progresso (HU-04).

**Motivo da prioridade:** a trilha é a principal representação do progresso e responde a "o que faço agora?".
**Teste independente:** com 3 lições concluídas, conferir 3 nós alcançados, o nó atual e o próximo passo; sem cartões disponíveis, conferir que não há lição e que o próximo vencimento é exibido.

**Cenários de aceitação**

1. **Dado** um estudante novo, sem cartões, **quando** ele abre a trilha, **então** vê o convite para criar a primeira matéria e enviar a primeira fonte, sem nós fictícios.
2. **Dado** lições concluídas, **quando** o estudante abre a trilha, **então** vê os nós alcançados, o nó atual com "Começar lição" (ou "Continuar lição", se houver uma em andamento) e o próximo passo. Os estados dos nós não dependem só de cor.
3. **Dado** que não há cartões disponíveis no dia, **quando** o estudante abre a trilha, **então** não há lição, e a tela mostra quando vence o próximo cartão e que o dia é neutro para a sequência (CB-13).

### História de usuário 4 Continuar estudando depois da meta P3

Como estudante, quero fazer lições extras enquanto houver cartões disponíveis, para aproveitar um dia com mais tempo.

**Motivo da prioridade:** amplia a US1 para quem estuda mais, sem regra nova de agendamento.
**Teste independente:** concluir a lição com cartões disponíveis restantes e iniciar uma extra; esgotar os disponíveis e confirmar que "Continuar" não aparece e que o próximo vencimento é exibido.

**Cenários de aceitação**

1. **Dado** a lição concluída e cartões disponíveis restantes, **quando** o estudante escolhe "Continuar", **então** uma nova lição é montada com as mesmas regras e vira um novo nó da trilha.
2. **Dado** que todos os cartões disponíveis do dia foram revisados, **quando** a lição termina, **então** "Continuar" não aparece, e o fechamento mostra quando vence o próximo cartão (CB-30).

## Casos de borda

- Avaliação enviada sem a revelação do verso naquela apresentação: não é registrada (CB-22).
- Mesma revisão reenviada ou enviada de duas abas: um único efeito; o mesmo identificador com nota diferente gera conflito (CB-24).
- Lição interrompida (aba fechada) com um cartão em passo curto: o cartão mantém o vencimento calculado; a lição continua em andamento e é retomada ao voltar à trilha no mesmo dia de estudo; o nó só acende na conclusão (CB-28).
- Lição deixada aberta de um dia de estudo anterior: é encerrada sem acender o nó, e uma nova lição é montada com os cartões disponíveis do dia; as revisões já registradas permanecem (D-005).
- Lição iniciada antes das 4h e continuada depois: cada revisão pertence ao dia de estudo do seu instante, no fuso vigente (CB-25).
- Cartão excluído, suspenso ou com a fonte excluída durante a lição: deixa de ser apresentado; as revisões registradas permanecem (CB-27).
- Cartão aceito durante uma lição aberta: entra só nas lições seguintes.
- Mudança da retenção desejada durante uma lição: vale a partir da próxima revisão (CB-29).
- Menos cartões disponíveis que o tamanho da lição: a lição tem só os disponíveis, e o fechamento indica que não há mais cartões no dia.
- Limite de novos por dia igual a zero: a lição só tem devidos.
- Lição interrompida ou encerrada no dia seguinte com cartões novos ainda não revisados: esses cartões não consumiram o limite de novos e voltam a ser elegíveis (D-007).
- Alteração do tamanho da lição com uma lição em andamento: vale a partir da próxima lição.
- Cartão marcado Errei várias vezes seguidas na mesma lição: volta a cada passo curto vencido enquanto a lição está em andamento, e não impede a conclusão (D-004).

## Requisitos funcionais

- **RF-001:** O servidor deverá montar a lição com cartões ativos devidos (vencimento antes da próxima virada das 4h no fuso do estudante), ordenados do vencimento mais antigo ao mais recente, seguidos de cartões novos na ordem de entrada, até o tamanho da lição em cartões distintos (deriva de RN-19 e RN-26 da base).
- **RF-002:** A quantidade de cartões novos revisados pela primeira vez no dia de estudo não deverá ultrapassar o limite de novos por dia do estudante. Um cartão novo só conta no limite quando é revisado pela primeira vez; entrar numa lição não consome o limite (deriva de RN-20 da base; D-007).
- **RF-003:** O verso só deverá ser enviado ao navegador quando o estudante pedir a revelação, e uma avaliação sem revelação naquela apresentação deverá ser recusada (deriva de RN-08 e CB-22 da base).
- **RF-004:** A autoavaliação deverá oferecer Errei, Difícil, Bom e Fácil para todos os cartões, correspondendo às notas Again, Hard, Good e Easy do FSRS (deriva de RN-17 da base).
- **RF-005:** O vencimento de cada cartão deverá ser calculado exclusivamente pelo FSRS, com os parâmetros vigentes do estudante e a variação aleatória leve dos intervalos ligada. Nenhuma regra de lição, meta, XP ou sequência altera esse cálculo (deriva de RN-26 da base).
- **RF-006:** Um cartão agendado para um passo curto deverá voltar na mesma lição quando o passo vencer, enquanto a lição estiver em andamento. A lição termina quando todos os cartões previstos foram revisados ao menos uma vez e nenhum passo curto já vencido aguarda reapresentação. Um cartão cujo passo curto ainda não venceu mantém o vencimento calculado pelo FSRS e entra na próxima lição (D-004; altera a RN-19 da base, deriva de RN-26).
- **RF-007:** Cada revisão deverá ser registrada como evento imutável, com nota, instante, duração (da exibição da frente até a autoavaliação), estado do cartão antes e depois e versão dos parâmetros usada (deriva de RN-17 da base; D-006).
- **RF-008:** Cada revisão enviada deverá carregar um identificador gerado no cliente. O reenvio com o mesmo identificador e o mesmo conteúdo devolve o resultado original; com conteúdo diferente, gera conflito (deriva de RN-10 da base).
- **RF-009:** Ao marcar Errei, o sistema deverá exibir a explicação do cartão, quando existir, e o acesso à evidência, sem nova chamada à IA (deriva de RN-16 e RF-23 da base).
- **RF-010:** A trilha deverá exibir os nós das lições concluídas, o nó atual e o próximo passo, e acender o nó quando a lição for concluída (deriva de RN-19 e RF-08 da base).
- **RF-011:** Uma lição interrompida deverá permanecer em andamento e ser retomada no ponto em que parou, dentro do mesmo dia de estudo. Uma lição aberta de um dia de estudo anterior deverá ser encerrada sem acender o nó, e uma nova lição deverá ser montada (deriva de CB-28 da base; D-005).
- **RF-012:** Depois de concluída uma lição, o estudante poderá iniciar lições extras enquanto houver cartões disponíveis. Cartões que ainda não venceram nunca entram em lições (deriva de RN-19 e RN-26 da base).
- **RF-013:** Sem cartões disponíveis, o sistema não deverá criar lição, e deverá exibir o instante do próximo vencimento no fuso do estudante (deriva de CB-13 e CB-30 da base).
- **RF-014:** O fechamento da lição deverá mostrar as revisões feitas e os cartões que se tornaram dominados nela. XP ganho e sequência entram no fechamento com [006](../006-xp-meta-sequencia/spec.md).
- **RF-015:** A lição deverá ser operável por teclado, com atalho para revelar e atalhos numéricos (1 a 4) para os quatro botões.

## Entidades principais

- **Lição:** sessão montada pelo servidor, com número na trilha, tamanho previsto, cartões previstos, indicação de extra, início e conclusão.
- **Revisão:** evento imutável de autoavaliação, com identificador do cliente.
- **Estado de agendamento do cartão:** estado do FSRS (aprendizado, revisão, reaprendizado), passo, estabilidade, dificuldade, vencimento e última revisão.
- **Parâmetros de agendamento:** versão vigente dos parâmetros do estudante ([001](../001-conta-acesso/spec.md)).

## Critérios de sucesso

- **CS-001:** Para uma sequência fixa de revisões de referência, os vencimentos calculados coincidem com os da biblioteca FSRS executada isoladamente com os mesmos parâmetros e a mesma semente.
- **CS-002:** Em 100% dos testes de reenvio e de duas abas, cada revisão produz um único efeito.
- **CS-003:** Em 100% dos testes, nenhum cartão com vencimento posterior à próxima virada das 4h aparece numa lição.
- **CS-004:** Uma lição de 10 cartões pode ser feita inteira só com o teclado, e cada transição de cartão ocorre em até 300 ms no percentil 95 no ambiente local.

## Requisitos de qualidade

- **RQ-001:** Revisões e seus efeitos permanecem consistentes sob reenvio, concorrência e falhas recuperáveis (RQ-02 da base).
- **RQ-002:** Instantes são guardados em UTC; o dia de estudo vira às 4h no fuso do estudante (RN-15 da base).
- **RQ-003:** A lição e a trilha atendem WCAG 2.2 AA, funcionam a partir de 320 px, anunciam discretamente o resultado a tecnologias assistivas e respeitam a preferência por movimento reduzido.
- **RQ-004:** Cada revisão é reproduzível a partir da versão dos parâmetros registrada.

## Suposições e dependências

- **Dependência:** [001-conta-acesso](../001-conta-acesso/spec.md) (preferências e parâmetros) e [003-cartoes-manuais](../003-cartoes-manuais/spec.md) (cartões ativos). A explicação e a evidência de cartões gerados dependem de [004](../004-geracao-cartoes/spec.md), mas podem ser testadas com dados fictícios.

## Esclarecimentos

### Sessão de 12/10/2026 ([registro](../../prompts/2026-10-12-esclarecimento-specs-mvp.md))

- **E19:** O último cartão marcado Errei obriga a esperar o passo curto? → Não. A lição termina quando todos os previstos foram revisados ao menos uma vez; o cartão em passo curto vence no instante calculado e entra na próxima lição (D-004).
- **E20:** O que acontece com uma lição deixada aberta de um dia de estudo anterior? → É encerrada sem acender o nó, e uma nova lição é montada (D-005).
- **E21:** A duração da revisão e a meta de 300 ms por transição estão confirmadas? → Sim (D-006).

### Revisão pelo checklist de 12/10/2026 ([registro](../../prompts/2026-10-12-revisao-requisitos-specs-mvp.md))

- **R6:** Quando um cartão novo passa a contar no limite de novos por dia? → Quando é revisado pela primeira vez (D-007).

## Questões abertas

- **Q-001:** Composição visual da trilha: densidade de nós, marcos periódicos e comportamento no celular ([UI-05](../../base-specs/design.md#12-pendências-de-design)). Não muda o comportamento desta spec, mas precisa estar definida antes da implementação da interface da US3. — **Responsável:** equipe — **Prazo:** 14/10/2026, antes da apresentação do MVP (meta da equipe: 15/10/2026)
- **Q-002:** EX-05 (níveis de dificuldade). A equipe propõe exibir a dificuldade calculada pelo FSRS em três faixas, sem permitir escolha nem filtro ([PO-01](../../produto/pauta-po.md#po-01-níveis-de-dificuldade-ex-05)). Até a resposta do PO, esta spec não tem nenhum requisito de dificuldade. — **Responsável:** PO (professor Aldo Nunes) — **Prazo:** próxima review

## Decisões confirmadas

- **D-001:** O FSRS é soberano: só ele calcula o vencimento, e as demais regras se adaptam a ele (RN-26). — **Confirmada por:** Artur Lins (equipe), [registro](../../prompts/2026-10-12-esquema-inicial-banco.md) — **Data:** 12/10/2026
- **D-002:** Tamanho padrão da lição de 10 cartões distintos e limite global de 20 novos por dia ([001](../001-conta-acesso/spec.md), D-001). — **Confirmada por:** Artur Lins (equipe) — **Data:** 12/10/2026
- **D-003:** Um cartão é **dominado** quando sua estabilidade no FSRS é de pelo menos 21 dias. O limiar fica numa configuração versionada (QA-24). — **Confirmada por:** Artur Lins (equipe) — **Data:** 12/10/2026
- **D-004:** A lição termina quando todos os cartões previstos foram revisados ao menos uma vez e nenhum passo curto já vencido aguarda reapresentação; cartões em passo curto ainda não vencido mantêm o vencimento do FSRS e entram na próxima lição. Altera a RN-19 da base, que será atualizada quando esta spec for aprovada. — **Confirmada por:** Artur Lins (equipe), esclarecimento E19 — **Data:** 12/10/2026
- **D-005:** Uma lição deixada aberta de um dia de estudo anterior é encerrada sem acender o nó, e uma nova lição é montada com os cartões disponíveis do dia. — **Confirmada por:** Artur Lins (equipe), esclarecimento E20 — **Data:** 12/10/2026
- **D-006:** A duração de uma revisão vai da exibição da frente até a autoavaliação; meta de até 300 ms por transição de cartão no percentil 95, no ambiente local (CS-004). — **Confirmada por:** Artur Lins (equipe), esclarecimento E21 — **Data:** 12/10/2026
- **D-007:** Um cartão novo conta no limite de novos por dia quando é revisado pela primeira vez; entrar numa lição não consome o limite. — **Confirmada por:** Artur Lins (equipe), revisão R6 — **Data:** 12/10/2026

## Exigências do PO

- **EX-03** (explicação do erro): coberta por US2 e RF-009.
- **EX-05** (dificuldade): Q-002, em pauta com o PO.

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | A explicação exibida é a gerada com o cartão, com evidência; nenhuma nova chamada à IA (RF-009) |
| II Proteção e isolamento | Lições só com cartões do estudante; verso só enviado depois da revelação |
| III Verificação humana | EX-05 fica com o PO (Q-002) |
| IV Servidor autoritativo | Lição, agendamento e revisão no servidor; idempotência (RF-008); eventos imutáveis (RF-007) |
| V Qualidade verificável | CS-001 compara com a biblioteca de referência; RQ-003 |
| VI Entrega incremental | US1 demonstrável com cartões manuais, sem IA |
| VII Rastreabilidade | IDs da base citados; sessão registrada |
