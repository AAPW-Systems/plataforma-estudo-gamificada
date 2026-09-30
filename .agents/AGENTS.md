# AGENTS.md

Instruções canônicas para **qualquer** agente de programação (Claude, Codex, Cursor, Copilot, Gemini etc.) neste repositório. Os arquivos `AGENTS.md` e `CLAUDE.md` da raiz apenas apontam para este. Edite somente aqui.

## Projeto

Plataforma web de estudos gamificada para a disciplina de IA do curso de Sistemas de Informação. O estudante envia seus materiais, a IA gera flashcards rastreáveis até o trecho de origem, a revisão segue repetição espaçada e o ritmo é gamificado com XP, sequência diária e uma rota de progressão. Há também um chat com os materiais (RAG), que responde apenas com base nas fontes enviadas e cita os trechos usados.

O projeto segue **SDD (Spec-Driven Development)** conforme as guidelines em `docs/sdd_guidelines/`, que devem ser seguidas **à risca**: o projeto é avaliado por elas.

## Estado atual

- **Fase:** brainstorming aprofundado concluído (29/09/2026). Recorte do MVP em `docs/produto/backlog.md`, pendente de validação com o professor (PO). Decisões de produto em `docs/produto/visao.md`. O próximo passo é resolver as pendências técnicas e escrever a spec de F-01.
- **Pendências:** `docs/produto/pendencias.md` lista o que está em aberto e o impacto de cada opção. Consulte antes de propor qualquer decisão técnica.
- **Exigências do PO:** `docs/produto/exigencias_po.md`. As exigências de 29/09/2026 (EX-01 a EX-05) já foram movidas para o backlog.
- **Stack:** direção parcial (Python, React, PostgreSQL, Keycloak, front e back separados). Framework do backend (QA-18) e stack de IA (QA-22) pendentes. **Não crie código de aplicação, dependências, Dockerfiles nem pastas de backend e frontend** antes de a stack estar registrada em um `research.md` aprovado.
- **Constituição:** v0.3 em rascunho, aguardando aprovação da equipe.
- **Specs:** nenhuma criada ainda (ver `docs/specs/README.md`).
- **Equipe:** Arthur Moura, Artur Lins, Caroline Santana, Pedro Paulo Lucena e William Johnson.
- **PO:** professor Aldo Nunes. Ainda não foi decidido se haverá um representante interno do PO na equipe.
- **Scrum Master:** rodízio semanal entre os integrantes (requisito obrigatório da disciplina).

Atualize esta seção sempre que a fase mudar.

## Leitura obrigatória antes de agir

1. `docs/constitution.md`: princípios que nenhuma entrega pode violar.
2. `docs/produto/visao.md` e `docs/produto/backlog.md`: o que é o produto e quais funcionalidades existem.
3. `docs/produto/exigencias_po.md`: exigências feitas diretamente pelo PO. **Consulta obrigatória ao escrever ou revisar qualquer spec.** Toda exigência que tocar a funcionalidade especificada deve ser coberta por requisitos da spec ou virar uma questão `Q-xxx`. Se uma exigência conflitar com a constituição ou com a visão, registre o conflito como questão para o PO; não o resolva por conta própria.
4. O guia de `docs/skills/` correspondente à tarefa:

| Tarefa | Guia |
|---|---|
| Criar ou avançar spec, plano, tarefas | `docs/skills/fluxo-sdd.md` |
| Qualquer sessão que altere arquivos | `docs/skills/registrar-prompt.md` |
| Código de backend, API, IA, testes | `docs/skills/padroes-implementacao.md` |
| Telas e componentes | `docs/skills/padroes-interface.md` |

5. Ao trabalhar em uma funcionalidade, todos os artefatos da pasta `docs/specs/NNN-*` correspondente.

## Mapa do repositório

```text
.agents/AGENTS.md          # este arquivo (fonte canônica para agentes)
AGENTS.md, CLAUDE.md       # ponteiros para este arquivo
README.md                  # visão geral para pessoas
docs/
├── constitution.md        # princípios estáveis do projeto
├── produto/               # visão, backlog (com recorte do MVP), pendências e exigências do PO
├── specs/NNN-nome-curto/  # uma pasta por funcionalidade (spec, plan, tasks...)
├── skills/                # guias de agente por tarefa, independentes de ferramenta
├── prompts/               # registro obrigatório de toda sessão com agente
├── init/                  # brainstorming inicial: SOMENTE LEITURA (histórico)
└── sdd_guidelines/        # material da disciplina: SOMENTE LEITURA
```

