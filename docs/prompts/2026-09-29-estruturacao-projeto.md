# Estruturação do projeto no padrão SDD

**Data:** 2026-09-29
**Autor:** Artur
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** estruturação (anterior à constituição e às specs)
**Funcionalidade:** projeto

## Contexto fornecido

- `docs/sdd_guidelines/` (guidelines SDD da disciplina: apostila, modelos, exemplos e atividades)
- `docs/init/` (brainstorming inicial: `Spec.md`, `Plan.md`, `Tasks.md`, `SKILL.md` e `DESIGN.md`)
- Pastas vazias `docs/prompts/`, `docs/specs/`, `docs/skills/` e `.agents/`

## Prompts

### Prompt 1

```text
precisamos organizar esse projeto numa estrutura de pastas que siga o padrão delimitado em  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\docs\\sdd_guidelines" . será um projeto em que será feita uma plataforma de estudos gamificada, que vai unir a estrutura de flashcards (inspirada no anki) porém com um ritmo de estudos ditado de forma gamificada (inspirada no duolingo, com streaks diários, pontos de experiência, uma rota que demonstre a progressão, etc.). Esse projeto será levado para a avaliação e as guidelines do sdd precisam ser seguidas a risca. também é essencial que todos os prompts sejam salvos em  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\docs\\prompts" , para que seja documentado. As specs com seus devidos planos deverão estar em  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\docs\\specs" . foi feito um brainstorming inicial por um dos componentes da equipe em  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\docs\\init" que precisa ser passado para o padrão do projeto. Como o trabalho é em equipe e nem todos usam o claude, ao invés de uma pasta .claude, será usada a pasta  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\.agents" para ter o agents.md. faça uma análise das guidelines e organize a estrutura do projeto. depois da estruturação, rodarei outra sessão para um brainstorming aprofundado, nesse momento, é importante apenas documentar o agents.md inicial e a estrutura do projeto, aproveitando o que já foi feito do brainstorming inicial. se tiver dúvidas, pergunte antes de gerar qualquer coisa
```

### Resposta a esclarecimento 1

```text
[Agente] O brainstorming inicial exclui repetição espaçada e streaks, e centra o produto em IA gerando conteúdo a partir de materiais enviados. Como tratar esse conflito agora?

[Resposta] o projeto é para uma matéria de IA na faculdade de sistemas de informação, então a IA é essencial. Inicialmente temos que criar o MVP com funcionalidades mais simples. No caso, vai permitir o usuário fazer upload de materiais de estudo e com base nele vai criar os flashcards. também terá um rag estilo uma versão simplificada do notebook lm da google. Ainda não decidimos o escopo do mvp, então é algo que pode ser decidido posteriomente, mas é importante de agora traçarmos o escopo da plataforma completa, ainda que de forma simples, a ser complementada posteriormente. no brainstorming aprofundado também iremos definir a stack e um esquema inicial do banco de dados. é obrigatório o uso de docker também. ao definir a stack também vamos definir se front e backend serão feitos de forma separada
```

### Resposta a esclarecimento 2

```text
[Agente] Como decompor o Spec.md monolítico no formato SDD (uma pasta por funcionalidade)?

[Resposta] Constituição + backlog (Recomendado): gerar constitution.md e um backlog/visão do produto mapeando HUs/RFs a funcionalidades candidatas; pastas specs/NNN-* só são criadas no brainstorming, uma de cada vez, com revisão.
```

### Resposta a esclarecimento 3

```text
[Agente] Um AGENTS.md apenas em .agents/ não é descoberto automaticamente pelas ferramentas. Como fazer?

[Resposta] Canônico + ponteiros (Recomendado): .agents/AGENTS.md é a fonte única; na raiz, AGENTS.md e CLAUDE.md de poucas linhas apenas apontam para ele.
```

### Resposta a esclarecimento 4

```text
[Agente] Qual o papel da pasta docs/skills?

[Resposta] Guias de agente por tarefa (Recomendado): instruções reutilizáveis e agnósticas de ferramenta; SKILL.md e DESIGN.md do init migram para cá após extrair os princípios para a constituição.
```

## Análise registrada pelo agente

- As guidelines exigem uma pasta por funcionalidade (`specs/NNN-nome-curto/`), com `spec.md`, `plan.md` e `tasks.md` como núcleo, uma constituição com princípios estáveis, portões de revisão humana entre as etapas e o modelo de spec ancorado.
- O `docs/init/Spec.md` descreve o sistema inteiro em um único arquivo, com a linha HU-12 da tabela quebrada e o RF-13 solto. `SKILL.md` e `DESIGN.md` funcionam como constituição, mas misturam princípios com detalhes de implementação.
- O init coloca a repetição espaçada e a sequência diária fora do escopo, o que conflita com a visão Anki + Duolingo. O conflito foi resolvido pela resposta 1 e registrado em `docs/produto/visao.md`.

## Saída aceita

| Artefato | Ação |
|---|---|
| `.agents/AGENTS.md` | criado (instruções canônicas para agentes) |
| `AGENTS.md` | criado (ponteiro) |
| `CLAUDE.md` | criado (ponteiro) |
| `README.md` | criado (visão geral e mapa do repositório) |
| `docs/constitution.md` | criado (v0.1, rascunho) |
| `docs/produto/visao.md` | criado (escopo da plataforma completa e questões QA-12 a QA-22) |
| `docs/produto/backlog.md` | criado (funcionalidades F-01 a F-13 rastreadas ao init) |
| `docs/skills/README.md` | criado |
| `docs/skills/fluxo-sdd.md` | criado |
| `docs/skills/registrar-prompt.md` | criado |
| `docs/skills/padroes-implementacao.md` | criado (migrado de `init/SKILL.md`) |
| `docs/skills/padroes-interface.md` | criado (migrado de `init/DESIGN.md`) |
| `docs/specs/README.md` | criado (convenção de pastas e índice) |
| `docs/prompts/README.md` | criado (convenção e modelo de registro) |
| `docs/prompts/2026-09-29-estruturacao-projeto.md` | criado (este registro) |
| `docs/init/README.md` | criado (marca o init como registro histórico e mapeia o destino do conteúdo) |
| `.gitignore` | criado (impede versionar `.env` com segredos) |
| `.gitattributes` | criado (finais de linha LF, necessários para scripts em contêineres com equipe em Windows) |

Os arquivos originais de `docs/init/` e `docs/sdd_guidelines/` não foram alterados.

## Alterações humanas

Pendente de revisão.

## Verificação

- Links relativos entre os documentos conferidos por script ao final da sessão.
- Nenhum segredo ou dado pessoal de terceiros incluído.

## Pendências

- Aprovação da constituição v0.1 pela equipe.
- Brainstorming aprofundado: recorte do MVP (QA-12), stack e separação entre front e backend (QA-18), esquema inicial do banco (QA-21), identidade visual (QA-19) e demais questões em `docs/produto/visao.md`.
- Completar os guias de `docs/skills/` com as seções dependentes da stack depois de QA-18.
