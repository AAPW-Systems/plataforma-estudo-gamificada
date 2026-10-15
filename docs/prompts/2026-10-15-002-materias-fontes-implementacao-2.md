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

### Prompt 2

```text
Registre a emenda da DTEC 027. a hifenização podemos usar um regex simples em python para resolver, logo depois da extração. Co-Authored-By não deve ser usado nem nesse nem em nenhum outro projeto (decisão global). os testes de leitor de tela serão feitos todos ao final do projeto.

$ docker compose up -d --build --wait
[saída do Docker Desktop colada pelo usuário: imagens plataforma-api:dev e plataforma-web:dev construídas em 273,7 s; contêineres migrate (Exited), api, worker, web e db (Healthy)]
```

### Prompt 3 (mensagem enviada no meio do trabalho)

```text
vi aqui que todos os commits estão saindo em nome de claude, esse também é um comportamento indesejado, pois prejudica o git blame
```

## Estado de partida

- CI da `develop`: a execução 20 (`3abeda8`) foi cancelada pela execução seguinte; as execuções 21 (`518c414`) e 22 (`710b18f`, cabeça) estão **verdes**. Nada a corrigir.
- Linha de base no host: backend com 1475 testes (1 pulado, superusuário) e frontend com 161.

## Saída aceita

A implementação da 002 está **concluída**: US3 (T040 a T046) e fase final (T047 a T051) com evidência, mais a T013 verificada por Artur Lins no Docker Desktop. O leitor de tela da T048 foi adiado, por decisão de Artur Lins, para uma rodada única no final do projeto. Todas as tarefas têm evidência, e a spec passa a **Convergida**.

| Artefato | Ação |
|---|---|
| `backend/src/app/materias/{dominio,dtos,excecoes,mapeadores,repositorios,rotas,servicos}.py` | alterados: renomear, impacto da exclusão e exclusão em cascata da matéria |
| `backend/src/app/fontes/{rotas,servicos,registros}.py` | alterados: renomear o título da fonte; participante trava as fontes da matéria e recusa apagar sem armazenamento |
| `backend/src/app/nucleo/participantes_acervo.py` | alterado: gancho opcional `travar_para_exclusao_de_materia` e `RegistroAcervo.travar_materia` |
| `backend/openapi.json`, `frontend/src/api/{esquema.gerado.d.ts,limites.gerado.ts}` | regenerados |
| `backend/tests/{functional,adversarial}/materias/`, `tests/security/`, `tests/unit/`, `tests/integration/test_contrato_openapi.py`, `tests/{apoio_acervo,participantes_falsos}.py` | criados e alterados: testes da US3, isolamento das quatro rotas novas, exclusão da conta com acervo completo |
| `frontend/src/funcionalidades/{acervo,materias,fontes}/`, `src/api/acervo.ts`, `src/estilos/global.css`, `src/rotas/_autenticado/materias/$materiaId.tsx` | criados e alterados: renomear no lugar, diálogo de exclusão da matéria, cabeçalho da matéria, renomear a fonte no painel |
| `docs/specs/002-materias-fontes/{tasks,traceability,quickstart,README}.md` | T040 a T047 e T049 a T051 marcadas com evidência; T048 parcial; nomes reais dos testes; medições; passo a passo da US3 |
| `docs/skills/{padroes-implementacao,contexto-tecnico}.md`, `.agents/AGENTS.md`, `docs/prompts/README.md` | alterados: padrões do acervo, estado das specs, Mapa do repositório, "Estado atual" e índice |

## Alterações humanas

Pendente de revisão.

## Verificação

**Ambiente da sessão.** Contêiner de nuvem Linux (não o Windows com Docker Desktop da equipe). Backend no host (`uv`, Python 3.13, `UV_PROJECT_ENVIRONMENT` fora do repositório) contra o PostgreSQL 16 do sistema; frontend nos Node 22 e 24; Chromium do Playwright global. O *build* das imagens do Compose é bloqueado pela rede do ambiente, então o `docker compose up --build` completo **não foi executado**; o CI do GitHub é a verificação em contêiner.

