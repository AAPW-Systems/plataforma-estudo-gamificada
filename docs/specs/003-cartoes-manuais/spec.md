# Especificação: cartões criados e gerenciados pelo estudante

**Identificador:** 003-cartoes-manuais
**Estágio:** MVP
**Funcionalidade do backlog:** [F-04](../../produto/backlog.md#funcionalidades-candidatas), parte manual do MVP (a geração por IA está em [004-geracao-cartoes](../004-geracao-cartoes/spec.md); o cartão com imagem do final acadêmico, em [011-cartao-imagem](../011-cartao-imagem/spec.md))
**Criada em:** 12/10/2026
**Status:** Rascunho
**Origem:** backlog, [base de especificação](../../base-specs/spec.md) (HU-15, RF-11, RN-05, RN-08, RN-14, RN-16, RN-26) e decisões da [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante individual que já sabe o que quer memorizar.
**Situação:** o estudante quer registrar uma pergunta e uma resposta que lembrou em aula, ou corrigir um cartão que não ficou bom.
**Problema observável:** sem criar e editar os próprios cartões, o estudante depende inteiramente da IA e não consegue tirar do estudo um cartão que atrapalha.
**Resultado esperado:** o estudante cria, edita, suspende, reativa e exclui cartões numa matéria. Cada cartão mostra a origem com honestidade, e os ativos entram nas lições.
**Alternativa atual:** cartões em papel ou em outro aplicativo, sem ligação com as fontes.

## Escopo

### Incluído

- Criar um cartão manual numa matéria: frente, verso, explicação opcional e, se quiser, a indicação de uma fonte da matéria como referência.
- Listar os cartões da matéria (ativos e suspensos), com a origem de cada um.
- Editar frente, verso e explicação de qualquer cartão do estudante.
- Suspender e reativar cartões.
- Excluir um cartão definitivamente, com confirmação.
- Buscar por texto e filtrar a lista de cartões da matéria por situação e por origem (D-005).
- Exibir a origem: "Gerado e verificado", "Editado por você", "Criado por você" e "Fonte apagada" (RN-05, RN-08).

### Fora do escopo

- Gerar cartões por IA, revisar os gerados e consultar a evidência de um cartão gerado: [004-geracao-cartoes](../004-geracao-cartoes/spec.md).
- Imagem na frente do cartão: final acadêmico, em [011-cartao-imagem](../011-cartao-imagem/spec.md).
- Mover um cartão para outra matéria, importar ou exportar baralhos.
- Reiniciar o aprendizado de um cartão: incremento posterior de F-05 (RN-26).
- Tipos de cartão com correção automática (RN-08).
- Formatação no texto do cartão (negrito, listas, fórmulas): o MVP aceita só texto puro com quebras de linha (D-003).

## Cenários de usuário e testes

### História de usuário 1 Criar um cartão P1

Como estudante, quero criar um cartão com frente, verso e uma explicação, para estudar o que eu mesmo escolhi.

**Motivo da prioridade:** permite construir e testar as lições sem esperar a geração por IA (ordem do backlog).
**Teste independente:** criar um cartão na matéria "Biologia" e confirmar que ele aparece na lista com "Criado por você" e entra como cartão novo na próxima lição ([005](../005-licao-trilha/spec.md)).

**Cenários de aceitação**

1. **Dado** uma matéria, **quando** o estudante preenche frente e verso e salva, **então** o cartão aparece na lista da matéria como ativo, com a origem "Criado por você", e passa a ser um cartão novo, que entra nas lições na ordem de criação.
2. **Dado** frente ou verso vazios, ou acima do limite, **quando** o estudante tenta salvar, **então** nada é criado e o erro aparece junto do campo, com os valores preservados.
3. **Dado** que o estudante indica uma fonte da matéria como referência, **quando** salva, **então** o cartão mostra "Criado por você" com o título da fonte, sem o selo de verificado.

### História de usuário 2 Editar um cartão P2

Como estudante, quero corrigir o texto de um cartão, para que ele diga exatamente o que preciso lembrar.

**Motivo da prioridade:** corrige cartões ruins sem perder o histórico de estudo.
**Teste independente:** editar um cartão gerado já revisado e confirmar que a origem muda para "Editado por você", o vínculo com o trecho continua e o próximo vencimento não muda.

**Cenários de aceitação**

1. **Dado** um cartão "Criado por você", **quando** o estudante altera a frente, **então** o novo texto aparece na lista e nas próximas lições, e o agendamento do cartão continua o mesmo (RN-26).
2. **Dado** um cartão "Gerado e verificado", **quando** o estudante altera frente, verso ou explicação, **então** a origem passa a "Editado por você", o selo de verificado é removido e a evidência continua acessível (RN-08).
3. **Dado** uma edição que não muda nenhum campo, **quando** o estudante salva, **então** a origem não muda.

### História de usuário 3 Suspender, reativar e excluir P2

Como estudante, quero tirar um cartão das lições temporariamente ou de vez, para não perder tempo com o que não serve mais.

**Motivo da prioridade:** sem isso, um cartão errado continuaria aparecendo indefinidamente.
**Teste independente:** suspender um cartão devido, confirmar que ele não entra na lição, reativá-lo e confirmar que ele volta com o mesmo estado de agendamento; excluir outro e confirmar que as revisões e o XP dele permanecem.

**Cenários de aceitação**

1. **Dado** um cartão ativo, **quando** o estudante o suspende, **então** ele não entra em lições, aparece como suspenso na lista e o estado de agendamento é preservado.
2. **Dado** um cartão suspenso, **quando** o estudante o reativa, **então** ele volta às lições conforme o vencimento calculado antes da suspensão. Se o vencimento já passou, o cartão é devido.
3. **Dado** um cartão, **quando** o estudante pede para excluí-lo, **então** um diálogo avisa que a exclusão é definitiva. Depois de confirmada, o cartão some, enquanto as revisões já registradas e o XP permanecem.

### História de usuário 4 Encontrar um cartão P3

Como estudante, quero buscar e filtrar os cartões de uma matéria, para encontrar rapidamente o cartão que quero editar ou suspender.

**Motivo da prioridade:** com cartões gerados, uma matéria passa de 100 cartões rapidamente; não bloqueia a criação nem a lição.
**Teste independente:** numa matéria com 120 cartões fictícios, buscar por uma palavra da frente, por uma palavra do verso e filtrar por suspensos e por origem, conferindo os resultados.

**Cenários de aceitação**

1. **Dado** uma matéria com muitos cartões, **quando** o estudante busca por um texto, **então** a lista mostra só os cartões cuja frente ou verso contém o texto, sem diferenciar maiúsculas, minúsculas e acentos.
2. **Dado** a lista de cartões, **quando** o estudante filtra por situação (ativo ou suspenso) ou por origem, **então** só os cartões correspondentes aparecem, e os filtros podem ser combinados com a busca.
3. **Dado** uma busca sem resultados, **quando** a lista é exibida, **então** ela informa que nenhum cartão corresponde à busca, diferente do estado de matéria sem cartões.

## Casos de borda

- Frente, verso ou explicação só com espaços.
- Texto com marcação ou script: exibido como texto, nunca executado.
- Cartão suspenso ou excluído enquanto está numa lição aberta: deixa de ser apresentado, e as revisões já registradas permanecem (CB-27).
- Edição concorrente em duas abas: a última gravação vale, e a lição em andamento não perde revisões.
- Fonte de referência excluída depois: o cartão é sempre mantido, mesmo que a fonte seja excluída com "Excluir os cartões junto", e mostra "Fonte apagada" com a descrição da origem (RN-14; D-006).
- Cartão aguardando revisão (gerado e ainda não aceito): não aparece nesta lista; é tratado em [004](../004-geracao-cartoes/spec.md).

## Requisitos funcionais

- **RF-001:** O estudante deverá conseguir criar um cartão numa matéria com frente (1 a 1.000 caracteres), verso (1 a 2.000 caracteres) e explicação opcional (até 1.000 caracteres) (deriva de RF-11 e RN-08 da base).
- **RF-002:** O estudante poderá indicar uma fonte da mesma matéria como referência de um cartão manual. O cartão guarda a descrição da origem (título, nome do arquivo e data do envio) e nunca recebe o selo de verificado (deriva de RN-05 da base).
- **RF-003:** Um cartão manual entra como cartão novo e é apresentado pela primeira vez conforme o limite de novos por dia, na ordem de criação (deriva de RN-20 da base).
- **RF-004:** O estudante deverá conseguir listar os cartões ativos e suspensos de uma matéria, com frente, origem e situação.
- **RF-005:** A edição de frente, verso ou explicação não deverá alterar o estado de agendamento do cartão (deriva de RN-26 da base).
- **RF-006:** Editar um cartão "Gerado e verificado" deverá mudar a origem para "Editado por você", remover o selo de verificado e manter o vínculo com os trechos (deriva de RN-08 da base).
- **RF-007:** Um cartão suspenso não deverá entrar em lições, e seu estado de agendamento deverá ser preservado até a reativação (deriva de RN-08 da base).
- **RF-008:** A exclusão de um cartão deverá exigir confirmação e preservar as revisões e o XP já registrados.
- **RF-009:** Todo cartão deverá exibir uma única origem: "Gerado e verificado", "Editado por você" ou "Criado por você", acrescida de "Fonte apagada" quando a fonte de referência tiver sido excluída.
- **RF-010:** O estudante deverá conseguir buscar os cartões da matéria por texto da frente ou do verso, sem diferenciar maiúsculas, minúsculas e acentos, e filtrá-los por situação e por origem (D-005).
- **RF-011:** Frente, verso e explicação deverão ser texto puro, com quebras de linha preservadas (D-003).

## Entidades principais

- **Cartão:** frente, verso, explicação, origem, situação (ativo, suspenso, aguardando revisão, recusado), matéria, estado de agendamento e datas.
- **Descrição da origem:** cópia do título da fonte, do nome do arquivo, da página (quando conhecida) e da data do envio, que sobrevive à exclusão da fonte.

## Critérios de sucesso

- **CS-001:** Um estudante cria 5 cartões em até 3 minutos, só com o teclado.
- **CS-002:** Em 100% dos testes de edição, o vencimento e a estabilidade do cartão são os mesmos antes e depois da edição.
- **CS-003:** Em 100% dos testes, cartões suspensos não aparecem em nenhuma lição até a reativação.

## Requisitos de qualidade

- **RQ-001:** Texto do cartão é sempre exibido como texto, sem interpretar marcação ou script.
- **RQ-002:** Cartões respeitam o isolamento entre estudantes ([001](../001-conta-acesso/spec.md), RF-007).
- **RQ-003:** O formulário e a lista operam por teclado e atendem WCAG 2.2 AA; a origem não depende só de cor.

## Suposições e dependências

- **Dependência:** [001-conta-acesso](../001-conta-acesso/spec.md) e [002-materias-fontes](../002-materias-fontes/spec.md) (matérias e, para a referência opcional, fontes).
- **Dependência:** a entrada do cartão nas lições é verificada com [005-licao-trilha](../005-licao-trilha/spec.md).

## Esclarecimentos

### Sessão de 12/10/2026 ([registro](../../prompts/2026-10-12-esclarecimento-specs-mvp.md))

- **E11:** O texto do cartão aceita formatação? → Não no MVP; só texto puro com quebras de linha (D-003).
- **E12:** Os limites de texto estão confirmados? → Sim: frente até 1.000 caracteres, verso até 2.000, explicação até 1.000 (D-004).
- **E13:** A lista de cartões tem busca e filtro? → Sim: busca por texto e filtro por situação e por origem (D-005).

### Revisão pelo checklist de 12/10/2026 ([registro](../../prompts/2026-10-12-revisao-requisitos-specs-mvp.md))

- **R1:** A exclusão de uma fonte com "Excluir os cartões junto" apaga os cartões criados pelo estudante que a citam? → Não; eles são sempre mantidos (D-006; [002](../002-materias-fontes/spec.md), D-009).

## Questões abertas

- **Q-001:** ~~Formatação simples no texto do cartão?~~ Resolvida em 12/10/2026 (D-003).

Nenhuma questão aberta impede o planejamento.

## Decisões confirmadas

- **D-001:** Modelo único de cartão (frente, verso, explicação e origem), sem tipos com correção automática; a explicação é opcional nos cartões criados pelo estudante. — **Confirmada por:** equipe, na [visão](../../produto/visao.md#flashcards-f-04) — **Data:** 29/09/2026
- **D-002:** O cartão criado pelo estudante pode citar uma fonte de referência, mas nunca recebe o selo de verificado (Princípio I, QA-20). — **Confirmada por:** equipe, na [constituição](../../constitution.md) v0.2 — **Data:** 29/09/2026
- **D-003:** Frente, verso e explicação são texto puro com quebras de linha no MVP; formatação fica para depois. — **Confirmada por:** Artur Lins (equipe), esclarecimento E11 — **Data:** 12/10/2026
- **D-004:** Limites de texto: frente de 1 a 1.000 caracteres, verso de 1 a 2.000 e explicação de até 1.000, configuráveis por ambiente; valem também para os cartões gerados. — **Confirmada por:** Artur Lins (equipe), esclarecimento E12 — **Data:** 12/10/2026
- **D-005:** A lista de cartões da matéria tem busca por texto e filtro por situação e por origem. — **Confirmada por:** Artur Lins (equipe), esclarecimento E13 — **Data:** 12/10/2026
- **D-006:** Um cartão criado pelo estudante que cita uma fonte como referência é sempre mantido quando a fonte é excluída, em qualquer opção do diálogo, e passa a mostrar "Fonte apagada" ([002](../002-materias-fontes/spec.md), D-009). — **Confirmada por:** Artur Lins (equipe), revisão R1 — **Data:** 12/10/2026

## Exigências do PO

- **EX-03:** coberta parcialmente: a explicação é opcional nos cartões criados pelo estudante (RF-001). A explicação obrigatória dos cartões gerados está em [004](../004-geracao-cartoes/spec.md), e a exibição ao errar, em [005](../005-licao-trilha/spec.md).

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | Conteúdo do estudante nunca recebe selo de verificado (RF-002, RF-006, RF-009) |
| II Proteção e isolamento | RQ-001 e RQ-002 |
| III Verificação humana | Exclusão com confirmação (US3); decisões do esclarecimento registradas pela equipe (D-003 a D-005) |
| IV Servidor autoritativo | Editar não altera o agendamento (RF-005); histórico preservado (RF-008) |
| V Qualidade verificável | CS-001 a CS-003 |
| VI Entrega incremental | US1 demonstrável sozinha, sem IA |
| VII Rastreabilidade | IDs da base citados; sessão registrada |
