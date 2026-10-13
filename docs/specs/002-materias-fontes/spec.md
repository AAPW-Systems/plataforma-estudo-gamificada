# Especificação: matérias, envio e processamento de fontes

**Identificador:** 002-materias-fontes
**Estágio:** MVP
**Funcionalidade do backlog:** [F-02](../../produto/backlog.md#funcionalidades-candidatas) e [F-03](../../produto/backlog.md#funcionalidades-candidatas), parte do MVP (os formatos e o envio múltiplo do final acadêmico estão em [009-formatos-fontes](../009-formatos-fontes/spec.md); a indexação, em [014-chat-fontes](../014-chat-fontes/spec.md))
**Criada em:** 12/10/2026
**Status:** Aprovada para planejamento em 12/10/2026 por Artur Lins (equipe)
**Origem:** backlog, [base de especificação](../../base-specs/spec.md) (HU-02, HU-03, HU-12, HU-13, RF-03, RF-04, RF-05, RF-06, RF-20, RN-02, RN-03, RN-14, RN-23, CB-04, CB-16, CB-23, CB-27) e decisões da [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante individual, com fontes próprias de várias matérias.
**Situação:** o estudante tem PDFs, anotações e textos de várias disciplinas e quer estudá-los com cartões.
**Problema observável:** os materiais ficam espalhados, e o estudante não sabe se um arquivo pode ser aproveitado até tentar.
**Resultado esperado:** o estudante organiza os estudos em matérias, envia uma fonte para a matéria, vê o processamento até a fonte ficar pronta para gerar cartões e, quando quiser, exclui a fonte ou a matéria sabendo exatamente o que será perdido.
**Alternativa atual:** pastas no próprio dispositivo, sem ligação entre o material e o que foi estudado.

## Escopo

### Incluído

- Criar, listar, renomear e excluir matérias (RN-23).
- Enviar uma fonte por vez a uma matéria: PDF com camada de texto, TXT ou Markdown, de até 2 MB (RN-02).
- Validar o arquivo antes de processá-lo: extensão, tipo real do conteúdo, tamanho e integridade.
- Processar a fonte em segundo plano, com estados visíveis (`pendente`, `processando`, `concluido`, `falhou`) e nova tentativa após falha técnica (RN-03).
- Extrair o texto e dividi-lo em trechos, guardando a página quando ela for conhecida (RF-06, parte do MVP).
- Listar as fontes da matéria (acervo), consultar os dados de cada uma e renomear o título (D-005).
- Excluir uma fonte definitivamente, com o impacto exibido e a escolha sobre os cartões aceitos (RN-14).
- Excluir uma matéria definitivamente, em cascata (D-002).
- Cotas por estudante (D-003).

### Fora do escopo

- Formatos SRT, VTT e DOCX e envio de mais de um arquivo: final acadêmico, em [009-formatos-fontes](../009-formatos-fontes/spec.md).
- Indexação para busca (embeddings e índice textual): final acadêmico, em [014-chat-fontes](../014-chat-fontes/spec.md).
- OCR de PDF digitalizado, XLSX e PPTX: referência pós-acadêmica.
- Arquivar com restauração: "arquivar" significa guardar no acervo, não ocultar (RN-14).
- Mover fontes entre matérias.
- Geração de cartões: [004-geracao-cartoes](../004-geracao-cartoes/spec.md).
- Visualizar ou baixar o arquivo original no MVP (D-007).

## Cenários de usuário e testes

### História de usuário 1 Criar matéria e enviar uma fonte P1

Como estudante, quero criar uma matéria e enviar uma fonte para ela, para ter meu material pronto para virar cartões.

**Motivo da prioridade:** é o primeiro passo da jornada principal. Sem fonte processada, não há geração de cartões.
**Teste independente:** criar a matéria "Biologia", enviar um PDF fictício com texto e acompanhar a fonte até `concluido`, com trechos e páginas; enviar um PDF sem texto e confirmar a recusa explicada.

**Cenários de aceitação**

1. **Dado** um estudante autenticado, **quando** ele cria a matéria "Biologia", **então** ela aparece na lista de matérias, vazia, com a ação de enviar a primeira fonte.
2. **Dado** uma matéria, **quando** o estudante envia um PDF com texto de 1 MB e título "Citologia", **então** a fonte aparece no acervo com o estado `pendente` e passa por `processando` até `concluido`, sem recarregar a página manualmente.
3. **Dado** uma fonte `concluido`, **quando** o estudante consulta a fonte, **então** vê título, nome do arquivo, tipo, tamanho, data do envio, número de páginas (quando conhecido) e quantidade de trechos.
4. **Dado** um arquivo de 3 MB, ou com extensão diferente do conteúdo real, ou corrompido, **quando** o estudante tenta enviá-lo, **então** o envio é recusado com uma explicação específica e nada é guardado.
5. **Dado** um PDF sem camada de texto, **quando** o processamento não encontra texto extraível, **então** a fonte fica `falhou` com a explicação de que PDFs digitalizados não são aceitos, sem oferecer nova tentativa (CB-23).
6. **Dado** uma falha técnica no processamento, **quando** o estudante pede nova tentativa, **então** o processamento recomeça sem duplicar trechos.
7. **Dado** um arquivo com conteúdo idêntico ao de uma fonte já existente na matéria, **quando** o estudante tenta enviá-lo, **então** o envio é recusado com a mensagem "Esta fonte já está nesta matéria" e o título da fonte existente (D-004).
8. **Dado** uma fonte com pouco texto extraível (por exemplo, um parágrafo), **quando** o processamento termina, **então** ela chega a `concluido`; a eventual falta de conteúdo para gerar cartões é tratada na geração (D-006).

### História de usuário 2 Excluir uma fonte decidindo sobre os cartões P2

Como estudante, quero excluir uma fonte de vez e decidir o que acontece com os cartões dela, para manter meu acervo limpo sem perder o que já estudei.

**Motivo da prioridade:** é uma ação destrutiva sobre o histórico do estudante (Princípio III). Ela só faz sentido depois que existem cartões, mas precisa estar pronta no MVP.
**Teste independente:** com uma fonte que tem 3 cartões aceitos e 2 aguardando revisão, abrir a exclusão, conferir o impacto, escolher "Manter os cartões" e confirmar que os 3 continuam nas lições com "Fonte apagada", e que os 2 aguardando revisão sumiram; repetir com "Excluir os cartões junto".

**Cenários de aceitação**

1. **Dado** uma fonte com cartões, **quando** o estudante pede para excluí-la, **então** um diálogo mostra o título, o caráter definitivo, a quantidade de cartões aceitos e de cartões aguardando revisão, e as opções "Manter os cartões" e "Excluir os cartões junto".
2. **Dado** a opção "Manter os cartões", **quando** o estudante confirma, **então** o arquivo e os trechos são apagados, os cartões aceitos continuam ativos com "Fonte apagada" e a descrição da origem, perdem o selo de verificado e mantêm o histórico de revisão (RN-14).
3. **Dado** a opção "Excluir os cartões junto", **quando** o estudante confirma, **então** os cartões da fonte são apagados, mas as revisões já registradas, o XP e a sequência permanecem.
4. **Dado** qualquer uma das opções, **quando** a exclusão termina, **então** os cartões aguardando revisão daquela fonte foram apagados.
5. **Dado** cartões criados pelo estudante que citam a fonte apenas como referência, **quando** a fonte é excluída com qualquer uma das opções, **então** esses cartões são sempre mantidos, com "Fonte apagada" e a descrição da origem; o diálogo mostra a quantidade deles separadamente (D-009).
6. **Dado** o diálogo aberto, **quando** o estudante cancela, **então** nada muda.

### História de usuário 3 Organizar matérias e fontes P3

Como estudante, quero renomear e excluir matérias e renomear fontes, para manter meus estudos organizados.

**Motivo da prioridade:** criar matérias já cobre a jornada principal; renomear e excluir são manutenção.
**Teste independente:** renomear uma matéria, tentar repetir um nome existente e excluir uma matéria com fontes e cartões, conferindo o impacto e a confirmação pelo nome.

**Cenários de aceitação**

1. **Dado** uma matéria, **quando** o estudante a renomeia para um nome livre, **então** o novo nome aparece em todas as telas.
2. **Dado** um nome que o estudante já usa em outra matéria (sem diferenciar maiúsculas e minúsculas), **quando** ele tenta usá-lo, **então** a operação é recusada com explicação.
3. **Dado** uma matéria com fontes e cartões, **quando** o estudante pede para excluí-la, **então** um diálogo mostra a quantidade de fontes, cartões ativos e cartões aguardando revisão que serão apagados, e só habilita a exclusão depois que o estudante digita o nome da matéria.
4. **Dado** a confirmação, **quando** a exclusão termina, **então** a matéria, as fontes, os trechos e os cartões são apagados, enquanto revisões, XP e sequência permanecem.
5. **Dado** uma fonte, **quando** o estudante renomeia o título para um valor de 1 a 120 caracteres, **então** o novo título aparece no acervo, e a descrição da origem já copiada nos cartões não muda (D-005).

## Casos de borda

- Envio interrompido no meio: o arquivo incompleto não é processado nem aparece no acervo (CB-04).
- Fonte excluída durante o processamento: o processamento é interrompido e nenhum trecho dela permanece (CB-16).
- Matéria excluída com fontes em processamento ou com geração em andamento: mesmo comportamento de CB-16 para cada fonte.
- Exclusão de fonte ou de matéria com cartões numa lição aberta: as revisões já registradas permanecem, e os cartões apagados deixam de ser apresentados (CB-27).
- Arquivo vazio, TXT com codificação inválida, PDF protegido por senha.
- Arquivo cujo nome tem caminhos, caracteres de controle ou mais de 255 caracteres: o nome é só exibido, nunca usado para guardar o arquivo.
- Mesmo arquivo enviado duas vezes à mesma matéria: recusado (D-004). O mesmo arquivo em matérias diferentes é aceito.
- Dois envios simultâneos do mesmo arquivo à mesma matéria: no máximo um é aceito.
- Cota atingida: 50 matérias, 30 fontes na matéria ou 100 MB no total. Fontes com `falhou` ocupam a cota até serem excluídas (D-010).
- Dois envios simultâneos que ultrapassariam a cota juntos: no máximo um é aceito.
- Texto da fonte com instruções direcionadas à IA: é guardado como conteúdo comum (CB-15; o tratamento na geração está em [004](../004-geracao-cartoes/spec.md)).

## Requisitos funcionais

- **RF-001:** O estudante deverá conseguir criar, listar, renomear e excluir matérias, com nome de 1 a 60 caracteres, sem espaços nas extremidades e único por estudante sem diferenciar maiúsculas e minúsculas (deriva de RN-23 e RF-20 da base).
- **RF-002:** A lista de matérias deverá mostrar, para cada uma, o nome, a quantidade de fontes, de cartões ativos e de cartões aguardando revisão.
- **RF-003:** O estudante deverá conseguir enviar uma fonte por vez a uma matéria, com título de 1 a 120 caracteres; se o título não for informado, o sistema usará o nome do arquivo sem a extensão, truncado em 120 caracteres (deriva de RF-03 da base).
- **RF-004:** O sistema deverá aceitar apenas PDF com camada de texto, TXT e Markdown de até 2 MB, verificando extensão, tipo real do conteúdo, tamanho e integridade antes do processamento, e recusar os demais com uma explicação específica (deriva de RN-02 da base).
- **RF-005:** O sistema deverá processar a fonte em segundo plano e exibir os estados `pendente`, `processando`, `concluido` e `falhou`, atualizados sem ação manual do estudante (deriva de RN-03 e RF-05 da base).
- **RF-006:** O processamento deverá extrair o texto, dividi-lo em trechos ordenados e guardar a página de cada trecho somente quando ela for conhecida (deriva de RF-06 e RN-05 da base).
- **RF-007:** O sistema deverá distinguir, na mensagem ao estudante, falha técnica (com nova tentativa) de conteúdo sem texto extraível (sem nova tentativa).
- **RF-008:** Uma nova tentativa ou um reprocessamento não deverá duplicar trechos nem alterar cartões já aceitos (deriva de RN-10 da base).
- **RF-009:** O estudante deverá conseguir listar as fontes da matéria e consultar os dados de cada uma, conforme US1, cenário 3 (deriva de RF-04 da base).
- **RF-010:** A exclusão de uma fonte deverá exibir o impacto antes da confirmação e oferecer "Manter os cartões" ou "Excluir os cartões junto", conforme RN-14 da base. As opções valem para os cartões gerados da fonte; cartões criados pelo estudante que só a citam como referência são sempre mantidos (D-009).
- **RF-011:** A exclusão de uma matéria deverá exibir o impacto, exigir que o estudante digite o nome dela e apagar fontes, trechos e cartões, preservando revisões, XP e sequência (D-002).
- **RF-012:** O sistema deverá recusar com explicação a criação de matéria ou o envio de fonte que ultrapasse as cotas de D-003. Fontes com `falhou` ocupam a cota até serem excluídas, e o acervo oferece a ação de excluí-las (D-010).
- **RF-013:** A exclusão de uma fonte em processamento deverá interromper o processamento sem deixar trechos (deriva de CB-16 da base).
- **RF-014:** O sistema deverá recusar o envio de um arquivo com conteúdo idêntico ao de uma fonte existente na mesma matéria, informando o título da fonte existente (D-004).
- **RF-015:** O estudante deverá conseguir renomear o título de uma fonte (1 a 120 caracteres), sem alterar a descrição da origem já copiada nos cartões (D-005).
- **RF-016:** O processamento deverá aceitar qualquer fonte válida com texto extraível, sem quantidade mínima de texto (D-006).

## Entidades principais

- **Matéria:** contêiner do estudante, com nome único.
- **Fonte:** arquivo enviado a uma matéria, com título, nome do arquivo, tipo real, tamanho, data, estado do processamento, motivo da falha e número de páginas (quando conhecido).
- **Trecho:** parte ordenada do texto de uma fonte, com a página quando conhecida.

## Critérios de sucesso

- **CS-001:** Com um conjunto de 10 arquivos fictícios válidos (PDF, TXT e MD), todas as fontes chegam a `concluido`, e em todos os PDFs as páginas dos trechos conferem com o arquivo.
- **CS-002:** Com um conjunto de 10 arquivos inválidos (acima do tamanho, tipo trocado, vazio, corrompido, PDF sem texto, PDF com senha), nenhum gera trecho, e todos recebem uma explicação específica.
- **CS-003:** Uma fonte de 2 MB em PDF chega a `concluido` em até 60 segundos no ambiente local.
- **CS-004:** Em todos os testes de exclusão, as contagens exibidas no diálogo coincidem com o que é efetivamente apagado.

## Requisitos de qualidade

- **RQ-001:** O nome enviado pelo estudante nunca compõe o local de armazenamento do arquivo.
- **RQ-002:** Logs não registram o conteúdo das fontes.
- **RQ-003:** Fontes, trechos e matérias respeitam o isolamento entre estudantes ([001](../001-conta-acesso/spec.md), RF-007).
- **RQ-004:** Os diálogos de exclusão operam por teclado, com foco controlado e ação destrutiva visualmente distinta, sem depender só de cor (WCAG 2.2 AA).
- **RQ-005:** Os limites (tamanho, formatos e cotas) são configuráveis por ambiente e são os mesmos na interface e na API.

## Suposições e dependências

- **Dependência:** [001-conta-acesso](../001-conta-acesso/spec.md).
- **Dependência:** as contagens de cartões no diálogo de exclusão só são diferentes de zero depois de [003](../003-cartoes-manuais/spec.md) e [004](../004-geracao-cartoes/spec.md). A US2 pode ser testada com cartões criados diretamente nos dados de teste.

## Esclarecimentos

### Sessão de 12/10/2026 ([registro](../../prompts/2026-10-12-esclarecimento-specs-mvp.md))

- **E6:** O que acontece com um arquivo idêntico enviado de novo à mesma matéria? → É recusado, com o título da fonte existente (D-004).
- **E7:** O título da fonte pode ser renomeado? → Sim; a descrição da origem já copiada nos cartões não muda (D-005).
- **E8:** Existe texto mínimo para aceitar uma fonte? → Não; a insuficiência é tratada na geração (D-006).
- **E9:** O estudante abre ou baixa o arquivo original no MVP? → Não (D-007).
- **E10:** A meta de 60 s para um PDF de 2 MB está confirmada? → Sim, medida no ambiente local do quickstart (D-008).

### Revisão pelo checklist de 12/10/2026 ([registro](../../prompts/2026-10-12-revisao-requisitos-specs-mvp.md))

- **R1:** "Excluir os cartões junto" apaga também os cartões criados pelo estudante que só citam a fonte como referência? → Não; eles são sempre mantidos com "Fonte apagada", e o diálogo os conta separadamente (D-009).
- **R2:** Uma fonte com `falhou` ocupa a cota? → Sim, até ser excluída (D-010).

## Questões abertas

- **Q-001:** ~~Abrir ou baixar o arquivo original no MVP?~~ Resolvida em 12/10/2026 (D-007).
- **Q-002:** ~~Arquivo idêntico enviado de novo à mesma matéria?~~ Resolvida em 12/10/2026 (D-004).

Nenhuma questão aberta impede o planejamento.

## Decisões confirmadas

- **D-001:** Os formatos e os limites do MVP são os da RN-02 da base (PDF com texto, TXT e MD, até 2 MB, um arquivo por envio). — **Confirmada por:** equipe, na [visão](../../produto/visao.md#matérias-e-fontes-f-02-f-03) — **Data:** 29/09/2026
- **D-002:** A exclusão de uma matéria é definitiva e em cascata (fontes, trechos e cartões), com o impacto exibido e a confirmação pelo nome digitado. Revisões, XP e sequência são preservados. Não há opção de manter os cartões, porque todo cartão pertence a uma matéria. — **Confirmada por:** Artur Lins (equipe) — **Data:** 12/10/2026
- **D-003:** Cotas por estudante: até 50 matérias, até 30 fontes por matéria e até 100 MB de fontes no total, configuráveis por ambiente. — **Confirmada por:** Artur Lins (equipe) — **Data:** 12/10/2026
- **D-004:** Um arquivo com conteúdo idêntico ao de uma fonte existente na mesma matéria é recusado, com o título da fonte existente. — **Confirmada por:** Artur Lins (equipe), esclarecimento E6 — **Data:** 12/10/2026
- **D-005:** O título da fonte pode ser renomeado; a descrição da origem copiada nos cartões não muda. — **Confirmada por:** Artur Lins (equipe), esclarecimento E7 — **Data:** 12/10/2026
- **D-006:** Qualquer fonte válida com texto extraível é aceita; a falta de conteúdo para gerar cartões é tratada na geração ([004](../004-geracao-cartoes/spec.md), US4). — **Confirmada por:** Artur Lins (equipe), esclarecimento E8 — **Data:** 12/10/2026
- **D-007:** O MVP não permite abrir nem baixar o arquivo original; a evidência mostra o trecho. — **Confirmada por:** Artur Lins (equipe), esclarecimento E9 — **Data:** 12/10/2026
- **D-008:** Meta de até 60 segundos para uma fonte de 2 MB em PDF chegar a `concluido`, medida no ambiente local do quickstart (CS-003). — **Confirmada por:** Artur Lins (equipe), esclarecimento E10 — **Data:** 12/10/2026
- **D-009:** Na exclusão de uma fonte, as opções "Manter os cartões" e "Excluir os cartões junto" valem para os cartões gerados da fonte; cartões criados pelo estudante que só a citam como referência são sempre mantidos, com "Fonte apagada", e contados separadamente no diálogo. — **Confirmada por:** Artur Lins (equipe), revisão R1 — **Data:** 12/10/2026
- **D-010:** Fontes com `falhou` ocupam a cota de fontes e de armazenamento até serem excluídas; o acervo oferece a ação de excluí-las. — **Confirmada por:** Artur Lins (equipe), revisão R2 — **Data:** 12/10/2026

## Exigências do PO

Nenhuma exigência (EX-01 a EX-05) toca esta funcionalidade diretamente. As fontes processadas aqui são a base de EX-02 e EX-03 ([004](../004-geracao-cartoes/spec.md)).

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | Os trechos guardam a página só quando conhecida (RF-006) |
| II Proteção e isolamento | RQ-001 a RQ-003; conteúdo da fonte tratado como dado |
| III Verificação humana | Exclusões com impacto e confirmação explícita (US2 e US3); decisões do esclarecimento registradas pela equipe (D-004 a D-008) |
| IV Servidor autoritativo | Estados do processamento vêm do servidor; reprocessamento sem duplicar (RF-008) |
| V Qualidade verificável | CS-001 a CS-004, com conjuntos de arquivos fictícios |
| VI Entrega incremental | US1 demonstrável sozinha |
| VII Rastreabilidade | IDs da base citados; sessão registrada |
