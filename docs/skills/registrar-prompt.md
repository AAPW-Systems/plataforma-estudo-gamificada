# Guia: registrar uma sessão com agente

Obrigatório pelo Princípio VII da [constituição](../constitution.md). A convenção completa e o modelo estão em [`../prompts/README.md`](../prompts/README.md).

## Quando registrar

Registre toda sessão que crie ou altere qualquer arquivo do repositório: documentação, specs, código, testes ou configuração. Sessões apenas de leitura ou de dúvida, sem alteração, não precisam de registro.

## Como o agente deve agir

1. **No início da sessão**, crie o arquivo de registro com o prompt inicial **literal**, sem resumir nem corrigir.
2. **Durante a sessão**, acrescente na ordem cada novo prompt do usuário e cada resposta dada a perguntas de esclarecimento.
3. **No fim da sessão**, preencha a lista de artefatos criados ou alterados, a verificação feita e as pendências.
4. A seção "Alterações humanas" é preenchida pela pessoa que revisou a saída. O agente deixa "pendente de revisão".

## O que nunca registrar

- Segredos, chaves de API, tokens ou senhas. Substitua por `[REMOVIDO]`.
- Dados pessoais de terceiros.
- Raciocínio interno do modelo. Registre apenas o que foi pedido, o que foi entregue e o que foi verificado (apostila, seção 11).
