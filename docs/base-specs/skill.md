# Instruções para agentes (ponteiro)

**Atualizado em:** 12/10/2026 ([registro da sessão](../prompts/2026-10-12-alinhamento-produto-arquitetura.md))

As instruções para agentes de programação **não ficam nesta pasta**. A fonte canônica é [`../../.agents/AGENTS.md`](../../.agents/AGENTS.md), complementada pelos guias de [`../skills/`](../skills/README.md). Manter uma segunda cópia aqui fazia as instruções divergirem.

A versão de 07/10/2026 deste arquivo está no histórico do git (commit `e32228a`). O conteúdo dela foi absorvido assim:

| Seção da versão de 07/10/2026 | Destino atual |
|---|---|
| Prioridade documental, escopo, decisões e alterações | [`AGENTS.md`](../../.agents/AGENTS.md) (regras 1 a 6) e [regra de documentação da base](spec.md#12-regra-de-documentação) |
| Arquitetura, nomenclatura, backend, banco, API, idempotência, dados e histórico | [`../skills/padroes-implementacao.md`](../skills/padroes-implementacao.md) e [`../arquitetura/README.md`](../arquitetura/README.md) |
| RAG, IA, embeddings e banco vetorial | [`../skills/padroes-implementacao.md`](../skills/padroes-implementacao.md#ia-geração-e-chat) e DTEC 005, 007 e 008 do [`research.md`](../research.md) |
| Segurança e autenticação | Princípio II da [constituição](../constitution.md) e [DTEC 003](../research.md#decisão-dtec-003-autenticação) |
| Frontend e interface | [`../skills/padroes-interface.md`](../skills/padroes-interface.md) e [`design.md`](design.md) |
| Testes e critério de conclusão | Regras 6 e 17 do [`AGENTS.md`](../../.agents/AGENTS.md) e [DTEC 014](../research.md#decisão-dtec-014-complementos-de-teste) |
| Dependências | [`../skills/padroes-implementacao.md`](../skills/padroes-implementacao.md#dependências) |
| Proibições | [`AGENTS.md`](../../.agents/AGENTS.md#regras-inegociáveis) e Princípios I a IV da [constituição](../constitution.md) |
