# AGENTS.md

Instruções canônicas para **qualquer** agente de programação (Claude, Codex, Cursor, Copilot, Gemini etc.) neste repositório. Os arquivos `AGENTS.md` e `CLAUDE.md` da raiz apenas apontam para este. Edite somente aqui.

## Projeto

Plataforma web de estudos gamificada para a disciplina de IA do curso de Sistemas de Informação. Funde repetição espaçada (algoritmo FSRS) com uma trilha visual de progressão. O estudante organiza os estudos em **matérias**, guarda nelas suas **fontes** e cria flashcards à mão ou pede à IA que os gere a partir das fontes, com referência ao trecho de origem; ele revisa os cartões gerados antes de aceitá-los. Os cartões são respondidos numa **trilha** unificada de lições, com XP, meta diária e sequência. No final acadêmico, cada matéria ganha um chat com as fontes (RAG), que responde apenas com base nelas e cita os trechos usados.

O produto tem três estágios: **MVP** (local), **final acadêmico** (publicado numa VPS) e **referência pós-acadêmica** (documentada, não implementada).

O projeto segue **SDD (Spec-Driven Development)** conforme as guidelines em `docs/sdd_guidelines/`, que devem ser seguidas **à risca**: o projeto é avaliado por elas.

## Estado atual

