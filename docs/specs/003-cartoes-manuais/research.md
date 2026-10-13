# Pesquisa e decisões técnicas

**Funcionalidade:** 003-cartoes-manuais (cartões criados e gerenciados pelo estudante)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-003-cartoes-manuais-plano.md))  
**Status:** DTEC 035 a 038 aprovadas em 13/10/2026 por Artur Lins, com o plano

Este arquivo registra apenas as dúvidas técnicas **novas** da spec 003. Não são reabertas as decisões já tomadas em [`../../research.md`](../../research.md): FSRS com a biblioteca `fsrs` (DTEC 012), camadas (DTEC 018) e participantes da exclusão (DTEC 027, com a emenda de 13/10/2026). Também valem as DTEC transversais propostas neste planejamento: busca com `unaccent` (DTEC 033) e paginação por cursor (DTEC 034). Da [spec 001](../001-conta-acesso/research.md) valem o isolamento (DTEC 019) e a exclusão da conta (DTEC 021). Da [spec 002](../002-materias-fontes/research.md) vale o impacto da exclusão sob concorrência (DTEC 031). A numeração das DTEC é única no projeto.

| Decisão | Título |
|---|---|
| [DTEC 035](#decisão-dtec-035-referência-de-um-cartão-manual-a-uma-fonte) | Referência de um cartão manual a uma fonte |
| [DTEC 036](#decisão-dtec-036-texto-limites-e-validação-dos-cartões) | Texto, limites e validação dos cartões |
| [DTEC 037](#decisão-dtec-037-estado-de-agendamento-edição-e-situação-do-cartão) | Estado de agendamento, edição e situação do cartão |
| [DTEC 038](#decisão-dtec-038-fronteira-com-a-spec-004-e-participante-da-exclusão) | Fronteira com a spec 004 e participante da exclusão |

## Decisão DTEC 035 Referência de um cartão manual a uma fonte

**Questão:** onde guardar a fonte que o estudante indica como referência de um cartão manual (RF-002), de modo que a descrição da origem (título, nome do arquivo e data do envio) sobreviva à exclusão e à renomeação da fonte (RN-05, D-005 da 002), que a 002 consiga contar e marcar esses cartões (D-009 da 002, D-006) e que o cartão nunca pareça verificado (Princípio I)? O [esquema inicial](../../arquitetura/esquema-inicial.dbml) não tinha esse lugar: `cartoes` não tinha coluna de fonte, e `evidencias_cartoes` liga o cartão a trechos que o sustentam.  
**Critérios:**

- separação entre **evidência** (sustentação de um cartão gerado, que dá o selo) e **referência** (citação feita pelo estudante, que nunca dá o selo);
- mesma matéria e mesmo dono garantidos pelo banco (RN-01);
- falha ruidosa se a exclusão da fonte esquecer os cartões (DTEC 027);
- listagem sem consultas extras;
- nenhuma regra nova da 004 embutida na 003.

**Alternativas consideradas:**

1. **Colunas em `cartoes`:** `fonte_id` anulável, mais as cópias `referencia_titulo`, `referencia_nome_arquivo` e `referencia_enviada_em`. A FK composta `(fonte_id, materia_id, usuario_id)` aponta para `fontes(id, materia_id, usuario_id)`, com `on delete restrict`.
2. **Tabela 1:1 `referencias_cartoes`:** mais normalizada, mas acrescenta uma junção a toda listagem e uma tabela inteira por quatro colunas de uma relação de zero ou um.
3. **Reaproveitar `evidencias_cartoes` com `trecho_id` nulo e uma coluna de fonte:** mistura evidência e referência na mesma tabela. Bastaria um erro de consulta para um cartão manual parecer sustentado, o que viola o Princípio I e a D-002.

**Decisão:** alternativa 1.  
**Justificativa:** a relação é de zero ou um e tem quatro colunas. Mantê-la no próprio cartão deixa a listagem numa única consulta, e os `CHECK` expressam no banco a regra de que referência não é evidência. A FK composta garante a mesma matéria e o mesmo dono sem código. O `restrict` transforma o esquecimento do participante numa falha visível nos testes, como prevê a DTEC 027.  
**Consequências:**

- **Índice novo em `fontes`:** único `(id, materia_id, usuario_id)` (`fontes_id_materia_usuario`), alvo da FK composta. A 003 o cria na sua migração, sem alterar o comportamento da 002.
- **`CHECK` em `cartoes`:**
  - as três cópias presentes juntas ou ausentes juntas;
  - `fonte_id` não nulo só com as cópias presentes;
  - referência só com `origem = 'criado'`.
- **"Fonte apagada":** cópias presentes e `fonte_id` nulo. É um valor derivado, nunca gravado à parte.
- **Exclusão da fonte:** o participante dos cartões executa `UPDATE cartoes SET fonte_id = NULL WHERE fonte_id = :f AND usuario_id = :u` na transação da exclusão, em qualquer modo (D-006). Com `fonte_id` nulo, a FK deixa de ser verificada (`MATCH SIMPLE`). Se o participante não rodar, a exclusão falha por `restrict`.
- **Renomeação da fonte:** não muda as cópias (D-005 da 002). A interface sempre mostra a cópia.
- **Criação com referência:** o serviço busca a fonte por `public_id`, dono e matéria, com `FOR SHARE`. Isso serializa a criação com a exclusão, que trava a fonte com `FOR UPDATE` (DTEC 031), e uma criação nunca cita uma fonte já apagada. Fonte inexistente, de outra matéria ou de outro estudante responde `422 dados_invalidos` no campo `fonteId`, com a mesma mensagem nos três casos (DTEC 019).
- **Estado da fonte:** qualquer estado é aceito (`pendente`, `processando`, `concluido` ou `falhou`), porque a referência copia só o título, o nome e a data, que existem desde o envio. A spec não restringe o estado.
- **Edição:** a referência é definida só na criação. A spec prevê editar frente, verso e explicação (US2), e trocar a referência exigiria mudar a spec antes.
- **Página:** não há coluna de página. A referência cita a fonte inteira, e a RN-05 só pede a página "quando conhecida".

**Condição para revisão:** uma spec que permita citar um trecho ou uma página específica num cartão manual, o que pediria uma tabela própria de referências.

## Decisão DTEC 036 Texto, limites e validação dos cartões

**Questão:** como normalizar e validar frente, verso e explicação (RF-001, RF-011, casos de borda de espaços e de marcação) com limites "configuráveis por ambiente" (D-004), de forma que a interface mostre os limites vigentes e o mesmo cálculo valha para a 004?  
**Critérios:**

- um único ponto de normalização e validação, reutilizado pela 004;
- contagem de caracteres igual no servidor e na interface;
- quebras de linha preservadas (RF-011);
- nenhuma regra só no navegador;
- limites configuráveis sem mudar o contrato versionado;
- proteção contra payloads extremos mesmo com configuração errada.

**Alternativas consideradas:**

1. **Validação no domínio contra a configuração, teto absoluto no DTO e no banco, e limites vigentes expostos por uma rota.** O domínio normaliza o texto e confere os limites de `nucleo/configuracao.py`. O DTO e o `CHECK` do banco só barram valores acima de tetos fixos. A interface lê os limites em `GET /api/v1/cartoes/limites`, no mesmo padrão do `GET /acervo/uso` da 002.
2. **Limites estáticos no OpenAPI (`maxLength`), gerados para `limites.gerado.ts`, como na 001:** simples, mas um OpenAPI versionado não varia por ambiente, o que contradiz a D-004.
3. **Validação só pelo Pydantic, com limites lidos da configuração na carga do módulo:** o OpenAPI passaria a variar por ambiente, e a mensagem de erro sairia do Pydantic, sem a mensagem em português por campo do domínio.

**Decisão:** alternativa 1.  
**Justificativa:** respeita a D-004 sem fazer o contrato variar por ambiente, mantém a regra num só lugar (`cartoes/dominio.py`) para a 003 e a 004 e conserva uma defesa em profundidade com os tetos.  
**Consequências:**

- **Normalização** (função pura `normalizar_texto_cartao`):
  - NFC;
  - `\r\n` e `\r` viram `\n`;
  - saem os caracteres de controle C0 e C1, exceto `\n` e `\t`;
  - saem os espaços e as quebras de linha nas extremidades.

  As quebras internas e os espaços internos são preservados, porque fazem parte do conteúdo (RF-011). Os caracteres bidirecionais são mantidos, porque podem ser legítimos em fórmulas e citações, e a exibição como texto puro (RQ-001) impede abuso.
- **Contagem:** em *code points* (o `len` do Python), depois da normalização. A interface conta da mesma forma (`[...texto].length` sobre `texto.normalize('NFC')`), e não em unidades UTF-16. Um emoji conta como 1 nos dois lados.
- **Regras:**
  - frente de 1 a `CARTAO_FRENTE_MAX` (padrão 1.000);
  - verso de 1 a `CARTAO_VERSO_MAX` (padrão 2.000);
  - explicação de 0 a `CARTAO_EXPLICACAO_MAX` (padrão 1.000), e vazia depois da normalização vira `NULL`.

  Um texto só com espaços vira vazio e é recusado na frente e no verso (caso de borda).
- **Erro:** `422 dados_invalidos` com a lista `campos`, uma mensagem por campo (ex.: "Use de 1 a 1.000 caracteres."). A interface mostra o erro junto do campo e preserva os valores (US1 cenário 2).
- **Tetos absolutos:** frente 4.000, verso 8.000 e explicação 4.000 caracteres. Eles valem no DTO (`max_length`, que barra o payload antes do domínio) e no `CHECK` do banco. A aplicação não sobe com um limite configurado acima do teto ou abaixo de 1. O corpo continua limitado a 64 KiB pela 001.
- **`GET /api/v1/cartoes/limites`:** devolve `{frenteMax, versoMax, explicacaoMax, buscaMax}`, com `Cache-Control: no-store`. A 004 usa os mesmos limites (D-004).
- **Exibição:** sempre como texto, com `white-space: pre-wrap`. O frontend proíbe `dangerouslySetInnerHTML` com a regra nativa `no-restricted-syntax` do ESLint (seletor `JSXAttribute[name.name='dangerouslySetInnerHTML']`), sem dependência nova, e nenhum cartão é interpretado como Markdown ou HTML no MVP (D-003, RQ-001).

**Condição para revisão:** formatação no texto do cartão (fora do MVP, D-003), que exigiria um formato seguro e um sanitizador.

## Decisão DTEC 037 Estado de agendamento, edição e situação do cartão

**Questão:** como criar um cartão novo com o estado do FSRS correto (RF-003), garantir que a edição nunca altere o agendamento (RF-005, CS-002), mesmo com uma revisão concorrente, e implementar suspender, reativar e excluir (RF-007, RF-008) sem perder estado nem histórico?  
**Critérios:**

- FSRS soberano: o estado inicial vem da biblioteca (RN-26, DTEC 012);
- nenhuma escrita de agendamento fora da revisão (005);
- nenhuma perda de atualização entre a edição (003) e a revisão (005);
- edição que não muda nada sem efeito (US2 cenário 3);
- última gravação vale entre duas abas (caso de borda);
- operações repetidas sem efeito colateral.

**Alternativas consideradas:**

1. **Escritas disjuntas por coluna:** a 003 grava o estado inicial uma única vez, na criação, a partir de `fsrs.Card()`. A edição atualiza só as colunas de conteúdo, e a revisão (005) só as de agendamento. Cada `UPDATE` trava a linha pelo tempo da própria instrução, e como os dois conjuntos de colunas não se cruzam, nenhum sobrescreve o outro.
2. **Controle otimista de versão (`versao` incrementada a cada escrita):** detectaria a edição concorrente em duas abas, mas a spec pede "a última gravação vale". E faria a edição falhar por causa de uma revisão, que não conflita com ela.
3. **Estado inicial escrito à mão pela aplicação (valores fixos):** dispensa chamar a biblioteca, mas pode divergir do `Card` numa versão nova do `fsrs`.

**Decisão:** alternativa 1.  
**Justificativa:** cumpre o CS-002 por construção, sem travas extras, e preserva a semântica de "última gravação vale" exigida pela spec. O estado inicial fica sempre igual ao da biblioteca fixada.  
**Consequências:**

- **Criação:** o mapeador lê `fsrs.Card()`: `estado_fsrs` = `aprendizado` (State.Learning), `passo` = 0, `estabilidade` e `dificuldade` nulas, `ultima_revisao` nula e `vencimento` = instante da criação. Um teste unitário confere esse espelho com a versão fixada. `entrada_estudo_em` recebe o instante da criação, e o cartão entra entre os novos na ordem de criação (RF-003, RN-20). Quem decide a lição é a 005.
- **Edição (`PATCH`):** o serviço lê o cartão do dono (`FOR UPDATE`), normaliza os campos enviados e compara com os atuais. Sem diferença, não grava nada: `atualizado_em` e `origem` não mudam (US2 cenário 3). Com diferença, um único `UPDATE` escreve só `frente`, `verso`, `explicacao`, `origem` e `atualizado_em`. As colunas do FSRS nunca aparecem no `UPDATE`, e um teste de integração confere todas elas antes e depois (CS-002). A regra de origem está na DTEC 038.
- **Campos parciais:** o `PATCH` aceita qualquer subconjunto de `frente`, `verso` e `explicacao`. Um campo ausente não muda; `explicacao: null` ou vazia remove a explicação.
- **Suspender e reativar:** `POST /cartoes/{id}/suspensao` e `POST /cartoes/{id}/reativacao` alteram só `situacao` e `atualizado_em`. São idempotentes: suspender um cartão suspenso responde `200` com o cartão, sem escrita. O agendamento nunca é tocado (RF-007). Na reativação, o cartão fica devido se o vencimento já passou, porque a lição (005) compara o vencimento com o instante atual, sem regra extra aqui (US3 cenário 2).
- **Excluir:** `DELETE /cartoes/{id}` responde `204`. Um segundo pedido responde `404`. A confirmação é um diálogo na interface (US3 cenário 3), porque a exclusão de um cartão não tem impacto variável que precise ser conferido no servidor, ao contrário da DTEC 031. As evidências da 004 vão em cascata pela FK dela.
- **Revisões e XP preservados (RF-008):** dependem das FKs `revisoes.cartao_id` e `eventos_xp.cartao_id` com `on delete set null`, criadas pela 005 e pela 006. A obrigação fica registrada no [plano](plan.md#obrigações-registradas-para-as-próximas-specs). Antes da 005, não existem revisões a preservar.
- **Lição aberta (CB-27):** a consulta da lição (005) só apresenta cartões existentes e ativos. A 003 não guarda estado de lição.

**Condição para revisão:** um requisito de detecção de conflito entre abas, que levaria à alternativa 2 só para o conteúdo.

## Decisão DTEC 038 Fronteira com a spec 004 e participante da exclusão

**Questão:** a tabela `cartoes`, os enums `origem_cartao` e `situacao_cartao` e a regra de edição de cartão gerado (RF-006) são compartilhados com a 004. Como dividir o trabalho para que a 003 seja implementada e testada sozinha, sem invadir a geração e sem contagens duplicadas na exclusão (DTEC 027)?  
**Critérios:**

- cada spec cria só o que usa (orientação do esquema);
- a RF-006 testável na 003;
- uma única regra de origem para a edição na lista (003) e para o "editar e aceitar" (004);
- contagens da exclusão sem dupla contagem;
- a 004 sem retrabalho na 003.

**Alternativas consideradas:**

1. **A 003 é dona da tabela, das regras de conteúdo e da contagem por situação; a 004 acrescenta a geração.** A 003 cria `origem_cartao` completo e `situacao_cartao` só com `ativo` e `suspenso`. Ela cria todas as colunas de `cartoes`, exceto `geracao_id` (004), `chave_imagem` (011) e `dominado_em` (005). E implementa a regra de origem e o participante que conta e apaga cartões por matéria, de qualquer origem.
2. **A 003 cria tudo agora (enums completos e todas as colunas):** menos migrações, mas colunas e valores sem uso nem teste, contra a orientação do esquema.
3. **Mover a RF-006 para a 004:** contraria a spec aprovada, que a coloca na 003.

**Decisão:** alternativa 1.  
**Justificativa:** a 003 entrega uma tabela completa para o seu escopo e testada de ponta a ponta. A 004 só acrescenta valores de enum, uma coluna, a tabela de evidências e o seu participante.  
**Consequências:**

- **Regra de origem** (função pura `origem_apos_edicao`): `gerado_verificado` com mudança efetiva de frente, verso ou explicação vira `editado`. `editado` e `criado` não mudam. Sem mudança efetiva, nada muda (RF-006, US2 cenários 2 e 3). A 004 reutiliza a mesma função no "editar e aceitar".
- **Teste da RF-006 na 003:** com um cartão `gerado_verificado` inserido por fábrica, a edição muda a origem para `editado`, e as colunas do FSRS não mudam. A manutenção do vínculo com os trechos (a evidência continua acessível) é verificada pela 004, dona de `evidencias_cartoes`, reexecutando o mesmo cenário com geração real. A 003 nunca toca essa tabela.
- **Situação visível:** as rotas da 003 operam só sobre cartões `ativo` ou `suspenso`. Um cartão aguardando revisão ou recusado (004) responde `404` em `GET`, `PATCH`, `DELETE`, suspensão e reativação, e não aparece na lista (caso de borda da spec). Essa condição fica no repositório (`situacoes_visiveis`), e a 004 não precisa alterá-la.
- **Enum:** a 004 acrescenta `aguardando_revisao` e `recusado` com `ALTER TYPE situacao_cartao ADD VALUE`, numa migração própria.
- **Participante dos cartões** (`cartoes/registros.py`, prioridade dos cartões, antes do participante de `fontes`):
  - `contar_por_materia`: `cartoes_ativos` (situação `ativo`) e `cartoes_suspensos` (situação `suspenso`), de **qualquer origem**, por matéria do dono (emenda da DTEC 027).
  - `impacto_fonte`: `cartoes_referencia`, ou seja, os cartões com `fonte_id` igual à fonte (só manuais, pelo `CHECK` da DTEC 035).
  - `ao_excluir_fonte(modo)`: anula `fonte_id` dos cartões que citam a fonte, em qualquer modo (D-006). Os cartões gerados da fonte são tratados pelo participante da 004.
  - `ao_excluir_materia`: apaga todos os cartões da matéria. As evidências (004) vão em cascata, e as revisões e o XP ficam com `cartao_id` nulo (005 e 006).
- **Participante da 004 (obrigação):** conta só `cartoes_aguardando_revisao` e `cartoes_gerados_aceitos` por fonte (pelas evidências), aplica o modo aos aceitos e apaga os aguardando revisão. Não conta de novo ativos nem suspensos por matéria. A ordem entre os dois participantes de cartões é indiferente, porque tocam linhas disjuntas: a referência só existe em cartões `criado`, e a evidência só em cartões gerados.
- **Exclusão da conta (DTEC 021):** `apagar_dados_usuario` dos cartões apaga todos os cartões do usuário e é registrado antes do de `fontes` e do de `materias`, por causa das FKs `restrict`.

**Condição para revisão:** um terceiro escritor de cartões (ex.: importação de baralhos, fora do escopo), que pediria um módulo de regras de cartão separado do domínio `cartoes`.

## Fontes consultadas

- Código e documentação da biblioteca `fsrs` (classe `Card`: valores padrão de `state`, `step`, `stability`, `difficulty`, `due` e `last_review`), consultados em 13/10/2026 para a DTEC 037. A versão fixada é conferida pelo teste de espelho na implementação.
- Documentação do PostgreSQL 17: FKs compostas com `MATCH SIMPLE` e colunas anuláveis, `ALTER TYPE ... ADD VALUE`, `SELECT ... FOR SHARE` e `CHECK`, consultada em 13/10/2026 para as DTEC 035 e 038.
- Documentação do ESLint (regra `no-restricted-syntax` com seletores de AST), consultada em 13/10/2026 para a DTEC 036.
- [Plano](../002-materias-fontes/plan.md) e [research](../002-materias-fontes/research.md) da spec 002 (DTEC 027 e 031), e spec 004 (fronteira da geração).