A estrutura de código (ex.: `backend/`, `frontend/`, `compose.yaml`) será definida no primeiro `plan.md` e registrada aqui.

## Regras inegociáveis

### Processo SDD

1. **Portões humanos:** não avance de spec para plano, nem de plano para tarefas, nem de tarefas para implementação sem a aprovação explícita de uma pessoa da equipe.
2. **Não decida produto:** dúvidas de produto viram questões `Q-xxx` na spec, com responsável e prazo. Apresente opções e consequências, mas não assuma respostas. A ausência de resposta não é aprovação.
3. **A spec não escolhe tecnologia.** Framework, banco e bibliotecas ficam no `plan.md` e no `research.md`, com alternativas e justificativa.
4. **IDs estáveis:** não renumere RF, RN, CS, RQ, US, T, F ou QA. Ao remover um item, marque-o como removido.
5. **Spec ancorada:** mudanças de comportamento atualizam a spec e se propagam para plano, tarefas, testes e contratos, sem reescrever o histórico.
6. **Checkbox só com evidência:** uma tarefa é marcada `[x]` apenas depois de verificada (teste executado ou demonstração).

### Registro de prompts

7. **Toda sessão que criar ou alterar arquivos é registrada** em `docs/prompts/AAAA-MM-DD-tema-curto.md`, conforme `docs/prompts/README.md`, com o prompt literal. Crie o registro no início da sessão, atualize-o ao longo dela e adicione a sessão ao índice.

### Produto e segurança

8. **Fontes exclusivas:** a IA do produto usa apenas os materiais do usuário e sempre cita a origem (Princípio I). A única exceção é a consulta externa acionada pelo usuário no tira-dúvidas de um flashcard (F-16, fora do MVP), nas condições do Princípio I.
9. **Sem segredos no repositório:** chaves e tokens nunca aparecem em código, documentação, exemplos ou prompts registrados. Use `.env` (ignorado pelo git) e documente as variáveis em `.env.example`.
10. **Sem dados pessoais reais** em testes, exemplos ou demonstrações.
11. **Docker obrigatório:** todo serviço roda em contêiner. O ambiente completo sobe com um comando documentado.

### Arquivos protegidos

12. `docs/sdd_guidelines/` e `docs/init/` são **somente leitura**. Novas decisões vão para a constituição, o produto, as specs ou os skills.

### Produtos de terceiros

13. **Sem menção a produtos concorrentes ou de referência na documentação oficial.** Prompts e conversas podem citar aplicativos e ferramentas de terceiros como exemplo; isso serve apenas de contexto para o agente. README, constituição, documentos de produto, specs, planos, pesquisas, tarefas, skills e interface descrevem cada capacidade pelo que ela faz (ex.: "repetição espaçada", "chat com citações", "rota de progressão"), nunca pelo nome ou pelo "estilo" de outro produto.
    - A regra não se aplica a tecnologias adotadas ou avaliadas no projeto (bibliotecas, frameworks, algoritmos, serviços), que continuam sendo nomeadas no `plan.md` e no `research.md`.
    - Exceções: `docs/prompts/`, que registra os prompts literalmente, e as pastas somente leitura (`docs/init/`, `docs/sdd_guidelines/`).

## Convenções

- **Idioma:** documentação, interface e mensagens em português brasileiro. Identificadores do domínio em português, sem acentos (constituição, "Restrições do projeto").
- **Pastas de spec:** `docs/specs/NNN-nome-curto/`, com número de 3 dígitos e kebab-case sem acentos.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/pt-br/) com descrição em português (ex.: `docs: adiciona constituição v0.1`, `feat(materiais): implementa envio [T012]`). Referencie IDs de tarefa quando houver.
- **Datas em documentos:** `DD/MM/AAAA` no texto e `AAAA-MM-DD` em nomes de arquivo.

## Como encerrar uma sessão

1. Verifique se os links relativos dos arquivos alterados funcionam.
2. Complete o registro em `docs/prompts/` (saída aceita, verificação, pendências).
3. Atualize os índices afetados (`docs/specs/README.md`, a coluna "Spec" do backlog, "Estado atual" acima).
4. Relate o que foi feito, como foi verificado e o que ficou pendente, sem declarar como verificado algo que não foi executado.
