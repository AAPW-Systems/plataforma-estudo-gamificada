# Pesquisa e decisões técnicas

**Funcionalidade:** 004-geracao-cartoes (geração de cartões pela IA e revisão dos gerados)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-004-geracao-cartoes-plano.md))  
**Status:** DTEC 041 a 047 propostas com o plano, aguardando o portão "Plano aprovado"

Este arquivo registra só as dúvidas técnicas **novas** da spec 004. As decisões já tomadas não são reabertas:

- de [`../../research.md`](../../research.md): fila (DTEC 006), LLM e framework (DTEC 007), observabilidade e avaliação (DTEC 011), acompanhamento por *polling* (DTEC 026), participantes da exclusão (DTEC 027, com a emenda de 13/10/2026) e paginação (DTEC 034);
- da [spec 001](../001-conta-acesso/research.md): isolamento (DTEC 019) e exclusão da conta (DTEC 021);
- da [spec 002](../002-materias-fontes/research.md): divisão em trechos (DTEC 029), estados e jobs travados (DTEC 030), exclusão sob concorrência (DTEC 031) e *advisory lock* por estudante (DTEC 032);
- da [spec 003](../003-cartoes-manuais/research.md): texto e limites (DTEC 036), estado do FSRS (DTEC 037) e fronteira com a 004 (DTEC 038).

Valem também as DTEC transversais propostas neste planejamento: aviso e ciência do provedor (DTEC 039) e consumo e orçamento da IA (DTEC 040). A numeração das DTEC é única no projeto.

