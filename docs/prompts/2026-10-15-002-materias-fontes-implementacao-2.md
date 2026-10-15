# Retomada da spec 002 a partir da T040 (US3 e fase final)

**Data:** 2026-10-15
**Autor:** Artur Lins (condução); implementação pelo agente
**Agente e modelo:** Claude Code (o identificador do modelo não é registrado em artefatos do repositório)
**Etapa SDD:** implementar
**Funcionalidade:** 002-materias-fontes

## Contexto fornecido

- Continuação do [registro anterior](2026-10-14-002-materias-fontes-implementacao.md), interrompido de propósito depois da US2 (T001 a T012 e T014 a T039 prontas; T013 humana).
- Esta sessão rodou num contêiner de nuvem Linux novo. O clone inicial estava na cabeça da `develop` (`710b18f`), com o CI verde (execução 22). O ambiente local foi refeito: PostgreSQL 16 do sistema, backend no host com `UV_PROJECT_ENVIRONMENT` fora do repositório, Node 22 (do contêiner) e Node 24 (instalado no diretório temporário da sessão, o do CI) e o Chromium do Playwright global.

## Prompts

### Prompt 1

```text
Continue a implementação da spec 002 (docs/specs/002-materias-fontes) na branch `develop`, a partir da T040
(US3: organizar matérias e fontes), seguindo o AGENTS.md e o SDD à risca. Antes de agir, leia o AGENTS.md,
o registro docs/prompts/2026-10-14-002-materias-fontes-implementacao.md (inclusive "Achados do CI",
"Decisões e divergências" e "Pendências"), o tasks.md da 002 e docs/skills/contexto-tecnico.md.

Estado de partida: T001 a T012 e T014 a T039 prontas e marcadas com evidência; T013 é humana (Artur Lins roda
o Compose no Windows). Backend: 1475 testes no host; frontend: 161 testes (rode também no Node 24, o do CI).
Primeiro confira o CI da `develop` (execução 20, commit 3abeda8 e seguintes) e corrija o que estiver vermelho.

Regras: testes antes do código (mostre vermelho, depois verde); um commit atômico por tarefa ou par
teste+implementação; suíte completa verde e `git pull --rebase origin develop` antes de cada push; só
`pymupdf` e `python-multipart` como dependências novas; dúvida de produto vira Q-xxx e pergunta a Artur;
marque [x] só com evidência. Não escreva identificador de modelo em artefatos do repositório. Não comece a 003.

Faça: US3 (T040 a T046): renomear matéria e fonte, excluir matéria com o nome digitado (reuse
ImpactoAlterado do núcleo, `travar_acervo` e a ordem dos participantes de DTEC 027/031), e o teste de exclusão
de conta com matérias, fontes e objetos; depois a fase final (T047 a T051): suítes, cobertura, CI, revisão de
logs/segurança/acessibilidade com axe no navegador real em 2 temas e a 320 px (inclusive o diálogo aberto),
medições (CS-003, tempo de envio, pico de memória), quickstart, padroes-implementacao.md, Mapa do repositório,
traceability.md e status da 002 em `Implementando`.

Ambiente local de verificação (se o contêiner for novo): backend no host com UV_PROJECT_ENVIRONMENT fora do
repositório contra um PostgreSQL local; para o navegador, Playwright global (/opt/node-tools) com o Chromium
em /opt/pw-browsers; ao simular falha de permissão como root, rode o worker como outro usuário (setpriv).
Cuidado: `pkill -f` com padrão que aparece na própria linha de comando mata o shell; use PIDs.

Ao encerrar: links relativos conferidos, registro completo, índices e "Estado atual" atualizados; relate o que
foi feito, como foi verificado e o que ficou pendente, sem declarar verificado o que não foi executado, e
repita o pedido a Artur sobre a T013 e as verificações humanas.
```

## Estado de partida

- CI da `develop`: a execução 20 (`3abeda8`) foi cancelada pela execução seguinte; as execuções 21 (`518c414`) e 22 (`710b18f`, cabeça) estão **verdes**. Nada a corrigir.
- Linha de base no host: backend com 1475 testes (1 pulado, superusuário) e frontend com 161.

## Saída aceita

*(preenchida ao encerrar a sessão)*

## Alterações humanas

Pendente de revisão.
