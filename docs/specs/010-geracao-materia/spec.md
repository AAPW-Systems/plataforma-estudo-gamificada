# Especificação: geração para a matéria inteira e quantidade proporcional ao volume

**Identificador:** 010-geracao-materia
**Estágio:** Final acadêmico
**Funcionalidade do backlog:** [F-04](../../produto/backlog.md#funcionalidades-candidatas), incremento do final acadêmico (a geração do MVP está em [004-geracao-cartoes](../004-geracao-cartoes/spec.md))
**Criada em:** 12/10/2026
**Status:** Rascunho
**Origem:** backlog ("avaliação da quantidade gerada em relação ao volume da fonte"), [base de especificação](../../base-specs/spec.md) (RN-22: "o estudante pede cartões de uma fonte ou de uma matéria" e "após o MVP: avaliar se a quantidade gerada é coerente com o volume da fonte"), decisão D-002 de [004](../004-geracao-cartoes/spec.md) e [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante com várias fontes numa matéria.
**Situação:** o estudante quer cartões de toda a matéria antes de uma prova, e as fontes têm tamanhos muito diferentes.
**Problema observável:** no MVP, ele pede fonte por fonte, sempre com até 10 cartões, mesmo quando uma fonte tem 3 páginas e outra tem 80.
**Resultado esperado:** o estudante pede cartões da matéria inteira, e a quantidade proposta acompanha o volume de cada fonte. A equipe mede se essa quantidade é coerente.
**Alternativa atual:** vários pedidos por fonte, com a mesma quantidade para fontes de tamanhos diferentes.

## Escopo

### Incluído

- Pedido de cartões para a matéria inteira, usando todas as fontes `concluido`.
- Quantidade sugerida proporcional ao volume de texto, com teto por pedido; o estudante pode reduzi-la.
- Distribuição dos cartões entre as fontes da matéria, proporcional ao volume de cada uma.
- Avaliação da coerência entre a quantidade gerada e o volume das fontes.
- Todas as regras de [004](../004-geracao-cartoes/spec.md) (validações, revisão dos gerados, resumo, "Gerar mais", falhas) continuam valendo.

### Fora do escopo

- Escolha de assuntos ou capítulos específicos dentro da fonte.
- Cobertura de assuntos e lacunas de material (F-13).
- Níveis de dificuldade (EX-05, PO-01).

## Cenários de usuário e testes

### História de usuário 1 Gerar cartões da matéria inteira P1

Como estudante, quero pedir cartões de todas as fontes de uma matéria de uma vez, para preparar o estudo da matéria inteira.

**Motivo da prioridade:** é o comportamento previsto na RN-22 que ficou fora do MVP.
**Teste independente:** com uma matéria de 3 fontes fictícias `concluido` de volumes diferentes e o provedor simulado, pedir cartões da matéria e conferir que os cartões aguardando revisão vêm das três fontes, na proporção do volume.

**Cenários de aceitação**

1. **Dado** uma matéria com fontes `concluido`, **quando** o estudante pede cartões da matéria, **então** vê a quantidade sugerida, pode reduzi-la e confirma o pedido.
2. **Dado** o pedido confirmado, **quando** a geração termina, **então** os cartões aguardando revisão estão distribuídos entre as fontes na proporção do volume de cada uma, e cada cartão indica a fonte de origem.
3. **Dado** uma matéria com fontes ainda em processamento, **quando** o estudante pede cartões, **então** só as fontes `concluido` entram, e a tela informa quais ficaram de fora.
4. **Dado** uma matéria sem nenhuma fonte `concluido`, **quando** o estudante abre a ação, **então** ela não está disponível, com a explicação.

### História de usuário 2 Quantidade coerente com o volume P2

Como estudante, quero que a quantidade sugerida acompanhe o tamanho da fonte, para não receber poucos cartões de um livro nem muitos de uma página.

**Motivo da prioridade:** melhora a qualidade percebida e é o item de avaliação previsto no backlog.
**Teste independente:** pedir cartões de fontes fictícias de 1, 10 e 50 páginas e conferir que as quantidades sugeridas crescem com o volume e respeitam o teto.

**Cenários de aceitação**

1. **Dado** uma fonte ou matéria, **quando** o estudante abre o pedido, **então** a quantidade sugerida segue a regra de proporção (Q-001), com o teto por pedido.
2. **Dado** fontes de volumes diferentes, **quando** a avaliação é executada, **então** o relatório mostra, para cada fonte, a quantidade sugerida, a quantidade gerada, a aprovada e a aceita, e a relação com o volume.

## Casos de borda

- Matéria com muitas fontes pequenas: cada fonte com conteúdo suficiente recebe ao menos um cartão, até o teto.
- Fonte excluída durante a geração da matéria: os cartões dela não são publicados, e os das outras fontes seguem (CB-16).
- Fonte cujo conteúdo já foi todo coberto por gerações anteriores: não recebe novos cartões (CB-26).
- O mesmo pedido enviado duas vezes: uma única geração (RN-10).
- Pedido que ultrapassaria o limite diário de gerações ([004](../004-geracao-cartoes/spec.md), Q-001): recusado com explicação.

## Requisitos funcionais

- **RF-001:** O estudante deverá conseguir pedir cartões para a matéria inteira, usando somente as fontes `concluido` da matéria (deriva de RN-22 da base).
- **RF-002:** O sistema deverá sugerir uma quantidade de cartões proporcional ao volume de texto, com teto por pedido (Q-001), e permitir que o estudante a reduza.
- **RF-003:** Num pedido da matéria, os cartões deverão ser distribuídos entre as fontes na proporção do volume de cada uma.
- **RF-004:** Todas as regras de [004](../004-geracao-cartoes/spec.md) (RF-002 a RF-018) deverão valer para o pedido da matéria.
- **RF-005:** O relatório de avaliação deverá registrar, por fonte, o volume, a quantidade sugerida, a gerada, a aprovada e a aceita.

## Entidades principais

- **Geração:** passa a admitir o pedido de uma matéria inteira, sem fonte única, com a quantidade pedida.

## Critérios de sucesso

- **CS-001:** No conjunto de avaliação, a quantidade sugerida cresce com o volume da fonte e nunca ultrapassa o teto.
- **CS-002:** A taxa de aceitação dos pedidos da matéria não é inferior à dos pedidos por fonte de [004](../004-geracao-cartoes/spec.md) em mais de 10 pontos percentuais.
- **CS-003:** Os critérios CS-001 a CS-004 de [004](../004-geracao-cartoes/spec.md) continuam atendidos.

## Requisitos de qualidade

- **RQ-001:** Um pedido da matéria respeita o orçamento diário de uso do provedor por estudante ([004](../004-geracao-cartoes/spec.md), RQ-002).
- **RQ-002:** O pedido da matéria não envia ao provedor trechos de outras matérias nem de outros estudantes.

## Suposições e dependências

- **Dependência:** [004-geracao-cartoes](../004-geracao-cartoes/spec.md) e [002-materias-fontes](../002-materias-fontes/spec.md).
- **Suposição:** o volume é medido pela quantidade de texto extraído, e não pelo tamanho do arquivo.

## Questões abertas

- **Q-001:** Qual a regra de proporção e qual o teto por pedido? **Recomendação:** 1 cartão a cada 300 palavras de texto extraído, no mínimo 3 por fonte com conteúdo suficiente e no máximo 30 por pedido; valores configuráveis e calibrados pelo relatório de avaliação. — **Responsável:** equipe — **Prazo:** 31/10/2026

## Decisões confirmadas

- **D-001:** No MVP o pedido é por fonte, com até 10 cartões; o pedido da matéria e a quantidade proporcional entram no final acadêmico ([004](../004-geracao-cartoes/spec.md), D-002). — **Confirmada por:** Artur Lins (equipe) — **Data:** 12/10/2026

## Exigências do PO

- **EX-02** (novos flashcards): ampliada; o "Gerar mais" de [004](../004-geracao-cartoes/spec.md) vale também para o pedido da matéria.

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | Herda as validações de 004 (RF-004); RQ-002 |
| II Proteção e isolamento | RQ-002 |
| III Verificação humana | O estudante revisa cada cartão; a proporção fica com a equipe (Q-001) |
| IV Servidor autoritativo | Quantidade e distribuição calculadas no servidor |
| V Qualidade verificável | CS-001 a CS-003 e relatório por fonte (RF-005) |
| VI Entrega incremental | US1 demonstrável com a quantidade fixa de 004 |
| VII Rastreabilidade | IDs da base citados; sessão registrada |
