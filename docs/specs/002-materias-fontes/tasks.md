# Tarefas da funcionalidade

**Funcionalidade:** 002-materias-fontes (matérias, envio e processamento de fontes)  
**Entrada:** [spec](spec.md), [plano](plan.md) (aprovado em 13/10/2026), [pesquisa](research.md), [modelo de dados](data-model.md), [contrato](contracts/openapi.yaml) e [quickstart](quickstart.md)  
**Formato:** `[ID] [P?] [US?] ação com caminho exato e resultado verificável`  
**Status:** aprovadas em 13/10/2026 por Artur Lins (equipe), junto com a [rastreabilidade](traceability.md)

- `[P]` indica que a tarefa pode ser executada em paralelo, porque não altera os mesmos arquivos nem depende de outra tarefa pendente.
- `[US1]` relaciona a tarefa a uma história de usuário.
- Marque `[x]` somente quando o resultado e a sua verificação estiverem concluídos (regra 6).
- **Caminhos:** `backend/src/app/` aparece abreviado como `app/`, e `backend/tests/` como `tests/`.
- **Pré-requisito:** as tarefas da [spec 001](../001-conta-acesso/tasks.md) até a US2 (T001 a T045) concluídas, porque esta spec usa a estrutura base, a sessão, o CSRF, o auxiliar de busca por dono (T043 da 001) e o teste que percorre as rotas (T041 da 001).
- **Testes antes do código:** em cada história, as tarefas de teste vêm antes das de implementação. Os testes começam falhando e passam ao fim da história.
- **Commits:** todo trabalho acontece na `develop` (regra 14), com um commit atômico por tarefa ou por par teste e implementação, citando o ID da tarefa (ex.: `feat(fontes): implementa o envio [T025]`). O escopo do commit (`materias`, `fontes`) identifica a spec.

## Fase 1 Preparação

