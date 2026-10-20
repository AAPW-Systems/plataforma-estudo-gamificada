# Guias de agente por tarefa

Instruções reutilizáveis e independentes de ferramenta: servem para Claude, Codex, Cursor, Copilot, Gemini ou qualquer outro agente, e também para pessoas. O [`AGENTS.md`](../../.agents/AGENTS.md) indica quando ler cada guia.

| Guia | Quando usar |
|---|---|
| [`fluxo-sdd.md`](fluxo-sdd.md) | Ao criar ou avançar qualquer artefato em `docs/specs/` |
| [`contexto-tecnico.md`](contexto-tecnico.md) | Ao planejar uma spec: resumo das DTEC, convenções e obrigações já aprovadas, no lugar da leitura de todos os planos anteriores |
| [`registrar-prompt.md`](registrar-prompt.md) | Em toda sessão com agente que crie ou altere arquivos |
| [`padroes-implementacao.md`](padroes-implementacao.md) | Ao escrever código de backend, API, processamento ou testes |
| [`padroes-interface.md`](padroes-interface.md) | Ao criar ou alterar telas e componentes |
| [`atualizar-readme-progresso.md`](atualizar-readme-progresso.md) | Em todo commit que conclua tarefas de uma spec ou mude o status dela |

## Regras para os guias

- Um guia descreve **como executar uma tarefa**. Princípios ficam na [constituição](../constitution.md), e decisões de produto ficam nas specs.
- Os guias não duplicam o conteúdo das guidelines SDD: eles apontam para [`../sdd_guidelines/`](../sdd_guidelines/00_COMECE_AQUI.md).
- Um guia só aponta para stack, biblioteca ou comando quando ele tiver sido decidido em um `research.md`.
- Cada guia novo precisa ser adicionado à tabela acima e ao `AGENTS.md`.