- **Fase:** alinhamento do produto e da arquitetura concluído (12/10/2026, [registro](../docs/prompts/2026-10-12-alinhamento-produto-arquitetura.md)). Esquema inicial do banco escrito em 12/10/2026 (`docs/arquitetura/esquema-inicial.dbml`, QA-21, [registro](../docs/prompts/2026-10-12-esquema-inicial-banco.md)). Specs 001 a 016 escritas em rascunho em 12/10/2026 (7 do MVP e 9 do final acadêmico, [registro](../docs/prompts/2026-10-12-specs-funcionalidades.md)). Specs do MVP (001 a 007) esclarecidas, revisadas pelo checklist e aprovadas para planejamento em 12/10/2026 por Artur Lins ([registro](../docs/prompts/2026-10-12-revisao-requisitos-specs-mvp.md)). Plano da 001 aprovado em 12/10/2026 por Artur Lins, com a estrutura base do repositório e as DTEC 015 a 023 ([registro](../docs/prompts/2026-10-12-001-conta-acesso-plano.md)). Tarefas (T001 a T065) e rastreabilidade da 001 aprovadas em 13/10/2026. Decisão de 13/10/2026: nenhum código é implementado antes de toda a documentação das specs do MVP (planos, tarefas e rastreabilidade da 002 a 007) estar pronta. Plano da 002 aprovado em 13/10/2026 por Artur Lins, com as DTEC 024 a 032 ([registro](../docs/prompts/2026-10-13-002-materias-fontes-plano.md)). Tarefas (T001 a T051) e rastreabilidade da 002 aprovadas em 13/10/2026 por Artur Lins. Plano da 003 aprovado em 13/10/2026 por Artur Lins, com as DTEC 033 a 038 e a emenda da DTEC 027 ([registro](../docs/prompts/2026-10-13-003-cartoes-manuais-plano.md)). Tarefas (T001 a T045) e rastreabilidade da 003 aprovadas em 13/10/2026 por Artur Lins. Plano da 004 aprovado em 13/10/2026 por Artur Lins, com as DTEC 039 a 047 ([registro](../docs/prompts/2026-10-13-004-geracao-cartoes-plano.md)); Tarefas (T001 a T059) e rastreabilidade da 004 aprovadas em 13/10/2026 por Artur Lins. Plano da 005 aprovado em 13/10/2026 por Artur Lins, com a DTEC 048 (transversal, dia de estudo) e as DTEC 049 a 056 ([registro](../docs/prompts/2026-10-13-005-licao-trilha-plano.md)). Tarefas (T001 a T049) e rastreabilidade da 005 aprovadas em 13/10/2026 por Artur Lins. Plano da 006 aprovado em 13/10/2026 por Artur Lins, com a DTEC 057 (transversal, disponibilidade e ganchos no núcleo) e as DTEC 058 a 063 ([registro](../docs/prompts/2026-10-13-006-xp-meta-sequencia-plano.md)). Tarefas (T001 a T045) e rastreabilidade da 006 aprovadas em 13/10/2026 por Artur Lins. Plano da 007 aprovado em 13/10/2026 por Artur Lins, com as DTEC 064 a 067, sem migração nem código de erro novo ([registro](../docs/prompts/2026-10-13-007-evolucao-plano.md)). Tarefas (T001 a T026) e rastreabilidade da 007 aprovadas em 13/10/2026 por Artur Lins. **Com isso, a documentação das specs do MVP (001 a 007) está completa e a implementação pode começar** (decisão de 13/10/2026 cumprida). Decisão de 14/10/2026 de Artur Lins: a proposta de divisão da implementação entre Artur Lins e Arthur Moura (`docs/specs/divisao-implementacao-mvp.md`) foi **descontinuada**; as specs do MVP são implementadas em sequência, uma de cada vez, por Artur Lins com o agente, sem ondas, antecipações nem pontos de sincronização com outra pessoa (os marcadores `[P]` e as frases sobre "pessoas diferentes" nas tarefas passam a indicar só independência de arquivos). A ordem segue os pré-requisitos das tarefas e a sequência das migrações `0001` a `0007`: 001 → 002 → 003 → base da 004 (T001 a T011) → 005 (com o restante da 004 em paralelo) → 006 → 007, que não tem migração e é o primeiro corte se o prazo apertar (suposição da spec). A implementação da 001 começou na `develop` em 13/10/2026, em paralelo ao plano da 007, por revisão da decisão anterior feita por Artur Lins ([registro](../docs/prompts/2026-10-13-001-conta-acesso-implementacao.md)). Implementação da 001 em andamento desde 13/10/2026 ([registro](../docs/prompts/2026-10-13-001-conta-acesso-implementacao-4.md)); US1 a US4 (T028 a T059) e a fase final, menos a T063 (teste guiado com três pessoas), que depende de pessoas, concluídas em 14/10/2026; a implementação da 002 foi concluída no código em 15/10/2026 (US1 a US3 e fase final, T001 a T051), com a T013 (Compose completo no Docker Desktop) e o leitor de tela da T048 em aberto por dependerem de pessoas ([registro](../docs/prompts/2026-10-15-002-materias-fontes-implementacao-2.md)); a próxima na sequência é a 003, que só começa por decisão de Artur Lins.
- **Produto:** visão v0.3 em `docs/produto/visao.md`; recorte por estágio em `docs/produto/backlog.md`; regras globais (RN, RF, HU, CB) em `docs/base-specs/spec.md`. O recorte do MVP foi aprovado em 12/10/2026; com o PO, seguem em pauta só as exigências consideradas incompatíveis, EX-01 e EX-05 (`docs/produto/pauta-po.md`, PO-01 e PO-02).
- **FSRS soberano (12/10/2026):** o agendamento é calculado só pela biblioteca `fsrs`; lição, meta, XP e sequência se adaptam a ele (RN-26 em `docs/base-specs/spec.md`).
- **Pendências:** `docs/produto/pendencias.md` lista o que está em aberto e o impacto de cada opção. Consulte antes de propor qualquer decisão técnica.
- **Exigências do PO:** `docs/produto/exigencias_po.md`. EX-01 a EX-05 estão no backlog; EX-01 e EX-05 aguardam resposta do PO.
- **Stack:** **aprovada em 12/10/2026** em `docs/arquitetura/README.md` e nas DTEC 001 a 014 de `docs/research.md` (FastAPI, PostgreSQL com pgvector, Procrastinate, autenticação própria com sessão em cookie, React com TypeScript e Tailwind, PydanticAI, Gemini e Groq, bge-m3 na Cloudflare no final acadêmico, pytest). Aprovadas com o plano da 001 em 12/10/2026: emenda da DTEC 002 (psycopg 3 no lugar do asyncpg), DTEC 015 (TanStack Router e Query, openapi-fetch), DTEC 016 (React Aria Components), DTEC 017 (GitHub Actions) e DTEC 018 (camadas DTO, mapeador, repositório e exceções); Python 3.13 com uv (alterado de 3.14 em 13/10/2026), Node 24 LTS com npm.
- **Código:** a criação de código, dependências, Dockerfiles e pastas de backend e frontend **está liberada**, dentro destes limites:
  - Use somente a stack aprovada. Tecnologia ou serviço fora dela exige antes uma nova DTEC no `research.md`.
  - A estrutura base (pastas, Compose, Dockerfiles, configuração, ferramentas de qualidade) segue a arquitetura e é registrada no "Mapa do repositório" abaixo e em `docs/skills/padroes-implementacao.md` assim que criada.
  - Comportamento de uma funcionalidade só é implementado com a spec, o plano e as tarefas dela aprovados (regra 1).
  - Todo código é escrito na branch `develop` (regra 14), com testes (regra 17).
