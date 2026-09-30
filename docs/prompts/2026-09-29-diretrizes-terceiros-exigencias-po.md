# Diretrizes sobre produtos de terceiros e exigências do PO

**Data:** 2026-09-29
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** estruturação
**Funcionalidade:** projeto

## Contexto fornecido

- `.agents/AGENTS.md`
- `README.md`
- `docs/produto/exigencias_po.md` (criado pela equipe antes da sessão)

## Prompts

### Prompt 1

```text
novas diretrizes a serem aplicadas no projeto via  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\.agents\\AGENTS.md": mesmo que os prompts tragam exemplos de ferramentas de terceiros,ela devem ser utilizadas apenas como contexto, na documentação oficial não deve ser mencionado (ex.: duolingo, anki, notebook lm). Sendo necessário ajustar o  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\README.md". No futuro, ao criar as specs, não devem ter a menção também de ferramentas concorrentes. Aproveitando a atualização de diretrizes, um novo documento foi criado, em que o PO fez novas exigências, em  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\docs\\produto\\exigencias_po.md", devendo esse documento ser sempre consultado no momento de escrita das specs
```

### Prompt 2

```text
precisaremos ajustar o escopo para os pedidos do PO, a busca na internet não fará parte do MVP, mas estará presente na versão final. A ideia do PO é permitir que o usuário, através de um flashcard, consulte um chat para tirar dúvidas da questão, permitindo, inclusive, a consulta externa. Ao nosso ver, é uma funcionalidade a ser considerada como extra, o happy path ainda será fazer o fluxo normal. Faça a inclusão das novas exigências no backlog, e deixe claro no  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\docs\\produto\\exigencias_po.md" que já foram movidas pra lá.
```

### Prompt 3

```text
a equipe tem uma nova integrante: Caroline Santana, adicione-a nos documentos que citam a equipe
```

## Saída aceita

| Artefato | Ação |
|---|---|
| `.agents/AGENTS.md` | alterado: regra 13 (produtos de terceiros), exigências do PO no estado atual, na leitura obrigatória e no mapa |
| `README.md` | alterado: descrição sem produtos de terceiros; exigências do PO no guia e na estrutura |
| `docs/produto/visao.md` | alterado: produtos de terceiros substituídos pela descrição das capacidades; escopo ajustado às exigências do PO (F-16, consulta externa, QA-26, QA-27) |
| `docs/produto/exigencias_po.md` | alterado: IDs EX-01 a EX-05, texto original preservado, situação "movida para o backlog" e destino |
| `docs/produto/backlog.md` | alterado: F-16, F-04 e F-05 ampliadas, seção "Exigências do PO", recorte e ordem do MVP |
| `docs/produto/pendencias.md` | alterado: QA-26, QA-27, VAL-01 e VAL-02 (constituição v0.3) |
| `docs/constitution.md` | alterado: v0.3, exceção da consulta externa no Princípio I e regras no Princípio II |
| `docs/skills/fluxo-sdd.md` | alterado: exigências do PO e regra de terceiros no fluxo da spec |
| `docs/prompts/README.md` | alterado: índice |
| `README.md`, `.agents/AGENTS.md`, `docs/constitution.md`, `docs/produto/pendencias.md`, `docs/produto/backlog.md` | alterados (prompt 3): Caroline Santana incluída na equipe, em ordem alfabética; contagens de "quatro" para "cinco" integrantes |
| `docs/prompts/2026-09-29-diretrizes-terceiros-exigencias-po.md` | criado |

## Alterações humanas

Pendente de revisão.

## Verificação

- Busca por nomes de produtos de terceiros em todo o repositório, fora de `docs/prompts/`, `docs/init/` e `docs/sdd_guidelines/`: nenhuma ocorrência restante.
- Links relativos dos arquivos alterados conferidos por script.

## Pendências

- O registro do brainstorming aprofundado mantém a lista de quatro integrantes, pois é histórico literal.
- `docs/prompts/` mantém as menções a produtos de terceiros, pois os prompts são registrados literalmente. `docs/init/` e `docs/sdd_guidelines/` são somente leitura.
- Conflito de EX-01 com o Princípio I resolvido pelo prompt 2: consulta externa só no tira-dúvidas do flashcard (F-16), fora do MVP. A exceção entrou na constituição v0.3, que depende de aprovação da equipe (VAL-02).
- Decisão do agente, a confirmar: F-16 entrou no MVP restrito aos materiais (EX-04), como caminho opcional, e é o segundo corte se faltar prazo. O ajuste do recorte depende da validação com o professor (VAL-01).
- QA-26 (significado dos níveis de dificuldade) precisa ser perguntada ao professor antes da spec de F-04.
- QA-27 (regras da consulta externa) fica para antes da spec do incremento de F-16.
