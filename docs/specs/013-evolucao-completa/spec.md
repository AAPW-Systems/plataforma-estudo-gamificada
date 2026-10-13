# Especificação: painel de evolução completo

**Identificador:** 013-evolucao-completa
**Estágio:** Final acadêmico
**Funcionalidade do backlog:** [F-12](../../produto/backlog.md#funcionalidades-candidatas), incremento do final acadêmico (a evolução mínima do MVP está em [007-evolucao](../007-evolucao/spec.md))
**Criada em:** 12/10/2026
**Status:** Rascunho
**Origem:** backlog ("painel completo: tempo dedicado, por matéria"), [base de especificação](../../base-specs/spec.md) (HU-08, RF-15, RN-25) e [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante que estuda há semanas e quer ajustar o próprio ritmo.
**Situação:** o estudante quer saber quanto tempo dedicou a cada matéria e como evoluiu no mês.
**Problema observável:** a evolução do MVP mostra só totais e o calendário, sem tempo dedicado, períodos nem visão por matéria.
**Resultado esperado:** o painel mostra tempo dedicado, revisões, XP e cartões dominados por período e por matéria, além dos indicadores do MVP.
**Alternativa atual:** a evolução mínima de [007](../007-evolucao/spec.md).

## Escopo

### Incluído

- Tempo dedicado: soma do tempo por revisão, com teto de 60 segundos por revisão (RN-25, D-001).
- Períodos: últimos 7 dias, últimos 30 dias, últimos 12 meses e desde o início (Q-001).
- Filtro por matéria e visão comparativa entre matérias.
- Por matéria: tempo dedicado, revisões, XP, cartões dominados e dias com revisão.
- Todos os indicadores do MVP ([007](../007-evolucao/spec.md)).
- Distribuição dos cartões por faixa de dificuldade calculada pelo FSRS, se o PO aprovar a proposta de PO-01 (Q-002).

### Fora do escopo

- Comparação com outros estudantes.
- Exportação de dados.
- Previsões ("você vai esquecer X"), recomendações e conquistas.

## Cenários de usuário e testes

### História de usuário 1 Ver o tempo dedicado P1

Como estudante, quero saber quanto tempo dediquei aos estudos, no total e por matéria, para planejar minha semana.

**Motivo da prioridade:** é o indicador da RN-25 que ficou fora do MVP.
**Teste independente:** com revisões fictícias de durações conhecidas, incluindo algumas acima de 60 segundos, conferir o tempo dedicado total e por matéria com o calculado à mão.

**Cenários de aceitação**

1. **Dado** revisões com durações de 20, 45 e 300 segundos, **quando** o estudante abre a evolução, **então** o tempo dedicado é de 125 segundos (o teto limita a última a 60).
2. **Dado** revisões em duas matérias, **quando** o estudante filtra por uma, **então** vê o tempo dedicado só daquela matéria.

### História de usuário 2 Comparar períodos e matérias P2

Como estudante, quero ver minha evolução por período e por matéria, para saber onde estou avançando e onde estou parado.

**Motivo da prioridade:** completa o painel; a US1 já entrega o indicador novo.
**Teste independente:** com dados fictícios de 90 dias em 3 matérias, alternar os períodos e as matérias e conferir cada valor.

**Cenários de aceitação**

1. **Dado** um período escolhido, **quando** o estudante abre a evolução, **então** todos os indicadores se referem a esse período, com a indicação clara do intervalo.
2. **Dado** a visão por matéria, **quando** o estudante a abre, **então** vê, lado a lado, tempo dedicado, revisões, XP, cartões dominados e dias com revisão de cada matéria.
3. **Dado** um período sem atividade, **quando** o estudante o escolhe, **então** vê "nenhuma atividade neste período", diferente do estado de quem nunca estudou.

## Casos de borda

- Matéria excluída: os valores dela continuam no total, agrupados como "matérias excluídas" na visão por matéria (Q-003).
- Revisão com duração zero ou ausente: conta zero segundos.
- Período que começa antes da criação da conta: começa na criação.
- Sequência e dias estudados continuam globais: não são divididos por matéria.

## Requisitos funcionais

- **RF-001:** O sistema deverá calcular o tempo dedicado como a soma das durações das revisões, limitando cada uma ao teto configurado (padrão de 60 segundos) (deriva de RN-25 da base).
- **RF-002:** O estudante deverá conseguir escolher o período dos indicadores entre os definidos em Q-001.
- **RF-003:** O estudante deverá conseguir ver os indicadores de uma matéria e a comparação entre matérias: tempo dedicado, revisões, XP, cartões dominados e dias com revisão.
- **RF-004:** Todos os indicadores deverão ser calculados no servidor e exibidos também em texto.

## Entidades principais

- **Resumo da evolução:** visão calculada por período e por matéria. Não cria dados novos.

## Critérios de sucesso

- **CS-001:** Para o conjunto fictício de 90 dias, todos os valores coincidem com os calculados à mão, em todos os períodos e matérias.
- **CS-002:** O painel carrega em até 1,5 segundo no percentil 95 na VPS, com um ano de histórico fictício.

## Requisitos de qualidade

- **RQ-001:** Gráficos sempre têm o valor em texto e uma alternativa acessível ([UI-04](../../base-specs/design.md#12-pendências-de-design)).
- **RQ-002:** O painel funciona a partir de 320 px, com a comparação entre matérias empilhada no celular.

## Suposições e dependências

- **Dependência:** [007-evolucao](../007-evolucao/spec.md), [005-licao-trilha](../005-licao-trilha/spec.md) (duração das revisões) e [012-filtro-dominio-materia](../012-filtro-dominio-materia/spec.md) (domínio por matéria).
- **Suposição:** o tempo de CS-002 é uma meta proposta pelo agente, a confirmar na revisão da spec.

## Questões abertas

- **Q-001:** Quais períodos o painel oferece ([QA-09](../../produto/backlog.md#funcionalidades-candidatas))? **Recomendação:** últimos 7 dias, últimos 30 dias, últimos 12 meses e desde o início. — **Responsável:** equipe — **Prazo:** 31/10/2026
- **Q-002:** Se o PO aprovar a proposta de [PO-01](../../produto/pauta-po.md#po-01-níveis-de-dificuldade-ex-05), o painel mostra quantos cartões estão em cada faixa de dificuldade calculada pelo FSRS, por matéria? Quais são os limites das faixas? **Recomendação:** sim, com três faixas sobre a dificuldade do FSRS (de 1 a 10): até 4, de 4 a 7 e acima de 7, só como leitura. — **Responsável:** PO (professor Aldo Nunes) e equipe — **Prazo:** próxima review
- **Q-003:** Os valores de matérias excluídas aparecem agrupados como "matérias excluídas" ou somem da visão por matéria (permanecendo só no total)? **Recomendação:** agrupados, para que a soma das matérias feche com o total. — **Responsável:** equipe — **Prazo:** 31/10/2026

## Decisões confirmadas

- **D-001:** Teto de 60 segundos por revisão no tempo dedicado, configurável ([QA-24](../../produto/pendencias.md#qa-24-valores-da-gamificação)). — **Confirmada por:** Artur Lins (equipe) — **Data:** 12/10/2026

## Exigências do PO

- **EX-05** (dificuldade): Q-002, em pauta com o PO (PO-01). Nenhuma escolha ou filtro por dificuldade.

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | Não se aplica |
| II Proteção e isolamento | Indicadores só do próprio estudante |
| III Verificação humana | EX-05 fica com o PO (Q-002) |
| IV Servidor autoritativo | RF-004 |
| V Qualidade verificável | CS-001 com dados calculados à mão; RQ-001 |
| VI Entrega incremental | US1 demonstrável sem a US2 |
| VII Rastreabilidade | IDs da base citados; sessão registrada |
