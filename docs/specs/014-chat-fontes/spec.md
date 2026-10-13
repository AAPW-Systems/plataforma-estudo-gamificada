# Especificação: chat com as fontes da matéria

**Identificador:** 014-chat-fontes
**Estágio:** Final acadêmico
**Funcionalidade do backlog:** [F-06](../../produto/backlog.md#funcionalidades-candidatas) e o incremento de [F-03](../../produto/backlog.md#funcionalidades-candidatas) do final acadêmico (indexação das fontes para busca)
**Criada em:** 12/10/2026
**Status:** Rascunho
**Origem:** backlog, [visão](../../produto/visao.md#chat-f-06-final-acadêmico-provisório) (decisões provisórias), [base de especificação](../../base-specs/spec.md) (HU-18, RF-06, RF-25, RN-01, RN-03, RN-04, RN-05, RN-14, RN-24, RQ-01, RQ-10, CS-06, CB-15), [QA-16](../../produto/pendencias.md#qa-16-escopo-do-chat) e [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante com várias fontes numa matéria.
**Situação:** o estudante tem uma dúvida pontual ("qual a diferença entre mitose e meiose?") e não lembra em qual fonte está a resposta.
**Problema observável:** procurar em várias fontes é lento, e uma IA genérica responde com conteúdo que pode não estar no material da disciplina.
**Resultado esperado:** ao lado das fontes da matéria, o estudante pergunta em linguagem natural e recebe uma resposta baseada apenas nas fontes dele, com citações que abrem o trecho e a página. Quando as fontes não sustentam a resposta, o chat diz isso.
**Alternativa atual:** buscar palavra por palavra em cada arquivo ou perguntar a uma IA genérica, sem citação.

## Escopo

### Incluído

- Indexação das fontes para busca por significado e por palavras (busca híbrida); `concluido` passa a incluir a indexação (RN-03).
- Indexação das fontes já existentes no momento da implantação.
- Chat ao lado das fontes, na página da matéria, perguntando sobre a matéria (padrão) ou sobre todas as matérias (Q-001).
- Resposta exibida à medida que é gerada.
- Citações clicáveis que abrem o trecho, com a página (ou o intervalo de tempo, [009](../009-formatos-fontes/spec.md)) quando conhecida.
- Resposta explícita de "não encontrei isso nas suas fontes" quando faltar evidência.
- Histórico de conversas salvo: listar, abrir, renomear e excluir conversas.
- Limite técnico de uso por estudante.
- Avaliação da qualidade contra uma solução de referência que usa só busca textual (RQ-10, CS-06).

### Fora do escopo

- Tira-dúvidas a partir de um cartão: [015-tira-duvidas-cartao](../015-tira-duvidas-cartao/spec.md).
- Criar flashcard a partir de uma resposta (F-15).
- Pesquisa externa (EX-01, PO-02).
- Enviar arquivos ou imagens pelo chat.
- Compartilhar conversas.

## Cenários de usuário e testes

### História de usuário 1 Perguntar às fontes e ver as citações P1

Como estudante, quero perguntar sobre minhas fontes e ver de onde veio cada parte da resposta, para tirar dúvidas confiando no que leio (HU-18).

**Motivo da prioridade:** é a capacidade de RAG avaliada no final acadêmico.
**Teste independente:** com uma matéria de 3 fontes fictícias indexadas e o provedor simulado, fazer uma pergunta respondível e conferir as citações; fazer uma pergunta sem resposta nas fontes e conferir a declaração de ausência.

**Cenários de aceitação**

1. **Dado** uma matéria com fontes indexadas, **quando** o estudante faz uma pergunta cuja resposta está nas fontes, **então** a resposta aparece à medida que é gerada e cita os trechos usados, cada citação com a fonte e a página quando conhecida.
2. **Dado** uma citação, **quando** o estudante a abre, **então** vê o trecho citado e a fonte, com a página ou o intervalo de tempo quando conhecido.
3. **Dado** uma pergunta sem resposta nas fontes, **quando** o chat responde, **então** declara que não encontrou a informação nas fontes da matéria, sem responder com conhecimento geral.
4. **Dado** uma pergunta que as fontes respondem em parte, **quando** o chat responde, **então** responde só a parte sustentada, com citação, e declara o que não encontrou.
5. **Dado** fontes que se contradizem sobre o ponto perguntado, **quando** o chat responde, **então** apresenta as duas posições com as respectivas citações, sem escolher uma como fato.
6. **Dado** uma fonte com instruções direcionadas à IA, **quando** um trecho dela é recuperado, **então** a instrução é tratada como conteúdo e não altera o comportamento do chat (CB-15).

### História de usuário 2 Ter as fontes indexadas automaticamente P1

Como estudante, quero que minhas fontes fiquem prontas para o chat sem nenhuma ação a mais, para perguntar logo depois de enviar.

**Motivo da prioridade:** sem indexação não há chat; faz parte do critério de pronto da US1.
**Teste independente:** enviar uma fonte nova e conferir que ela só chega a `concluido` depois de indexada; conferir que as fontes enviadas antes da implantação também ficam indexadas.

**Cenários de aceitação**

1. **Dado** uma fonte enviada, **quando** o processamento termina, **então** ela só aparece como `concluido` depois de extraída, dividida em trechos e indexada.
2. **Dado** uma falha no serviço de indexação, **quando** o processamento é executado, **então** a fonte fica `falhou` com a opção de tentar de novo, e os trechos já extraídos não são duplicados.
3. **Dado** fontes enviadas antes da implantação do chat, **quando** a implantação é feita, **então** elas são indexadas em segundo plano, e o chat avisa enquanto uma fonte da matéria ainda não estiver pronta.
4. **Dado** uma fonte excluída, **quando** a exclusão termina, **então** os dados de indexação dela também são apagados, e ela nunca mais aparece em respostas (RN-14).

### História de usuário 3 Retomar conversas P2

Como estudante, quero encontrar minhas conversas anteriores, para continuar uma dúvida sem repetir o contexto.

**Motivo da prioridade:** continuidade; a US1 entrega valor numa conversa única.
**Teste independente:** criar duas conversas, sair, voltar, abrir a primeira, continuar, renomear e excluir a segunda.

**Cenários de aceitação**

1. **Dado** conversas anteriores na matéria, **quando** o estudante abre o chat, **então** vê a lista das conversas, da mais recente para a mais antiga, e pode abrir qualquer uma.
2. **Dado** uma conversa aberta, **quando** o estudante faz uma nova pergunta, **então** o chat considera as mensagens anteriores da conversa, mas continua respondendo só com base nas fontes.
3. **Dado** uma conversa que cita uma fonte depois excluída, **quando** o estudante a abre, **então** as citações dessa fonte mostram "Fonte apagada", com a descrição da origem e sem o trecho (RN-14).
4. **Dado** uma conversa, **quando** o estudante a exclui e confirma, **então** ela e suas mensagens são apagadas.

## Casos de borda

- Pergunta vazia, só com espaços ou acima de 2.000 caracteres.
- Matéria sem fontes indexadas: o chat explica que é preciso enviar uma fonte e não chama a IA.
- Limite de uso atingido: a pergunta é recusada com a indicação de quando o limite volta.
- Provedor de IA ou de busca indisponível no meio da resposta: a resposta é marcada como interrompida, sem ser apresentada como completa, e o estudante pode tentar de novo.
- Conexão interrompida durante a resposta: ao voltar, a conversa mostra a resposta como concluída ou interrompida, nunca pela metade como se estivesse completa.
- Pergunta que tenta obter dados de outro estudante ou as instruções do sistema: a resposta usa só as fontes do estudante e não revela instruções internas.
- Mesma pergunta enviada duas vezes (clique duplo): uma única resposta.
- Fonte excluída enquanto uma resposta é gerada: a resposta não cita a fonte depois de excluída.

## Requisitos funcionais

- **RF-001:** O processamento de uma fonte deverá incluir a indexação para busca híbrida, e a fonte só deverá ficar `concluido` depois de indexada (deriva de RN-03 e RF-06 da base).
- **RF-002:** A busca deverá considerar somente trechos de fontes do estudante autenticado e do escopo escolhido (a matéria ou todas as matérias), nunca de outros estudantes (deriva de RN-01 da base).
- **RF-003:** A resposta deverá usar somente os trechos recuperados das fontes do estudante, e toda afirmação deverá citar ao menos um trecho (deriva de RN-04 e RN-24 da base).
- **RF-004:** Sem evidência suficiente, o chat deverá declarar que não encontrou a informação nas fontes e não deverá responder com conhecimento geral (deriva de RN-24 da base).
- **RF-005:** Cada citação deverá identificar a fonte e o trecho e, somente quando conhecida, a página ou o intervalo de tempo, e abrir o trecho citado (deriva de RN-05 e RN-24 da base).
- **RF-006:** A resposta deverá ser exibida à medida que é gerada, e uma resposta interrompida deverá ser marcada como tal.
- **RF-007:** O estudante deverá conseguir listar, abrir, continuar, renomear e excluir as próprias conversas.
- **RF-008:** Citações a fontes excluídas deverão exibir "Fonte apagada" com a descrição da origem, sem o trecho (deriva de RN-14 da base).
- **RF-009:** A exclusão de uma fonte deverá apagar seus dados de indexação (deriva de RN-14 da base).
- **RF-010:** O sistema deverá aplicar um limite de uso do chat por estudante, configurável por ambiente (Q-002).
- **RF-011:** O conteúdo das fontes recuperado pela busca deverá ser tratado como dado e nunca como instrução (deriva de CB-15 da base).
- **RF-012:** Antes do primeiro uso do chat, o sistema deverá informar que trechos das fontes e as perguntas são enviados a provedores externos de IA e de busca.
- **RF-013:** Cada resposta deverá registrar o provedor, o modelo, a versão das instruções e os trechos recuperados, sem guardar o conteúdo das perguntas e respostas nos logs nem nos rastros de observabilidade.

## Entidades principais

- **Índice do trecho:** representação do trecho para a busca por significado e por palavras, com o modelo e a versão usados.
- **Conversa:** título, matéria (ou todas), criação e última atividade.
- **Mensagem:** pergunta ou resposta, situação (concluída ou interrompida) e instante.
- **Citação:** vínculo entre uma resposta e um trecho, com a cópia da descrição da origem.

## Critérios de sucesso

- **CS-001:** No conjunto de avaliação revisado por pessoa (pelo menos 30 perguntas, com respondíveis, sem resposta, parciais, contraditórias e adversariais), todas as citações das respostas apontam para trechos que sustentam a afirmação citada (meta em Q-003).
- **CS-002:** Em 100% das perguntas sem resposta nas fontes, o chat declara a ausência e não apresenta afirmação como fato.
- **CS-003:** A busca híbrida supera a solução de referência só com busca textual na métrica de recuperação definida no plano, no mesmo conjunto de perguntas (CS-06 e RQ-10 da base).
- **CS-004:** Em 100% dos testes de isolamento, nenhum trecho de outro estudante é recuperado ou citado.
- **CS-005:** O primeiro trecho da resposta aparece em até 3 segundos no percentil 95 na VPS, com o provedor disponível.

## Requisitos de qualidade

- **RQ-001:** As regras do chat não dependem de um provedor ou modelo específico (RQ-05 da base).
- **RQ-002:** O chat atende WCAG 2.2 AA: a resposta em andamento é anunciada de forma discreta, sem anunciar cada palavra, e as citações operam por teclado.
- **RQ-003:** No desktop, o chat fica ao lado das fontes; no celular, em abas, a partir de 320 px.
- **RQ-004:** O conjunto de avaliação registra provedor, modelo, versão das instruções e modelo de busca; trocar qualquer um exige executá-lo de novo.
- **RQ-005:** Mensagens de erro ao estudante não expõem detalhes dos provedores.

## Suposições e dependências

- **Dependência:** [002-materias-fontes](../002-materias-fontes/spec.md) (fontes e trechos) e [004-geracao-cartoes](../004-geracao-cartoes/spec.md) (tela de evidência e aviso de provedor externo).
- **Dependência:** provedores de embeddings e reranking ([DTEC 008](../../research.md#decisão-dtec-008-embeddings-e-reranking)) e framework de agentes ([QA-31](../../produto/pendencias.md#qa-31-framework-de-agentes-do-final-acadêmico)), decididos no plano.
- **Suposição:** as decisões provisórias de QA-16 (histórico salvo, resposta em andamento, citações clicáveis, limite técnico) valem para esta spec até a confirmação em Q-001 e Q-002.
- **Suposição:** o tempo de CS-005 é uma meta proposta pelo agente, a confirmar na revisão da spec.

## Questões abertas

- **Q-001:** Confirmar as decisões provisórias de [QA-16](../../produto/pendencias.md#qa-16-escopo-do-chat): pergunta sobre a matéria (padrão) ou sobre todas, e histórico de conversas salvo. **Recomendação:** confirmar as duas. — **Responsável:** equipe — **Prazo:** 31/10/2026
- **Q-002:** Qual o limite de uso do chat por estudante? **Recomendação:** 50 perguntas por dia de estudo, configurável, com a indicação de quando o limite volta. — **Responsável:** equipe — **Prazo:** 31/10/2026
- **Q-003:** Qual a meta de qualidade das citações no conjunto de avaliação para considerar o chat pronto? **Recomendação:** pelo menos 90% das afirmações das respostas respondíveis sustentadas pela citação, e 0% de respostas com conhecimento externo nas perguntas sem resposta. — **Responsável:** equipe — **Prazo:** 31/10/2026

## Decisões confirmadas

- **D-001:** O chat entra no final acadêmico, ao lado das fontes da matéria, com busca híbrida, reranking, citações e avaliação contra a solução de referência. — **Confirmada por:** equipe, no [backlog](../../produto/backlog.md#final-acadêmico); recorte aprovado ([PO-03](../../produto/pauta-po.md#po-03-novo-recorte-do-mvp)) — **Data:** 12/10/2026

## Exigências do PO

- **EX-04** (explicações com referência): a busca e as citações desta spec são reaproveitadas em [015](../015-tira-duvidas-cartao/spec.md).
- **EX-01** (pesquisa externa): fora do escopo; em pauta com o PO (PO-02).

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | RF-003 a RF-005; US1, cenários 3 a 5; CS-001 e CS-002 |
| II Proteção e isolamento | RF-002, RF-011 a RF-013; CS-004 |
| III Verificação humana | Q-001 a Q-003 ficam com a equipe e o PO |
| IV Servidor autoritativo | Busca e resposta no servidor; resposta interrompida nunca apresentada como completa |
| V Qualidade verificável | Conjunto de avaliação e comparação com a referência (CS-001 a CS-003) |
| VI Entrega incremental | US1 com a US2 como critério de pronto; a US3 amplia |
| VII Rastreabilidade | RF-013; IDs da base citados; sessão registrada |