- **Constituição:** v0.4 em rascunho, aguardando aprovação da equipe.
- **Specs:** 001 em `Implementando` (Fases 1 e 2 e as histórias P1, T001 a T045, na `develop` com o CI verde e o Compose completo verificado; US3 e US4 (T046 a T059) concluídas; fase final: T060 a T062, T064 e T065 concluídas e T063 pendente (teste guiado com três pessoas)); 002 em `Implementando` (todas as tarefas prontas na `develop` com evidência, exceto a T013, o Compose completo no Docker Desktop, e a T048, que só falta o leitor de tela; ambas dependem de pessoas e mantêm a spec em `Implementando`; backend com 1607 testes e frontend com 206, CI verde); 003 em `Tarefas aprovadas`; 004 em `Tarefas aprovadas`; 005 em `Tarefas aprovadas`; 006 em `Tarefas aprovadas`; 007 (MVP) em `Tarefas aprovadas`; 008 a 016 (final acadêmico) em `Especificando`. Cada spec pertence a um único estágio; o índice está em `docs/specs/README.md`.
- **Equipe:** Arthur Moura, Artur Lins, Caroline Santana, Pedro Paulo Lucena e William Johnson.
- **PO:** professor Aldo Nunes. Ainda não foi decidido se haverá um representante interno do PO na equipe.
- **Scrum Master:** rodízio semanal entre os integrantes (requisito obrigatório da disciplina).

Atualize esta seção sempre que a fase mudar.

## Leitura obrigatória antes de agir

1. `docs/constitution.md`: princípios que nenhuma entrega pode violar.
2. `docs/produto/visao.md` e `docs/produto/backlog.md`: o que é o produto e quais funcionalidades existem em cada estágio.
   - `docs/base-specs/`: regras globais (`spec.md`), telas (`design.md`) e orientação técnica (`plan.md`) que servem de base para cada spec. Cite os IDs dela; não os renumere.
   - `docs/arquitetura/README.md` e `docs/research.md`: arquitetura vigente e decisões técnicas. `docs/arquitetura/referencia-pos-academica.md` descreve o que **não** é implementado.
3. `docs/produto/exigencias_po.md` e `docs/produto/pauta-po.md`: exigências feitas diretamente pelo PO e itens em discussão com ele. **Consulta obrigatória ao escrever ou revisar qualquer spec.** Toda exigência que tocar a funcionalidade especificada deve ser coberta por requisitos da spec ou virar uma questão `Q-xxx`. Se uma exigência conflitar com a constituição ou com a visão, registre o conflito como questão para o PO; não o resolva por conta própria.
4. O guia de `docs/skills/` correspondente à tarefa:

| Tarefa | Guia |
|---|---|
| Criar ou avançar spec, plano, tarefas | `docs/skills/fluxo-sdd.md` e `docs/skills/contexto-tecnico.md` (resumo das decisões aprovadas; leia-o no lugar dos planos anteriores) |
| Qualquer sessão que altere arquivos | `docs/skills/registrar-prompt.md` |
| Código de backend, API, IA, testes | `docs/skills/padroes-implementacao.md` |
| Telas e componentes | `docs/skills/padroes-interface.md` |

5. Ao trabalhar em uma funcionalidade, todos os artefatos da pasta `docs/specs/NNN-*` correspondente.

## Mapa do repositório

