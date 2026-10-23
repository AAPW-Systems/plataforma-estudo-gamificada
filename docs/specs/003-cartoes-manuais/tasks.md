# Tarefas da funcionalidade

**Funcionalidade:** 003-cartoes-manuais (cartões criados e gerenciados pelo estudante)  
**Entrada:** [spec](spec.md), [plano](plan.md) (aprovado em 13/10/2026), [pesquisa](research.md), [modelo de dados](data-model.md), [contrato](contracts/openapi.yaml) e [quickstart](quickstart.md)  
**Formato:** `[ID] [P?] [US?] ação com caminho exato e resultado verificável`  
**Status:** aprovadas em 13/10/2026 por Artur Lins (equipe), junto com a [rastreabilidade](traceability.md)

- `[P]` indica que a tarefa pode ser executada em paralelo, porque não altera os mesmos arquivos nem depende de outra tarefa pendente.
- `[US1]` relaciona a tarefa a uma história de usuário.
- Marque `[x]` somente quando o resultado e a sua verificação estiverem concluídos (regra 6).
- **Caminhos:** `backend/src/app/` aparece abreviado como `app/`, e `backend/tests/` como `tests/`.
- **Pré-requisitos:**
  - as tarefas da [spec 001](../001-conta-acesso/tasks.md) até a US2 (T001 a T045): estrutura base, sessão, CSRF, contrato (T037), teste que percorre as rotas (T041) e auxiliar de busca por dono (T043);
  - as tarefas da [spec 002](../002-materias-fontes/tasks.md) até a US1 (T001 a T031): matérias, fontes, o registro de participantes (T005) e o `DialogoConfirmacao` (T012);
  - para a T011, também as US2 e US3 da 002 (T032 a T046), cujos testes funcionais ela reexecuta com cartões reais.
- **Testes antes do código:** em cada história, as tarefas de teste vêm antes das de implementação. Os testes começam falhando e passam ao fim da história.
- **Commits:** todo trabalho acontece na `develop` (regra 14), com um commit atômico por tarefa ou por par teste e implementação, citando o ID da tarefa (ex.: `feat(cartoes): implementa a criação [T015]`). O escopo do commit (`cartoes`) identifica a spec.

## Fase 1 Preparação

