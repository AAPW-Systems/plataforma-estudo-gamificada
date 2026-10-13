# Plano de implementação

**Funcionalidade:** 003-cartoes-manuais (cartões criados e gerenciados pelo estudante)  
**Spec:** [spec.md](spec.md), aprovada em 12/10/2026  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-003-cartoes-manuais-plano.md))  
**Responsáveis:** Artur Lins (decisões técnicas); equipe na revisão  
**Status:** aprovado em 13/10/2026 por Artur Lins (equipe), com as DTEC 033 a 038 e a emenda da DTEC 027

Este plano **reaproveita sem redefinir** o que as specs 001 e 002 já definiram:

- da [001](../001-conta-acesso/plan.md) e das DTEC 015 a 018: a estrutura base do repositório, as camadas do backend, a hierarquia de erros, o formato de erro, o camelCase, o prefixo `/api/v1`, a sessão e o CSRF;
- da [002](../002-materias-fontes/plan.md): os domínios `materias` e `fontes`, o registro de participantes da exclusão (DTEC 027) e o diálogo destrutivo da interface.

Aqui está só o que a 003 acrescenta.

## Resumo técnico

Os cartões ficam no domínio `cartoes` do backend ([arquitetura, seção 5.1](../../arquitetura/README.md#51-organização-mvc-por-domínio)), com as camadas da [DTEC 018](../../research.md#decisão-dtec-018-camadas-do-backend-dto-mapper-repositório-e-exceções). As dependências vão num só sentido: `cartoes` → `materias` (dono da matéria) e `cartoes` → `fontes` (fonte de referência). Nem `materias` nem `fontes` importam `cartoes`: as contagens e os efeitos da exclusão chegam pelo participante que `cartoes` registra (DTEC 027).

**Criação.** O texto é normalizado e validado num único ponto, contra limites configuráveis por ambiente ([DTEC 036](research.md#decisão-dtec-036-texto-limites-e-validação-dos-cartões)). O cartão nasce ativo, com a origem `criado` e o estado inicial de `fsrs.Card()` ([DTEC 037](research.md#decisão-dtec-037-estado-de-agendamento-edição-e-situação-do-cartão)). A fonte de referência opcional é guardada no próprio cartão, como `fonte_id` com cópia da descrição da origem e uma FK composta `restrict` ([DTEC 035](research.md#decisão-dtec-035-referência-de-um-cartão-manual-a-uma-fonte)).

**Edição, suspensão e exclusão.** A edição escreve só as colunas de conteúdo e a origem, nunca as do FSRS. Por isso o agendamento não muda (CS-002), mesmo com uma revisão concorrente. Suspender e reativar alteram só a situação. A exclusão é física, e as revisões e o XP ficam preservados pelas FKs `set null` da 005 e da 006.

**Busca e lista.** A busca usa `unaccent` sem índice ([DTEC 033](../../research.md#decisão-dtec-033-busca-sem-diferenciar-maiúsculas-e-acentos)), e a lista é paginada por cursor ([DTEC 034](../../research.md#decisão-dtec-034-paginação-das-listagens-por-cursor)).

**Fronteira com a 004.** A 003 é dona da tabela, da regra de origem e da contagem por situação. A 004 acrescenta dois valores de enum, a coluna da geração, as evidências e o seu participante ([DTEC 038](research.md#decisão-dtec-038-fronteira-com-a-spec-004-e-participante-da-exclusão)).

**Riscos principais:**

- O prazo de 15/10/2026.
- Uma escrita indevida no estado do FSRS (CS-002).
- Um cartão manual exibido como verificado (Princípio I).
- Texto do cartão interpretado como marcação (RQ-001).
- Uma contagem divergente na exclusão de fontes e matérias.

A ordem US1 → US2 → US3 → US4 entrega primeiro a história P1, que a 005 precisa para montar lições sem a IA.

## Contexto técnico

- **Linguagem e versão:** as da 001: Python 3.13 com uv; TypeScript *strict* em Node 24 LTS com npm.
- **Dependências novas do backend:** nenhuma. A biblioteca `fsrs` (DTEC 012) já entra na 001, que a usa para os parâmetros iniciais do FSRS, e a 003 a usa para o estado inicial do cartão.
- **Dependências novas do frontend:** nenhuma. O painel usa o `Dialog` e o `Modal` do React Aria Components (DTEC 016) como painel lateral, e a lista usa o `useInfiniteQuery` do TanStack Query (DTEC 015).
- **Persistência:** a tabela `cartoes`, os enums `origem_cartao`, `situacao_cartao` (`ativo` e `suspenso`) e `estado_fsrs`, a extensão `unaccent` e o índice `fontes_id_materia_usuario`, todos criados pela migração `0004_cartoes` ([modelo de dados](data-model.md)).
- **Testes:** pytest com pytest-asyncio, httpx, Hypothesis e Postgres real. No frontend, Vitest, Testing Library, MSW e `vitest-axe`. Os cartões de teste são gerados por fábricas, sem dados pessoais (regra 10).
- **Plataforma de execução:** os serviços do Compose da 001 e da 002, sem serviço nem volume novo.
- **Limites de desempenho:**
  - Criar, editar, suspender e excluir respondem em até 200 ms no percentil 95, no ambiente local.
  - A listagem com busca numa matéria de 1.000 cartões responde em até 100 ms no percentil 95 (DTEC 033).
- **Escala prevista:** dezenas de estudantes, até 50 matérias por estudante e de centenas a poucos milhares de cartões por matéria.

## Verificação da constituição

| Princípio | Como o plano atende | Evidência prevista |
|---|---|---|
| I Fontes exclusivas | Referência não é evidência: colunas próprias, `CHECK` "referência só em `criado`" e `verificado` só com `gerado_verificado` (DTEC 035 e 038). A cópia da origem sobrevive à exclusão da fonte | Testes de domínio e de integração dos `CHECK`; teste funcional da US1-3 sem selo; teste de "Fonte apagada" |
| II Proteção e isolamento | Filtro de dono no repositório e FKs compostas (matéria e fonte do mesmo dono); 6 rotas na tabela de isolamento (DTEC 019); texto só como texto, com lint contra HTML injetado; logs sem conteúdo; termo de busca sempre parametrizado e escapado | Testes `security/` e `adversarial/`; teste de logs; regra de lint na integração contínua |
| III Verificação humana | Exclusão de cartão com diálogo de confirmação; DTEC 033 a 038 registradas para aprovação | Teste de componente do diálogo; aprovação do plano |
| IV Servidor autoritativo | Estado inicial de `fsrs.Card()`; edição e situação sem escrita no FSRS (RN-26); origem decidida no servidor; limites vigentes vindos do servidor | Teste de CS-002 com todas as colunas do FSRS; teste de espelho do `Card` |
| V Qualidade verificável | Contrato OpenAPI validado; CS-001 a CS-003 com testes ou medição; WCAG 2.2 AA com axe (RQ-003) | `contracts/openapi.yaml`, `traceability.md`, relatórios da integração contínua |
| VI Entrega incremental | US1 (P1) demonstrável sozinha, sem IA, e já usável pela 005 | `quickstart.md` |
| VII Rastreabilidade | DTEC com alternativas; registro da sessão; IDs da spec nos testes | `docs/prompts/`, `traceability.md` |

Não há exceção aos princípios. As exceções técnicas estão em [Complexidade e exceções](#complexidade-e-exceções).

## Arquitetura e fluxo

### Dependências entre domínios

```text
cartoes ──(dono da matéria)──> materias
   │──(fonte de referência)──> fontes
   └─ registra participante ──> nucleo/participantes_acervo <── usado por materias e fontes
```

`materias` e `fontes` não importam `cartoes`. Um teste de arquitetura verifica essa direção. A 004 estende o mesmo domínio `cartoes`.

### Fluxos da spec

| Fluxo | Passos principais |
|---|---|
| **Limites (RF-001)** | `GET /cartoes/limites` → limites de `nucleo/configuracao.py` → `200` com `no-store`. A interface lê ao abrir a matéria e repete os limites no contador dos campos. |
| **Criar (US1)** | DTO (tetos) → `normalizar_texto_cartao` e `validar_limites` (`422` por campo) → transação: matéria do dono (`404`) → com `fonteId`, fonte do dono e da matéria `FOR SHARE` (`422` em `fonteId`) e cópia de título, nome e data → estado de `fsrs.Card()`, `situacao = ativo`, `origem = criado`, `entrada_estudo_em = now()` → inserção → `201` com `Location`. |
| **Listar e buscar (RF-004, US4)** | Matéria do dono (`404`) → validação do cursor contra os filtros (`422 cursor_invalido`) → consulta com `situacao IN (ativo, suspenso)`, filtros opcionais de situação, origem e busca (`lower(unaccent(...)) LIKE` escapado), ordem `criado_em desc, id desc`, `limite + 1` linhas → `count` com os mesmos filtros → `200` com `itens`, `proximoCursor` e `total`. |
| **Consultar** | Cartão do dono, em situação visível (`404`) → `200`. |
| **Editar (US2)** | DTO parcial (`minProperties: 1`) → normalização dos campos enviados → transação: cartão do dono `FOR UPDATE` (`404`) → `houve_mudanca` → sem mudança: `200` sem escrita → com mudança: `origem_apos_edicao`, `UPDATE` de `frente`, `verso`, `explicacao`, `origem` e `atualizado_em` → `200`. |
| **Suspender e reativar (US3-1, 2)** | Cartão do dono `FOR UPDATE` (`404`) → já na situação pedida: `200` sem escrita → senão, `UPDATE` de `situacao` e `atualizado_em` → `200`. |
| **Excluir (US3-3)** | Diálogo na interface → `DELETE` → `DELETE ... WHERE public_id AND usuario_id AND situacao IN (ativo, suspenso)` → nenhuma linha: `404` → `204`. |
| **Exclusão de fonte (002, DTEC 027)** | Participante dos cartões: `impacto_fonte` conta os cartões com `fonte_id` igual à fonte (`cartoes_referencia`); `ao_excluir_fonte(modo)` anula `fonte_id` deles, em qualquer modo (D-006). |
| **Exclusão de matéria (002, DTEC 027)** | `contar_por_materia` devolve `cartoes_ativos` e `cartoes_suspensos` de qualquer origem; `ao_excluir_materia` apaga os cartões da matéria antes do participante de `fontes`. |
| **Lista de matérias (002, RF-002)** | `contar_por_materia` alimenta `cartoesAtivos` (só ativos, emenda da DTEC 027). |
| **Excluir a conta (DTEC 021)** | `apagar_dados_usuario` dos cartões, registrado antes do de `fontes` e do de `materias`, apaga todos os cartões do usuário. |

### Tarefas assíncronas criadas ou alteradas nesta spec

Nenhuma. Todas as operações da 003 são síncronas e curtas.

## Estrutura do repositório

Somente o que a 003 acrescenta às estruturas da [001](../001-conta-acesso/plan.md#estrutura-do-repositório) e da [002](../002-materias-fontes/plan.md#estrutura-do-repositório):

```text
.env.example                      # + CARTAO_FRENTE_MAX, CARTAO_VERSO_MAX, CARTAO_EXPLICACAO_MAX
backend/
├── migracoes/versions/0004_cartoes.py  # unaccent, enums, cartoes, CHECKs, índices, índice em fontes
├── src/app/
│   ├── nucleo/configuracao.py    # + limites dos cartões, validados contra os tetos
│   └── cartoes/
│       ├── rotas.py              # /cartoes/limites, /materias/{id}/cartoes, /cartoes/{id}...
│       ├── dtos.py, mapeadores.py, servicos.py, repositorios.py, modelos.py, excecoes.py
│       ├── dominio.py            # normalizar_texto_cartao, validar_limites, houve_mudanca,
│       │                         # origem_apos_edicao, rotulos, estado_inicial (fsrs.Card)
│       ├── cursor.py             # codificar e decodificar o cursor (DTEC 034)
│       └── registros.py          # participante da exclusão e apagar_dados_usuario
└── tests/
    ├── fabricas_cartoes.py       # cartões fictícios (manuais, "gerados" por fábrica, suspensos)
    ├── unit/cartoes/             # normalização, limites, origem, mudança, cursor, espelho do Card
    ├── integration/cartoes/      # repositório, CHECKs, FKs, busca, migração, participante
    ├── functional/cartoes/       # cenários da US1 a US4 pela API
    ├── functional/fontes/, functional/materias/  # + reexecução da US2 e da US3 da 002 com cartões reais
    ├── security/, adversarial/
    └── arquitetura/              # + materias e fontes não importam cartoes
frontend/
├── eslint.config.js              # + no-restricted-syntax contra dangerouslySetInnerHTML (DTEC 036)
└── src/
    ├── rotas/_autenticado/materias/$materiaId.cartoes.tsx  # aba Cartões; filtros na URL
    ├── funcionalidades/cartoes/  # lista, filtros, painel criar/editar, selo de origem,
    │                             # diálogo de exclusão, consultas e mutações
    └── componentes/ui/           # + CampoTextoLongo (contador em code points), SeloOrigem
```

**Decisão de estrutura:**

- `cartoes` segue a arquitetura (5.1). `dominio.py` concentra as regras puras que a 004 reutiliza (normalização, limites, mudança efetiva e origem), sem SQLAlchemy nem FastAPI.
- `cursor.py` é um módulo puro do domínio. Se a 014 também paginar, ele sobe para o núcleo nessa spec, sem antecipar a abstração agora.
- A página da matéria ganha a navegação entre "Fontes" e "Cartões" ([design, seção 9.4](../../base-specs/design.md)). A aba Cartões é uma rota filha com parâmetros de busca validados (`busca`, `situacao`, `origem`), para que filtros e busca sobrevivam ao recarregamento e ao botão Voltar.

## Contratos

O contrato completo está em [`contracts/openapi.yaml`](contracts/openapi.yaml), validado com `openapi-spec-validator`:

| Método e caminho | Uso | História |
|---|---|---|
| `GET /api/v1/cartoes/limites` | Limites de texto vigentes | US1, US2 |
| `GET /api/v1/materias/{materiaId}/cartoes` | Lista, busca e filtra (paginada) | US1, US4 |
| `POST /api/v1/materias/{materiaId}/cartoes` | Cria um cartão manual | US1 |
| `GET /api/v1/cartoes/{cartaoId}` | Consulta um cartão | US2 |
| `PATCH /api/v1/cartoes/{cartaoId}` | Edita frente, verso ou explicação | US2 |
| `DELETE /api/v1/cartoes/{cartaoId}` | Exclui definitivamente | US3 |
| `POST /api/v1/cartoes/{cartaoId}/suspensao` | Suspende | US3 |
| `POST /api/v1/cartoes/{cartaoId}/reativacao` | Reativa | US3 |

- **Erros:** o corpo e os códigos da 001 e da 002 continuam iguais. A 003 acrescenta `cursor_invalido` (422). Os erros de texto e de fonte de referência usam `dados_invalidos`, com `campos`.
- **Isolamento:** as 6 rotas com `{materiaId}` ou `{cartaoId}` entram na tabela de `tests/security/test_isolamento_rotas.py` (DTEC 019).
- **Limites:** os vigentes vêm de `GET /cartoes/limites`; os `maxLength` do OpenAPI são só os tetos absolutos (DTEC 036). O teto da busca (100) é estático e vai para `limites.gerado.ts`.
- **Cache:** listagem, consulta e limites com `Cache-Control: no-store`.
- **Sem estado do FSRS:** nenhum esquema expõe vencimento, estabilidade ou passo. A spec não pede, e a lição (005) é quem os usa.

## Dados

- **Entidades e regras:** `cartoes`, detalhada em [data-model.md](data-model.md). O [esquema inicial](../../arquitetura/esquema-inicial.dbml) foi atualizado: referência com cópia da origem, `entrada_estudo_em` no lugar de `aceito_em`, o índice `cartoes_materia`, o índice por `fonte_id`, o índice único em `fontes` e a marcação da spec que cria cada coluna e valor de enum.
- **Migração `0004_cartoes`:** revisada à mão. PK `bigint generated always as identity`; `CREATE EXTENSION IF NOT EXISTS unaccent`; enums; tabela com as FKs compostas e os `CHECK`; índices. Ela sobe e desce nos testes. A descida remove a tabela, os enums e o índice em `fontes`, mas não a extensão, que pode ter outros usos.
- **Origem e validação:** só a criação da 003 e a aceitação da 004 inserem cartões. Os limites ficam em `nucleo/configuracao.py`, os tetos no DTO e no `CHECK`, e os limites vigentes são expostos à interface.
- **Retenção e descarte:** exclusão física (RN-14). As revisões e o XP sobrevivem pelas FKs `set null` da 005 e da 006. Na exclusão da conta, os cartões saem antes das fontes e das matérias.
- **Dados de teste:** as fábricas geram cartões com textos fictícios, como "Qual organela produz ATP?" e "Mitocôndria", além de:
  - textos com acentos, cedilha, maiúsculas e curingas, para a busca;
  - textos com marcação e script, para a RQ-001;
  - textos no limite exato e um caractere acima;
  - cartões `gerado_verificado` inseridos direto pela fábrica, para a RF-006.

## Estratégia de testes

Marcadores obrigatórios da 001 (`unit`, `integration`, `functional`, `security`, `adversarial`); cada teste cita no nome ou na *docstring* o requisito, cenário ou CS que cobre.

- **Unitários (`unit`):**
  - **Normalização:** NFC, `\r\n`, controles C0 e C1, extremidades, quebras internas preservadas, só espaços vira vazio. Com Hypothesis: idempotência (`normalizar(normalizar(x)) == normalizar(x)`) e nenhuma quebra interna perdida.
  - **Limites:** 0, 1, máximo e máximo + 1 em *code points*, inclusive com emoji e caracteres combinados; explicação vazia vira `None`; mensagens por campo.
  - **Mudança e origem:** tabela de `origem_apos_edicao` (3 origens × com e sem mudança); `houve_mudanca` depois da normalização (ex.: só espaços nas extremidades não é mudança).
  - **Estado inicial:** espelho de `fsrs.Card()` na versão fixada.
  - **Cursor:** ida e volta, adulteração, base64 inválido e filtros diferentes, todos com `cursor_invalido`.
  - **Rótulos:** origem e "Fonte apagada".
  - **Configuração:** a aplicação não sobe com limite acima do teto ou abaixo de 1.
- **Integração (`integration`):**
  - **Repositório:** contra o Postgres, com filtro de dono e situações visíveis.
  - **`CHECK` e FKs:** cópias juntas, referência só em `criado`, `entrada_estudo_em` coerente, matéria de outro dono recusada pela FK composta, fonte de outra matéria recusada pela FK composta e `restrict` ao apagar a fonte sem o participante.
  - **Busca:** "celula" encontra "Célula"; "ÇÃO" encontra "ação"; `%` e `_` literais; busca no verso; combinação com filtros.
  - **Paginação:** sem repetição nem salto com criação e exclusão entre as páginas.
  - **Edição sem escrita no FSRS (CS-002):** todas as colunas do FSRS iguais antes e depois, inclusive com uma atualização de agendamento simulada em paralelo, numa conexão separada.
  - **Migração `0004`:** sobe e desce.
  - **Participante:** `contar_por_materia` com ativos e suspensos separados; `impacto_fonte`; `ao_excluir_fonte` nos dois modos; `ao_excluir_materia`.
  - **Exclusão da conta:** o teste de catálogo da 001 continua verde com cartões criados.
- **Contrato:** o OpenAPI gerado contém o `contracts/openapi.yaml`, e toda resposta de erro observada valida contra `Erro`.
- **Funcionais (`functional`):** um teste por cenário de aceitação, de ponta a ponta pela API, com cookies e CSRF reais:
  - **US1:** cenários 1 a 3. A entrada na lição como cartão novo é verificada pelo estado gravado (novo, ativo, `entrada_estudo_em` na ordem de criação) e reverificada com a lição real pela 005.
  - **US2:** cenários 1 a 3, com o cenário 2 sobre um cartão `gerado_verificado` da fábrica.
  - **US3:** cenários 1 a 3. "Não entra na lição" é verificado pela situação e reverificado pela 005 (CS-003). A preservação das revisões e do XP é reverificada pela 005 e pela 006.
  - **US4:** cenários 1 a 3, com 120 cartões fictícios.
  - **Casos de borda:** só espaços; marcação devolvida literalmente; cartão aguardando revisão ausente da lista (por fábrica, com o valor de enum criado no teste até a 004); "Fonte apagada" depois da exclusão da fonte com "Excluir os cartões junto" (D-006).
  - **CS-002:** 20 edições variadas sobre cartões em estados diferentes do FSRS (novo, revisão, reaprendizado, por fábrica), com vencimento e estabilidade idênticos antes e depois.
  - **Reexecução da 002 (DTEC 027):** os testes funcionais da US2 e da US3 da 002 rodam também com cartões reais, no lugar do participante falso. A exclusão da fonte nos dois modos mantém os cartões de referência com "Fonte apagada", e a exclusão da matéria apaga ativos e suspensos, com as contagens exibidas iguais às apagadas (CS-004 da 002).
- **Segurança (`security`):**
  - **Isolamento:** duas contas nas 6 rotas com identificador e o teste que percorre as rotas (DTEC 019).
  - **Propriedade:** criar cartão em matéria alheia (`404`); citar fonte alheia ou de outra matéria (`422` com a mesma mensagem de uma inexistente); editar, suspender e excluir cartão alheio (`404` idêntico).
  - **Situações:** cartão aguardando revisão (fábrica) inacessível pelas rotas da 003.
  - **Logs:** sem frente, verso, explicação, termo de busca nem título da referência, verificados com captura.
  - **Proteções herdadas:** `401` sem sessão e `403` sem CSRF nas rotas novas.
- **Adversariais (`adversarial`):**
  - **Entradas:** `<script>`, `<img onerror>`, *bidi* e caracteres de largura zero, devolvidos literalmente; payload no teto mais um; corpo acima de 64 KiB (`413` da 001); campos extras (`extra="forbid"`); `fonteId` que não é UUID; busca com 101 caracteres, só curingas ou `\`; `limite` 0 e 101; cursor de outra conta.
  - **Concorrência:**
    - duas edições simultâneas: a última vale, sem erro;
    - edição durante a atualização do agendamento: nenhuma perde a outra;
    - criação com referência durante a exclusão da fonte: ou o cartão nasce antes e fica com "Fonte apagada", ou a criação recebe `422`, e nunca há referência a uma fonte inexistente;
    - exclusão do cartão durante a edição: `404` ou edição aplicada antes, sem erro 500;
    - suspensão repetida em paralelo: um único efeito.
  - **Reenvio:** `DELETE` repetido responde `404` sem efeito.
- **Frontend (Vitest, Testing Library, MSW e `vitest-axe`):**
  - **Painel:** na criação, `Ctrl/⌘+Enter` aciona "Salvar e criar outro", que mantém o painel aberto, vazio e com o foco na frente, e "Salvar" fecha o painel; na edição, `Ctrl/⌘+Enter` salva e fecha; `Enter` quebra a linha e `Esc` fecha sem salvar, pedindo confirmação se houver texto digitado; contador em *code points* com os limites de `/cartoes/limites`, erro do `422` junto do campo com os valores preservados, envio sem duplicar enquanto salva e escolha opcional da fonte da matéria.
  - **Lista:** selo de origem com texto e ícone, "Fonte apagada", situação, texto com quebras de linha e marcação exibida literalmente, "Carregar mais".
  - **Filtros:** busca com *debounce*, filtros na URL, estado vazio da matéria diferente do estado "nenhum resultado".
  - **Ações:** suspender e reativar com anúncio por `aria-live`; diálogo de exclusão com foco preso e devolvido.
  - **Acessibilidade:** axe sem violações (RQ-003).
- **Jornada:** a verificação manual da P1 e o CS-001 estão no [quickstart](quickstart.md). O Playwright entra no final acadêmico (DTEC 014).
- **Casos de falha:**
  - banco indisponível na criação: `500 erro_interno`, nada gravado, e a interface mantém o rascunho no painel;
  - perda de conexão no envio do painel: os valores são preservados e o envio pode ser repetido;
  - migração sem permissão para `CREATE EXTENSION`: a migração falha com mensagem clara, e a aplicação não sobe.

## Observabilidade e operação

- **Eventos de log (structlog, JSON):**
  - `cartao_criado`, com `com_referencia`;
  - `cartao_editado`, com `origem_mudou`;
  - `cartao_edicao_sem_mudanca`;
  - `cartao_suspenso`, `cartao_reativado` e `cartao_excluido`;
  - `cartoes_referencia_marcados`, com a quantidade, na exclusão da fonte;
  - `cartoes_materia_apagados`, com a quantidade.

  Todos vão com `public_id` do cartão e do usuário, nunca com texto, termo de busca ou título da referência.
- **Saúde:** sem mudança. A migração aplicada garante a extensão.
- **Corpo:** o limite de 64 KiB da 001 cobre o maior cartão possível (tetos somando 16 mil caracteres, até 64 KiB em UTF-8 no pior caso). O teto do DTO recusa antes, com `422`.

## Variáveis de ambiente (acréscimos ao `.env.example`)

| Variável | Uso | Padrão no exemplo |
|---|---|---|
| `CARTAO_FRENTE_MAX` | RF-001, D-004 | `1000` |
| `CARTAO_VERSO_MAX` | RF-001, D-004 | `2000` |
| `CARTAO_EXPLICACAO_MAX` | RF-001, D-004 | `1000` |

A aplicação não sobe com valor menor que 1 ou acima dos tetos (4.000, 8.000 e 4.000).

## Riscos técnicos

| Risco | Consequência | Mitigação | Como verificar |
|---|---|---|---|
| Prazo de 15/10/2026 | US3 e US4 sem tempo | US1 primeiro, que já serve à 005; tarefas por história | Quickstart da P1 funcionando antes da US2 |
| Escrita indevida no estado do FSRS | Viola RF-005, CS-002 e RN-26 | `UPDATE` só de colunas de conteúdo; teste que compara todas as colunas do FSRS | Testes de CS-002 e de concorrência |
| Cartão manual exibido como verificado | Viola o Princípio I e a D-002 | `verificado` derivado só de `gerado_verificado`; `CHECK` "referência só em `criado`" | Testes de domínio, de integração e da US1-3 |
| Texto interpretado como marcação | XSS (viola RQ-001) | Só texto no React, `pre-wrap` e lint contra `dangerouslySetInnerHTML` | Testes adversariais e de componente; lint na integração contínua |
| Exclusão da fonte esquecendo os cartões de referência | Falha na exclusão ou referência inválida | `restrict` na FK composta e participante obrigatório (DTEC 027) | Reexecução dos testes funcionais da 002 com cartões reais |
| Contagem dupla com a 004 | Diálogo com números errados (CS-004 da 002) | Divisão de contagens escrita na DTEC 038 | Reexecução pela 004 dos mesmos testes |
| `unaccent` indisponível na imagem | Migração falha | Contrib incluído na imagem `pgvector/pgvector`; migração testada na integração contínua | Teste da migração `0004` |
| Contagem de caracteres diferente no front e no back | Erro só depois do envio | *Code points* nos dois lados, com testes de emoji e combinados | Testes unitários e de componente |
| Valor de enum da 004 ausente | Teste de "aguardando revisão fora da lista" sem dado | O teste cria o valor numa transação própria até a 004 ser implementada; a 004 o reexecuta com dados reais | Teste funcional do caso de borda |

## Complexidade e exceções

| Exceção | Por que é necessária | Alternativa mais simples rejeitada porque |
|---|---|---|
| FK composta de três colunas para a fonte, com índice único novo em `fontes` | Garante mesma matéria e mesmo dono no banco (RN-01, DTEC 035) | FK simples para `fontes.id` deixaria a aplicação ser a única barreira contra citar uma fonte de outra matéria ou de outro estudante |
| Cópias da descrição da origem no cartão | A descrição sobrevive à exclusão e à renomeação da fonte (RN-05, D-005 da 002) | Ler o título da fonte na hora perderia a origem quando a fonte fosse apagada |
| Extensão `unaccent` | Busca sem acentos com semântica de substring (RF-010, DTEC 033) | Uma coluna derivada mantida pela aplicação dependeria de todo escritor de cartões lembrar dela |
| Paginação por cursor | Lista estável sob escrita concorrente, com custo constante (DTEC 034) | *Offset* repete e pula itens quando há criação ou exclusão entre as páginas |
| Limites configuráveis com rota própria | D-004 exige limites por ambiente | Limites no OpenAPI fariam o contrato variar por ambiente |
| Colunas de agendamento criadas pela 003 | RF-003, RF-005 e CS-002 exigem o estado do FSRS no cartão desde a criação | Deixá-las para a 005 obrigaria a migrar cartões já criados sem estado |

## Saídas do planejamento

- [`research.md`](research.md): DTEC 035 a 038. As decisões transversais deste planejamento estão em [`../../research.md`](../../research.md): DTEC 033, DTEC 034 e a emenda da DTEC 027.
- [`data-model.md`](data-model.md): entidade, estados, restrições e validações.
- [`contracts/openapi.yaml`](contracts/openapi.yaml): contrato da API.
- [`quickstart.md`](quickstart.md): validação local.
- **Propagação:** foram atualizados com as decisões acima:
  - o [`esquema-inicial.dbml`](../../arquitetura/esquema-inicial.dbml);
  - a [arquitetura](../../arquitetura/README.md) (seção 3: `unaccent`);
  - os [padrões de implementação](../../skills/padroes-implementacao.md) (busca e paginação);
  - o plano, o `research.md`, as tarefas e o README da [spec 002](../002-materias-fontes/README.md) (emenda da DTEC 027, com registro no histórico).

### Obrigações registradas para as próximas specs

- **004:**
  - acrescentar `aguardando_revisao` e `recusado` a `situacao_cartao` e a coluna `geracao_id`, mantendo o `CHECK` de `entrada_estudo_em` (que recebe o instante da aceitação);
  - reutilizar `normalizar_texto_cartao`, `validar_limites`, `houve_mudanca` e `origem_apos_edicao` no "editar e aceitar";
  - registrar o participante dos cartões gerados e das gerações, sem contar de novo ativos e suspensos por matéria (DTEC 038);
  - reexecutar com geração real o teste da US2-2 (evidência mantida depois da edição) e os testes funcionais da US2 e da US3 da 002.
- **005:**
  - criar `revisoes.cartao_id` com `on delete set null` e a coluna `dominado_em`;
  - montar a lição só com cartões existentes e ativos, com os novos na ordem de `entrada_estudo_em` (RF-003, CB-27);
  - reverificar com lições reais a US1-1 (cartão novo entra na lição), a US3-1 e o CS-003 (suspenso fora da lição), e a US3-2 (reativado com o vencimento anterior).
- **006:** criar `eventos_xp.cartao_id` com `on delete set null` e reverificar a US3-3 (XP preservado depois da exclusão do cartão).
- **011:** criar `chave_imagem` e seguir a DTEC 025 para a imagem (objeto antes das linhas na exclusão do cartão).

O `tasks.md` só é criado depois da aprovação deste plano (portão "Plano aprovado").
