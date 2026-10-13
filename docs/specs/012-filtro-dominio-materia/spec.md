# Especificação: filtro da lição por matéria e domínio por matéria

**Identificador:** 012-filtro-dominio-materia
**Estágio:** Final acadêmico
**Funcionalidade do backlog:** [F-07](../../produto/backlog.md#funcionalidades-candidatas), incremento do final acadêmico (a trilha do MVP está em [005-licao-trilha](../005-licao-trilha/spec.md))
**Criada em:** 12/10/2026
**Status:** Rascunho
**Origem:** backlog ("filtro e domínio por matéria no Final"), [base de especificação](../../base-specs/spec.md) (RF-28, RN-19, RN-26) e [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante com várias matérias e uma prova próxima.
**Situação:** o estudante tem prova de Biologia amanhã e quer revisar só essa matéria hoje.
**Problema observável:** no MVP, a lição mistura todas as matérias, e o estudante não sabe o quanto já domina de cada uma.
**Resultado esperado:** o estudante filtra a lição por uma matéria, sem mudar quando cada cartão volta, e vê o domínio de cada matéria (cartões dominados sobre cartões ativos).
**Alternativa atual:** suspender os cartões das outras matérias, o que atrasa o agendamento delas.

## Escopo

### Incluído

- Escolha de uma matéria para a próxima lição, ou "Todas as matérias" (padrão).
- O filtro restringe quais cartões disponíveis entram na lição, sem alterar o agendamento (RN-26).
- Domínio por matéria: cartões dominados sobre cartões ativos, em quantidade e percentual.
- Exibição do domínio na trilha e na lista de matérias.

### Fora do escopo

- Filtro por mais de uma matéria, por fonte ou por origem do cartão.
- Revisão antecipada de cartões que ainda não venceram, mesmo com filtro (RN-26).
- Meta diária por matéria: a meta continua global.
- Seleção por dificuldade (EX-05, PO-01).

## Cenários de usuário e testes

### História de usuário 1 Estudar só uma matéria P1

Como estudante, quero fazer uma lição só com os cartões de uma matéria, para me concentrar no que tenho de estudar agora.

**Motivo da prioridade:** é o pedido mais direto de quem estuda para uma prova.
**Teste independente:** com cartões disponíveis em duas matérias, filtrar por uma, fazer a lição e confirmar que só cartões dela aparecem, e que o vencimento dos cartões da outra matéria não mudou.

**Cenários de aceitação**

1. **Dado** cartões disponíveis em Biologia e em História, **quando** o estudante escolhe Biologia e começa a lição, **então** a lição só tem cartões disponíveis de Biologia, montados com as mesmas regras de [005](../005-licao-trilha/spec.md).
2. **Dado** uma lição filtrada, **quando** ela é concluída, **então** o nó da trilha acende e indica a matéria; XP, meta e sequência são calculados como em qualquer lição.
3. **Dado** uma matéria sem cartões disponíveis, **quando** o estudante a escolhe, **então** não há lição, e a tela mostra o próximo vencimento da matéria e as matérias com cartões disponíveis.
4. **Dado** que o estudante filtrou por Biologia, **quando** os cartões de História vencem, **então** o vencimento deles é o mesmo calculado pelo FSRS, sem antecipação nem adiamento.
5. **Dado** cartões novos de várias matérias, **quando** o estudante filtra por uma, **então** o limite diário de novos continua global, contando os novos apresentados em qualquer matéria.

### História de usuário 2 Ver o domínio de cada matéria P2

Como estudante, quero ver quanto já domino de cada matéria, para decidir onde concentrar o estudo.

**Motivo da prioridade:** orienta o uso do filtro, mas o filtro funciona sem ele.
**Teste independente:** com uma matéria de 20 cartões ativos, 5 deles dominados, conferir o domínio "5 de 20 (25%)" na trilha e na lista de matérias.

**Cenários de aceitação**

1. **Dado** uma matéria com cartões ativos, **quando** o estudante abre a trilha ou a lista de matérias, **então** vê o domínio da matéria como "dominados de ativos" e em percentual, sempre em texto.
2. **Dado** uma matéria sem cartões ativos, **quando** o estudante a vê, **então** o domínio aparece como "sem cartões ativos", sem percentual.

## Casos de borda

- Matéria excluída com a lição filtrada por ela em andamento: a lição é encerrada; as revisões registradas permanecem.
- Filtro escolhido com uma lição sem filtro em andamento: a lição em andamento é concluída ou retomada antes; o filtro vale para a próxima.
- Cartões suspensos: não contam como ativos no domínio.
- Lição extra filtrada depois da meta: permitida enquanto houver cartões disponíveis na matéria.

## Requisitos funcionais

- **RF-001:** O estudante deverá conseguir escolher uma matéria, ou todas, para a próxima lição (deriva de RF-28 e RN-19 da base).
- **RF-002:** O filtro deverá restringir apenas quais cartões disponíveis entram na lição, sem alterar vencimentos, passos ou parâmetros do FSRS (deriva de RN-26 da base).
- **RF-003:** O limite de novos por dia, a meta diária, o XP e a sequência deverão continuar globais.
- **RF-004:** O nó de uma lição filtrada deverá indicar a matéria.
- **RF-005:** O sistema deverá exibir o domínio de cada matéria: cartões ativos dominados sobre cartões ativos, em quantidade e percentual (deriva de RN-19 da base).

## Entidades principais

- **Lição:** passa a registrar, opcionalmente, a matéria do filtro.

## Critérios de sucesso

- **CS-001:** Em 100% dos testes, os vencimentos de todos os cartões são os mesmos com e sem o uso do filtro, para a mesma sequência de revisões.
- **CS-002:** Em 100% dos testes, nenhuma lição filtrada contém cartão de outra matéria.

## Requisitos de qualidade

- **RQ-001:** O seletor de matéria opera por teclado e anuncia a matéria escolhida.
- **RQ-002:** O domínio nunca é exibido só por cor ou só por gráfico.

## Suposições e dependências

- **Dependência:** [005-licao-trilha](../005-licao-trilha/spec.md) e [006-xp-meta-sequencia](../006-xp-meta-sequencia/spec.md).
- **Dependência:** a definição de cartão dominado de [005](../005-licao-trilha/spec.md), D-003.

## Questões abertas

- **Q-001:** O filtro escolhido deve ficar salvo para as próximas lições ou voltar a "Todas as matérias" a cada lição? **Recomendação:** voltar a "Todas as matérias" a cada dia de estudo, para que nenhuma matéria fique esquecida por um filtro antigo. — **Responsável:** equipe — **Prazo:** 31/10/2026

## Decisões confirmadas

- **D-001:** O filtro por matéria restringe quais cartões disponíveis entram na lição, sem alterar o agendamento (RN-26 da base). — **Confirmada por:** Artur Lins (equipe), [registro](../../prompts/2026-10-12-esquema-inicial-banco.md) — **Data:** 12/10/2026

## Exigências do PO

Nenhuma exigência toca esta funcionalidade diretamente. A proposta para EX-05 (PO-01) proíbe o filtro por dificuldade.

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | Não se aplica |
| II Proteção e isolamento | Filtro só sobre matérias do estudante |
| III Verificação humana | Q-001 fica com a equipe |
| IV Servidor autoritativo | RF-002, RF-003; CS-001 |
| V Qualidade verificável | CS-001 e CS-002 |
| VI Entrega incremental | US1 demonstrável sem a US2 |
| VII Rastreabilidade | IDs da base citados; sessão registrada |