- **CI da `develop`:** execuções 21 (`518c414`) e 22 (`710b18f`) verdes na partida; execução 23 (`95ada97`, código da US3) e execução 24 (`0217345`, com a documentação da fase final) verdes nos dois jobs. O commit que registra estes resultados é só de documentação e o seu CI não foi aguardado.
- **Backend no host:** `ruff format --check`, `ruff check` e `mypy` limpos; **1607 passed e 1 skipped** (permissão de escrita, pulado como superusuário) em três execuções completas seguidas (a terceira com cobertura: **94%**). Linha de base de partida: 1475. Os 132 testes novos incluem 32 funcionais e 35 adversariais da US3, os unitários do domínio e do registro de participantes, os de isolamento e de proteções herdadas das rotas novas (parametrizados) e o de exclusão da conta com acervo completo.
- **Frontend:** **206 passed** nos Node 22 e 24 (de 161), `eslint`, `tsc`, `prettier --check` e `vite build` limpos; cobertura de 93,3% das instruções e 96,5% das linhas.
- **Vermelho antes do verde:** as suítes novas do backend começaram com 76 falhas (rotas inexistentes) e as de componente com 4 arquivos sem os componentes; as duas correções de cache da lista de matérias nasceram de 2 testes vermelhos.
- **Mutações verificadas (cada uma derrubou o teste esperado):** sem a trava das fontes antes de contar; sem o recálculo do impacto; sem a conferência do nome digitado; sem o `FOR UPDATE` da matéria (a segunda exclusão paralela passou a dar `409` em vez de `404`).

### Evidência da T013 e da hifenização (continuação, 15/10/2026)

- **T013:** Artur Lins rodou `docker compose up -d --build --wait` no Docker Desktop e colou a saída: imagens construídas, `migrate` terminado e `db`, `api`, `worker` e `web` `Healthy`. O *healthcheck* da `api` exige `200` em `/health/ready`, que grava e apaga um objeto no volume `arquivos`.
- **Hifenização:** `tests/unit/fontes/test_extracao.py` e `tests/integration/fontes/test_extracao.py::test_hifenizacao_do_pdf_e_desfeita_depois_da_extracao`. Com a função trocada por uma que devolve o texto como veio, 11 testes falham. Backend no host depois da mudança: `ruff` e `mypy` limpos, **1629 passed, 1 skipped**.

### Evidência da T046 (US3, Chromium real)

API, worker, Vite e PostgreSQL locais; arquivos fictícios gerados por `python -m tests.fabricas_arquivos`; conta e dados criados pela interface. **21 de 21 verificações:** foco no campo ao abrir o renomear e nome atual preenchido; nome em uso recusado junto do campo, com o valor preservado e `aria-invalid`; novo nome normalizado no título e na lista, e foco devolvido ao botão; título da fonte vazio recusado e novo título no painel, que mantém arquivo e trechos; diálogo de exclusão da matéria com «2 fontes», botão desabilitado de início e com a caixa diferente, foco preso em 8 Tab, Escape fecha e devolve o foco, cancelar não exclui e o nome digitado é descartado; confirmação com o nome exato leva à lista, sem a matéria excluída; axe sem violações no formulário com erro, no diálogo aberto e na lista. No banco, nenhuma linha de fonte ou trecho da matéria excluída e, no volume, nenhum arquivo; os logs trazem `materia_excluida` só com `public_id` e contagens.

**Achado:** depois de excluir ou renomear, a lista de matérias (não montada na página da matéria, só invalidada) mostrava por um instante a matéria excluída ou o nome velho. Corrigido no cache (`95ada97`), com dois testes.

### Evidência da T048 (acessibilidade, logs, repositório)