- [x] T001 Acrescentar os limites dos cartões:
  - **`.env.example`:** `CARTAO_FRENTE_MAX=1000`, `CARTAO_VERSO_MAX=2000` e `CARTAO_EXPLICACAO_MAX=1000` ([plano](plan.md#variáveis-de-ambiente-acréscimos-ao-envexample)).
  - **Configuração:** os campos correspondentes e os tetos (4.000, 8.000 e 4.000) em `app/nucleo/configuracao.py`.

  **Testes** em `tests/unit/nucleo/test_configuracao.py`: a aplicação não sobe com limite menor que 1 ou acima do teto, e sobe com os padrões (D-004, DTEC 036).
- [x] T002 [P] Acrescentar a `frontend/eslint.config.js` a regra nativa `no-restricted-syntax` com o seletor `JSXAttribute[name.name='dangerouslySetInnerHTML']` (DTEC 036, RQ-001). **Verificação:** um arquivo temporário com o atributo faz `docker compose run --rm web npm run lint` falhar, e o código atual passa.

## Fase 2 Base compartilhada (bloqueia todas as histórias)

- [x] T003 Criar a entidade e a migração dos cartões:
  - **Entidade:** `app/cartoes/modelos.py` (Cartao), com os enums `OrigemCartao`, `SituacaoCartao` e `EstadoFsrs`.
  - **Migração** `backend/migracoes/versions/0004_cartoes.py`, conforme o [modelo de dados](data-model.md):
    - `CREATE EXTENSION IF NOT EXISTS unaccent` (DTEC 033);
    - enums `origem_cartao` (três valores), `situacao_cartao` (`ativo` e `suspenso`) e `estado_fsrs`;
    - tabela `cartoes` sem `geracao_id`, `dominado_em` e `chave_imagem`, com PK `generated always as identity` e `public_id` com `gen_random_uuid()`;
    - FK composta `(materia_id, usuario_id)` → `materias` e FK composta `(fonte_id, materia_id, usuario_id)` → `fontes`, ambas `restrict`;
    - índice único `fontes_id_materia_usuario` em `fontes`;
    - os `CHECK` de tamanho, de cópias da referência, de referência só em `criado` e de `entrada_estudo_em`;
    - os índices `cartoes_devidos`, `cartoes_novos`, `cartoes_materia` e `fonte_id`;
    - a descida remove tudo, menos a extensão.

  **Verificação:** `tests/integration/test_migracoes.py` sobe e desce. `tests/integration/cartoes/test_restricoes.py` mostra que:
  - cada `CHECK` recusa a linha inválida;
  - a FK composta impede um cartão numa matéria de outro dono e uma referência a uma fonte de outra matéria ou de outro dono;
  - apagar uma fonte citada falha por `restrict`, e com `fonte_id` nulo a linha continua válida (DTEC 035).
- [ ] T004 [P] Criar `tests/fabricas_cartoes.py`, com a linha de comando `python -m tests.fabricas_cartoes --email --materia --quantidade`. A linha de comando só roda com `APP_AMBIENTE=desenvolvimento` e só para contas do domínio `exemplo.com` (regra 10). A fábrica gera:
  - cartões manuais com e sem referência;
  - cartões `gerado_verificado` inseridos direto (RF-006);
  - cartões suspensos;
  - cartões em estados do FSRS diferentes (novo, revisão, reaprendizado), para o CS-002;
  - textos com acentos, cedilha, maiúsculas, curingas (`%`, `_`, `\`), marcação e script, quebras de linha e emoji.

  Teste em `tests/unit/test_fabricas_cartoes.py`: cada cartão gerado respeita os `CHECK` e os limites, e a linha de comando recusa outro ambiente e outro domínio.
- [ ] T005 [P] Ampliar `tests/arquitetura/test_camadas.py`: `app/materias` e `app/fontes` não importam `app/cartoes`, e `app/cartoes/dominio.py` e `cursor.py` não importam FastAPI nem SQLAlchemy.
- [ ] T006 [P] Criar em `frontend/src/componentes/ui/`, sobre o React Aria (DTEC 016), cada um com teste e `vitest-axe`:
  - `CampoTextoLongo`: `TextArea` com rótulo, erro associado por `aria-describedby`, contador em *code points* (`[...texto.normalize('NFC')].length`) e limite recebido por propriedade (DTEC 036);
  - `SeloOrigem`: "Gerado e verificado", "Editado por você", "Criado por você" e o complemento "Fonte apagada", sempre com texto e ícone (RF-009, RQ-003).
- [ ] T007 **Verificar a base:** `docker compose up --build` aplica a `0004`, a extensão `unaccent` existe (`\dx` no `psql`) e a integração contínua passa na `develop`. Registrar a evidência no registro de prompts da sessão de implementação.

## Fase 3 História de usuário 1 Criar um cartão (P1)

**Objetivo:** o estudante cria um cartão com frente, verso, explicação opcional e, se quiser, uma fonte da matéria como referência. O cartão aparece na lista como ativo, com a origem honesta, e fica pronto para entrar nas lições como cartão novo.  
**Teste independente:** criar um cartão na matéria "Biologia" e confirmar que ele aparece na lista com "Criado por você" e que o estado gravado é o de um cartão novo na ordem de criação (passos 1 a 7 da US1 no [quickstart](quickstart.md)). A entrada numa lição real é reverificada pela 005.

- [ ] T008 [P] [US1] Criar os testes unitários em `tests/unit/cartoes/test_dominio.py` e `tests/unit/cartoes/test_cursor.py`:
  - **Normalização:** NFC, `\r\n` e `\r`, controles C0 e C1 removidos (exceto `\n` e `\t`), extremidades, quebras internas preservadas, só espaços vira vazio. Com Hypothesis: idempotência e nenhuma quebra interna perdida (RF-011).
  - **Limites:** 0, 1, máximo e máximo + 1 em *code points*, com emoji e caracteres combinados; explicação vazia vira `None`; uma mensagem por campo (RF-001).
  - **Estado inicial:** igual ao de `fsrs.Card()` na versão fixada (RF-003, DTEC 037).
  - **Rótulos e derivados:** `verificado` só com `gerado_verificado`; `fonteApagada` com cópias presentes e fonte nula (RF-009).
  - **Cursor:** ida e volta; base64 inválido, adulterado e de filtros diferentes, todos com `cursor_invalido` (DTEC 034).
- [ ] T009 [P] [US1] Criar os testes de integração em `tests/integration/cartoes/test_repositorio.py` e `tests/integration/cartoes/test_participante.py`:
  - **Repositório:** criação com filtro de dono; listagem só de `ativo` e `suspenso`, na ordem `criado_em desc, id desc`; paginação sem repetição nem salto com criação e exclusão entre as páginas; `total` correto.
  - **Referência:** cópia de título, nome e data da fonte; `FOR SHARE` na fonte.
  - **Participante (DTEC 027, emenda e DTEC 038):**
    - `contar_por_materia` com `cartoes_ativos` e `cartoes_suspensos` separados, de qualquer origem;
    - `impacto_fonte` com `cartoes_referencia`;
    - `ao_excluir_fonte` anulando `fonte_id` nos modos `manter` e `excluir`, sem tocar outros cartões;
    - `ao_excluir_materia` apagando os cartões da matéria;
    - `apagar_dados_usuario` apagando todos os cartões do usuário, na ordem anterior às fontes e às matérias.
- [ ] T010 [P] [US1] Criar os testes funcionais em `tests/functional/cartoes/test_us1_criar.py`:
  - cenários 1 a 3 da US1. No cenário 1, o estado gravado é o de cartão novo (`aprendizado`, passo 0, sem última revisão), e `entrada_estudo_em` segue a ordem de criação (RF-003). No cenário 3, sai `verificado = false` com a referência (RF-002);
  - `GET /cartoes/limites` com os valores da configuração;
  - listagem com frente, origem e situação (RF-004) e a matéria sem cartões com `total = 0`;
  - casos de borda: frente, verso ou explicação só com espaços; marcação e script devolvidos literalmente (RQ-001);
  - fonte de referência em `pendente` e em `falhou` aceita (DTEC 035).
- [ ] T011 [US1] Reexecutar com cartões reais os testes funcionais de exclusão da 002 (DTEC 027):
  - **Onde:** parametrizar `tests/functional/fontes/test_us2_exclusao_fonte.py` e `tests/functional/materias/test_us3_organizar.py`, criados pela T033 e pela T040 da 002, para rodarem também com o participante real dos cartões, no lugar do participante falso.
  - **Exclusão da fonte:** nos dois modos, os cartões de referência são mantidos, com `fonteApagada = true` e a cópia intacta (D-006, D-009 da 002).
  - **Exclusão da matéria:** o impacto conta ativos e suspensos, e a exclusão os apaga.
  - **Contagens:** CS-004 da 002 com cartões reais, e a lista de matérias mostra só os ativos (emenda da DTEC 027).
- [ ] T012 [P] [US1] Criar os testes de segurança em `tests/security/cartoes/test_cartoes_seguranca.py`:
  - **Tabela de isolamento:** acrescentar a `tests/security/test_isolamento_rotas.py` os casos de `GET` e `POST /materias/{id}/cartoes` (DTEC 019).
  - **Propriedade:** criar cartão em matéria alheia responde `404`; uma fonte de outro estudante, de outra matéria ou inexistente responde `422` em `fonteId`, com a mesma mensagem (DTEC 035).
  - **Logs:** sem frente, verso, explicação nem título da referência, verificados com captura.
  - **Proteções herdadas:** `401` sem sessão e `403` sem CSRF nas rotas novas.
- [ ] T013 [P] [US1] Criar os testes adversariais em `tests/adversarial/cartoes/test_criar_adversarial.py`:
  - **Entradas:** `<script>`, `<img onerror>`, caracteres bidirecionais e de largura zero devolvidos literalmente; payload no teto mais um (`422` do DTO); corpo acima de 64 KiB (`413` da 001); campos extras (`extra="forbid"`); `fonteId` que não é UUID; `limite` 0 e 101; cursor de outra conta (`422 cursor_invalido`, sem vazar nada).
  - **Concorrência:** criação com referência durante a exclusão da fonte. Ou o cartão nasce antes e fica com "Fonte apagada", ou a criação recebe `422`; nunca há referência a uma fonte inexistente.
- [ ] T014 [US1] Implementar `app/cartoes/dominio.py` (`normalizar_texto_cartao`, `validar_limites`, `estado_inicial`, rótulos e derivados) e `app/cartoes/cursor.py`, até que a T008 passe.
- [ ] T015 [US1] Implementar a criação e a listagem do domínio `cartoes`, até que as T009 a T013 passem:
  - **Camadas:** `app/cartoes/excecoes.py`, `repositorios.py` (filtro de dono, `situacoes_visiveis`, paginação, `FOR SHARE` na fonte), `servicos.py` (`limites`, `criar`, `listar`), `dtos.py` (tetos), `mapeadores.py` e `rotas.py` (`GET /cartoes/limites`, `GET` e `POST /materias/{id}/cartoes`, `Location` e `no-store`);
  - **Registros:** `app/cartoes/registros.py`, com o participante da exclusão e o `apagar_dados_usuario`, importado pela composição em `principal.py` e em `worker.py`.
- [ ] T016 [US1] Ampliar `tests/integration/test_contrato_openapi.py` para verificar também `docs/specs/003-cartoes-manuais/contracts/openapi.yaml`, incluindo `cursor_invalido` no enum de `Erro`. Regenerar e versionar `backend/openapi.json` e rodar `npm run gerar:api` (o teto da busca vai para `limites.gerado.ts`).
- [ ] T017 [P] [US1] Criar os testes de componente em `frontend/src/funcionalidades/cartoes/`, todos com axe sem violações:
  - **Painel de criação:**
    - abre com o foco na frente;
    - `Ctrl/⌘+Enter` aciona "Salvar e criar outro" (painel aberto, vazio, foco na frente), e "Salvar" fecha;
    - `Enter` quebra a linha;
    - `Esc` fecha, pedindo confirmação se houver texto;
    - contadores com os limites de `/cartoes/limites`;
    - erro do `422` junto do campo, com os valores preservados;
    - um único envio enquanto salva;
    - escolha opcional entre as fontes da matéria.
  - **Lista:** `SeloOrigem`, situação, texto com quebras de linha (`pre-wrap`) e marcação exibida literalmente; estado vazio com "Criar o primeiro cartão"; "Carregar mais" com `useInfiniteQuery`.
  - **Erro de rede:** o rascunho é mantido no painel.
- [ ] T018 [US1] Implementar as telas, até que a T017 passe:
  - a rota `frontend/src/rotas/_autenticado/materias/$materiaId.cartoes.tsx`;
  - a navegação entre "Fontes" e "Cartões" na página da matéria ([design, 9.4](../../base-specs/design.md#94-matéria));
  - o painel de criação, a lista e as consultas e mutações em `frontend/src/funcionalidades/cartoes/`, invalidando a lista de cartões e a de matérias depois de criar.
- [ ] T019 [US1] Executar os passos 1 a 7 da US1 no quickstart, inclusive o CS-001 cronometrado só com teclado, e os testes `functional`, `security` e `adversarial` da US1. Registrar a evidência.

## Fase 4 História de usuário 2 Editar um cartão (P2)

**Objetivo:** o estudante corrige frente, verso ou explicação sem mudar o agendamento. Um cartão gerado editado passa a "Editado por você".  
**Teste independente:** editar um cartão "Gerado e verificado" da fábrica e confirmar que a origem muda para "Editado por você" e que vencimento, estabilidade e as demais colunas do FSRS não mudam. A evidência mantida é reverificada pela 004.

- [ ] T020 [P] [US2] Criar os testes unitários em `tests/unit/cartoes/test_edicao.py`:
  - `houve_mudanca` depois da normalização (só espaços nas extremidades ou `\r\n` no lugar de `\n` não é mudança; explicação vazia e nula são iguais);
  - tabela de `origem_apos_edicao`: três origens, com e sem mudança (RF-006, US2-3).
- [ ] T021 [P] [US2] Criar os testes de integração em `tests/integration/cartoes/test_edicao_fsrs.py` (CS-002, RF-005):
  - todas as colunas do FSRS iguais antes e depois de uma edição;
  - edição sem mudança: nenhuma escrita, com `atualizado_em` igual;
  - uma atualização do agendamento simulada numa conexão separada, em paralelo à edição: as duas sobrevivem.
- [ ] T022 [P] [US2] Criar os testes funcionais em `tests/functional/cartoes/test_us2_editar.py`:
  - cenários 1 a 3 da US2, o 2 sobre um cartão `gerado_verificado` da fábrica (`verificado` passa a `false`);
  - `GET /cartoes/{id}`;
  - edição parcial e remoção da explicação com `null`;
  - CS-002 com 20 edições sobre cartões em estados diferentes do FSRS.
- [ ] T023 [P] [US2] Criar os testes de segurança e adversariais em `tests/security/cartoes/test_editar_seguranca.py` e `tests/adversarial/cartoes/test_editar_adversarial.py`:
  - acrescentar à tabela de isolamento `GET` e `PATCH /cartoes/{id}`; cartão alheio responde `404` idêntico;
  - cartão aguardando revisão responde `404` (a fixture acrescenta o valor de enum numa transação própria até a 004 existir; DTEC 038);
  - corpo vazio (`minProperties`) e campos extras;
  - duas edições simultâneas: a última vale, sem erro;
  - exclusão durante a edição: `404` ou edição aplicada antes, nunca `500`.
- [ ] T024 [US2] Implementar `houve_mudanca` e `origem_apos_edicao` em `app/cartoes/dominio.py`, mais `consultar` e `editar` em `servicos.py` e `repositorios.py` (`FOR UPDATE`; `UPDATE` só de `frente`, `verso`, `explicacao`, `origem` e `atualizado_em`). Implementar também os DTOs e as rotas `GET` e `PATCH /cartoes/{id}`, até que as T020 a T023 passem.
- [ ] T025 [P] [US2] Criar os testes de componente da edição em `frontend/src/funcionalidades/cartoes/`: painel com os valores atuais, `Ctrl/⌘+Enter` salva e fecha, `SeloOrigem` atualizado para "Editado por você" depois de editar um gerado, erro do `422` junto do campo e axe sem violações.
- [ ] T026 [US2] Implementar a ação "Editar" na lista, reutilizando o painel, até que a T025 passe.
- [ ] T027 [US2] Executar o teste independente da US2 e a verificação complementar do quickstart (edição e CS-002 pela consulta ao banco) e registrar a evidência.

## Fase 5 História de usuário 3 Suspender, reativar e excluir (P2)

**Objetivo:** o estudante tira um cartão das lições temporariamente ou de vez, preservando o agendamento e o histórico.  
**Teste independente:** suspender um cartão e conferir a situação e o vencimento; reativá-lo e conferir o mesmo vencimento; excluir outro com o diálogo e conferir que ele some. A ausência nas lições (CS-003) e a preservação das revisões e do XP são reverificadas pela 005 e pela 006.

- [ ] T028 [P] [US3] Criar os testes funcionais em `tests/functional/cartoes/test_us3_suspender_excluir.py`:
  - cenários 1 a 3 da US3;
  - suspensão e reativação com as colunas do FSRS iguais (RF-007);
  - reativação de um cartão com o vencimento no passado: o vencimento continua no passado, ou seja, o cartão fica devido;
  - suspensão e reativação repetidas, sem escrita (`atualizado_em` igual);
  - `DELETE` seguido de `GET` e de outro `DELETE`: `404`;
  - lista filtrada pela situação, com o suspenso visível como suspenso (RF-004).
- [ ] T029 [P] [US3] Criar os testes de segurança e adversariais em `tests/security/cartoes/test_situacao_seguranca.py` e `tests/adversarial/cartoes/test_situacao_adversarial.py`:
  - acrescentar à tabela de isolamento `DELETE /cartoes/{id}`, `POST /cartoes/{id}/suspensao` e `POST /cartoes/{id}/reativacao`, com `404` idêntico para cartão alheio;
  - suspensão repetida em paralelo: um único efeito;
  - reexecutar `tests/security/identidade/test_exclusao_completa.py` (001) com cartões criados: `cartoes` fica vazia para a conta (DTEC 021).
- [ ] T030 [US3] Implementar `suspender`, `reativar` e `excluir` em `app/cartoes/servicos.py` e `repositorios.py`, mais os DTOs e as rotas correspondentes, até que as T028 e T029 passem.
- [ ] T031 [P] [US3] Criar os testes de componente em `frontend/src/funcionalidades/cartoes/`:
  - ações "Suspender" e "Reativar" com o anúncio por `aria-live`;
  - `DialogoExclusaoCartao` (sobre o `DialogoConfirmacao` destrutivo da 002): aviso de exclusão definitiva, foco preso e devolvido ao acionador, cancelar sem efeito, ação destrutiva distinta por texto e ícone;
  - "Fonte apagada" exibida junto da descrição da origem;
  - axe sem violações.
- [ ] T032 [US3] Implementar as ações e o diálogo na lista, invalidando a lista de cartões e a de matérias, até que a T031 passe.
- [ ] T033 [US3] Executar o teste independente da US3 e a verificação complementar do quickstart (suspender, reativar, excluir, "Fonte apagada" e exclusão da matéria `Química`) e registrar a evidência.

## Fase 6 História de usuário 4 Encontrar um cartão (P3)

**Objetivo:** o estudante busca por texto da frente ou do verso, sem diferenciar maiúsculas e acentos, e filtra por situação e origem.  
**Teste independente:** numa matéria com 120 cartões fictícios, buscar por uma palavra da frente e por uma do verso, filtrar por suspensos e por origem e conferir os resultados (US4 no quickstart).

- [ ] T034 [P] [US4] Criar os testes de integração em `tests/integration/cartoes/test_busca.py` (DTEC 033):
  - "celula" encontra "Célula" e "CÉLULA"; "ÇÃO" encontra "ação";
  - busca no verso;
  - `%`, `_` e `\` tratados como literais;
  - combinação de busca com situação e origem;
  - o termo nunca é concatenado ao SQL (consulta com parâmetro conferida).
- [ ] T035 [P] [US4] Criar os testes funcionais em `tests/functional/cartoes/test_us4_encontrar.py`:
  - cenários 1 a 3 da US4, com 120 cartões da fábrica;
  - `total` com filtros e sem filtros (estado vazio da matéria diferente de "nenhum resultado");
  - paginação com filtros;
  - cursor reaproveitado com outros filtros: `422 cursor_invalido`;
  - busca só com espaços equivale a sem busca.
- [ ] T036 [P] [US4] Criar os testes adversariais em `tests/adversarial/cartoes/test_busca_adversarial.py`: busca com 101 caracteres (`422`), só curingas, barra invertida isolada, aspas e trechos de SQL tratados como texto, e valores fora dos enums de `situacao` e `origem` (`422`).
- [ ] T037 [US4] Implementar em `app/cartoes/repositorios.py` a função única `filtro_busca` (`lower(unaccent(...)) LIKE` com escape), os filtros de situação e origem e o resumo dos filtros no cursor. Implementar também os parâmetros da rota de listagem, até que as T034 a T036 passem.
- [ ] T038 [P] [US4] Criar os testes de componente em `frontend/src/funcionalidades/cartoes/`:
  - busca com *debounce* de 300 ms;
  - filtros de situação e origem combináveis;
  - `busca`, `situacao` e `origem` na URL (parâmetros validados), preservados ao recarregar;
  - "Nenhum cartão corresponde à busca" diferente do estado de matéria sem cartões;
  - total exibido;
  - axe sem violações.
- [ ] T039 [US4] Implementar a barra de busca e filtros na rota da aba Cartões, até que a T038 passe.
- [ ] T040 [US4] Executar o teste independente da US4 com os 120 cartões do quickstart e registrar a evidência.

## Fase final Qualidade transversal

- [ ] T041 Executar nos contêineres as suítes completas do backend e do frontend, a qualidade estática (inclusive a regra de lint da T002) e a verificação do contrato, e confirmar a integração contínua aprovada na `develop`. Registrar as contagens de testes e a cobertura.
- [ ] T042 Revisar e registrar as evidências:
  - **Logs:** `api` sem texto de cartão, termo de busca nem título de referência.
  - **Repositório:** sem segredos nem arquivos gerados versionados (regras 9 e 10).
  - **Acessibilidade (RQ-003):** teclado e leitor de tela no painel, na lista, nos filtros e no diálogo; origem sem depender só de cor; uso em 320 px sem rolagem horizontal; contraste.
- [ ] T043 Medir e registrar, no ambiente local:
  - criar, editar, suspender e excluir: percentil 95 até 200 ms;
  - listagem com busca numa matéria de 1.000 cartões: percentil 95 até 100 ms (condição de revisão da DTEC 033).
- [ ] T044 Atualizar o [quickstart](quickstart.md) com os comandos realmente verificados, `docs/skills/padroes-implementacao.md` com os comandos novos e o "Mapa do repositório" do `.agents/AGENTS.md` com o domínio `cartoes`.
- [ ] T045 Atualizar o [traceability.md](traceability.md) com os nomes reais dos testes e corrigir requisitos sem teste ou tarefa.

## Dependências

- **Specs anteriores:** as T001 a T045 da 001 e as T001 a T031 da 002 bloqueiam toda esta lista. A T011 também depende das T032 a T046 da 002.
- **Preparação e base:** a Fase 1 bloqueia a Fase 2, e a Fase 2 (T003 a T007) bloqueia todas as histórias. A T003 bloqueia a T004 e todos os testes de integração; a T006 bloqueia a T017.
- **US1:** T008 a T013 sem dependência entre si → T014 → T015 → T016 → T018 (usa os tipos gerados) → T019. A T017 pode ser escrita em paralelo ao backend. A T011 passa quando a T015 registra o participante.
- **US2:** depende da US1 (T015). T020 a T023 em paralelo → T024; T025 → T026 → T027.
- **US3:** depende da US1. Pode ser feita em paralelo à US2, por pessoas diferentes, porque altera funções distintas de `servicos.py` e `rotas.py`, com commits separados.
- **US4:** depende da US1 (listagem e cursor). Pode ser feita em paralelo à US2 e à US3.
- **Specs seguintes:** a 004 reexecuta a US2-2 com geração real e evidência, e a T011 com o seu participante. A 005 reverifica a US1-1, a US3-1, a US3-2 e o CS-003 com lições reais. A 006 reverifica o XP preservado da US3-3 ([obrigações no plano](plan.md#obrigações-registradas-para-as-próximas-specs)).
- **Fase final:** depende de todas as histórias.

## Pontos de paralelismo

- **Base:** T004, T005 e T006 alteram arquivos distintos.
- **Histórias:** em cada uma, as tarefas de teste marcadas com `[P]` podem ser escritas em paralelo. O frontend (T017 e T018; T025 e T026; T031 e T032; T038 e T039) avança em paralelo ao backend depois da T016.
- **Entre histórias:** depois da US1, a US2, a US3 e a US4 podem seguir com pessoas diferentes.

## Estratégia de incremento

1. **Base completa:** a T007 prova que a migração e a extensão sobem e que a integração contínua passa.
2. **P1 demonstrável:** entregar a US1 (criar e listar, com o participante da exclusão), que já permite à 005 montar lições sem a IA.
3. **Histórias seguintes:** acrescentar a US2, a US3 e a US4 sem quebrar a P1. A suíte completa passa a cada commit.
4. **Verificação final:** executar a fase final e atualizar os artefatos afetados. Nenhum merge na `main` acontece sem todos os testes passando (regra 17).
