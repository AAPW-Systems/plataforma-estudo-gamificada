# Prompts para trabalhar com os artefatos

Substitua os campos entre colchetes e forneça os arquivos citados ao agente. Não aceite alterações sem revisar as diferenças.

## Criar a primeira especificação

```text
Leia a descrição abaixo e produza uma spec de funcionalidade usando o modelo fornecido. Concentre-se no que o usuário precisa e no comportamento observável. Não escolha tecnologia. Marque dúvidas como questões abertas em vez de inventar respostas.

Descrição:
[cole aqui]

Modelo:
[anexe modelos/spec.md]
```

## Revisar a especificação

```text
Revise spec.md usando checklists/requirements.md. Para cada problema, cite o requisito ou seção afetada, explique por que não é verificável e proponha uma pergunta concreta. Não altere decisões de produto sem minha confirmação.
```

## Esclarecer sem ampliar o escopo

```text
Leia spec.md e liste no máximo cinco dúvidas que mudam comportamento, escopo, risco ou critério de aceitação. Ordene por impacto. Não faça perguntas sobre detalhes que podem ser decididos no plano técnico.
```

## Produzir o plano

```text
Com base em spec.md e constitution.md aprovados, produza plan.md. Resolva dúvidas técnicas em research.md, compare alternativas e registre consequências. Use caminhos reais do repositório. Não mude os requisitos para facilitar a implementação.
```

## Criar tarefas

```text
Leia spec.md, plan.md, research.md, data-model.md e contracts/. Gere tasks.md em ordem de dependência. Agrupe por história para permitir implementação e teste independentes. Cada tarefa deve ter ID, caminho exato e resultado verificável. Marque [P] somente quando os arquivos e dependências permitirem trabalho paralelo.
```

## Analisar consistência

```text
Compare spec.md, plan.md e tasks.md sem editar os arquivos. Aponte requisitos sem cobertura, tarefas que criam comportamento não especificado, contradições e termos vagos. Classifique cada achado como bloqueador, importante ou melhoria.
```

## Implementar uma história

```text
Implemente somente as tarefas ainda abertas da história [US1]. Preserve mudanças existentes de outras pessoas. Execute os testes relacionados, marque como concluídas apenas as tarefas verificadas e relate qualquer divergência entre o código e a spec antes de alterar o comportamento.
```

## Verificar convergência

```text
Compare implementação, testes e documentação com spec.md, plan.md e tasks.md. Se houver lacunas, acrescente tarefas específicas ao final de tasks.md sem ocultar o histórico. Considere concluído somente quando os critérios de aceitação possuírem evidência de verificação.
```