| Decisão | Título |
|---|---|
| [DTEC 041](#decisão-dtec-041-janela-de-trechos-cobertura-e-não-repetição) | Janela de trechos, cobertura e não repetição |
| [DTEC 042](#decisão-dtec-042-validação-estrutural-e-de-sustentação) | Validação estrutural e de sustentação |
| [DTEC 043](#decisão-dtec-043-execução-estados-e-falhas-da-geração) | Execução, estados e falhas da geração |
| [DTEC 044](#decisão-dtec-044-pedido-de-geração-sob-reenvio-e-concorrência) | Pedido de geração sob reenvio e concorrência |
| [DTEC 045](#decisão-dtec-045-revisão-dos-cartões-gerados) | Revisão dos cartões gerados |
| [DTEC 046](#decisão-dtec-046-participante-da-exclusão-descartes-e-retenção) | Participante da exclusão, descartes e retenção |
| [DTEC 047](#decisão-dtec-047-instruções-embutidas-contradições-e-avaliação) | Instruções embutidas, contradições e avaliação |

## Decisão DTEC 041 Janela de trechos, cobertura e não repetição

**Questão:** uma fonte de 2 MB tem cerca de 1.700 trechos (DTEC 029), uns 500 mil *tokens*, o que não cabe numa chamada da camada gratuita nem na meta de 2 minutos (CS-006). Como escolher o que cada geração envia ao modelo e, com isso, garantir que "Gerar mais" não repita cartões existentes, aguardando revisão ou recusados da matéria (RF-013, D-008, CS-007) e que uma fonte esgotada responda "não há novos cartões" (CB-26)?  
**Critérios:**

- verificação determinística, testável sem o modelo real;
- custo por geração limitado e independente do tamanho da fonte;
- CB-26 sem gastar chamada ao provedor;
- repetição detectada também entre fontes da mesma matéria;
- nenhuma tecnologia nova no MVP.

**Alternativas consideradas:**

1. **Passada única pela fonte, com cobertura registrada e filtro de repetição.** Cada geração envia uma janela contígua de trechos ainda não cobertos e registra os trechos enviados. Depois das validações, um filtro lexical compara cada cartão com todos os cartões da matéria.
2. **Enviar a lista de cartões existentes no prompt e confiar no modelo.** Não é verificável e não escala para milhares de cartões.
3. **Similaridade semântica com embeddings.** O bge-m3 só entra no final acadêmico (DTEC 008), então seria tecnologia nova no MVP.

**Decisão:** alternativa 1.  
**Justificativa:** a cobertura por trecho é a forma mais forte de não repetir, porque cada geração lê um conteúdo que nenhuma outra leu. O filtro lexical cobre a sobreposição entre trechos vizinhos e a repetição entre fontes. O CB-26 vira uma consulta, sem custo de IA.  
**Consequências:**

- **Registro (`geracoes_trechos`):** a geração grava os trechos que enviou ao modelo (RF-017). Um trecho está **coberto** quando aparece numa geração `concluida`. Uma geração que termina em `falhou` não cobre nada, e os trechos dela voltam a ficar disponíveis.
- **Janela:** são os trechos não cobertos da fonte, em `ordem`, a partir do primeiro, até `GERACAO_JANELA_MAX_CARACTERES` (padrão 30.000, uns 8 mil *tokens*). Um trecho nunca é cortado, e a janela tem pelo menos um trecho. Como cada fonte tem no máximo uma geração em andamento (DTEC 044), duas gerações nunca disputam a mesma janela.
- **Fonte esgotada (CB-26):** sem trecho não coberto, o pedido responde `409 sem_conteudo_novo` na hora, sem criar geração nem contar no limite.
- **Rótulos locais:** os trechos vão ao modelo como `T1` a `Tn`, e o servidor guarda a correspondência. O modelo nunca vê nem devolve identificadores do banco.
- **Contexto contra repetição:** o prompt recebe também as frentes dos cartões já ligados aos trechos vizinhos da janela (um antes e um depois), por causa da sobreposição de 150 caracteres da DTEC 029. São no máximo 30 frentes, e o filtro abaixo é que garante o resultado.
- **Filtro de repetição** (função pura `assinatura_conteudo` em `cartoes/geracao/dominio.py`):
  - a assinatura é o conjunto de radicais de conteúdo de frente e verso: NFC, minúsculas, sem acentos, divisão em palavras, sem as palavras vazias do português (lista própria, versionada no código), palavras com 3 caracteres ou mais, cortadas nos 5 primeiros caracteres, e números preservados;
  - um cartão candidato é `repetido` se a frente normalizada for igual à de outro cartão, ou se a similaridade de Jaccard entre as assinaturas for de `GERACAO_LIMIAR_REPETICAO` (padrão 0,7) ou mais;
  - a comparação é feita contra todos os cartões da matéria, em qualquer situação e de qualquer origem, e contra os candidatos já aceitos no mesmo lote;
  - roda na transação de publicação, sob o *advisory lock* do estudante (DTEC 043), para enxergar as publicações concorrentes de outras fontes da mesma matéria. São alguns milhares de conjuntos pequenos, em memória, em poucos milissegundos.
- **Descarte:** o repetido é registrado em `cartoes_descartados` com o motivo `repetido` (DTEC 046).
- **Limitação conhecida (registrada no plano):** cobrir uma fonte grande inteira pede muitos "Gerar mais". Uma fonte de 2 MB tem perto de 60 janelas, contra o limite de 20 gerações por dia (D-005). A demonstração do MVP usa PDFs pequenos, e a limitação é explicada ao PO. A repetição semântica sem palavras em comum (paráfrase) só é detectável com embeddings, no final acadêmico.

**Condição para revisão:** embeddings disponíveis (spec 010 ou 014), que permitiriam a similaridade semântica, ou o conjunto de avaliação mostrar repetição acima do CS-007.

## Decisão DTEC 042 Validação estrutural e de sustentação

**Questão:** como verificar, antes de publicar, que cada cartão tem estrutura válida (RF-006) e é sustentado pelo trecho que cita (RF-006, RF-008, CS-001 a CS-004), sabendo que uma segunda chamada de IA não prova sustentação (Princípio V, RN-22)?  
**Critérios:**

- nenhum cartão visível sem passar por um portão determinístico;
- cada reprovação com um motivo registrado (RF-007);
- independência do provedor (RQ-001);
- limiares configuráveis e calibrados pelo conjunto de avaliação;
- custo de chamadas compatível com a camada gratuita.

**Alternativas consideradas:**

1. **Só portões determinísticos:** estrutura, citação literal e cobertura lexical.
2. **Só uma chamada de IA juíza:** não prova sustentação, e o resultado dependeria do modelo.
3. **Portões determinísticos seguidos de uma juíza que só reprova:** a juíza roda uma vez, em lote, sobre os sobreviventes, e pode descartar, nunca aprovar sozinha.

**Decisão:** alternativa 3, com a juíza ligada por configuração (`GERACAO_VERIFICADOR_IA`, padrão `true`).  
**Justificativa:** os portões determinísticos garantem por construção o que pode ser garantido, ou seja, um trecho existente da mesma fonte e uma citação literal. Eles também barram afirmações sem apoio lexical. A juíza acrescenta a leitura de sentido (ex.: uma negação, ou um cartão que toma partido numa contradição) sem nunca ser a única barreira. O relatório de avaliação mostra a precisão com e sem a juíza, e a decisão de mantê-la passa a ter evidência.  
**Consequências:**

- **Saída do gerador** (modelo Pydantic `CartaoProposto`):
  - `frente`, `verso` e `explicacao`;
  - `trechos`: de 1 a 3 rótulos `Tn`;
  - `citacao`: de 20 a 300 caracteres, copiada literalmente de um dos trechos citados.

  A resposta (`SaidaGeracao`) traz até 15 cartões e a lista `pontos_contraditorios` (DTEC 047). O tipo da saída limita os tamanhos, e uma saída fora do esquema conta como resposta malformada (DTEC 043).
- **Portões, em ordem** (funções puras em `cartoes/geracao/validacao.py`, cada uma com o seu motivo):
  1. **Estrutura (`estrutura_invalida`):** frente, verso e explicação passam por `normalizar_texto_cartao` e `validar_limites` da 003 (DTEC 036, D-004). A explicação é obrigatória e não pode ser vazia.
  2. **Vínculo (`sem_evidencia`):** todo rótulo citado existe na janela enviada, o que implica a mesma fonte, matéria e estudante.
  3. **Citação literal (`citacao_nao_encontrada`):** a citação, normalizada (NFC, minúsculas, espaços e quebras colapsados, aspas e hífens tipográficos unificados), é substring de um dos trechos citados normalizados. Os deslocamentos da citação no trecho original são guardados para o destaque na tela, sem copiar o texto (RN-05).
  4. **Cobertura lexical (`cobertura_insuficiente`):** a fração dos radicais de conteúdo do verso que aparecem nos trechos citados é de `GERACAO_LIMIAR_COBERTURA` (padrão 0,6) ou mais, e o mesmo vale para a explicação. A frente não entra, porque a pergunta pode ser formulada com outras palavras.
  5. **Juíza (`reprovado_verificador`):** uma chamada para todos os sobreviventes, com os trechos citados de cada um. Ela devolve, por cartão, `sustentado` e um motivo curto entre `nao_sustentado`, `contradicao`, `fora_do_trecho` e `explicacao_nao_sustentada`. Só quem tem `sustentado = true` segue adiante. Um índice de cartão ausente na resposta conta como reprovação. Uma falha da juíza (timeout ou resposta malformada, depois das novas tentativas) faz a geração falhar, sem publicar nada sem verificação (RF-016).
  6. **Repetição (`repetido`):** DTEC 041, já na transação de publicação.
  7. **Excedente (`excedente`):** a partir do 11º aprovado, na ordem da resposta (caso de borda).
- **Explicação "com a citação" (RF-008):** a explicação passa pelos mesmos portões do verso e, na tela, aparece sempre junto do acesso à evidência, com a citação destacada no trecho.
- **Contagens:** `geracoes.quantidade_gerada` são os cartões devolvidos pelo modelo, e `quantidade_aprovada` são os publicados. Os demais ficam em `cartoes_descartados`, com o motivo.
- **Calibração:** os dois limiares, a lista de palavras vazias e o uso da juíza são parâmetros experimentais. O conjunto de avaliação (DTEC 047) é que justifica uma mudança, e cada mudança gera uma nova versão das instruções.

**Condição para revisão:** o conjunto de avaliação mostrar menos de 90% de cartões sustentados (D-006) ou um descarte excessivo de cartões corretos (taxa de aprovação baixa com o revisor concordando com os descartados).

## Decisão DTEC 043 Execução, estados e falhas da geração

**Questão:** como executar a geração em segundo plano (RF-003) com estados visíveis, sem publicar cartões parciais (RF-016), sem duplicar efeitos, terminando sem efeito se a fonte sumiu (CB-16, DTEC 021 e 031) e distinguindo a falha técnica da geração sem cartões sustentados (US4-6)?  
**Critérios:** os da DTEC 030 (estado no domínio, tarefa idempotente, sem estado travado), mais nenhuma trava de banco aberta durante a chamada ao provedor e a meta do CS-006.  
**Alternativas consideradas:**

1. **Tarefa `gerar_cartoes` em duas transações, com as chamadas ao provedor entre elas, travas por geração e falha com código persistido.** É o padrão da DTEC 030, aplicado à geração.
2. **Uma só transação em volta de tudo:** manteria travas abertas durante 30 a 90 s de rede e bloquearia a exclusão da fonte (DTEC 031) por todo esse tempo.
3. **Publicar cada cartão assim que for validado:** deixaria cartões parciais visíveis numa falha, contra a RF-016.

**Decisão:** alternativa 1.

```text
pendente ──worker inicia──> processando ──cartões publicados (0 a 10)──> concluida
                                 │
                                 └── provedor indisponível, cota do provedor, resposta malformada,
                                     orçamento esgotado ou fonte excluída ──> falhou (código)
```

**Justificativa:** o estado fica em `geracoes` (Princípio IV). A publicação é atômica, e nenhuma trava fica aberta durante a rede. O código de falha permite uma mensagem certa ao estudante sem expor detalhes do provedor (RQ-005).  
**Consequências:**

- **Enfileiramento:** `gerar_cartoes(geracao_id)` entra na fila na transação que cria a geração (emenda da DTEC 002), com `queueing_lock=f"geracao:{id}"` e `lock=f"geracao:{id}"`.
- **Transação A:**
  1. `SELECT ... FOR UPDATE` da geração. Se ela não existe, ou não está em `pendente` nem em `processando`, a tarefa termina sem efeito.
  2. Se a fonte não existe mais (`fonte_id` nulo), grava `falhou` com `fonte_excluida`.
  3. Senão, grava `processando` e `iniciada_em`, apaga os `geracoes_trechos` de uma execução anterior interrompida, escolhe a janela (DTEC 041) e grava os trechos dela.
- **Chamadas, fora de transação:**
  - lê os textos dos trechos da janela;
  - chama o gerador e, se houver sobreviventes e a juíza estiver ligada, a juíza, ambas por `ia/cliente.py` (DTEC 040);
  - roda os portões 1 a 5 da DTEC 042.
- **Transação B:**
  1. `SELECT ... FOR UPDATE` da geração e `SELECT ... FOR SHARE` da fonte (DTEC 031).
  2. Se a fonte sumiu, ou se a geração já não está em `processando`, termina sem efeito. Nesse caso, o participante da exclusão já gravou `falhou`.
  3. *Advisory lock* do estudante no espaço `publicacao_cartoes` (DTEC 041).
  4. Filtro de repetição e corte do excedente.
  5. Inserção dos cartões em `aguardando_revisao` (origem `gerado_verificado`, estado inicial de `fsrs.Card()`, `geracao_id`), das evidências e dos descartados.
  6. Gravação de `concluida`, `quantidade_gerada`, `quantidade_aprovada` e `concluida_em`.
- **Novas tentativas:** `RetryStrategy(max_attempts=2, exponential_wait=5, retry_exceptions={ErroTransitorio, ErroTransitorioIA})`, ou seja, até 2 novas tentativas (DTEC 040), igual à DTEC 030. Durante elas, a geração fica em `processando`. Na última, a tarefa grava `falhou` com o código em vez de relançar, como na DTEC 030. A transação A aceita `processando`, então a repetição é segura.
- **Resposta malformada:** o PydanticAI pede a correção da saída uma vez (`output_retries=1`). Se ainda não validar contra o esquema, a geração termina em `falhou` com `resposta_invalida`, sem nova tentativa da fila.
- **Códigos de falha** (`codigo_falha_geracao`), com mensagens de um catálogo da aplicação devolvidas como `mensagemFalha` (RQ-005):
  - `provedor_indisponivel`: "Não conseguimos gerar cartões agora por um problema no serviço de IA. Tente novamente em alguns minutos.";
  - `limite_provedor`: "O serviço de IA atingiu o limite de uso por hoje. Tente novamente mais tarde.";
  - `resposta_invalida`: "Não conseguimos gerar cartões válidos desta vez. Tente novamente.";
  - `orcamento_esgotado`: "Você atingiu o uso diário de IA. O limite volta às 4h.";
  - `fonte_excluida`: sem mensagem, porque a geração some da tela junto com a fonte.

  Nenhuma das falhas conta no limite diário (D-010).
- **Sem cartões sustentados (US4-6):** a geração termina em `concluida` com `quantidade_aprovada = 0`. A interface mostra "Não foi possível gerar cartões sustentados por esta fonte", diferente de uma falha técnica, e a janela fica coberta.
- **"Tentar de novo":** é um novo pedido, com uma nova chave (DTEC 044). A geração que falhou continua no histórico.
- **Jobs travados:** a tarefa `reenfileirar_tarefas_travadas` (DTEC 030) também cobre `gerar_cartoes`.
- **Desempenho (CS-006):** 2 chamadas de até 60 s cada, com cerca de 8 mil *tokens* de entrada. A meta é de 30 a 60 s com o provedor disponível. A medição está no quickstart.
- **Logs:** `geracao_pedida`, `geracao_iniciada`, `geracao_concluida` (quantidades, motivos dos descartes e duração), `geracao_falhou` (código e tentativa) e `chamada_ia` (operação, modelo, *tokens* e latência). Todos levam o `public_id` da geração e do usuário, e nenhum leva texto de trechos, cartões ou instruções (RQ-003).

**Condição para revisão:** uma geração da matéria inteira (spec 010), que pode pedir várias janelas por geração e publicação em lotes.

## Decisão DTEC 044 Pedido de geração sob reenvio e concorrência

**Questão:** como tratar o pedido de geração (RF-001, RF-004) de modo que o reenvio devolva a mesma geração (RN-10), que um novo pedido para uma fonte com geração em andamento devolva a existente (caso de borda) e que o limite de 20 gerações por dia de estudo (D-005, RF-019, sem as falhas, D-010) e o orçamento (RQ-002) valham mesmo com pedidos simultâneos?  
**Critérios:** proteção persistente, nunca só em memória (RN-10); nenhuma 21ª geração sob concorrência; nenhuma trava compartilhada entre estudantes; mensagem com o horário em que o limite volta.  
**Alternativas consideradas:**

1. **Chave de idempotência única, índice único parcial por fonte em andamento e *advisory lock* do estudante para o limite**, no padrão da DTEC 032.
2. **Contar sem trava:** dois pedidos simultâneos com 19 gerações no dia passariam os dois.
3. **Contador diário desnormalizado em `usuarios`:** disputaria a linha com a sessão e o perfil (001), e mais uma regra para manter coerente.

**Decisão:** alternativa 1.  
**Justificativa:** cada garantia fica com o mecanismo mais simples que a cumpre por construção: unicidade para o reenvio e a fonte, e serialização por estudante para a contagem.  
**Consequências:**

- **`POST /fontes/{fonteId}/geracoes`**, com corpo `{chaveIdempotencia}` (UUID gerado no cliente a cada intenção de gerar). Tudo acontece numa transação:
  1. Fonte do dono, com `FOR SHARE` (`404`). Isso serializa o pedido com a exclusão da fonte (DTEC 031).
  2. Geração existente com `(usuario_id, chave_idempotencia)`: da mesma fonte, `200` com ela; de outra fonte, `409 idempotencia_divergente` (RN-10).
  3. Ciência da versão vigente do aviso (DTEC 039); sem ela, `409 ciencia_aviso_pendente`.
  4. Fonte em `concluido`; senão, `409 fonte_nao_concluida`.
  5. *Advisory lock* do estudante no espaço `geracoes`.
  6. Geração da fonte em `pendente` ou `processando`: `200` com ela.
  7. Gerações do estudante no dia de estudo com `estado <> 'falhou'`. Se forem `GERACAO_LIMITE_DIA` (20) ou mais: `429 limite_geracoes_excedido`, com `Retry-After` até a próxima virada das 4h no fuso do estudante e a mensagem "Você atingiu o limite de 20 gerações hoje. Ele volta às 4h."
  8. Orçamento de *tokens* do dia (DTEC 040); esgotado: `429 orcamento_ia_esgotado`.
  9. Trechos não cobertos (DTEC 041); nenhum: `409 sem_conteudo_novo`.
  10. Inserção em `pendente` e enfileiramento: `202` com a geração e `Location`.
- **Defesas no banco:**
  - índice único `(usuario_id, chave_idempotencia)`;
  - índice único parcial `geracoes_fonte_em_andamento` em `(fonte_id) WHERE estado IN ('pendente', 'processando')`.

  Se uma corrida que o *advisory lock* não cobre violar um índice, o repositório converte o erro e o serviço devolve a geração existente.
- **Reenvio e "uma por fonte" não contam no limite**, porque não criam geração.
- **`GET /geracoes/uso`:** `{limiteDia, usadasHoje, voltaEm, orcamentoDisponivel}`, com `no-store`. A interface desabilita "Pedir cartões" e "Gerar mais" com a explicação antes do clique, mas o servidor continua decidindo.
- **Fonte em outro estado:** a ação nem aparece na interface para `pendente`, `processando` e `falhou` (caso de borda), e o servidor responde `409 fonte_nao_concluida` mesmo assim.

**Condição para revisão:** limite por plano ou por papel (painel administrativo, [016](../016-painel-administrativo/spec.md)).

## Decisão DTEC 045 Revisão dos cartões gerados

**Questão:** como implementar aceitar, editar e aceitar, recusar e aceitar todos (RF-010), com a ordem de entrada no estudo (RF-011, RN-20), o motivo opcional da recusa (RF-020), o resumo (RF-012) e o selo de verificado coerente depois da exclusão da fonte (DTEC 027), reutilizando as regras da 003 (DTEC 038)?  
**Critérios:**

- uma única regra de origem e de texto;
- idempotência pelo estado, sem chave extra;
- ordem dos novos igual à ordem da tela;
- taxa de aceitação calculável por geração, fonte e no total (CS-005);
- nenhuma regra só no navegador.

**Alternativas consideradas:**

1. **Transições de situação no próprio cartão, com o motivo numa coluna**, e as rotas de ação sob `/cartoes/{id}` e `/geracoes/{id}`. A revisão é por geração.
2. **Tabela `decisoes_revisao` com uma linha por decisão:** dá histórico, mas a spec não pede histórico de decisões, e seria mais uma junção para cada contagem.
3. **Revisão por matéria, com tudo o que aguarda numa lista:** o resumo deixaria de corresponder a "uma geração terminou" (RF-012).

**Decisão:** alternativa 1.  
**Justificativa:** a situação já é o estado da decisão. A idempotência sai dela sem chave adicional, e as contagens do resumo e da taxa de aceitação são consultas sobre `cartoes`.  
**Consequências:**

- **Transições** (todas com o cartão do dono `FOR UPDATE`):

  ```text
  aguardando_revisao ──aceitar──────────> ativo     (gerado_verificado)
  aguardando_revisao ──editar e aceitar─> ativo     (editado, ou gerado_verificado sem mudança efetiva)
  aguardando_revisao ──recusar──────────> recusado  (motivo opcional)
  ```

- **Aceitar:** `POST /cartoes/{id}/aceitacao`, com corpo opcional `{frente?, verso?, explicacao?}`.
  - Com corpo, é "editar e aceitar": `normalizar_texto_cartao`, `validar_limites` (`422` por campo), `houve_mudanca` e `origem_apos_edicao` da 003.
  - A situação vai para `ativo`, e `entrada_estudo_em` e `vencimento` recebem o instante da aceitação. O cartão nunca foi revisado, então isso só define o início do estudo, sem tocar no agendamento (RN-26, DTEC 037).
  - As evidências ficam intactas.
- **Recusar:** `POST /cartoes/{id}/recusa`, com corpo opcional `{motivo?}` (`incorreto`, `irrelevante`, `repetido` ou `mal_escrito`). A situação vai para `recusado`, e o motivo para `motivo_recusa`. Um novo pedido com o motivo sobre um cartão já recusado só grava ou troca o motivo: é o "um clique" depois de recusar (D-007).
- **Aceitar todos:** `POST /geracoes/{id}/aceitacao`. Na mesma transação, aceita todos os cartões da geração ainda em `aguardando_revisao`, na ordem de exibição (`id`). Cada um recebe o instante da transação mais `i` microssegundos em `entrada_estudo_em`, para que a ordem dos novos (RN-20) fique igual à da tela. Repetido, só acha cartões já decididos e responde `200` com o resumo, sem efeito. Os recusados não mudam.
- **Idempotência pelo estado:**
  - aceitar um aceito responde `200` sem efeito, mesmo com corpo;
  - aceitar um recusado, ou recusar um aceito, responde `409 cartao_ja_decidido`;
  - recusar um recusado responde `200` (e grava o motivo, se vier).
- **Ordem da revisão:** `GET /geracoes/{id}/cartoes` devolve os aguardando revisão da geração (no máximo 10, sem paginação), em ordem de `id`, cada um com a evidência inteira: título da fonte, texto do trecho, página quando conhecida e deslocamentos da citação.
- **Resumo (RF-012):** `GET /geracoes/{id}` devolve `geradosPublicados` (`quantidade_aprovada`), `aceitos` (cartões da geração em `ativo` ou `suspenso`), `recusados` e `aguardandoRevisao`. A revisão termina quando `aguardandoRevisao = 0`. Um aceito depois excluído pelo estudante deixa de contar, o que a spec não proíbe.
- **Selo de verificado e "Fonte apagada" nos gerados:** são derivados, nunca gravados.
  - `fonteApagada` = cartão com `geracao_id` cuja geração tem `fonte_id` nulo;
  - `verificado` = `origem = 'gerado_verificado' AND NOT fonteApagada`.

  Isso emenda a derivação da 003 (`verificado` só pela origem), que passa a fazer um *left join* com `geracoes` na listagem e na consulta, sem custo relevante. A obrigação fica registrada na propagação do plano.
- **Rotas da 003:** continuam operando só sobre `ativo` e `suspenso` (DTEC 038). Um cartão aguardando revisão ou recusado responde `404` nelas, sem mudança na 003.
- **Explicação obrigatória:** `CHECK (origem <> 'gerado_verificado' OR explicacao IS NOT NULL)`. Um cartão gerado em que o estudante apaga a explicação vira `editado`, pela regra da 003.
- **Taxa de aceitação (CS-005):** aceitos (inclusive editados) sobre aceitos mais recusados, por geração, por fonte (pela geração) e no total, numa consulta de análise (`cartoes/geracao/analise.py`) usada pelo relatório de avaliação, com a distribuição dos motivos de recusa por modelo e versão das instruções.

**Condição para revisão:** um requisito de desfazer a decisão, ou de histórico de decisões, que levaria à alternativa 2.

## Decisão DTEC 046 Participante da exclusão, descartes e retenção

**Questão:** como cumprir a obrigação da DTEC 027 e da DTEC 038 para os cartões gerados e as gerações (contagem por fonte, modo da exclusão, aguardando revisão apagados, gerações interrompidas, CB-16), e onde guardar os cartões descartados (RF-007) e os recusados sem guardar conteúdo derivado de uma fonte que o estudante apagou (Princípio II)?  
**Critérios:**

- contagens exibidas iguais às apagadas (CS-004 da 002);
- nenhuma contagem dupla com o participante da 003;
- conteúdo derivado da fonte apagado com ela, em qualquer modo, exceto os aceitos no modo "Manter";
- análise da qualidade possível com saídas reais;
- nenhum conteúdo em logs (RQ-003).

**Alternativas consideradas:**

1. **Participante da 004 pela geração, com os descartados em tabela própria e os recusados e descartados apagados junto com a fonte.**
2. **Descartados só com motivo e contagem, sem texto:** mais privacidade, mas a análise ficaria restrita ao conjunto de avaliação.
3. **Manter os recusados no modo "Manter":** preserva a taxa de aceitação da fonte, mas guarda conteúdo invisível derivado de uma fonte apagada.

**Decisão:** alternativa 1.  
**Justificativa:** a geração é por fonte, então `geracoes.fonte_id` identifica, sem ambiguidade, os cartões gerados de uma fonte, sem precisar percorrer evidências. Os descartados com texto permitem ajustar as instruções com casos reais, e são apagados em todos os caminhos de exclusão.  
**Consequências:**

- **FK composta da geração para a fonte:** `(fonte_id, materia_id, usuario_id)` → `fontes(id, materia_id, usuario_id)` `ON DELETE SET NULL (fonte_id)`, recurso do PostgreSQL 15 em diante. Ela garante a mesma matéria e o mesmo dono, e anula só `fonte_id` quando a fonte é apagada.
- **Participante `geracoes_cartoes`** (`cartoes/geracao/registros.py`), na mesma transação da exclusão e antes do participante de `fontes`:
  - **`contar_por_materia`:** `cartoes_aguardando_revisao` por matéria. Ativos e suspensos já são contados pela 003 (emenda da DTEC 027).
  - **`impacto_fonte`:** `cartoes_aguardando_revisao` (situação `aguardando_revisao`) e `cartoes_gerados_aceitos` (situação `ativo` ou `suspenso`, origem `gerado_verificado` ou `editado`) das gerações da fonte.
  - **`ao_excluir_fonte(modo)`:**
    1. grava `falhou` com `fonte_excluida` nas gerações da fonte em `pendente` ou `processando` (CB-16). O worker que estiver no meio encontra a geração fora de `processando`, ou a fonte apagada, e termina sem efeito;
    2. apaga os cartões `aguardando_revisao` e `recusado` dessas gerações, e os descartados delas;
    3. modo `excluir`: apaga os aceitos (`ativo` e `suspenso`) dessas gerações;
    4. modo `manter`: os aceitos ficam. As evidências perdem o `trecho_id` pelo `ON DELETE SET NULL` quando os trechos saem com a fonte, e as cópias da origem continuam lá. O cartão passa a exibir "Fonte apagada", sem selo (DTEC 045).
  - **`ao_excluir_materia`:** sem ação própria. O participante da 003 apaga todos os cartões da matéria, e as gerações, os descartados e os trechos das gerações saem em cascata com a matéria.
- **Ordem entre os participantes de cartões:** indiferente, porque tocam linhas disjuntas (DTEC 038). A referência só existe em cartões `criado`, e a geração só em cartões gerados.
- **`cartoes_descartados`:**
  - colunas: geração, usuário, motivo, detalhe curto (ex.: o motivo da juíza), frente, verso e explicação tal como vieram do modelo (anuláveis) e criação;
  - FK para a geração com `ON DELETE CASCADE`;
  - nunca aparece ao estudante, e nenhuma rota a expõe;
  - é lida só pela consulta de análise e pelo relatório de avaliação;
  - **sai junto** com a fonte (participante), a matéria (cascata) e a conta (`apagar_dados_usuario`).
- **Gerações depois da exclusão da fonte:** continuam existindo, com `fonte_id` nulo e sem conteúdo, para as contagens de consumo e o histórico. Elas não aparecem mais na tela.
- **Exclusão da conta (DTEC 021):** o domínio `cartoes` registra o `apagar_dados_usuario` das gerações (com os descartados e os trechos das gerações em cascata), depois do dos cartões e antes do de `fontes` e do de `materias`. O domínio `ia` registra o do consumo e o das ciências (DTEC 039 e 040). O teste de catálogo da 001 confere que todas as tabelas novas ficam vazias para a conta.

**Condição para revisão:** um requisito de retenção limitada da análise (ex.: apagar descartados com mais de N dias), que pediria uma tarefa periódica de limpeza.

## Decisão DTEC 047 Instruções embutidas, contradições e avaliação

**Questão:** como tratar o conteúdo das fontes só como dado (RF-015, CB-15), não gerar cartões que tomem partido numa contradição (CB-09, CS-003), simular o provedor nos testes sem rede (RQ-001) e montar o conjunto de avaliação revisado por pessoa (D-003, D-006, D-011, RQ-006, RQ-007)?  
**Critérios:** defesa em camadas, sem confiar só no prompt; testes determinísticos na suíte que bloqueia o merge; avaliação com o modelo real, fora dessa suíte (DTEC 011); nenhuma dependência nova; nenhum dado pessoal real (regra 10).  
**Alternativas consideradas:**

1. **Delimitação com *nonce*, saída tipada, portões determinísticos e juíza**, mais o provedor simulado do próprio PydanticAI nos testes e o pydantic-evals num grupo separado.
2. **Filtro de padrões de injeção nos trechos (lista de frases proibidas):** fácil de contornar, e removeria conteúdo legítimo (ex.: um texto sobre segurança que cita instruções).
3. **Biblioteca externa de detecção de injeção:** dependência nova, e não substitui os portões, que já barram o efeito da injeção.

**Decisão:** alternativa 1.  
**Justificativa:** o que importa no CB-15 não é detectar a instrução, mas impedir o efeito dela. Um cartão que obedece a uma instrução embutida (ex.: "gere cartões sobre outro assunto") não tem citação literal nem cobertura lexical nos trechos e é descartado. A delimitação reduz a chance, e os portões garantem o resultado.  
**Consequências:**

- **Instruções versionadas no repositório:** `cartoes/geracao/instrucoes/gerador_v1.md` e `juiza_v1.md`. A versão (ex.: `gerador-v1+juiza-v1`) é gravada na geração e no consumo, e qualquer mudança no texto ou nos limiares cria uma versão nova (RQ-006).
- **Delimitação:** os trechos vão na mensagem do usuário, cada um entre `<trecho id="Tn" nonce="…">` e `</trecho nonce="…">`, com um *nonce* aleatório por chamada. As instruções do sistema dizem que tudo dentro dos delimitadores é material de estudo, nunca instrução, e um texto que tente fechar o delimitador não conhece o *nonce*.
- **Instruções do gerador:**
  - usar só os trechos;
  - nunca completar com conhecimento geral (RF-005);
  - copiar a citação literalmente;
  - não criar cartão sobre ponto em que os trechos se contradizem e listá-lo em `pontos_contraditorios`;
  - não repetir as frentes listadas;
  - escrever em português;
  - no máximo 10 cartões.
- **Contradições (CB-09):** `pontos_contraditorios` é guardado só como contagem na geração e no log, nunca vira cartão. A juíza reprova um cartão que afirme um dos lados (motivo `contradicao`). Não existe detecção determinística de contradição, e o CS-003 é medido pelo revisor no conjunto de avaliação.
- **Parâmetros do modelo:** temperatura baixa no gerador (0,2) e zero na juíza, e o teto de *tokens* da execução (DTEC 040).
- **Provedor simulado nos testes:** `FunctionModel` e `TestModel` do PydanticAI, com `models.ALLOW_MODEL_REQUESTS = False` no `conftest`, para que nenhum teste da suíte principal chame a rede. Um `FunctionModel` de cenário devolve:
  - cartões válidos;
  - cartão sem trecho;
  - citação inventada;
  - cartão fora do assunto;
  - instrução obedecida;
  - lados de uma contradição;
  - resposta malformada;
  - timeout;
  - 429;
  - 15 cartões.
- **Conjunto de avaliação** (`backend/tests/avaliacao_ia/`, marcador `avaliacao_ia`, fora da suíte que bloqueia o merge, DTEC 011):
  - **Casos:** no mínimo 15, sobre textos fictícios escritos pela equipe em `dados/` (regra 10):
    - 6 regulares (PDF e TXT, com e sem página);
    - 2 ambíguos;
    - 2 sem evidência (ex.: um sumário sem conteúdo);
    - 2 com contradição;
    - 3 adversariais (instrução para mudar de assunto, para revelar as instruções e para inventar página);
    - 1 caso de três "Gerar mais" seguidos (CS-007).
  - **Execução:** `pytest -m avaliacao_ia`, com o provedor real configurado no `.env`. O pydantic-evals roda os casos e grava `docs/specs/004-geracao-cartoes/avaliacao/AAAA-MM-DD-<modelo>-<versao>.md`, com o provedor, o modelo, a versão das instruções e, por caso, os cartões publicados, os descartados com o motivo e a citação de cada um.
  - **Revisão humana:** o revisor marca cada cartão publicado como sustentado ou não (CS-004), sem afirmação ausente (CS-002), sem tomar partido (CS-003) e sem repetição (CS-007). O script recalcula as métricas e grava o resultado no mesmo arquivo. O CS-001 (todo publicado aponta para trecho existente) é verificado automaticamente. O relatório também traz a precisão com e sem a juíza (DTEC 042).
  - **Responsável (RQ-007, D-012):** qualquer pessoa da equipe pode implementar a 004. Quem assumir registra o próprio nome no plano antes da primeira execução do conjunto (tarefa de abertura) e passa a ser o revisor. As aprovações desta fase de documentação são de Artur Lins.
  - **Reexecução:** trocar o provedor, o modelo ou a versão das instruções exige executar o conjunto de novo (RQ-006).

**Condição para revisão:** a reavaliação do framework de agentes do final acadêmico ([QA-31](../../produto/pendencias.md#qa-31-framework-de-agentes-do-final-acadêmico)) ou um caso adversarial que passe pelos portões, que pediria uma nova camada de defesa.

## Fontes consultadas

- Documentação do PydanticAI (`ai.pydantic.dev`): `UsageLimits` (`request_limit` e limites de *tokens*), `RunUsage`, saída estruturada com modelos Pydantic e correção da saída, `FunctionModel`, `TestModel` e `models.ALLOW_MODEL_REQUESTS`, consultada em 13/10/2026.
- Documentação do pydantic-evals (conjuntos de casos e avaliadores), consultada em 13/10/2026 para a DTEC 047.
- Documentação do PostgreSQL 17: `ON DELETE SET NULL (coluna)` em FK composta (PostgreSQL 15 em diante), índice único parcial, `ALTER TYPE ... ADD VALUE` (o valor novo só pode ser usado depois do *commit* da transação que o criou) e *advisory locks*, consultada em 13/10/2026 para as DTEC 044 a 046.
- Documentação do Procrastinate (`RetryStrategy`, *queueing locks* e *locks*), já citada nas DTEC 030 e 040.
- Planos e `research.md` das specs 002 e 003 (DTEC 027, 029 a 032 e 035 a 038) e o [esquema inicial](../../arquitetura/esquema-inicial.dbml).
