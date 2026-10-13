# Especificação: tira-dúvidas a partir de um cartão

**Identificador:** 015-tira-duvidas-cartao
**Estágio:** Final acadêmico
**Funcionalidade do backlog:** [F-16](../../produto/backlog.md#funcionalidades-candidatas)
**Criada em:** 12/10/2026
**Status:** Rascunho
**Origem:** [exigências do PO](../../produto/exigencias_po.md) EX-04 e EX-01, backlog, [visão](../../produto/visao.md#tira-dúvidas-do-flashcard-f-16), [base de especificação](../../base-specs/spec.md) (HU-19, RF-26, RN-04, RN-24), [PO-02](../../produto/pauta-po.md#po-02-pesquisa-externa-ex-01) e [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante no meio de uma lição.
**Situação:** o estudante errou um cartão, leu a explicação curta e ainda não entendeu.
**Problema observável:** para tirar a dúvida, ele precisa sair da lição, procurar nas fontes e perder o ritmo.
**Resultado esperado:** a partir do cartão, sem sair da lição, o estudante abre um tira-dúvidas que já conhece o cartão, faz perguntas e recebe respostas baseadas nas fontes da matéria, com a referência. Depois, volta ao cartão e segue a lição (EX-04).
**Alternativa atual:** a explicação curta ([005](../005-licao-trilha/spec.md)) e, fora da lição, o chat da matéria ([014](../014-chat-fontes/spec.md)).

## Escopo

### Incluído

- Ação secundária "Tirar dúvida" no cartão, durante a lição, depois de revelado o verso.
- Painel de conversa com o cartão (frente, verso, explicação e evidência) como contexto.
- Respostas apenas com base nas fontes da matéria do cartão, com citações, reaproveitando a busca e as regras de [014](../014-chat-fontes/spec.md).
- Retorno à lição no mesmo ponto, sem efeito sobre a revisão e o agendamento.

### Fora do escopo

- Consulta externa (EX-01): em pauta com o PO ([PO-02](../../produto/pauta-po.md#po-02-pesquisa-externa-ex-01)); a equipe propõe retirá-la (Q-001).
- Criar ou editar cartões a partir da conversa (F-15).
- Tira-dúvidas fora da lição (na lista de cartões).

## Cenários de usuário e testes

### História de usuário 1 Tirar uma dúvida sobre o cartão sem sair da lição P1

Como estudante, quero perguntar sobre o cartão que estou revisando e receber a resposta com a referência, para entender o conteúdo sem perder o ritmo da lição (HU-19, EX-04).

**Motivo da prioridade:** é a única história desta spec e atende a uma exigência do PO.
**Teste independente:** numa lição com um cartão gerado de uma fonte fictícia indexada, revelar o verso, abrir o tira-dúvidas, perguntar "por que essa é a resposta?", conferir a resposta com citação e voltar à lição; conferir que o vencimento do cartão e a duração da revisão não mudaram por causa do tira-dúvidas.

**Cenários de aceitação**

1. **Dado** um cartão com o verso revelado, **quando** o estudante escolhe "Tirar dúvida", **então** abre um painel que mostra o cartão como contexto, sem esconder os botões de autoavaliação.
2. **Dado** o painel aberto, **quando** o estudante pergunta sobre o cartão, **então** a resposta usa só as fontes da matéria do cartão e cita os trechos, com a página quando conhecida.
3. **Dado** uma pergunta sem resposta nas fontes, **quando** o tira-dúvidas responde, **então** declara que não encontrou a informação nas fontes, sem usar conhecimento geral.
4. **Dado** o painel aberto, **quando** o estudante o fecha, **então** volta ao mesmo cartão, no mesmo ponto da lição, e pode se autoavaliar normalmente.
5. **Dado** um cartão cuja fonte foi apagada, ou um cartão manual sem fonte, **quando** o estudante abre o tira-dúvidas, **então** a busca usa as demais fontes da matéria. Se a matéria não tiver fontes indexadas, o painel explica que não há fontes para consultar.
6. **Dado** um cartão com o verso ainda não revelado, **quando** o estudante está na frente, **então** a ação "Tirar dúvida" não está disponível, para não entregar a resposta antes da autoavaliação.

## Casos de borda

- Pergunta que pede a resposta de outro cartão da lição: a resposta segue as fontes, sem regra especial.
- Tempo gasto no tira-dúvidas: não entra na duração da revisão nem no tempo dedicado (Q-002).
- Limite de uso atingido: o painel informa, e a lição segue normalmente.
- Provedor indisponível: o painel mostra a falha, e a lição segue normalmente.
- O estudante se autoavalia com o painel aberto: a revisão é registrada normalmente, e o painel se fecha.

## Requisitos funcionais

- **RF-001:** Durante a lição, depois de revelado o verso, o estudante deverá conseguir abrir o tira-dúvidas de um cartão, com o cartão como contexto (deriva de RF-26 da base, EX-04).
- **RF-002:** O tira-dúvidas deverá seguir as regras de [014](../014-chat-fontes/spec.md) RF-002 a RF-006 e RF-010 a RF-013, com o escopo limitado às fontes da matéria do cartão (deriva de RN-24 da base).
- **RF-003:** Abrir, usar ou fechar o tira-dúvidas não deverá alterar a revisão, o agendamento, o XP, a meta nem a sequência (deriva de RN-26 da base).
- **RF-004:** O tempo no tira-dúvidas não deverá entrar na duração da revisão do cartão (Q-002).
- **RF-005:** O tira-dúvidas deverá ser um caminho opcional: a lição deverá continuar operável sem ele, inclusive quando ele estiver indisponível.

## Entidades principais

- **Conversa de tira-dúvidas:** conversa ([014](../014-chat-fontes/spec.md)) ligada a um cartão e à sua matéria.

## Critérios de sucesso

- **CS-001:** Num conjunto de avaliação de pelo menos 15 perguntas sobre cartões (respondíveis, sem resposta e adversariais), as metas de [014](../014-chat-fontes/spec.md) CS-001 e CS-002 são atendidas.
- **CS-002:** Em 100% dos testes, o vencimento do cartão é o mesmo com e sem o uso do tira-dúvidas, para a mesma nota.
- **CS-003:** Em teste guiado com três pessoas, cada uma abre o tira-dúvidas, recebe uma resposta com citação e volta à lição em até 1 minuto, sem ajuda.

## Requisitos de qualidade

- **RQ-001:** O painel opera por teclado, devolve o foco ao cartão ao ser fechado e funciona a partir de 320 px.
- **RQ-002:** As regras de privacidade e de provedor externo de [014](../014-chat-fontes/spec.md) valem aqui.

## Suposições e dependências

- **Dependência:** [014-chat-fontes](../014-chat-fontes/spec.md) (indexação, busca e citações) e [005-licao-trilha](../005-licao-trilha/spec.md) (lição).
- **Dependência:** resposta do PO em [PO-02](../../produto/pauta-po.md#po-02-pesquisa-externa-ex-01).

## Questões abertas

- **Q-001:** EX-01 (pesquisa externa). A equipe propõe retirá-la, por ser incompatível com o Princípio I. Se o PO a mantiver, ela entra como incremento desta spec, com as regras de [QA-27](../../produto/pendencias.md#qa-27-regras-da-consulta-externa) e do Princípio I (acionada a cada pergunta, separada visualmente, com a fonte externa citada, nunca verificada nem indexada). Até a resposta, esta spec não tem nenhum requisito de consulta externa. — **Responsável:** PO (professor Aldo Nunes) — **Prazo:** próxima review
- **Q-002:** O tempo gasto no tira-dúvidas entra no tempo dedicado da evolução ([013](../013-evolucao-completa/spec.md)), separado das revisões? **Recomendação:** não entra no tempo dedicado, para não misturar estudo ativo com leitura. — **Responsável:** equipe — **Prazo:** 31/10/2026
- **Q-003:** As conversas de tira-dúvidas ficam salvas no histórico do chat da matéria, identificadas pelo cartão, ou são descartadas ao fechar? **Recomendação:** ficam salvas, identificadas pelo cartão, porque reaproveitam o histórico de [014](../014-chat-fontes/spec.md) sem custo adicional. — **Responsável:** equipe — **Prazo:** 31/10/2026

## Decisões confirmadas

- **D-001:** O tira-dúvidas é restrito às fontes no final acadêmico e é um caminho opcional, fora do fluxo principal da lição. — **Confirmada por:** equipe, na [visão](../../produto/visao.md#tira-dúvidas-do-flashcard-f-16) — **Data:** 12/10/2026

## Exigências do PO

- **EX-04** (explicações adicionais com referência): coberta por US1, RF-001 e RF-002.
- **EX-01** (pesquisa externa): Q-001, em pauta com o PO.

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | RF-002; a exceção da consulta externa só entra com a resposta do PO (Q-001) |
| II Proteção e isolamento | RQ-002 |
| III Verificação humana | EX-01 fica com o PO (Q-001) |
| IV Servidor autoritativo | RF-003; CS-002 |
| V Qualidade verificável | CS-001 a CS-003 |
| VI Entrega incremental | História única, sobre 005 e 014 |
| VII Rastreabilidade | IDs da base citados; sessão registrada |