```text
.agents/AGENTS.md          # este arquivo (fonte canônica para agentes)
AGENTS.md, CLAUDE.md       # ponteiros para este arquivo
README.md                  # visão geral para pessoas
compose.yaml, .env.example # ambiente completo (db, migrate, api, worker, web) e variáveis, sem segredos
.github/workflows/ci.yml   # integração contínua (DTEC 017): backend e frontend nas imagens dev
backend/                   # API e worker (Python 3.13, uv); Dockerfile, pyproject.toml, uv.lock, openapi.json
├── src/app/               #   um pacote por domínio (identidade, materias, fontes, revisao, saude) + nucleo (transversal)
├── migracoes/             #   migrações Alembic
└── tests/                 #   unit, integration, functional, security, adversarial, arquitetura
frontend/                  # interface (Node 24, npm); Dockerfile, Caddyfile (imagem prod), package.json
├── src/                   #   api/ (cliente e tipos gerados), componentes/ui/, funcionalidades/<dominio>/, rotas/, testes/
└── scripts/gerar-api.mjs  #   gera os tipos a partir de backend/openapi.json
docs/
├── constitution.md        # princípios estáveis do projeto
├── research.md            # decisões técnicas transversais (DTEC), válidas para todas as specs
├── arquitetura/           # arquitetura vigente (MVP e final acadêmico), referência pós-acadêmica e esquema inicial do banco (DBML)
├── base-specs/            # regras, telas e orientação técnica globais, base para as specs
├── produto/               # visão, backlog (recorte por estágio), pendências, exigências e pauta do PO
├── specs/NNN-nome-curto/  # uma pasta por funcionalidade (spec, plan, tasks...)
├── skills/                # guias de agente por tarefa, independentes de ferramenta
├── prompts/               # registro obrigatório de toda sessão com agente
├── reunioes/              # atas das reuniões da equipe (AAAA-MM-DD.md)
└── sdd_guidelines/        # material da disciplina: SOMENTE LEITURA
```