axe (WCAG 2.2 AA) no Chromium real: **82 de 82 verificações** em tema claro e escuro (`data-tema="escuro"`), a 1100 px e a 320 px, na lista de matérias, na página da matéria (envio e acervo), no formulário de renomear a matéria e a fonte com erro, no painel da fonte e nos **dois diálogos de exclusão abertos**; sem rolagem horizontal a 320 px; Cancelar, Salvar, Excluir e o campo do nome alcançáveis dentro da tela; Tab alcança as cinco ações principais; foco visível com contorno de 3 px. Logs reais (1.831 linhas da `api`, 139 do `worker`): sem nome, título, e-mail, senha nem texto de trecho. Repositório: sem segredos e sem arquivos gerados versionados. **Falta o leitor de tela (pessoa).**

### Evidência da T049 (medições)

PDF fictício de 2 MB (380 páginas, 760 trechos): envio até **Concluído** em 8,9 s a 9,2 s (10 rodadas; meta de 60 s); resposta do envio com mediana de 251 ms (1 MB) e 262 ms (2 MB), máximo de 295 ms; pico de memória: 114 MiB no subprocesso de extração e 130 MiB no processo do worker (teto de 512 MiB por extração); na API, 155 MiB no processo e 65 MiB no subprocesso da verificação (teto de 256 MiB). A amostragem lê `/proc` a cada 20 ms; o script de medição ficou no diretório temporário da sessão e não foi versionado.

## Decisões e divergências a confirmar com Artur Lins

- **Gancho opcional da DTEC 027 (decidido em 15/10/2026):** registrado como emenda da DTEC 027 em `docs/research.md`, com a 003, a 004 e a 014 como responsáveis por implementá-lo nos participantes delas.
- **Participante de `fontes` sem armazenamento:** antes, ignorava os objetos em silêncio (órfãos); agora levanta `RuntimeError`. O armazenamento é entregue no `lifespan` da API.
- **Ordem das recusas na exclusão da matéria:** primeiro o nome digitado (`422`), depois o impacto (`409`). Um cliente com os dois errados recebe o `422`.
- **Hifenização (DTEC 029), decidida em 15/10/2026:** regra simples em Python (`desfazer_hifenizacao`) logo depois da extração do PDF, em vez do `TEXT_DEHYPHENATE` que não funciona; emenda registrada em `specs/002-materias-fontes/research.md`, versão da extração `v2`, commit `f413871`. Limite conhecido e testado: um composto quebrado na linha ("guarda-\nchuva") também é juntado.
- **Autoria e rodapé dos commits (decisão global de Artur Lins, 15/10/2026):** nenhum `Co-Authored-By`, em nenhum projeto, e os commits saem em nome de quem conduz, não do agente, para o `git blame` mostrar a pessoa. Os 6 commits desta sessão até o `49a5369` e os anteriores saíram com a autoria `Claude <noreply@anthropic.com>` (identidade padrão do ambiente de nuvem); como a regra 14 proíbe reescrever o histórico da `develop`, eles ficam. A partir do `f413871` a identidade do repositório é `Artur Lins <artur.olins@gmail.com>` (configuração local do clone). Sugestão, não aplicada: um `.mailmap` na raiz mapearia `Claude <noreply@anthropic.com>` para Artur Lins na exibição do `git blame` e do `git log`, sem reescrever nada.
- **Observação sobre logs:** as linhas do Procrastinate (`Starting job fontes.processar_fonte[2](fonte_id=1)`) trazem o `id` interno numérico da fonte; não é conteúdo nem sai pela API, mas é um identificador interno em log.
- **Cobertura:** `fontes/extracao.py`, `nucleo/isolamento.py` e `worker.py` aparecem baixos (16%, 67% e 0%) porque rodam em subprocessos que a cobertura não acompanha; têm testes de integração que os exercem.

## Pendências

- **Rodada final com leitor de tela (decisão de 15/10/2026):** lista de matérias, página da matéria, envio e os dois diálogos de exclusão da 002, junto com os da 001 (T061).
- **Teste guiado com três pessoas da 001 (T063)**, que segue aberto.
- **Autoria dos commits antigos:** decidir se entra um `.mailmap` (ver "Decisões").
- **Quando a 003 começar:** reexecutar os testes funcionais da US2 e da US3 da 002 com cartões reais e implementar o gancho `travar_para_exclusao_de_materia` no participante dos cartões (DTEC 027, emenda). A 003 não foi iniciada.
