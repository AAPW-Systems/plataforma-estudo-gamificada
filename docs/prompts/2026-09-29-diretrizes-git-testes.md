# Diretrizes de git e testes

**Data:** 2026-09-29
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** estruturação
**Funcionalidade:** projeto

## Contexto fornecido

- `.agents/AGENTS.md`

## Prompts

### Prompt 1

```text
novas diretrizes a serem incluídas em  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\.agents\\AGENTS.md": 1) na fase de desenvolvimento, ao se implementar uma spec, deve-se sempre usar o git flow, sendo proibido implementar as funcionalidades diretamente na branch main. Por ser um projeto simples, vamos focar em ter a branch main e develop apenas, devendo o desenvolvimento e testes sempre ocorrer na develop, depois sendo unida à main mediante pull request ou merge. 2) usar convetional commits (já tem essa convenção descrita, apenas para reforçar). 3) buscar usar commits atômicos, a fim de facilitar a reversão no caso de bugs. 4) na fase de desenvolvimento, ao se criar cada spec deverão ser criados testes (principalmente os unitários, de integração, de segurança, funcional e adversariais), com pytest, devendo todos os testes passarem antes de qualquer merge com a main
```

### Prompt 2

```text
adicione o pytest no research.md
```

### Prompt 3

```text
adicione nas pendências o que ficou pendente nesta sessão
```

## Saída aceita

| Artefato | Ação |
|---|---|
| `.agents/AGENTS.md` | alterado: nova seção "Git e testes (fase de desenvolvimento)" com as regras 14 a 17; convenção de commits remete às regras; regra 17, "Estado atual" e mapa do repositório apontam para `docs/research.md` |
| `docs/research.md` | criado: `research.md` do projeto, para decisões técnicas transversais, com a DTEC 001 (pytest) |
| `docs/produto/pendencias.md` | alterado: QA-28 (complementos do pytest), QA-29 (testes do frontend), QA-30 (branch `develop` e verificação automática antes do merge) e VAL-05 (aprovação das regras de git e testes), com resumo e mapa de dependências |
| `docs/skills/padroes-implementacao.md` | alterado: seção "Testes" referencia a DTEC 001 e os marcadores por tipo de teste |
| `docs/prompts/2026-09-29-diretrizes-git-testes.md` | criado |
| `docs/prompts/README.md` | alterado (índice) |

## Alterações humanas

Pendente de revisão.

## Verificação

- Leitura do `AGENTS.md` alterado: numeração das regras existentes (1 a 13) preservada; novas regras numeradas de 14 a 17.
- Como nenhuma spec existe ainda, o pytest foi registrado em um `research.md` do projeto (`docs/research.md`), previsto em `produto/visao.md` ("`research.md` da funcionalidade ou do projeto"), seguindo o modelo de `sdd_guidelines/modelos/research.md`.
- Versão estável mais recente do pytest conferida no PyPI com `pip index versions pytest` (9.1.1).

## Pendências

Registradas em [`produto/pendencias.md`](../produto/pendencias.md):

- QA-28: complementos do pytest (dependem de QA-18).
- QA-29: ferramenta de testes do frontend.
- QA-30: criação da branch `develop`, integração contínua e proteção da `main`.
- VAL-05: aprovação das regras 14 a 17 do `AGENTS.md` e da DTEC 001 pela equipe.