A estrutura de código segue a [arquitetura](../docs/arquitetura/README.md); `backend/` e `frontend/` foram criados na spec 001 e o mapa acima os descreve até o segundo nível (atualize-o quando um domínio ou uma pasta de primeiro nível nascer). **Backend e frontend são projetos separados**, cada um em sua pasta na raiz (`backend/` e `frontend/`), com dependências, testes e Dockerfile próprios. A fronteira entre eles é o contrato OpenAPI, e o `compose.yaml` da raiz sobe os dois ([arquitetura, seção 5.1](../docs/arquitetura/README.md#51-organização-mvc-por-domínio)). Até 12/10/2026, `docs/base-specs/` se chamava `docs/init/`; os registros de prompts anteriores a essa data citam o nome antigo.

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

8. **Fontes exclusivas:** a IA do produto usa apenas os materiais do usuário e sempre cita a origem (Princípio I). A única exceção é a consulta externa acionada pelo usuário no tira-dúvidas de um flashcard (F-16, fora do MVP), nas condições do Princípio I, que está em pauta com o PO (`docs/produto/pauta-po.md`, PO-02).
9. **Sem segredos no repositório:** chaves e tokens nunca aparecem em código, documentação, exemplos ou prompts registrados. Use `.env` (ignorado pelo git) e documente as variáveis em `.env.example`.
10. **Sem dados pessoais reais** em testes, exemplos ou demonstrações.
11. **Docker obrigatório:** todo serviço roda em contêiner. O ambiente completo sobe com um comando documentado.

### Arquivos protegidos

12. `docs/sdd_guidelines/` é **somente leitura**. `docs/base-specs/` pode ser atualizado, mas só para refletir decisões já registradas na visão, na constituição, nas specs aprovadas ou no `research.md`; ele nunca é o primeiro lugar de uma decisão nova. Os registros em `docs/prompts/` não são reescritos depois de encerrados.

### Produtos de terceiros

13. **Sem menção a produtos concorrentes ou de referência na documentação oficial.** Prompts e conversas podem citar aplicativos e ferramentas de terceiros como exemplo; isso serve apenas de contexto para o agente. README, constituição, documentos de produto, specs, planos, pesquisas, tarefas, skills e interface descrevem cada capacidade pelo que ela faz (ex.: "repetição espaçada", "chat com citações", "trilha de progressão"), nunca pelo nome ou pelo "estilo" de outro produto.
    - A regra não se aplica a tecnologias adotadas ou avaliadas no projeto (bibliotecas, frameworks, algoritmos, serviços), que continuam sendo nomeadas no `plan.md` e no `research.md`.
    - Exceções: `docs/prompts/`, que registra os prompts literalmente, e a pasta somente leitura `docs/sdd_guidelines/`.

### Git e testes (fase de desenvolvimento)

14. **Fluxo de branches simplificado:** o repositório usa apenas duas branches permanentes.
    - `main`: versão estável. **É proibido implementar funcionalidades diretamente na `main`.** Ela só recebe código por pull request (ou merge) vindo da `develop`.
    - `develop`: onde ocorrem o desenvolvimento e os testes de toda spec. Se ela ainda não existir ao iniciar a primeira implementação, crie-a a partir da `main`.
    - Nunca reescreva o histórico da `main` nem da `develop` (sem `push --force` e sem `rebase` de commits já publicados).
15. **Conventional Commits** em todo commit, com descrição em português (ver "Convenções").
16. **Commits atômicos:** cada commit contém uma única mudança lógica e coerente (ex.: uma tarefa `T-xxx` ou parte dela), deixa o projeto funcionando e os testes passando, e pode ser revertido com `git revert` sem arrastar mudanças não relacionadas. Não misture refatoração, correção e funcionalidade no mesmo commit.
17. **Testes obrigatórios por spec, com pytest** ([DTEC 001](../docs/research.md#decisão-dtec-001-ferramenta-de-testes-do-backend)): toda spec implementada vem acompanhada de testes automatizados escritos com pytest, cobrindo principalmente:
    - **Unitários:** regras e invariantes de negócio isoladas.
    - **De integração:** interação entre camadas e serviços reais (banco, fila, autenticação, provedor de IA simulado).
    - **Funcionais:** os critérios de aceitação das histórias da spec, de ponta a ponta pela API.
    - **De segurança:** autenticação, autorização, isolamento entre usuários, validação de entrada e ausência de vazamento de dados.
    - **Adversariais:** entradas maliciosas ou inesperadas (arquivos malformados, injeção de prompt nos materiais, payloads extremos, reenvios e concorrência).

    Os testes ficam ligados aos requisitos da spec pelo `traceability.md`. **Nenhum merge na `main` acontece sem que todos os testes passem**, executados na `develop` imediatamente antes do merge; testes falhando, pulados sem justificativa registrada ou desativados bloqueiam o merge.

## Convenções

- **Idioma:** documentação, interface e mensagens em português brasileiro. Identificadores do domínio em português, sem acentos (constituição, "Restrições do projeto").
- **Pastas de spec:** `docs/specs/NNN-nome-curto/`, com número de 3 dígitos e kebab-case sem acentos.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/pt-br/) com descrição em português (ex.: `docs: adiciona constituição v0.1`, `feat(materiais): implementa envio [T012]`). Referencie IDs de tarefa quando houver. Commits atômicos e fluxo de branches conforme as regras 14 a 16.
- **Datas em documentos:** `DD/MM/AAAA` no texto e `AAAA-MM-DD` em nomes de arquivo.
- **Banco de dados:** o [esquema inicial](../docs/arquitetura/esquema-inicial.dbml) é a referência do modelo, mas o SQL exportado pelo dbdiagram não é migração. As migrações (Alembic) criam as chaves primárias como `bigint generated always as identity`; a exportação gera `generated by default`, que aceitaria ids inseridos à mão. Em relações 1:1 no DBML, a FK é criada na tabela à direita da `Ref`.

## Como encerrar uma sessão

1. Verifique se os links relativos dos arquivos alterados funcionam.
2. Complete o registro em `docs/prompts/` (saída aceita, verificação, pendências).
3. Atualize os índices afetados (`docs/specs/README.md`, a coluna "Spec" do backlog, "Estado atual" acima).
4. Relate o que foi feito, como foi verificado e o que ficou pendente, sem declarar como verificado algo que não foi executado.
