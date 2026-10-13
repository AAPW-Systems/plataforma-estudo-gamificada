# Pesquisa e decisões técnicas

**Funcionalidade:** 002-materias-fontes (matérias, envio e processamento de fontes)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-002-materias-fontes-plano.md))  
**Status:** DTEC 028 a 032 aprovadas em 13/10/2026 por Artur Lins, com o plano

Este arquivo registra apenas as dúvidas técnicas **novas** da spec 002. Não são reabertas as decisões já tomadas em [`../../research.md`](../../research.md): fila (DTEC 006), extração com PyMuPDF (DTEC 009), armazenamento (DTEC 010), camadas (DTEC 018). Também valem as DTEC transversais propostas neste planejamento: isolamento do processamento de arquivos (DTEC 024), consistência entre armazenamento e banco (DTEC 025), acompanhamento na interface (DTEC 026) e participantes da exclusão (DTEC 027). Da [spec 001](../001-conta-acesso/research.md) valem o isolamento (DTEC 019) e as chaves por usuário (DTEC 021). A numeração das DTEC é única no projeto.

| Decisão | Título |
|---|---|
| [DTEC 028](#decisão-dtec-028-validação-do-arquivo-no-envio) | Validação do arquivo no envio |
| [DTEC 029](#decisão-dtec-029-extração-normalização-e-divisão-em-trechos) | Extração, normalização e divisão em trechos |
| [DTEC 030](#decisão-dtec-030-estados-falhas-e-novas-tentativas-do-processamento) | Estados, falhas e novas tentativas do processamento |
| [DTEC 031](#decisão-dtec-031-impacto-da-exclusão-sob-concorrência) | Impacto da exclusão sob concorrência |
| [DTEC 032](#decisão-dtec-032-cotas-e-duplicatas-sob-concorrência) | Cotas e duplicatas sob concorrência |

## Decisão DTEC 028 Validação do arquivo no envio

**Questão:** como verificar extensão, tipo real do conteúdo, tamanho e integridade antes de aceitar uma fonte (RF-004, US1 cenário 4, CS-002), com uma explicação específica para cada recusa e sem guardar nada do que foi recusado?  
**Critérios:** cada caso de borda da spec com uma mensagem própria; nenhuma tecnologia nova; resistência a arquivos disfarçados e malformados (Princípio II); nome enviado nunca usado como caminho (RQ-001); latência baixa.  
**Alternativas consideradas:**

1. **Verificação própria por assinatura e decodificação, com a abertura do PDF isolada (DTEC 024):** os três formatos do MVP têm verificação trivial. O PDF tem o cabeçalho `%PDF-` e é aberto pelo PyMuPDF; TXT e MD passam por decodificação UTF-8 estrita.
2. **`python-magic` (libmagic):** detecta centenas de tipos, mas exige uma biblioteca de sistema na imagem e uma DTEC nova, sem ganho para três formatos. Também não diferencia TXT de MD nem verifica a integridade do PDF.
3. **Biblioteca `filetype` (assinaturas em Python puro):** não reconhece texto e também seria dependência nova.

**Decisão:** alternativa 1, com a ordem e os códigos abaixo. Os textos de TXT e MD só são aceitos em **UTF-8**, com ou sem BOM. O recurso para Windows-1252 foi rejeitado porque quase todo binário vira "texto válido" nessa codificação, e o caso "codificação inválida" deixaria de existir. A detecção automática de codificação foi rejeitada por exigir dependência nova e errar em textos curtos.

| Ordem | Verificação | Recusa |
|---:|---|---|
| 1 | Corpo da requisição acima de `FONTE_TAMANHO_MAX_BYTES` + 64 KiB (sobrecarga do *multipart*), pelo `Content-Length` ou durante a leitura | `413 arquivo_muito_grande` |
| 2 | Exatamente um campo de arquivo `arquivo`; campo `titulo` opcional | `422 dados_invalidos` |
| 3 | Gravação em arquivo temporário com cálculo do SHA-256 e do tamanho; arquivo com 0 byte, ou acima do limite | `422 arquivo_vazio`; `413 arquivo_muito_grande` |
| 4 | Extensão do nome enviado (`.pdf`, `.txt`, `.md`, `.markdown`, sem diferenciar maiúsculas e minúsculas) | `422 formato_nao_aceito` |
| 5 | Assinatura: `.pdf` exige `%PDF-` nos primeiros 1.024 bytes; `.txt` e `.md` não podem ter assinatura de PDF, ZIP, imagem nem byte nulo | `422 tipo_divergente` |
| 6 | TXT e MD: decodificação UTF-8 estrita (BOM removido) e ausência de caracteres de controle além de tabulação, quebra de linha e retorno de carro | `422 codificacao_invalida`; `422 tipo_divergente` |
| 7 | TXT e MD: texto sem nenhum caractere visível depois da normalização | `422 arquivo_vazio` |
| 8 | PDF, num subprocesso isolado (DTEC 024): abre com o PyMuPDF, recusa o que exige senha (`needs_pass`) e confere de 1 a `PDF_MAX_PAGINAS` páginas | `422 arquivo_corrompido` (não abre, sem páginas, tempo ou memória esgotados); `422 pdf_protegido`; `422 pdf_paginas_excedidas` |

**Justificativa:** cobre todos os casos de borda da spec com códigos estáveis, sem dependência nova. A abertura do PDF em subprocesso impede que um arquivo malicioso derrube a API. A ausência de camada de texto **não** é verificada aqui: ela é resultado da extração, e a spec a trata como falha de processamento (US1 cenário 5, CB-23).  
**Consequências:**

- **Status 413:** a hierarquia `ErroAplicacao` ganha a subclasse `ConteudoMuitoGrande` (413), usada só por esta rota no MVP. É uma extensão aditiva da DTEC 018, registrada em [`padroes-implementacao.md`](../../skills/padroes-implementacao.md#erros-e-respostas-da-api).
- **Nome exibido** (`nome_arquivo`): fica só o último segmento depois de `/` ou `\`, em NFC. Saem os caracteres de controle (C0, C1) e os de direção bidirecional (U+202A a U+202E e U+2066 a U+2069), e o resultado é truncado em 255 caracteres. Se ficar vazio, vira `arquivo`. A chave do objeto é `usuarios/{public_id_usuario}/fontes/{uuid4}`, sem nada do nome (RQ-001, DTEC 021).
- **Título padrão** (RF-003): o nome exibido sem a extensão, truncado em 120 caracteres. Se ficar vazio, vira "Fonte sem título".
- **Tipo gravado** (`tipo_midia`): `application/pdf`, `text/plain` ou `text/markdown`, conforme o conteúdo verificado e nunca conforme o `Content-Type` enviado pelo navegador.
- **Arquivo temporário:** é apagado ao fim da requisição em qualquer caminho, de sucesso ou de erro.
- **Limites configuráveis** (RQ-005): `FONTE_TAMANHO_MAX_BYTES` (2 MiB) e `PDF_MAX_PAGINAS` (500). As extensões aceitas são fixas no código do MVP: novos formatos são da [spec 009](../009-formatos-fontes/spec.md). A interface lê os limites vigentes em `GET /api/v1/acervo/uso`.

**Condição para revisão:** formatos novos ([009](../009-formatos-fontes/spec.md)) ou um caso real de arquivo legítimo recusado por codificação.

## Decisão DTEC 029 Extração, normalização e divisão em trechos

**Questão:** como transformar o arquivo em trechos ordenados, com página só quando conhecida (RF-006, CS-001), reprodutíveis e adequados à geração de cartões ([004](../004-geracao-cartoes/spec.md)) e à futura indexação ([014](../014-chat-fontes/spec.md))? A DTEC 009 deixou os parâmetros de divisão como experimentais.  
**Critérios:** página correta em 100% dos trechos de PDF (CS-001); nenhum texto perdido; reprodutibilidade (Princípio IV); trechos de tamanho útil para o modelo de linguagem e para embeddings; nenhuma dependência nova; meta de 60 s para 2 MB (CS-003).  
**Alternativas consideradas:**

1. **Divisor próprio por estrutura, como função pura:** unidades por página (PDF), por seção de título (MD) ou documento inteiro (TXT); dentro da unidade, parágrafos acumulados até o tamanho alvo, com corte em frase e sobreposição curta. Testado com Hypothesis por invariantes.
2. **Divisor de biblioteca (ex.: `semchunk` ou os divisores de frameworks de LLM):** dependência nova, sem garantia de que um trecho nunca atravesse duas páginas.
3. **Janelas de tamanho fixo, sem estrutura:** simples, mas corta frases e parágrafos no meio, o que piora a geração e a citação.

**Decisão:** alternativa 1, com estes parâmetros iniciais, configuráveis por ambiente:

| Parâmetro | Variável | Valor inicial |
|---|---|---:|
| Tamanho alvo do trecho | `TRECHO_TAMANHO_ALVO` | 1.200 caracteres |
| Tamanho máximo | `TRECHO_TAMANHO_MAXIMO` | 2.000 caracteres |
| Sobreposição com o trecho anterior | `TRECHO_SOBREPOSICAO` | 150 caracteres |

**Justificativa:** é a única alternativa que garante uma página por trecho (CS-001) sem dependência nova. Os tamanhos ficam bem abaixo da janela do bge-m3 (8.192 *tokens*, DTEC 008) e permitem citar o trecho inteiro na evidência. Como são parâmetros experimentais, a avaliação da [004](../004-geracao-cartoes/spec.md) pode ajustá-los sem mudar o código.  
**Consequências:**

- **Extração (no subprocesso, DTEC 024):**
  - **PDF:** `page.get_text("text", sort=True, flags=TEXT_DEHYPHENATE)` página a página. A página é o **número físico** (índice + 1), que coincide com o contador de qualquer leitor de PDF, e não o rótulo lógico (ex.: "iv").
  - **TXT e MD:** o texto já decodificado na validação, sem página. O MD é guardado como texto-fonte, sem renderização, e a interface sempre o exibe como texto puro, o que elimina o risco de injeção de HTML.
- **Normalização:**
  - NFC; `\r\n` e `\r` viram `\n`.
  - Saem os caracteres de controle, exceto `\n` e `\t`.
  - Espaços e tabulações repetidos viram um espaço, e três ou mais quebras de linha viram duas.
  - Os espaços no fim de cada linha são removidos.
- **Sem texto:** um PDF cujas páginas, depois de normalizadas, não têm nenhum caractere alfanumérico resulta em `sem_texto` (CB-23). Não há quantidade mínima de texto (RF-016, D-006).
- **Deslocamentos:** `inicio_caractere` e `fim_caractere` são relativos ao texto normalizado da fonte inteira, com as páginas unidas por `\n\n`, de modo que `texto_completo[inicio:fim] == trecho.texto`. O texto completo não é guardado: os deslocamentos servem à ordem, ao destaque e à evolução da indexação.
- **Divisão:**
  - **Unidades:** cada página do PDF; no MD, cada seção iniciada por um título ATX (`#` a `######` seguido de espaço, fora de blocos de código cercados); no TXT, o documento inteiro.
  - **Acúmulo:** dentro da unidade, parágrafos (separados por linha em branco) são acumulados até o alvo.
  - **Partes longas:** um parágrafo acima do máximo é cortado em fim de frase (`.`, `!`, `?` ou `…` seguidos de espaço), e uma frase acima do máximo, no último espaço antes do limite. Sem espaço, o corte cai no próprio limite.
  - **Sobreposição:** o trecho seguinte começa com até 150 caracteres do anterior, alinhados ao início de uma palavra, e nunca atravessa a unidade.
  - **Sobra:** uma sobra final menor que 200 caracteres é unida ao trecho anterior se o total couber no máximo.
- **Invariantes testados com Hypothesis:**
  - `texto_completo[inicio:fim] == texto`.
  - A ordem é contígua a partir de 0, e os inícios não diminuem.
  - Nenhum trecho passa do máximo.
  - Todo caractere visível do texto pertence a pelo menos um trecho.
  - Nenhum trecho de PDF atravessa páginas, e todo trecho de PDF tem página.
  - Nenhum trecho de TXT ou MD tem página.
- **Versão:** `fontes.versao_extracao` guarda a versão do extrator e os parâmetros (ex.: `v1-a1200-m2000-s150`). Trechos de uma fonte `concluido` nunca são substituídos no MVP (DTEC 030). Uma futura reextração com outra versão será uma decisão própria, que precisa preservar as evidências dos cartões.
- **Desempenho:** os trechos são inseridos em lote (blocos de 500) na mesma transação. Um texto de 2 MB gera cerca de 1.700 trechos, bem dentro da meta do CS-003.

**Condição para revisão:** a avaliação da geração ([004](../004-geracao-cartoes/spec.md)) ou da busca ([014](../014-chat-fontes/spec.md)) indicar outros tamanhos, ou formatos novos ([009](../009-formatos-fontes/spec.md)) exigirem outras unidades (ex.: blocos de legenda com marcação de tempo).

## Decisão DTEC 030 Estados, falhas e novas tentativas do processamento

**Questão:** como implementar os estados `pendente`, `processando`, `concluido` e `falhou` (RF-005), distinguir falha técnica de conteúdo sem texto (RF-007), repetir sem duplicar (RF-008) e se recuperar de um worker que morre no meio, cumprindo as heranças da DTEC 021 (tarefa idempotente, enfileirada na mesma transação, sem efeito se o registro não existir mais)?  
**Critérios:** RN-03 e RN-10 da base; CB-16; nenhuma tarefa perdida ou duplicada; mensagem certa ao estudante; nada de estado travado para sempre.  
**Alternativas consideradas:**

1. **Tarefa `processar_fonte` com trava de fila e de execução, novas tentativas automáticas só para erros transitórios, código de falha persistido e tarefa periódica para jobs travados.**
2. **Sem novas tentativas automáticas:** toda falha transitória (ex.: banco reiniciando) viraria `falhou` e exigiria a ação do estudante.
3. **Estado só nas tabelas do Procrastinate:** acopla a API à fila e não distingue o tipo de falha.

**Decisão:** alternativa 1.

```text
pendente ──worker inicia──> processando ──trechos gravados──> concluido
                                 │
                                 ├── sem texto ─────────────> falhou (sem_texto)
                                 ├── ilegível ──────────────> falhou (conteudo_invalido)
                                 └── erro transitório, tentativas esgotadas ──> falhou (falha_tecnica)
falhou (falha_tecnica) ──nova tentativa do estudante──> pendente
```

**Justificativa:** o estado do domínio fica na tabela `fontes` (Princípio IV). A fila garante entrega e repetição, e a combinação de trava de fila, verificação de estado e transação com `FOR UPDATE` garante um único efeito.  
**Consequências:**

- **Enfileiramento:** `processar_fonte(fonte_id)` é enfileirada na transação que insere a fonte (emenda da DTEC 002). Ela usa `queueing_lock=f"fonte:{fonte_id}"` (no máximo um job na fila) e `lock=f"fonte:{fonte_id}"` (nunca duas execuções simultâneas). O identificador interno só circula dentro da fila, nunca na API.
- **Passos da tarefa:**
  1. **Transação A:** `SELECT ... FOR UPDATE` da fonte. Se não existir, termina sem efeito. Se já estiver `concluido`, também termina sem efeito, e por isso os trechos de uma fonte concluída nunca são substituídos (RF-008). Senão, grava `processando`.
  2. **Leitura:** lê o objeto para um arquivo temporário (`ler_para_arquivo`). Se o objeto não existe e a fonte também não, termina sem efeito; se a fonte existe, `falha_tecnica`.
  3. **Extração e divisão:** extração no subprocesso isolado (DTEC 024), depois divisão (DTEC 029).
  4. **Transação B:** `SELECT ... FOR UPDATE` da fonte. Se ela não existe mais (excluída no meio, CB-16 e RF-013), termina sem efeito. Senão, apaga eventuais trechos de uma execução anterior não concluída, insere os novos e grava `concluido`, `total_trechos`, `total_paginas`, `versao_extracao` e `processada_em`.
  5. **Fim:** o arquivo temporário é apagado em qualquer caminho.
- **Novas tentativas automáticas:** `RetryStrategy(max_attempts=2, exponential_wait=5, retry_exceptions={ErroTransitorio})`, em que `ErroTransitorio` agrupa falhas de E/S do armazenamento e de conexão com o banco. Durante as tentativas, a fonte fica `processando`. Na última tentativa (lida pelo contexto do job), a tarefa grava `falhou` com `falha_tecnica` em vez de relançar.
- **Falhas de conteúdo** (`sem_texto`, `conteudo_invalido`) são gravadas na hora, sem nova tentativa.
- **Nova tentativa pelo estudante:** `POST /api/v1/fontes/{id}/reprocessamento`.
  - Na transação, trava a fonte e exige `falhou` com `falha_tecnica`; caso contrário, `409 reprocessamento_indisponivel`.
  - Grava `pendente`, limpa o código e enfileira de novo.
  - Se a trava de fila acusar job já enfileirado (`AlreadyEnqueued`), o pedido é tratado como sucesso. O enfileiramento roda num *savepoint*, para não abortar a transação.
- **Jobs travados:** um worker morto deixa o job em `doing` e a fonte em `processando`. A tarefa periódica `reenfileirar_tarefas_travadas` roda a cada 10 minutos, com `queueing_lock` próprio, no núcleo (`nucleo/fila.py`), e vale também para a 004. Ela usa `get_stalled_jobs` (sem sinal de vida há mais de 60 s, configurável), `retry_job` para cada um e `prune_stalled_workers`. Como a tarefa é idempotente, repetir é seguro.
- **Catálogo de mensagens:** o banco guarda só o código (`fontes.codigo_falha`), e a mensagem vem de um catálogo único da aplicação, devolvido pela API como `mensagemFalha`:
  - `falha_tecnica`: "Não conseguimos processar esta fonte por um problema técnico. Tente novamente."
  - `sem_texto`: "Este PDF não tem texto selecionável. PDFs digitalizados (imagens de páginas) não são aceitos."
  - `conteudo_invalido`: "Não foi possível ler o conteúdo deste arquivo. Verifique se ele abre normalmente e envie de novo."
- **Logs:** os eventos `fonte_recebida`, `processamento_iniciado`, `processamento_concluido` (duração, páginas, trechos) e `processamento_falhou` (código e tentativa) levam o `public_id` da fonte e do usuário, nunca o conteúdo nem o nome do arquivo (RQ-002).

**Condição para revisão:** uma reextração de fontes concluídas, que exigiria preservar as evidências, ou uma taxa de `falha_tecnica` que indique problema de infraestrutura.

## Decisão DTEC 031 Impacto da exclusão sob concorrência

**Questão:** como garantir que as contagens exibidas no diálogo de exclusão coincidam com o que é efetivamente apagado (CS-004)? Entre a consulta do impacto e a confirmação, uma geração pode terminar ou um cartão pode ser aceito em outra aba.  
**Critérios:** CS-004 em 100% dos testes, inclusive concorrentes; Princípio III (o estudante decide sabendo o que perde); simplicidade.  
**Alternativas consideradas:**

1. **Confirmação com as contagens exibidas:** o pedido de exclusão reenvia o impacto que o estudante viu. O servidor trava a fonte (ou a matéria e as suas fontes), recalcula na mesma transação e, se houver diferença, recusa com `409 impacto_alterado`. A interface recarrega o impacto e mostra o diálogo atualizado.
2. **Confiar na consulta anterior:** apaga o que existir no momento, mesmo que seja diferente do exibido, o que contraria o CS-004 sob concorrência.
3. **Token de impacto assinado com validade:** equivale à alternativa 1, com mais estado e mais código.

**Decisão:** alternativa 1.  
**Justificativa:** o estudante nunca apaga algo diferente do que viu, e o caso comum (sem concorrência) não tem custo extra.  
**Consequências:**

- **Fonte:**
  - `GET /fontes/{id}/impacto-exclusao` devolve título, estado e as contagens da DTEC 027 (`cartoesGeradosAceitos`, `cartoesAguardandoRevisao`, `cartoesReferencia`).
  - `POST /fontes/{id}/exclusao` recebe `modoCartoes` (`manter` ou `excluir`) e `impactoConfirmado`.
  - A exclusão trava a fonte (`FOR UPDATE`), recalcula, apaga o objeto (DTEC 025), executa os participantes com o modo escolhido e apaga trechos e fonte, tudo na mesma transação. Resposta `204`.
- **Matéria:**
  - `GET /materias/{id}/impacto-exclusao` devolve nome, `fontes`, `cartoesAtivos` e `cartoesAguardandoRevisao`. Desde a emenda de 13/10/2026 da DTEC 027, `cartoesAtivos` é a soma de `cartoes_ativos` e `cartoes_suspensos` dos participantes.
  - `POST /materias/{id}/exclusao` recebe `nomeConfirmacao` e `impactoConfirmado`. O nome é comparado depois de NFC e sem espaços nas extremidades, **diferenciando** maiúsculas e minúsculas, por ser confirmação de ação destrutiva; se não confere, `422 confirmacao_invalida`.
  - A exclusão trava a matéria e as suas fontes (`FOR UPDATE`, em ordem de `id`, para evitar *deadlock*), recalcula e executa os participantes: cartões e gerações primeiro, `fontes` por último (objetos antes das linhas). Depois apaga a matéria. Resposta `204`.
- **Processamento em andamento:** a exclusão não espera o worker. A transação B do worker encontra a fonte apagada e termina sem gravar nada (CB-16, RF-013). Um job ainda na fila roda e termina sem efeito.
- **Obrigação da 004:** a tarefa de geração, ao publicar cartões, trava a fonte com `FOR SHARE`. Assim a publicação e a exclusão se serializam, e uma geração nunca publica cartões de uma fonte já apagada (CB-16).
- **Lição aberta (CB-27):** a exclusão não toca `revisoes`, `eventos_xp` nem `dias_estudo`. Os cartões apagados deixam de vir na próxima consulta da lição (spec 005).

**Condição para revisão:** exclusão de fontes em lote (fora do escopo), que exigiria impacto agregado.

## Decisão DTEC 032 Cotas e duplicatas sob concorrência

**Questão:** como impedir que dois envios ou duas criações simultâneas ultrapassem as cotas de D-003 (50 matérias, 30 fontes por matéria, 100 MB por estudante) ou aceitem o mesmo arquivo duas vezes na mesma matéria (D-004)?  
**Critérios:** "no máximo um é aceito" nos casos de borda da spec; nenhum serviço novo; nenhum bloqueio entre estudantes diferentes; nenhuma interferência com as travas da 001 na linha `usuarios`.  
**Alternativas consideradas:**

1. ***Advisory lock* por estudante na transação, mais índices únicos:** `pg_advisory_xact_lock(<espaço do acervo>, usuario_id)` serializa só as operações de cota do mesmo estudante. O índice único `(materia_id, hash_sha256)` resolve a duplicata, e o índice `(usuario_id, lower(nome))` resolve o nome repetido.
2. **`SELECT ... FOR UPDATE` na linha do usuário:** mesmo efeito, mas disputa a linha com a atualização de `ultimo_uso_em` da sessão e com o perfil (001).
3. **Contadores desnormalizados em `usuarios`:** mais uma regra para manter coerente em toda escrita, sem ganho no volume do projeto.

**Decisão:** alternativa 1. Ela refina a recomendação inicial da rodada de alinhamento (travar a linha do usuário), com o mesmo efeito e sem disputar a linha com a 001.  
**Justificativa:** é o mesmo mecanismo já usado na DTEC 020, sem colisão com outras travas. As contagens são consultas indexadas sobre poucas linhas por estudante.  
**Consequências:**

- **Criar matéria:**
  1. Abre a transação e pega o *advisory lock*.
  2. Se já há `COTA_MATERIAS` matérias, recusa com `409 cota_materias_excedida`.
  3. Insere a matéria. A violação do índice de nome vira `409 materia_nome_em_uso`, também ao renomear.
- **Enviar fonte:**
  1. **Pré-verificação sem trava**, só para falhar cedo, antes de gravar o objeto: matéria do estudante (`404`), duplicata (`409 fonte_duplicada`) e cotas (`409 cota_fontes_excedida` ou `409 cota_armazenamento_excedida`).
  2. **Gravação do objeto** (DTEC 025).
  3. **Transação:** *advisory lock*, nova verificação das cotas, inserção (o índice único resolve a corrida da duplicata) e enfileiramento.
  4. **Em qualquer erro depois da gravação**, o objeto é apagado.
- **Mensagens:**
  - `fonte_duplicada`: "Esta fonte já está nesta matéria: «{título existente}»" (D-004).
  - Cotas: a mensagem cita o limite (ex.: "Você atingiu o limite de 30 fontes nesta matéria. Exclua uma fonte para enviar outra."). Fontes com `falhou` contam nas cotas (D-010).
- **Matéria excluída durante um envio:** a inserção da fonte trava a matéria em modo de chave compartilhada (FK), e a exclusão trava a mesma linha com `FOR UPDATE`, então as duas operações se serializam. Se a exclusão vence, a inserção falha na FK e responde `404 recurso_nao_encontrado` (e o objeto é apagado).
- **Variáveis** (RQ-005): `COTA_MATERIAS` (50), `COTA_FONTES_POR_MATERIA` (30) e `COTA_ARMAZENAMENTO_BYTES` (104.857.600). Os valores vigentes e o uso atual vão para a interface em `GET /api/v1/acervo/uso`.

**Condição para revisão:** cotas por plano ou por papel (ex.: painel administrativo, [016](../016-painel-administrativo/spec.md)).

## Fontes consultadas

- Documentação do Procrastinate (`procrastinate.readthedocs.io/en/stable`): *Retry a task* (`RetryStrategy`, `retry_exceptions`), *Queueing locks* (`AlreadyEnqueued`), *Locks* e *Retry stalled jobs* (`get_stalled_jobs`, `retry_job`, `prune_stalled_workers`), consultadas em 13/10/2026.
- Documentação do PyMuPDF: `Document.needs_pass`, `Document.page_count`, `Page.get_text` com `sort` e a opção `TEXT_DEHYPHENATE`.
- Especificação ISO 32000 (PDF): o cabeçalho `%PDF-` pode aparecer nos primeiros 1.024 bytes.
- Documentação do PostgreSQL: *advisory locks*, `SELECT ... FOR UPDATE`/`FOR SHARE` e travas de linha tomadas por chaves estrangeiras.
- Unicode Technical Report #36 (*Unicode Security Considerations*): caracteres de controle bidirecional em nomes exibidos.
