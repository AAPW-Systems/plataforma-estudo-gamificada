# Plano de implementação

**Funcionalidade:** 002-materias-fontes (matérias, envio e processamento de fontes)  
**Spec:** [spec.md](spec.md), aprovada em 12/10/2026  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-002-materias-fontes-plano.md))  
**Responsáveis:** Artur Lins (decisões técnicas); equipe na revisão  
**Status:** em revisão; aguarda o portão "Plano aprovado"

Este plano **reaproveita sem redefinir** a estrutura base do repositório, as camadas do backend, a hierarquia de erros, o formato de erro, o camelCase, o prefixo `/api/v1`, a sessão e o CSRF definidos no [plano da spec 001](../001-conta-acesso/plan.md) e nas DTEC 015 a 018. Aqui estão só o que a 002 acrescenta.

## Resumo técnico

Matérias e fontes são dois domínios do backend (`materias` e `fontes`, [arquitetura, seção 5.1](../../arquitetura/README.md#51-organização-mvc-por-domínio)), com as camadas da [DTEC 018](../../research.md#decisão-dtec-018-camadas-do-backend-dto-mapper-repositório-e-exceções) e a dependência num só sentido: `fontes` → `materias`.

**Envio.** Recebe um arquivo por vez (*multipart*) e o grava num arquivo temporário enquanto calcula o SHA-256. A validação de extensão, assinatura, codificação e integridade acontece antes de qualquer gravação ([DTEC 028](research.md#decisão-dtec-028-validação-do-arquivo-no-envio)). A abertura do PDF roda num subprocesso com tempo limite e teto de memória ([DTEC 024](../../research.md#decisão-dtec-024-execução-isolada-do-processamento-de-arquivos-não-confiáveis)). Depois o objeto é gravado em `usuarios/{public_id}/fontes/{uuid}` (DTEC 021). Numa transação com *advisory lock* por estudante, a API confere as cotas, insere a fonte (índice único contra duplicata) e enfileira `processar_fonte` ([DTEC 032](research.md#decisão-dtec-032-cotas-e-duplicatas-sob-concorrência)). Se algo falhar depois da gravação, o objeto é apagado, e uma reconciliação diária remove os órfãos ([DTEC 025](../../research.md#decisão-dtec-025-consistência-entre-o-armazenamento-de-objetos-e-o-banco)).

**Processamento.** O worker extrai o texto no mesmo tipo de subprocesso isolado, normaliza e divide em trechos por estrutura, com uma página por trecho de PDF ([DTEC 029](research.md#decisão-dtec-029-extração-normalização-e-divisão-em-trechos)). Ele grava tudo numa transação que trava a fonte e termina sem efeito se a fonte não existir mais. O estado e o código de falha ficam na tabela `fontes`, com novas tentativas automáticas só para erros transitórios e recuperação de jobs travados ([DTEC 030](research.md#decisão-dtec-030-estados-falhas-e-novas-tentativas-do-processamento)).

**Exclusões.** Mostram o impacto e exigem, na confirmação, as contagens exibidas (`409 impacto_alterado` se mudaram, [DTEC 031](research.md#decisão-dtec-031-impacto-da-exclusão-sob-concorrência)). Elas acionam os participantes registrados por cada domínio ([DTEC 027](../../research.md#decisão-dtec-027-participantes-da-exclusão-de-fontes-e-matérias)), o que permite à 002 ser implementada e testada antes das tabelas de cartões da 003.

**Interface.** Acompanha o processamento por *polling* condicional ([DTEC 026](../../research.md#decisão-dtec-026-acompanhamento-de-processamentos-assíncronos-na-interface)).

**Riscos principais:**

- O prazo de 15/10/2026.
- Arquivos maliciosos ou patológicos no parser de PDF.
- Contagens do diálogo divergentes do que é apagado (CS-004).
- Corridas nas cotas e duplicatas.
- Página errada nos trechos (CS-001).

A ordem US1 → US2 → US3 entrega primeiro a história P1 demonstrável.

## Contexto técnico

- **Linguagem e versão:** as da 001: Python 3.13 com uv; TypeScript *strict* em Node 24 LTS com npm.
- **Dependências novas do backend:**
  - **PyMuPDF** (`pymupdf`): DTEC 009, licença AGPL-3.0, compatível com o uso acadêmico.
  - **`python-multipart`:** pacote exigido pelo próprio FastAPI para formulários *multipart*, sem tecnologia nova.

  As demais dependências são as da 001. O Hypothesis, já presente, cobre os invariantes da divisão.
- **Dependências novas do frontend:** nenhuma. O envio usa o `FileTrigger` e o `DropZone` do React Aria Components (DTEC 016) e o `FormData` pelo `openapi-fetch`.
- **Persistência:** as tabelas `materias`, `fontes` e `trechos` e os enums `estado_fonte` e `codigo_falha_fonte`, criados pela migração `0003_acervo` ([modelo de dados](data-model.md)). Os objetos ficam no adaptador de disco (`ARMAZENAMENTO_DIRETORIO`, volume `arquivos` no Compose).
- **Testes:** pytest com pytest-asyncio, httpx, Hypothesis e Postgres real. No frontend, Vitest, Testing Library, MSW e `vitest-axe`. Todos os arquivos de teste são **gerados** por fábricas, sem dados pessoais nem binários versionados (regra 10).
- **Plataforma de execução:** os serviços do Compose da 001, mais o volume nomeado `arquivos`, montado em `/dados/arquivos` na `api` e no `worker`.
- **Limites de desempenho ou custo:**
  - Um PDF de 2 MB chega a `concluido` em até 60 s no ambiente local (CS-003, D-008).
  - A verificação de integridade no envio custa de 0,2 a 0,5 s por PDF (criação do subprocesso).
  - Pico de memória: 2 × 256 MiB na API e 512 MiB por extração no worker.
- **Escala prevista:** dezenas de estudantes, até 50 matérias, 30 fontes por matéria e 100 MB por estudante (D-003).

## Verificação da constituição

| Princípio | Como o plano atende | Evidência prevista |
|---|---|---|
| I Fontes exclusivas | Trechos com página só quando conhecida: número físico em PDF, nula em TXT e MD (DTEC 029); conteúdo guardado como dado (CB-15) | Testes de invariantes da divisão; teste de CS-001 com páginas conferidas |
| II Proteção e isolamento | Filtro de dono no repositório e rotas na tabela de isolamento (DTEC 019); validação por conteúdo real; parser em subprocesso com limites (DTEC 024); nome enviado nunca na chave (RQ-001); logs sem conteúdo (RQ-002) | Testes `security/` e `adversarial/`; teste de logs; teste da chave do objeto |
| III Verificação humana | Exclusões com impacto, escolha explícita e confirmação pelo nome; contagens conferidas na confirmação (DTEC 031); DTEC 024 a 032 registradas para aprovação | Testes de componente dos diálogos; testes de CS-004 com concorrência; aprovação do plano |
| IV Servidor autoritativo | Estado e código de falha vêm do servidor; a interface só consulta (DTEC 026); idempotência por trava de fila, de execução e `FOR UPDATE` (DTEC 030); cotas sob *advisory lock* (DTEC 032) | Testes de integração da tarefa e de concorrência |
| V Qualidade verificável | Contrato OpenAPI validado; conjuntos de 10 arquivos válidos e 10 inválidos gerados por fábrica (CS-001, CS-002); meta de tempo medida (CS-003); WCAG 2.2 AA com axe (RQ-004) | `contracts/openapi.yaml`, `traceability.md`, relatórios da integração contínua |
| VI Entrega incremental | US1 (P1) demonstrável sozinha; US2 com participante falso até a 003 | `quickstart.md` |
| VII Rastreabilidade | DTEC com alternativas; registro da sessão; IDs da spec nos testes | `docs/prompts/`, `traceability.md` |

Não há exceção aos princípios. As exceções técnicas estão em [Complexidade e exceções](#complexidade-e-exceções).

## Arquitetura e fluxo

### Dependências entre domínios

```text
fontes ──(dono da matéria)──> materias
   │                              │
   └─ registra participante ──> nucleo/participantes_acervo <── participantes de cartoes (003, 004), busca/chat (014)
materias ── usa ─────────────────┘
```

`materias` não importa `fontes`: as contagens de fontes e a exclusão das fontes de uma matéria chegam pelo participante que `fontes` registra (DTEC 027). Um teste de arquitetura verifica essa direção.

### Fluxos da spec

| Fluxo | Passos principais |
|---|---|
| **Criar matéria (US1-1)** | DTO (1 a 60 caracteres) → normalização (NFC, sem espaços nas extremidades, sem caracteres de controle) → transação com *advisory lock* do estudante → cota (`409 cota_materias_excedida`) → inserção. O índice `lower(nome)` gera `409 materia_nome_em_uso` → `201`. |
| **Listar matérias (RF-002)** | Repositório de matérias do dono → `contar_por_materia` de cada participante (fontes: `count`; cartões: zero até a 003) → `200`, ordenado por nome. |
| **Enviar fonte (US1-2, 4, 7)** | Limite do corpo da rota → *multipart* → arquivo temporário com SHA-256 e tamanho → validações da DTEC 028 (PDF em subprocesso) → pré-verificação sem trava (matéria, duplicata, cotas) → gravação do objeto → transação: *advisory lock*, cotas, inserção (índice único), enfileiramento de `processar_fonte` com `queueing_lock` → `201` com `pendente`. Em qualquer erro depois da gravação, o objeto é apagado; o temporário é sempre apagado. |
| **Processar fonte (US1-2, 5, 6, 8)** | Worker: transação A (trava; inexistente ou `concluido` termina sem efeito; grava `processando`) → leitura do objeto para temporário → extração em subprocesso → normalização e divisão → transação B (trava; inexistente termina sem efeito; trechos em lote; `concluido`). Sem texto: `falhou/sem_texto`. Ilegível: `falhou/conteudo_invalido`. Erro transitório: nova tentativa automática; esgotadas, `falhou/falha_tecnica`. |
| **Acompanhar (RF-005)** | A interface consulta `GET /materias/{id}/fontes` a cada 2 s enquanto houver fonte `pendente` ou `processando`; anuncia mudanças por `aria-live`. |
| **Nova tentativa (US1-6)** | Transação: trava; exige `falhou/falha_tecnica` (`409 reprocessamento_indisponivel`) → `pendente` → enfileiramento num *savepoint* (`AlreadyEnqueued` é sucesso) → `202`. |
| **Consultar e renomear fonte (US1-3, US3-5)** | `GET /fontes/{id}` com título, arquivo, tipo, tamanho, envio, páginas e trechos. `PATCH` altera só `titulo` (1 a 120 caracteres); as cópias nos cartões não mudam (D-005). |
| **Excluir fonte (US2)** | `GET impacto-exclusao` (participantes) → diálogo → `POST exclusao` com `modoCartoes` e `impactoConfirmado` → transação: `FOR UPDATE` na fonte, recálculo (`409 impacto_alterado`), apagar o objeto, `ao_excluir_fonte(modo)` dos participantes, apagar trechos e fonte → `204`. |
| **Excluir matéria (US3-3, 4)** | `GET impacto-exclusao` → diálogo com o nome digitado → `POST exclusao` com `nomeConfirmacao` e `impactoConfirmado` → `422 confirmacao_invalida` se o nome não confere → transação: `FOR UPDATE` na matéria e nas fontes (por `id`), recálculo, participantes de cartões e gerações, participante de `fontes` (objetos e linhas), apagar a matéria → `204`. |
| **Excluir a conta (DTEC 021)** | `apagar_dados_usuario` da 002, registrado depois dos participantes de cartões: apaga fontes (trechos em cascata) e matérias. Os objetos saem pela `apagar_objetos_usuario`, que já existe. |

### Tarefas assíncronas criadas ou alteradas nesta spec

| Tarefa | Gatilho | Comportamento |
|---|---|---|
| `processar_fonte(fonte_id)` | Envio e nova tentativa (mesma transação) | DTEC 030: `queueing_lock` e `lock` por fonte; `RetryStrategy(max_attempts=2, exponential_wait=5)` só para `ErroTransitorio`; sem efeito se a fonte não existir ou já estiver concluída |
| `reconciliar_objetos` | Periódica, diária às 3h30 UTC | DTEC 025: apaga objetos sob `usuarios/*/fontes/` sem linha em `fontes` e criados há mais de `RECONCILIACAO_MARGEM_MIN` (60) |
| `reenfileirar_tarefas_travadas` | Periódica, a cada 10 min (núcleo) | DTEC 030: `get_stalled_jobs` (sem sinal de vida há `FILA_SEGUNDOS_TRAVADO`, padrão 60), `retry_job` e `prune_stalled_workers`; vale para toda tarefa idempotente |

### Interface de armazenamento (DTEC 010, 021 e 025)

A 002 completa a interface iniciada na 001: `gravar(chave, arquivo_origem)`, `ler_para_arquivo(chave, destino)`, `apagar(chave)` (idempotente), `apagar_prefixo(prefixo)` e `listar_prefixo(prefixo)`. Os adaptadores `memoria` e `disco` implementam todas as operações, e uma suíte de contrato roda os mesmos testes contra os dois. O adaptador de disco resolve a chave dentro da raiz e recusa *path traversal* (DTEC 010), grava por arquivo temporário seguido de `os.replace` (gravação atômica) e define permissão `0600`.

## Estrutura do repositório

Somente o que a 002 acrescenta à [estrutura da 001](../001-conta-acesso/plan.md#estrutura-do-repositório):

```text
compose.yaml                      # + volume nomeado "arquivos" em /dados/arquivos (api e worker)
.env.example                      # + variáveis da tabela abaixo
backend/
├── migracoes/versions/0003_acervo.py   # enums, materias, fontes, trechos, CHECKs e índices
├── src/app/
│   ├── nucleo/
│   │   ├── erros.py              # + ConteudoMuitoGrande (413)
│   │   ├── middlewares.py        # + limite de corpo por rota (envio de fonte)
│   │   ├── isolamento.py         # executar_isolado (DTEC 024)
│   │   ├── participantes_acervo.py  # registro, ContagensAcervo (DTEC 027)
│   │   ├── armazenamento/        # + gravar, ler_para_arquivo, apagar, listar_prefixo
│   │   └── fila.py               # + reenfileirar_tarefas_travadas
│   ├── materias/
│   │   ├── rotas.py, dtos.py, mapeadores.py, servicos.py, dominio.py
│   │   ├── repositorios.py, modelos.py, excecoes.py
│   │   └── registros.py          # apagar_dados_usuario (DTEC 021)
│   └── fontes/
│       ├── rotas.py              # /materias/{id}/fontes, /fontes/{id}..., /acervo/uso
│       ├── dtos.py, mapeadores.py, servicos.py, repositorios.py, modelos.py, excecoes.py
│       ├── dominio.py            # nome exibido, título padrão, transições, catálogo de falhas
│       ├── validacao.py          # DTEC 028 (assinaturas, UTF-8, integridade via isolamento)
│       ├── extracao.py           # funções executadas no subprocesso (verificar_pdf, extrair)
│       ├── divisao.py            # divisor puro (DTEC 029)
│       ├── tarefas.py            # processar_fonte, reconciliar_objetos
│       └── registros.py          # participante da matéria e apagar_dados_usuario
└── tests/
    ├── fabricas_arquivos.py      # gera PDFs (PyMuPDF), TXT e MD válidos e inválidos
    ├── unit/materias/, unit/fontes/  # domínio, validação, divisão (Hypothesis), mapeadores
    ├── integration/              # repositórios, tarefas, armazenamento, isolamento, migração
    ├── functional/               # cenários da US1 a US3 pela API
    ├── security/, adversarial/
    └── arquitetura/              # + materias não importa fontes
frontend/src/
├── api/acompanhamento.ts         # intervalo do polling (DTEC 026)
├── rotas/_autenticado/
│   ├── materias/index.tsx        # lista de matérias
│   ├── materias/$materiaId.tsx   # página da matéria: acervo (cartões a partir da 003)
│   └── materias/$materiaId.fontes.$fonteId.tsx   # painel de dados da fonte
├── funcionalidades/materias/     # lista, formulário criar/renomear, diálogo de exclusão
├── funcionalidades/fontes/       # acervo, envio, estado, painel, diálogo de exclusão, consultas
└── componentes/ui/               # + ZonaArquivo, GrupoOpcoes, DialogoConfirmacao (destrutivo), SeloEstado
```

**Decisão de estrutura:**

- Os dois domínios seguem a arquitetura (5.1). `validacao.py`, `extracao.py` e `divisao.py` são módulos de domínio de `fontes` com regras puras e sem FastAPI nem SQLAlchemy. `extracao.py` só é executado dentro do subprocesso.
- `registros.py` concentra o que cada domínio registra no núcleo (participante e `apagar_dados_usuario`). É importado pela composição em `principal.py` e em `worker.py`.
- A navegação ganha o item "Matérias". A matéria é o ponto de entrada de fontes e, depois, de cartões ([design, seções 9.3 e 9.4](../../base-specs/design.md)).

## Contratos

O contrato completo está em [`contracts/openapi.yaml`](contracts/openapi.yaml), validado com `openapi-spec-validator`:

| Método e caminho | Uso | História |
|---|---|---|
| `GET /api/v1/acervo/uso` | Limites vigentes e uso das cotas | US1 |
| `GET /api/v1/materias` | Lista as matérias com contagens | US1, US3 |
| `POST /api/v1/materias` | Cria uma matéria | US1 |
| `GET /api/v1/materias/{materiaId}` | Consulta uma matéria | US1 |
| `PATCH /api/v1/materias/{materiaId}` | Renomeia | US3 |
| `GET /api/v1/materias/{materiaId}/impacto-exclusao` | Impacto da exclusão | US3 |
| `POST /api/v1/materias/{materiaId}/exclusao` | Exclui em cascata | US3 |
| `GET /api/v1/materias/{materiaId}/fontes` | Acervo da matéria | US1 |
| `POST /api/v1/materias/{materiaId}/fontes` | Envia uma fonte (*multipart*) | US1 |
| `GET /api/v1/fontes/{fonteId}` | Consulta uma fonte | US1 |
| `PATCH /api/v1/fontes/{fonteId}` | Renomeia o título | US3 |
| `POST /api/v1/fontes/{fonteId}/reprocessamento` | Nova tentativa após falha técnica | US1 |
| `GET /api/v1/fontes/{fonteId}/impacto-exclusao` | Impacto da exclusão | US2 |
| `POST /api/v1/fontes/{fonteId}/exclusao` | Exclui a fonte | US2 |

- **Erros:** o corpo e os códigos da 001 continuam iguais. A 002 acrescenta:
  - `materia_nome_em_uso`
  - `cota_materias_excedida`, `cota_fontes_excedida`, `cota_armazenamento_excedida`
  - `fonte_duplicada`
  - `arquivo_muito_grande` (413)
  - `formato_nao_aceito`, `tipo_divergente`, `arquivo_vazio`, `arquivo_corrompido`, `pdf_protegido`, `pdf_paginas_excedidas`, `codificacao_invalida`
  - `confirmacao_invalida`, `impacto_alterado`, `reprocessamento_indisponivel`
- **Isolamento:** as 11 rotas com `{materiaId}` ou `{fonteId}` entram na tabela de `tests/security/test_isolamento_rotas.py` (DTEC 019).
- **Limites:** os estáticos (60 e 120 caracteres) vêm do OpenAPI para `limites.gerado.ts`, como na 001. Os configuráveis por ambiente (tamanho, páginas, cotas) vêm de `GET /acervo/uso`, porque o OpenAPI versionado não pode variar por ambiente (RQ-005).
- **Cache:** listagens, consultas e impactos respondem com `Cache-Control: no-store` (DTEC 026).

## Dados

- **Entidades e regras:** `materias`, `fontes` e `trechos`, detalhadas em [data-model.md](data-model.md). O [esquema inicial](../../arquitetura/esquema-inicial.dbml) foi atualizado: `codigo_falha` no lugar de `motivo_falha`, `versao_extracao`, `total_trechos`, título com até 120 caracteres (também na cópia de `evidencias_cartoes`), índice único de conteúdo por matéria e índice por `usuario_id`.
- **Migração `0003_acervo`:** revisada à mão, com PK `bigint generated always as identity`, as FKs compostas, os `CHECK` de coerência do estado e os índices do modelo de dados. Ela sobe e desce nos testes.
- **Origem e validação:** só o envio cria fontes, e só o worker cria trechos. Os limites ficam em `nucleo/configuracao.py` (pydantic-settings), são repetidos como `CHECK` no banco onde são estáticos e são expostos à interface (RQ-005).
- **Retenção e descarte:** a exclusão é física (RN-14). Os objetos são apagados antes das linhas na exclusão isolada e depois das linhas na exclusão da conta (DTEC 021 e 025). Os órfãos são removidos pela reconciliação. Os arquivos temporários são apagados ao fim de cada requisição ou tarefa.
- **Dados de teste:** as fábricas geram, sem dados pessoais:
  - **PDFs válidos:** com texto em várias páginas, com uma página por parágrafo conhecido e com páginas em branco intercaladas.
  - **PDFs inválidos ou recusados:** sem texto (só desenho vetorial), protegido por senha, corrompido (bytes truncados) e disfarçado (TXT com extensão `.pdf`).
  - **TXT e MD:** UTF-8 com e sem BOM, Latin-1 inválido em UTF-8, só espaços, com byte nulo e com instruções à IA.

## Estratégia de testes

Marcadores obrigatórios da 001 (`unit`, `integration`, `functional`, `security`, `adversarial`); cada teste cita no nome ou na *docstring* o requisito, cenário ou CS que cobre.

- **Unitários (`unit`):**
  - **Matérias:** normalização do nome, limites 0, 1, 60 e 61 e comparação da confirmação (NFC, extremidades, caixa).
  - **Nome e título:** sanitização do nome do arquivo (caminhos, controles, bidi, 255 caracteres, vazio) e título padrão (extensão, 120 caracteres, vazio).
  - **Validação (DTEC 028):** tabela com cada recusa e o seu código; UTF-8 com BOM; `.markdown`; extensão em maiúsculas.
  - **Divisão (DTEC 029):** invariantes com Hypothesis, títulos MD dentro de bloco de código, frase maior que o máximo, sobra final pequena e PDF com páginas vazias.
  - **Falhas e estados:** catálogo de mensagens e regras de transição.
  - **Participantes:** soma de `ContagensAcervo` e prioridade.
  - **Mapeadores.**
- **Integração (`integration`):**
  - **Repositórios:** contra o Postgres, com filtro de dono, índices únicos (nome sem caixa, conteúdo por matéria) e `CHECK` de estado.
  - **Migração `0003`:** sobe e desce.
  - **Enfileiramento atômico:** o *rollback* do envio não deixa job nem linha, e o objeto é compensado.
  - **`processar_fonte`:** com o adaptador de disco numa pasta temporária, cobre sucesso, sem texto, ilegível (subprocesso que estoura o tempo), erro transitório com nova tentativa e esgotamento, fonte apagada antes da transação B (sem trechos), reexecução de fonte concluída (sem efeito) e job travado reenfileirado.
  - **Isolamento (DTEC 024):** função que dorme além do limite e função que aloca além da memória terminam com resultado tipado, sem derrubar o processo (só em Linux).
  - **Armazenamento:** suíte de contrato dos adaptadores (`gravar`, `ler_para_arquivo`, `apagar` idempotente, `apagar_prefixo`, `listar_prefixo`, *path traversal*).
  - **`reconciliar_objetos`:** respeita a margem.
  - **Exclusão da conta:** remove matérias, fontes e trechos, e o teste de catálogo da 001 continua verde.
- **Contrato:** o OpenAPI gerado contém o `contracts/openapi.yaml`, e toda resposta de erro observada valida contra `Erro`.
- **Funcionais (`functional`):** um teste por cenário de aceitação, de ponta a ponta pela API, com cookies e CSRF reais e o worker executado em processo (`run_worker_async` com `wait=False`):
  - **US1:** cenários 1 a 8.
  - **US2:** cenários 1 a 6, com um participante falso de cartões que conta e registra as chamadas. Os mesmos testes são reexecutados com cartões reais pelas tarefas da 003 e da 004 (DTEC 027).
  - **US3:** cenários 1 a 5.
  - **CS-001:** 10 arquivos válidos gerados chegam a `concluido`, com páginas conferidas contra a fábrica.
  - **CS-002:** 10 inválidos, nenhum trecho e um código específico para cada.
  - **CS-003:** um PDF de 2 MB chega a `concluido` em menos de 60 s.
  - **CS-004:** as contagens exibidas coincidem com o apagado.
- **Segurança (`security`):**
  - **Isolamento:** duas contas nas 11 rotas com identificador e o teste que percorre as rotas (DTEC 019).
  - **Cotas e propriedade:** enviar fonte para matéria de outro estudante (`404`), renomear e excluir recurso alheio (`404` idêntico) e um `materiaId` válido de outro dono no *multipart*.
  - **Armazenamento e logs:** a chave do objeto nunca contém o nome enviado (RQ-001), e os logs não contêm texto de trecho, conteúdo nem nome de arquivo, verificado com captura (RQ-002).
  - **Proteções herdadas:** `401` sem sessão e `403` sem CSRF nas rotas novas.
- **Adversariais (`adversarial`):**
  - **Arquivos:**
    - Disfarçados (PDF com extensão `.txt` e o inverso, ZIP com extensão `.md`).
    - Corpo acima do limite pelo `Content-Length` e por *streaming* sem `Content-Length`.
    - Nomes com `../`, caminho do Windows, caracteres de controle, RTL e mais de 255 caracteres.
    - Dois arquivos no mesmo envio e *multipart* malformado.
    - PDF que demora a abrir ou exige muita memória (simulado no isolamento) e PDF com 501 páginas.
  - **Injeção de prompt:** TXT com instruções à IA é guardado como trecho comum (CB-15).
  - **Concorrência:**
    - Dois envios simultâneos do mesmo arquivo à mesma matéria: um `201` e um `409 fonte_duplicada`.
    - Dois envios que juntos passariam a cota: um aceito.
    - Duas criações simultâneas de matéria no limite e duas com o mesmo nome.
    - Exclusão da fonte durante o processamento: nenhum trecho (CB-16).
    - Exclusão da matéria durante um envio: `404` e objeto compensado.
    - Exclusão com impacto alterado entre a consulta e a confirmação: `409`.
  - **Reenvio:** nova tentativa pedida duas vezes em paralelo gera um único job e nenhum trecho duplicado (RF-008).
- **Frontend (Vitest, Testing Library, MSW e `vitest-axe`):**
  - **Matérias:** lista com contagens, estado vazio com "Criar primeira matéria" e formulário com erro por campo vindo do `422` e do `409`.
  - **Envio:** formatos e limites visíveis vindos de `/acervo/uso`, botão e arrastar e soltar, envio sem duplicar enquanto carrega e recusa com a mensagem do servidor junto do campo.
  - **Acervo:** estados com texto e ícone (sem depender só de cor), *polling* que para em estado final, anúncio por `aria-live` e "Tentar novamente" só com `podeTentarNovamente`.
  - **Painel da fonte:** os dados do cenário 3 da US1.
  - **Diálogos de exclusão:**
    - Foco preso e devolvido ao acionador.
    - Escolha obrigatória entre manter e excluir.
    - Contagem dos cartões de referência separada.
    - Botão de excluir a matéria habilitado só com o nome digitado.
    - Recarga do impacto após `409 impacto_alterado`.
  - **Acessibilidade:** axe sem violações nas telas e diálogos (RQ-004).
- **Jornada:** a verificação manual da história P1 está no [quickstart](quickstart.md). O Playwright entra no final acadêmico (DTEC 014).
- **Casos de falha:** armazenamento indisponível no envio (`500 erro_interno`, nada gravado no banco), banco indisponível no meio do processamento (nova tentativa automática), worker parado (fonte permanece `pendente` até ele voltar, sem erro visível ao estudante além do estado) e diretório de armazenamento sem permissão (a aplicação não sobe: `/health/ready` também verifica a escrita no armazenamento).

## Observabilidade e operação

- **Eventos de log (structlog, JSON):** `materia_criada`, `materia_excluida`, `fonte_recebida`, `fonte_recusada` (código), `processamento_iniciado`, `processamento_concluido` (duração, páginas, trechos), `processamento_falhou` (código, tentativa), `fonte_excluida` (modo, contagens), `objeto_compensado`, `objetos_reconciliados` (quantidade) e `isolamento_esgotado` (tempo ou memória). Sempre com `public_id` e nunca com conteúdo, texto de trecho ou nome de arquivo (RQ-002).
- **Saúde:** `/health/ready` passa a verificar também a escrita e a remoção de um objeto de sonda no armazenamento.
- **Tempo limite e retomada:** os tempos limite do isolamento ficam na configuração. A tarefa tem novas tentativas para erros transitórios, e os jobs travados voltam à fila a cada 10 minutos.
- **Corpo:** a rota de envio aceita até `FONTE_TAMANHO_MAX_BYTES` + 64 KiB. As demais rotas da 002 mantêm o limite de 64 KiB da 001.

## Variáveis de ambiente (acréscimos ao `.env.example`)

| Variável | Uso | Padrão no exemplo |
|---|---|---|
| `FONTE_TAMANHO_MAX_BYTES` | RN-02, RF-004 | `2097152` |
| `PDF_MAX_PAGINAS` | DTEC 028 | `500` |
| `COTA_MATERIAS`, `COTA_FONTES_POR_MATERIA`, `COTA_ARMAZENAMENTO_BYTES` | D-003 | `50`, `30`, `104857600` |
| `TRECHO_TAMANHO_ALVO`, `TRECHO_TAMANHO_MAXIMO`, `TRECHO_SOBREPOSICAO` | DTEC 029 | `1200`, `2000`, `150` |
| `VALIDACAO_ARQUIVO_TEMPO_S`, `VALIDACAO_ARQUIVO_MEMORIA_MB`, `VALIDACAO_ARQUIVO_CONCORRENCIA` | DTEC 024 (API) | `10`, `256`, `2` |
| `EXTRACAO_TEMPO_S`, `EXTRACAO_MEMORIA_MB` | DTEC 024 (worker) | `30`, `512` |
| `RECONCILIACAO_MARGEM_MIN` | DTEC 025 | `60` |
| `FILA_SEGUNDOS_TRAVADO` | DTEC 030 | `60` |

`ARMAZENAMENTO_ADAPTADOR` e `ARMAZENAMENTO_DIRETORIO` já existem desde a 001. A aplicação valida todas as variáveis ao iniciar. Por exemplo, ela não sobe com `TRECHO_SOBREPOSICAO >= TRECHO_TAMANHO_ALVO` nem com `TRECHO_TAMANHO_ALVO > TRECHO_TAMANHO_MAXIMO`.

## Riscos técnicos

| Risco | Consequência | Mitigação | Como verificar |
|---|---|---|---|
| Prazo de 15/10/2026 | US2 e US3 sem tempo | US1 primeiro; participante falso dispensa esperar a 003; tarefas por história | Quickstart da P1 funcionando antes da US2 |
| PDF malicioso ou patológico | API ou worker travado ou sem memória | Subprocesso com tempo e memória limitados (DTEC 024); limite de páginas | Testes de isolamento e adversariais |
| Página errada no trecho | Evidência enganosa (viola CS-001 e Princípio I) | Número físico; trecho nunca atravessa página; invariantes com Hypothesis | Teste de CS-001 contra a fábrica |
| Contagens divergentes na exclusão | Viola CS-004 | Recontagem na transação com `409 impacto_alterado` (DTEC 031) | Testes concorrentes |
| Corrida nas cotas ou duplicatas | Cota ultrapassada ou arquivo duplicado | *Advisory lock* e índice único (DTEC 032) | Testes adversariais de concorrência |
| Objeto órfão ou linha sem objeto | Custo, privacidade ou fonte quebrada | Objeto antes da linha, compensação e reconciliação (DTEC 025) | Testes de integração com falha simulada |
| `RLIMIT_AS` indisponível fora do Linux | Teste de memória não roda no Windows da equipe | Todos os testes rodam no contêiner (DTEC 001); marcador por plataforma | Integração contínua |
| Licença AGPL do PyMuPDF | Restrição numa evolução comercial | Registrada na DTEC 009 e na referência pós-acadêmica | Revisão antes de qualquer uso comercial |
| Participante esquecido por uma spec futura | Exclusão deixa cartões ou falha por FK `restrict` | Obrigação escrita na DTEC 027; testes funcionais da US2 e US3 reexecutados com dados reais | Falha de FK nos testes da 003 e da 004 |
| Spawn de subprocesso lento no envio | Envio mais lento | Custo medido (0,2 a 0,5 s), semáforo de 2 | Teste de tempo do envio no quickstart |

## Complexidade e exceções

| Exceção | Por que é necessária | Alternativa mais simples rejeitada porque |
|---|---|---|
| Registro de participantes da exclusão (indireção entre domínios) | A 002 precisa contar e afetar cartões que só existem a partir da 003 (DTEC 027) | Criar as tabelas de cartões na 002 ou consultá-las direto acopla domínios e quebra a posse das tabelas |
| Subprocesso para abrir e extrair arquivos | Um parser em C não é interrompível por *thread*; o arquivo é do usuário (DTEC 024) | *Thread* com tempo limite não para o trabalho nem limita a memória |
| Colunas novas em `fontes` (`codigo_falha`, `versao_extracao`, `total_trechos`) e remoção de `motivo_falha` | RF-007 exige distinguir falhas; reprodutibilidade (DTEC 029); listagem sem contagem por fonte | Mensagem livre em `motivo_falha` não permite decidir a nova tentativa nem traduzir a mensagem num único ponto |
| Nova subclasse `ConteudoMuitoGrande` (413) | Semântica HTTP correta para arquivo grande (DTEC 028) | Usar 422 para tamanho daria dois status para o mesmo código (`arquivo_muito_grande`) quando o limite de transporte atua |
| Pré-verificação de cotas e duplicata fora da trava | Evita gravar o objeto quando a recusa é certa | Só a verificação na transação: grava e compensa objetos à toa em todo envio recusado |

## Saídas do planejamento

- [`research.md`](research.md): DTEC 028 a 032. As decisões transversais deste planejamento (DTEC 024 a 027) estão em [`../../research.md`](../../research.md).
- [`data-model.md`](data-model.md): entidades, estados e validações.
- [`contracts/openapi.yaml`](contracts/openapi.yaml): contrato da API.
- [`quickstart.md`](quickstart.md): validação local.
- **Propagação:** foram atualizados com as decisões acima o [`esquema-inicial.dbml`](../../arquitetura/esquema-inicial.dbml), a [arquitetura](../../arquitetura/README.md) (seções 5.3, 5.6, 6 e 8) e os [padrões de implementação](../../skills/padroes-implementacao.md) (validação de arquivos, participantes e a subclasse 413).
- **Obrigações registradas para as próximas specs:**
  - **003:** participante dos cartões criados à mão.
  - **004:** participante dos cartões gerados e das gerações, mais `FOR SHARE` na fonte ao publicar (DTEC 031).
  - **014:** participante dos índices e citações.
- `tasks.md`: criado somente depois da aprovação deste plano (portão "Plano aprovado").