- [ ] T001 Acrescentar `pymupdf` (DTEC 009) e `python-multipart` a `backend/pyproject.toml`, em versões fixas no `backend/uv.lock`. **Verificação:** `docker compose run --rm api uv run python -c "import pymupdf, multipart"` funciona em Python 3.13.
- [ ] T002 Acrescentar a configuração do acervo:
  - **Compose:** volume nomeado `arquivos` em `/dados/arquivos` nos serviços `api` e `worker` do `compose.yaml`.
  - **`.env.example`:** as variáveis da tabela "Variáveis de ambiente" do [plano](plan.md#variáveis-de-ambiente-acréscimos-ao-envexample), sem valores secretos.
  - **Configuração:** os campos correspondentes em `app/nucleo/configuracao.py`.

  **Testes** em `tests/unit/nucleo/test_configuracao.py`: a aplicação não sobe com `TRECHO_SOBREPOSICAO >= TRECHO_TAMANHO_ALVO`, com `TRECHO_TAMANHO_ALVO > TRECHO_TAMANHO_MAXIMO`, nem com cota ou limite menor que 1 (RQ-005).

## Fase 2 Base compartilhada (bloqueia todas as histórias)

- [ ] T003 [P] Criar os testes do isolamento em `tests/integration/nucleo/test_isolamento.py`. Eles verificam que:
  - uma função que termina devolve o resultado;
  - uma função que dorme além do limite é morta e devolve `tempo_esgotado`;
  - uma função que aloca além do teto devolve `memoria_esgotada` (marcada para rodar só em Linux);
  - uma exceção no filho vira um resultado tipado;
  - o processo pai continua respondendo em todos os casos;
  - o semáforo limita as execuções simultâneas.

  Implementar `app/nucleo/isolamento.py` (`executar_isolado`, contexto `spawn`, `RLIMIT_AS`, DTEC 024).
- [ ] T004 [P] Ampliar a suíte de contrato do armazenamento em `tests/integration/nucleo/test_armazenamento_contrato.py`, contra os dois adaptadores. Ela cobre:
  - `gravar` atômico, com temporário e `os.replace`, e permissão `0600` no disco;
  - `ler_para_arquivo`;
  - `apagar` idempotente;
  - `listar_prefixo`, com a data de criação;
  - *path traversal* recusado em todas as operações.

  Implementar as operações em `app/nucleo/armazenamento/interface.py`, `memoria.py` e `disco.py` (DTEC 010, 021 e 025).
- [ ] T005 [P] Criar os testes do registro de participantes em `tests/unit/nucleo/test_participantes_acervo.py`: registro, ordem por prioridade, soma de `ContagensAcervo` com campos ausentes valendo zero e chamada na transação recebida. Implementar `app/nucleo/participantes_acervo.py` (DTEC 027) e o participante falso de cartões em `tests/participantes_falsos.py`, que devolve contagens configuráveis e registra cada chamada com o modo.
- [ ] T006 [P] Acrescentar `ConteudoMuitoGrande` (413) a `app/nucleo/erros.py`, com o caso correspondente em `tests/unit/nucleo/test_erros.py`. Criar o limite de corpo por rota em `app/nucleo/middlewares.py`, com testes em `tests/unit/nucleo/test_middlewares.py`:
  - a rota de envio aceita até `FONTE_TAMANHO_MAX_BYTES` + 64 KiB;
  - acima disso, ela recusa com `413 arquivo_muito_grande`, pelo `Content-Length` ou durante a leitura sem `Content-Length`;
  - as demais rotas mantêm 64 KiB.
- [ ] T007 [P] Implementar em `app/nucleo/fila.py` a tarefa periódica `reenfileirar_tarefas_travadas`: a cada 10 minutos, com `queueing_lock` próprio, ela chama `get_stalled_jobs` com `FILA_SEGUNDOS_TRAVADO`, `retry_job` e `prune_stalled_workers` (DTEC 030). Teste em `tests/integration/nucleo/test_tarefas_travadas.py`: um job em `doing` de um worker sem sinal de vida volta à fila.
- [ ] T008 Criar as entidades e a migração do acervo:
  - **Entidades:** `app/materias/modelos.py` (Materia) e `app/fontes/modelos.py` (Fonte, Trecho).
  - **Migração** `backend/migracoes/versions/0003_acervo.py`, conforme o [modelo de dados](data-model.md):
    - enums `estado_fonte` e `codigo_falha_fonte`;
    - as três tabelas, com PK `generated always as identity` e `public_id` com `gen_random_uuid()`;
    - FK composta `(materia_id, usuario_id)` com `restrict` e `trechos` com `cascade`;
    - índices únicos `(usuario_id, lower(nome))`, `(id, usuario_id)`, `(materia_id, hash_sha256)` e `(fonte_id, ordem)`;
    - `CHECK` de coerência de `codigo_falha`, `total_trechos` e `versao_extracao` com o estado, `CHECK` de tamanho e de `fim_caractere > inicio_caractere`.

  **Verificação:** `tests/integration/test_migracoes.py` sobe e desce. `tests/integration/fontes/test_restricoes.py` mostra que cada `CHECK` e cada índice único recusa a linha inválida e que a FK composta impede uma fonte numa matéria de outro dono.
- [ ] T009 [P] Ampliar `tests/arquitetura/test_camadas.py` com as regras novas: `app/materias` não importa `app/fontes`, e `app/fontes/extracao.py`, `divisao.py` e `validacao.py` não importam FastAPI nem SQLAlchemy.
- [ ] T010 [P] Criar `tests/fabricas_arquivos.py`, com a linha de comando `python -m tests.fabricas_arquivos <diretório>`. A fábrica gera:
  - os 10 arquivos válidos do CS-001: PDFs com texto em várias páginas e o texto conhecido de cada página, PDF com páginas em branco intercaladas, PDF de quase 2 MB, TXT e MD em UTF-8 com e sem BOM, MD com títulos e bloco de código, TXT de um parágrafo;
  - os 10 inválidos do CS-002: acima do tamanho, TXT com extensão `.pdf`, PDF com extensão `.txt`, vazio, corrompido, PDF sem texto, PDF com senha, Latin-1, TXT só com espaços e TXT com byte nulo;
  - os adversariais: ZIP com extensão `.md`, PDF com 501 páginas e TXT com instruções à IA.

  Teste em `tests/unit/test_fabricas_arquivos.py`: cada arquivo tem a propriedade esperada (páginas, `needs_pass`, ausência de texto, tamanho). Os arquivos gerados não têm dados pessoais (regra 10) e não são versionados.
- [ ] T011 Ampliar `app/saude/rotas.py`: `/health/ready` grava e apaga um objeto de sonda no armazenamento. Teste em `tests/integration/test_saude.py`: um diretório sem permissão de escrita gera `503`.
- [ ] T012 [P] Criar em `frontend/src/componentes/ui/`, sobre o React Aria (DTEC 016), cada um com teste e `vitest-axe`:
  - `ZonaArquivo`: `FileTrigger` e `DropZone`, com formatos e limites visíveis;
  - `GrupoOpcoes`: `RadioGroup`;
  - `DialogoConfirmacao`: variante destrutiva, distinta também por texto e ícone;
  - `SeloEstado`: texto e ícone, sem depender só de cor.

  Criar `frontend/src/api/acompanhamento.ts` (intervalo de 2 s e regra "consulta enquanto houver item não final", DTEC 026), com teste.
- [ ] T013 **Verificar a base:** `docker compose up --build` sobe com o volume `arquivos`, `/health/ready` responde `200` e a integração contínua passa na `develop`. Registrar a evidência no registro de prompts da sessão de implementação.

## Fase 3 História de usuário 1 Criar matéria e enviar uma fonte (P1)

**Objetivo:** o estudante cria uma matéria, envia uma fonte, acompanha o processamento até `concluido` e recebe uma explicação específica para cada arquivo recusado.  
**Teste independente:** criar a matéria "Biologia", enviar um PDF fictício com texto e acompanhar a fonte até `concluido`, com trechos e páginas; enviar um PDF sem texto e confirmar a recusa explicada (passos 1 a 12 da US1 no [quickstart](quickstart.md)).

- [ ] T014 [P] [US1] Criar os testes unitários do domínio de matérias em `tests/unit/materias/test_dominio.py`, com Hypothesis na normalização: NFC, extremidades, caracteres de controle e nomes com 0, 1, 60 e 61 caracteres (RF-001).
- [ ] T015 [P] [US1] Criar os testes unitários do domínio de fontes em `tests/unit/fontes/test_dominio.py`:
  - **Nome exibido:** caminhos POSIX e Windows, controles C0 e C1, bidi, 255 e 256 caracteres, resultado vazio (RQ-001).
  - **Título padrão:** sem extensão, truncado em 120, vazio vira "Fonte sem título" (RF-003).
  - **Transições de estado:** as permitidas e as recusadas, conforme o [modelo de dados](data-model.md#estados-e-transições).
  - **Catálogo de falhas:** `mensagemFalha` e `podeTentarNovamente` por código (RF-007).
- [ ] T016 [P] [US1] Criar os testes unitários da validação em `tests/unit/fontes/test_validacao.py`: uma linha por verificação da tabela da DTEC 028, com o código esperado; UTF-8 com BOM; extensões `.markdown` e `.PDF`; `%PDF-` depois de bytes iniciais, dentro dos 1.024 primeiros (RF-004).
- [ ] T017 [P] [US1] Criar os testes unitários da divisão em `tests/unit/fontes/test_divisao.py`:
  - **Invariantes da DTEC 029 com Hypothesis:** deslocamentos que conferem com o texto, ordem contígua, máximo respeitado, cobertura de todo caractere visível, nenhum trecho de PDF atravessando páginas e página só em PDF.
  - **Casos fixos:** título MD dentro de bloco de código, frase maior que o máximo, palavra maior que o máximo, sobra final pequena, páginas vazias e `versao_extracao` refletindo os parâmetros (RF-006).
- [ ] T018 [P] [US1] Criar os testes da extração em `tests/integration/fontes/test_extracao.py`, com PyMuPDF real no subprocesso:
  - páginas físicas iguais às da fábrica;
  - hifenização desfeita;
  - normalização;
  - PDF sem texto devolve `sem_texto` (CB-23);
  - PDF que estoura o tempo devolve `conteudo_invalido`;
  - TXT e MD sem página.
- [ ] T019 [P] [US1] Criar os testes funcionais em `tests/functional/fontes/test_us1_materia_fonte.py`, com o worker executado em processo:
  - **Cenários da US1:** 1 a 8.
  - **Cotas:** atingida para matérias, para fontes da matéria e para armazenamento, com fontes `falhou` contando (RF-012, D-010).
  - **Mesmo arquivo:** aceito em outra matéria (D-004).
  - **Critérios de sucesso:** CS-001 (10 válidos em `concluido`, páginas conferidas), CS-002 (10 inválidos, nenhum trecho, código específico para cada) e CS-003 (PDF de 2 MB em menos de 60 s).
- [ ] T020 [P] [US1] Criar os testes de integração do processamento em `tests/integration/fontes/test_processar_fonte.py`:
  - **Sucesso e falhas:** sucesso; `sem_texto`; `conteudo_invalido`; erro transitório com nova tentativa; tentativas esgotadas resultando em `falha_tecnica`.
  - **Exclusão e idempotência:** fonte apagada antes da transação B termina sem trechos (CB-16); reexecução de fonte `concluido` não tem efeito (RF-008).
  - **Limpeza:** o arquivo temporário é apagado.
  - **Envio:** o *rollback* do envio não deixa linha nem job, e o objeto é compensado.
  - **Reconciliação:** `reconciliar_objetos` respeita a margem (DTEC 025).
- [ ] T021 [P] [US1] Criar os testes de segurança em `tests/security/fontes/test_acervo_seguranca.py`:
  - **Tabela de isolamento:** acrescentar a `tests/security/test_isolamento_rotas.py` os casos de `GET /materias/{id}`, `GET` e `POST /materias/{id}/fontes`, `GET /fontes/{id}` e `POST /fontes/{id}/reprocessamento` (DTEC 019). Um recurso de outro estudante gera `404` idêntico ao de inexistente (RQ-003).
  - **Chave do objeto:** nunca contém o nome enviado (RQ-001).
  - **Logs:** sem texto de trecho, conteúdo nem nome de arquivo, verificado com captura (RQ-002).
  - **Proteções herdadas:** `401` sem sessão e `403` sem CSRF nas rotas novas.
- [ ] T022 [P] [US1] Criar os testes adversariais em `tests/adversarial/fontes/test_envio_adversarial.py`:
  - **Arquivos e envio:**
    - Arquivos disfarçados, ZIP com extensão `.md` e PDF com 501 páginas.
    - Corpo acima do limite com e sem `Content-Length`.
    - Nomes com `../`, caminho do Windows, RTL e 300 caracteres.
    - Dois arquivos no mesmo envio e *multipart* malformado.
    - Envio interrompido no meio: nada guardado e o temporário apagado (CB-04).
  - **Conteúdo:** TXT com instruções à IA guardado como trecho comum (CB-15).
  - **Concorrência:**
    - Dois envios simultâneos do mesmo arquivo: um `201` e um `409 fonte_duplicada`.
    - Dois envios que juntos passariam a cota: um aceito.
    - Duas criações de matéria no limite e duas com o mesmo nome em caixas diferentes.
    - Duas novas tentativas paralelas: um job e nenhum trecho duplicado.
- [ ] T023 [US1] Implementar o domínio `materias` para a US1, até que a T014 e os cenários 1 e as cotas de matéria da T019 passem:
  - `app/materias/dominio.py`, `excecoes.py`, `repositorios.py` (*advisory lock* do acervo; `IntegrityError` do nome vira `Conflito`), `servicos.py` (`criar`, `listar` com `contar_por_materia` dos participantes, `consultar`), `dtos.py`, `mapeadores.py` e `rotas.py` (`GET` e `POST /materias`, `GET /materias/{id}`);
  - `registros.py`, com `apagar_dados_usuario` das matérias no registro de exclusão (DTEC 021).
- [ ] T024 [US1] Implementar `app/fontes/dominio.py`, `validacao.py`, `extracao.py` e `divisao.py`, até que as T015 a T018 passem.
- [ ] T025 [US1] Implementar `app/fontes/repositorios.py` e `servicos.py` para a US1 (DTEC 025, 028, 030 e 032):
  - **`enviar`:** pré-verificação, gravação do objeto, transação com *advisory lock*, cotas, inserção, enfileiramento com `queueing_lock` e compensação;
  - **Consultas:** `listar`, `consultar` e `uso_do_acervo`;
  - **`reprocessar`:** transição condicional e enfileiramento em *savepoint*.

  Em `app/fontes/registros.py`, registrar o participante de matéria (`contar_por_materia`) e o `apagar_dados_usuario` das fontes.
- [ ] T026 [US1] Implementar `app/fontes/tarefas.py` (`processar_fonte` com `RetryStrategy` e `lock`, e `reconciliar_objetos` às 3h30 UTC) e registrar as tarefas em `app/worker.py`, até que a T020 passe.
- [ ] T027 [US1] Implementar `app/fontes/dtos.py`, `mapeadores.py` e `rotas.py`: `GET /acervo/uso`, `GET` e `POST /materias/{id}/fontes`, `GET /fontes/{id}` e `POST /fontes/{id}/reprocessamento`, com o limite de corpo da rota de envio e `Cache-Control: no-store`. **Pronto quando:** as T019, T021 e T022 passam.
- [ ] T028 [US1] Ampliar `tests/integration/test_contrato_openapi.py` para verificar também `docs/specs/002-materias-fontes/contracts/openapi.yaml`. Regenerar e versionar `backend/openapi.json` e rodar `npm run gerar:api`.
- [ ] T029 [P] [US1] Criar os testes de componente em `frontend/src/funcionalidades/materias/` e `frontend/src/funcionalidades/fontes/`, todos com axe sem violações:
  - **Matérias:** lista com contagens e estado vazio "Criar primeira matéria"; formulário com erro por campo vindo do `422` e do `409`, com valor preservado.
  - **Envio:**
    - Formatos e limites lidos de `/acervo/uso`.
    - Botão e arrastar e soltar.
    - Envio que não duplica enquanto carrega.
    - Recusa com a mensagem do servidor junto do campo.
  - **Acervo:** estados com `SeloEstado`, *polling* que para em estado final, anúncio em `aria-live` e "Tentar novamente" só com `podeTentarNovamente`.
  - **Painel da fonte:** os dados do cenário 3.
- [ ] T030 [US1] Implementar as telas, até que a T029 passe:
  - `frontend/src/rotas/_autenticado/materias/index.tsx` ([design, 9.3](../../base-specs/design.md#93-matérias));
  - `materias/$materiaId.tsx`, com o acervo e o envio ([design, 9.4 e 9.5](../../base-specs/design.md#94-matéria)), e a área de cartões vazia até a 003;
  - o painel `materias/$materiaId.fontes.$fonteId.tsx`;
  - os componentes de `frontend/src/funcionalidades/materias/` e `fontes/`;
  - o item "Matérias" na navegação.
- [ ] T031 [US1] Executar os passos 1 a 12 da US1 no quickstart e os testes `functional`, `security` e `adversarial` da US1, e registrar a evidência.

## Fase 4 História de usuário 2 Excluir uma fonte decidindo sobre os cartões (P2)

**Objetivo:** o estudante exclui uma fonte de vez, vê o impacto antes e escolhe o que acontece com os cartões.  
**Teste independente:** com o participante falso devolvendo 3 cartões aceitos, 2 aguardando revisão e 1 de referência, abrir a exclusão, conferir o impacto, escolher "Manter os cartões" e confirmar que o participante recebeu o modo `manter`, que o arquivo e os trechos sumiram e que a fonte não existe mais. Repetir com "Excluir os cartões junto". A repetição com cartões reais é feita pelas tarefas da 003 e da 004 (DTEC 027).

- [ ] T032 [P] [US2] Criar os testes unitários em `tests/unit/fontes/test_exclusao.py`: comparação do impacto confirmado com o recalculado e modo obrigatório (`manter` ou `excluir`).
- [ ] T033 [P] [US2] Criar os testes funcionais em `tests/functional/fontes/test_us2_exclusao_fonte.py`, com o participante falso:
  - cenários 1 a 6 da US2;
  - os aguardando revisão sempre afetados;
  - a contagem de referência separada e o modo nunca aplicado a ela (D-009);
  - cancelar não chama nada;
  - CS-004: contagens exibidas iguais às recebidas pelo participante e ao que foi apagado (arquivo, trechos, fonte).
- [ ] T034 [P] [US2] Criar os testes adversariais em `tests/adversarial/fontes/test_exclusao_fonte_adversarial.py`:
  - exclusão durante o processamento: nenhum trecho permanece (RF-013, CB-16);
  - impacto alterado entre a consulta e a confirmação: `409 impacto_alterado`, nada apagado;
  - duas exclusões paralelas: um `204` e um `404`;
  - falha do armazenamento ao apagar o objeto: transação desfeita, fonte intacta e nova tentativa bem-sucedida.
- [ ] T035 [P] [US2] Acrescentar à tabela de isolamento os casos de `GET /fontes/{id}/impacto-exclusao` e `POST /fontes/{id}/exclusao`, com `404` idêntico para fonte de outro estudante.
- [ ] T036 [US2] Implementar em `app/fontes/servicos.py` e `repositorios.py` o `impacto_exclusao` e o `excluir`: `FOR UPDATE`, recálculo, objeto antes das linhas e `ao_excluir_fonte(modo)` dos participantes. Implementar também os DTOs e as rotas correspondentes, até que as T032 a T035 passem (DTEC 031).
- [ ] T037 [P] [US2] Criar o teste de componente `frontend/src/funcionalidades/fontes/DialogoExclusaoFonte.test.tsx`. O diálogo deve:
  - mostrar título, caráter definitivo, aceitos, aguardando e referência em linhas separadas;
  - exigir uma escolha;
  - prender o foco e devolvê-lo ao acionador;
  - não mudar nada ao cancelar;
  - recarregar o impacto depois de `409`;
  - ter ação destrutiva distinta por texto e ícone (RQ-004);
  - passar no axe sem violações.
- [ ] T038 [US2] Implementar o diálogo e a ação "Excluir" no acervo, inclusive para fontes `falhou` (RF-012, D-010), invalidando as consultas da matéria e do acervo depois da exclusão.
- [ ] T039 [US2] Executar o teste independente da US2 e a verificação complementar do quickstart, e registrar a evidência.

## Fase 5 História de usuário 3 Organizar matérias e fontes (P3)

**Objetivo:** o estudante renomeia matérias e fontes e exclui uma matéria em cascata, com confirmação pelo nome.  
**Teste independente:** renomear uma matéria, tentar repetir um nome existente e excluir uma matéria com fontes e cartões (participante falso), conferindo o impacto e a confirmação pelo nome.

- [ ] T040 [P] [US3] Criar os testes funcionais em `tests/functional/materias/test_us3_organizar.py`:
  - cenários 1 a 5 da US3;
  - exclusão da matéria apagando as fontes, os trechos e os objetos e chamando os participantes na ordem de prioridade;
  - renomeação da fonte alterando só `fontes.titulo` (D-005);
  - CS-004 para a matéria.
- [ ] T041 [P] [US3] Criar os testes adversariais em `tests/adversarial/materias/test_organizar_adversarial.py`:
  - exclusão da matéria durante um envio: `404` e objeto compensado;
  - exclusão com fonte em processamento: nenhum trecho permanece;
  - impacto alterado: `409`;
  - duas renomeações concorrentes para o mesmo nome: uma recusada;
  - confirmação com outra caixa ou com espaços nas extremidades: só a caixa diferente é recusada (`422 confirmacao_invalida`).
- [ ] T042 [P] [US3] Criar os testes de segurança:
  - acrescentar à tabela de isolamento os casos de `PATCH /materias/{id}`, `GET /materias/{id}/impacto-exclusao`, `POST /materias/{id}/exclusao` e `PATCH /fontes/{id}`;
  - reexecutar `tests/security/identidade/test_exclusao_completa.py` (001) com matérias, fontes, trechos e objetos criados: nada permanece depois da exclusão da conta (DTEC 021).
- [ ] T043 [US3] Implementar `renomear`, `impacto_exclusao` e `excluir` em `app/materias/servicos.py`:
  - **Exclusão:** `FOR UPDATE` na matéria e nas fontes por `id`, participantes por prioridade e confirmação pelo nome.
  - **Participante de `fontes`:** `ao_excluir_materia` apaga os objetos e as linhas.
  - **Renomeação de fonte:** `renomear` em `app/fontes/servicos.py`.
  - **DTOs e rotas** correspondentes, até que as T040 a T042 passem.
- [ ] T044 [P] [US3] Criar os testes de componente: renomeação da matéria (erro de nome em uso), `DialogoExclusaoMateria.test.tsx` (contagens, botão habilitado só com o nome exato, `409` recarregando, foco e axe) e renomeação da fonte (1 a 120 caracteres).
- [ ] T045 [US3] Implementar na interface a renomeação e a exclusão da matéria e a renomeação da fonte. Depois da exclusão da matéria, a tela volta para a lista de matérias.
- [ ] T046 [US3] Executar o teste independente da US3 e registrar a evidência.

## Fase final Qualidade transversal

- [ ] T047 Executar nos contêineres as suítes completas do backend e do frontend, a qualidade estática e a verificação do contrato, e confirmar a integração contínua aprovada na `develop`. Registrar as contagens de testes e a cobertura.
- [ ] T048 Revisar e registrar as evidências:
  - **Logs:** `api` e `worker` sem conteúdo de fonte, texto de trecho ou nome de arquivo (RQ-002).
  - **Repositório:** sem segredos nem arquivos gerados versionados (regras 9 e 10).
  - **Acessibilidade (RQ-004):** teclado e leitor de tela na lista de matérias, na página da matéria, no envio e nos dois diálogos; uso em 320 px sem rolagem horizontal; contraste.
- [ ] T049 Medir e registrar:
  - o tempo do PDF de 2 MB até `concluido` (CS-003);
  - o tempo de um envio de PDF, incluindo a verificação isolada;
  - o pico de memória do `worker` durante a extração.
- [ ] T050 Atualizar o [quickstart](quickstart.md) com os comandos realmente verificados, `docs/skills/padroes-implementacao.md` com os comandos novos e o "Mapa do repositório" do `.agents/AGENTS.md` com os domínios `materias` e `fontes`.
- [ ] T051 Atualizar o [traceability.md](traceability.md) com os nomes reais dos testes e corrigir requisitos sem teste ou tarefa.

## Dependências

- **Spec 001:** as T001 a T045 da 001 bloqueiam toda esta lista.
- **Preparação e base:** a Fase 1 bloqueia a Fase 2, e a Fase 2 (T003 a T013) bloqueia todas as histórias. T008 bloqueia T020, T023 e T025; T003 bloqueia T018 e T024; T010 bloqueia T016 a T022.
- **US1:** T023 e T024 em paralelo → T025 → T026 → T027 → T028. As tarefas de teste T014 a T022 e T029 não dependem umas das outras. T030 depende de T012 e T028, porque usa os tipos gerados.
- **US2:** depende das rotas da US1 (T027). T032 a T035 rodam em paralelo.
- **US3:** depende da US1. Pode ser feita em paralelo à US2, por pessoas diferentes, porque altera funções distintas de `servicos.py` e `rotas.py`, com commits separados.
- **Specs seguintes:** os testes funcionais da US2 e da US3 são reexecutados com cartões reais pelas tarefas da 003 (participante dos cartões criados à mão) e da 004 (participante dos cartões gerados e das gerações), conforme a DTEC 027.
- **Fase final:** depende de todas as histórias.

## Pontos de paralelismo

- **Base:** T003 a T007, T009, T010 e T012 alteram arquivos distintos.
- **Histórias:** em cada uma, as tarefas de teste marcadas com `[P]` podem ser escritas em paralelo. O frontend (T029 e T030; T037 e T038; T044 e T045) avança em paralelo ao backend depois da T028.

## Estratégia de incremento

1. **Base completa:** a T013 prova que o ambiente sobe com o volume de arquivos e que a integração contínua passa.
2. **P1 demonstrável:** entregar a US1 (envio e processamento), que é o que a geração de cartões ([004](../004-geracao-cartoes/spec.md)) precisa.
3. **Histórias seguintes:** acrescentar a US2 e a US3 sem quebrar a P1. A suíte completa passa a cada commit.
4. **Verificação final:** executar a fase final e atualizar os artefatos afetados. Nenhum merge na `main` acontece sem todos os testes passando (regra 17).
