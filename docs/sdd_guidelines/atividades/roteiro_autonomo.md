# Roteiro autônomo de SDD

Use este roteiro para uma funcionalidade pequena do projeto. O trabalho pode ser dividido em mais de uma sessão, mas preserve a ordem das revisões.

## Etapa 1 Escolher uma jornada

Escolha uma ação que uma pessoa consiga iniciar e concluir. Evite especificar “o sistema inteiro”. Registre usuário, situação, problema e resultado esperado.

**Saída:** título e parágrafo inicial de `spec.md`.

## Etapa 2 Definir escopo

Liste o que a primeira versão precisa fazer e o que ficará de fora. Inclua pelo menos uma falha que possa prejudicar o usuário.

**Saída:** seções de escopo e casos de borda.

## Etapa 3 Escrever histórias e critérios

Defina a história P1 e seu teste independente. Escreva cenários com estado inicial, ação e resultado observável. Adicione histórias posteriores somente quando forem independentes ou ampliarem a P1.

**Saída:** histórias e cenários de aceitação.

## Etapa 4 Revisar requisitos

Use `modelos/checklists/requirements.md`. Para cada item não atendido, corrija a spec ou registre uma questão para o PO. Não use o plano para esconder uma dúvida de produto.

**Saída:** `checklists/requirements.md` com decisão de aprovação.

## Etapa 5 Pesquisar decisões técnicas

Liste apenas dúvidas que impedem o plano. Compare alternativas usando critérios do projeto. Registre uma condição para revisar cada decisão.

**Saída:** `research.md`.

## Etapa 6 Produzir o plano

Escolha arquitetura, dependências, contratos, dados, testes e observabilidade. Explique como o plano atende a constituição. Use diretórios e nomes reais.

**Saída:** `plan.md`, `data-model.md`, `contracts/` e `quickstart.md` quando aplicáveis.

## Etapa 7 Quebrar em tarefas

Organize preparação, base compartilhada, histórias em prioridade e qualidade final. Toda tarefa precisa indicar ação, caminho e resultado verificável. Marque paralelismo somente quando não houver dependência nem disputa pelos mesmos arquivos.

**Saída:** `tasks.md`.

## Etapa 8 Conferir rastreabilidade

Escolha cada requisito e localize cenário, teste planejado e tarefa. Se algum elemento não existir, corrija os artefatos antes de implementar.

**Saída:** `traceability.md`.

## Etapa 9 Implementar por história

Conclua primeiro a base indispensável e depois a P1. Execute seu teste independente. Atualize a tarefa somente depois da verificação. Mudanças de comportamento voltam para a spec; mudanças técnicas relevantes voltam para o plano ou para `research.md`.

## Etapa 10 Convergir

Compare o estado final com spec, plano e tarefas. Registre lacunas. Se houver tarefas novas, implemente e repita a verificação até que não existam divergências conhecidas ou até que uma pendência esteja explicitamente aceita.
