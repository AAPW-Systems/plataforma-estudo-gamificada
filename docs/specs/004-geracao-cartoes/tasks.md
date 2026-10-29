# Tarefas da funcionalidade

**Funcionalidade:** 004-geracao-cartoes (geração de cartões pela IA e revisão dos gerados)  
**Entrada:** [spec](spec.md), [plano](plan.md) (aprovado em 13/10/2026), [pesquisa](research.md), [modelo de dados](data-model.md), [contrato](contracts/openapi.yaml) e [quickstart](quickstart.md)  
**Formato:** `[ID] [P?] [US?] ação com caminho exato e resultado verificável`  
**Status:** aprovadas em 13/10/2026 por Artur Lins (equipe), junto com a [rastreabilidade](traceability.md)

- `[P]` indica que a tarefa pode ser executada em paralelo, porque não altera os mesmos arquivos nem depende de outra tarefa pendente.
- `[US1]` relaciona a tarefa a uma história de usuário.
- Marque `[x]` somente quando o resultado e a sua verificação estiverem concluídos (regra 6).
- **Caminhos:** `backend/src/app/` aparece abreviado como `app/`, e `backend/tests/` como `tests/`.
- **Pré-requisitos:**
  - da [spec 001](../001-conta-acesso/tasks.md), as tarefas até a US2 (T001 a T045): estrutura base, sessão, CSRF, contrato (T037), teste que percorre as rotas (T041), auxiliar de busca por dono (T043) e registro `apagar_dados_usuario`;
  - da [spec 002](../002-materias-fontes/tasks.md), as tarefas até a US1 (T001 a T031): fontes, trechos, participantes (T005) e jobs travados (T007). Para a T020, também as US2 e US3 da 002 (T032 a T046), cujos testes funcionais ela reexecuta;
  - da [spec 003](../003-cartoes-manuais/tasks.md), as tarefas da US1 e da US2 (T001 a T027): tabela `cartoes`, regras de texto e de origem, painel de criação e edição. Para a T020, também a T023 (caso "aguardando revisão fora da lista").
- **Testes antes do código:** em cada história, as tarefas de teste vêm antes das de implementação. Os testes começam falhando e passam ao fim da história.
- **Provedor nos testes:** a suíte principal nunca chama o provedor real (`ALLOW_MODEL_REQUESTS = False`). Ela usa os cenários de `FunctionModel` da T006. Só o marcador `avaliacao_ia` (Fase 7) usa o provedor real, fora da suíte que bloqueia o merge.
- **Commits:** todo trabalho acontece na `develop` (regra 14), com um commit atômico por tarefa ou por par teste e implementação, citando o ID da tarefa (ex.: `feat(geracao): implementa a janela de trechos [T023]`). Os escopos `geracao` e `ia` identificam esta spec.

## Fase 1 Preparação

- [x] T001 **Registrar a pessoa responsável (RQ-007, D-012):** quem assumir a implementação da 004 escreve o próprio nome no campo "Responsável pela implementação e revisor do conjunto de avaliação" do [plano](plan.md) e no registro de prompts da sessão de implementação. **Verificação:** o nome está nos dois lugares antes de qualquer outra tarefa, e Artur Lins aprova a mudança.
- [x] T002 Acrescentar a `backend/pyproject.toml`, em versões fixas no `backend/uv.lock` (DTEC 007 e 011):
  - `pydantic-ai-slim` com os extras `google` e `groq`;
  - `pydantic-evals`, no grupo de desenvolvimento;
  - o marcador `avaliacao_ia` registrado e excluído da execução padrão (`addopts = -m "not avaliacao_ia"`).

  **Verificação:** `docker compose run --rm api uv run python -c "import pydantic_ai, pydantic_evals"` funciona em Python 3.13, e `pytest --markers` lista `avaliacao_ia`.
- [ ] T003 Acrescentar a configuração da IA e da geração:
  - **`.env.example`:** as variáveis da [tabela do plano](plan.md#variáveis-de-ambiente-acréscimos-ao-envexample), com as chaves vazias (regra 9);
  - **Configuração:** `app/ia/configuracao.py` (`IA_*`, com as chaves em `SecretStr` e o aviso de cada provedor: versão e parágrafos) e os campos `GERACAO_*` em `app/nucleo/configuracao.py`;
  - **`tests/conftest.py`:** `models.ALLOW_MODEL_REQUESTS = False` e `IA_PROVEDOR=teste`.

  **Testes** em `tests/unit/nucleo/test_configuracao.py` e `tests/unit/ia/test_configuracao.py`. A aplicação **não** sobe com:
  - limiar fora de (0, 1];
  - janela menor que `TRECHO_TAMANHO_MAXIMO`;
  - `GERACAO_CARTOES_MAX` acima de 10 ou abaixo de 1;
  - `IA_PROVEDOR=teste` com `APP_AMBIENTE=producao`;
  - provedor real sem a chave.

  Todo provedor configurado tem versão e texto do aviso (DTEC 039), e a aplicação sobe com os padrões.

## Fase 2 Base compartilhada (bloqueia todas as histórias)

- [ ] T004 Criar as entidades e a migração da geração:
  - **Entidades:**
    - `app/ia/modelos.py`: `ConsumoIa` e `CienciaAvisoIa`;
    - `app/cartoes/geracao/modelos.py`: `Geracao`, `GeracaoTrecho`, `Evidencia` e `CartaoDescartado`, com os enums `EstadoGeracao`, `CodigoFalhaGeracao` e `MotivoDescarte`;
    - em `app/cartoes/modelos.py`: `geracao_id`, `motivo_recusa`, o enum `MotivoRecusa` e os valores novos de `SituacaoCartao`.
  - **Migração** `backend/migracoes/versions/0005_geracao_cartoes.py`, conforme o [modelo de dados](data-model.md):
    - `ALTER TYPE situacao_cartao ADD VALUE` para `aguardando_revisao` e `recusado`, dentro de `op.get_context().autocommit_block()`, antes de tudo;
    - os enums novos e as tabelas `geracoes`, `geracoes_trechos`, `evidencias_cartoes`, `cartoes_descartados`, `consumo_ia` e `ciencias_aviso_ia`, com PK `generated always as identity`;
    - a FK composta da geração para a fonte com `ON DELETE SET NULL (fonte_id)`;
    - o índice único parcial `geracoes_fonte_em_andamento` e os demais índices;
    - as colunas novas de `cartoes`, os `CHECK` novos e o índice `geracao_id`;
    - a descida, que remove o que a subida criou, menos os valores de enum, e recusa descer se houver cartão `aguardando_revisao` ou `recusado`.

  **Verificação:** `tests/integration/test_migracoes.py` sobe e desce, e a descida é recusada com cartão gerado. `tests/integration/geracao/test_restricoes.py` mostra que:
  - cada `CHECK` recusa a linha inválida (situação × origem, `motivo_recusa`, explicação obrigatória, `codigo_falha` coerente, `geracao_id` nulo em `criado`, citação com `inicio < fim`);
  - a FK composta recusa uma geração com fonte de outra matéria ou de outro dono;
  - apagar a fonte anula só o `fonte_id` da geração, mantendo `materia_id`;
  - o índice parcial recusa uma segunda geração em andamento da mesma fonte e aceita uma nova depois da primeira terminar.
- [ ] T005 [P] Criar `app/fontes/consultas.py`, a leitura que a geração usa sem acessar o ORM de `fontes`:
  - `fonte_do_dono(sessao, usuario_id, public_id, travar=FOR SHARE)`: id, matéria, estado, título, nome do arquivo e data do envio;
  - `trechos_da_fonte(sessao, usuario_id, fonte_id, ids|None)`: id, ordem, texto, página e tamanho, em ordem.

  **Testes** em `tests/integration/fontes/test_consultas.py`: o filtro de dono, a ordem e uma fonte alheia sem resultado (DTEC 019).
- [ ] T006 [P] Criar as fábricas da geração:
  - **`tests/fabricas_geracao.py`:** fontes `concluido` com trechos fictícios de biologia e de história, com e sem página; um trecho com instrução embutida; um par de trechos contraditórios; a fonte de 2 MB. A linha de comando `python -m tests.fabricas_geracao --email --materia --tamanho-mb` só roda com `APP_AMBIENTE=desenvolvimento` e só para contas `@exemplo.com` (regra 10).
  - **`tests/cenarios_provedor.py`:** um `FunctionModel` para cada cenário da [DTEC 047](research.md#decisão-dtec-047-instruções-embutidas-contradições-e-avaliação):
    - cartões válidos com citação literal;
    - cartão sem trecho e rótulo `T999`;
    - citação inventada;
    - cartão fora do assunto;
    - instrução obedecida;
    - lados de uma contradição;
    - resposta malformada;
    - timeout, 5xx e 429 (por minuto e cota diária);
    - 15 cartões;
    - campos com 50 mil caracteres.

    Também um `FunctionModel` da juíza que aprova, reprova ou omite índices, e um contador de chamadas.

  **Teste** em `tests/unit/test_fabricas_geracao.py`: cada trecho respeita as invariantes da DTEC 029; a linha de comando recusa outro ambiente e outro domínio; os cenários "válidos" passam nos portões quando avaliados à mão.
- [ ] T007 [P] Ampliar `tests/arquitetura/test_camadas.py`:
  - `app/ia`, `app/fontes` e `app/materias` não importam `app/cartoes`;
  - `app/ia` não importa nenhum domínio de negócio;
  - `pydantic_ai` só é importado em `app/ia/` e em `app/cartoes/geracao/agentes.py`, e as chaves e o provedor só são lidos em `app/ia/`;
  - `app/cartoes/geracao/dominio.py` e `validacao.py` não importam FastAPI, SQLAlchemy nem `pydantic_ai`.
- [ ] T008 [P] Criar os testes do domínio `ia`:
  - **`tests/unit/ia/test_orcamento.py`:** início do dia de estudo (virada das 4h, fuso, horário de verão) e soma de *tokens* com nulos.
  - **`tests/unit/ia/test_classificacao_erros.py`:** timeout, conexão, 5xx e 429 por minuto são transitórios; cota diária vira `limite_provedor`; saída fora do esquema vira `resposta_invalida`.
  - **`tests/unit/ia/test_provedores.py`:** `gemini`, `groq` e `teste` geram o modelo certo, sem rede.
  - **`tests/integration/ia/test_cliente.py`:**
    - uma linha de `consumo_ia` por chamada, com sucesso ou falha, com provedor, modelo, versão, *tokens* e latência, e sem conteúdo;
    - orçamento esgotado impede a chamada (`OrcamentoEsgotado`) sem chamar o modelo;
    - `UsageLimits` aplicado;
    - timeout de `IA_TIMEOUT_SEGUNDOS`.
  - **`tests/integration/ia/test_registros.py`:** `apagar_dados_usuario` apaga o consumo e as ciências do usuário.
- [ ] T009 Implementar o núcleo do domínio `ia`, até que a T008 passe:
  - `app/ia/provedores.py`;
  - `app/ia/cliente.py` (`executar(agente, entrada, contexto)`: orçamento, timeout, `UsageLimits`, classificação dos erros em `ErroTransitorioIA`, `LimiteProvedor`, `RespostaInvalida` e `OrcamentoEsgotado`, e o registro do consumo numa transação própria);
  - `app/ia/repositorios.py`, `excecoes.py` e `registros.py`, importado pela composição em `principal.py` e em `worker.py`.
- [ ] T010 [P] Criar em `frontend/src/componentes/ui/`, sobre o React Aria (DTEC 016), cada um com teste e `vitest-axe`:
  - `CitacaoDestacada`: o texto do trecho com o intervalo da citação em `<mark>`, contado em *code points* como no servidor, sempre como texto puro;
  - `PainelEvidencia`: fonte, trecho com a citação destacada e a página só quando conhecida; ou "Fonte apagada" com título, arquivo, página e data, sem o trecho. Recolhido por padrão e expansível ([design, 9.8](../../base-specs/design.md#98-evidência)).
- [ ] T011 **Verificar a base:** `docker compose up --build` aplica a `0005`, `\dT+ situacao_cartao` mostra os quatro valores, e a integração contínua passa na `develop`. Registrar a evidência no registro de prompts da sessão de implementação.

## Fase 3 História de usuário 1 Gerar cartões de uma fonte e escolher quais entram (P1)

**Objetivo:** o estudante dá ciência do aviso, pede cartões de uma fonte concluída, acompanha a geração e decide cada cartão: aceitar, editar e aceitar, recusar com motivo opcional, ou aceitar todos.  
**Teste independente:** com uma fonte fictícia `concluido` e o provedor simulado, pedir cartões, aceitar 3, editar e aceitar 1 e recusar 2, e confirmar que só os 4 aceitos ficam ativos, cada um com a origem e a evidência corretas (passos 1 a 10 da US1 no [quickstart](quickstart.md)).

- [ ] T012 [P] [US1] Criar os testes unitários da janela e da repetição em `tests/unit/geracao/test_janela.py` e `tests/unit/geracao/test_repeticao.py` (DTEC 041):
  - **Janela:** ordem; teto de caracteres; trecho nunca cortado; pelo menos um trecho mesmo acima do teto; só trechos não cobertos; fonte esgotada devolve vazio.
  - **Assinatura:** NFC, acentos, caixa, palavras vazias, radicais de 5 caracteres e números. Com Hypothesis: a assinatura é idempotente, e o Jaccard é simétrico e vai de 0 a 1.
  - **Repetição:** frente igual; limiar exato e um pouco abaixo; repetição dentro do mesmo lote; comparação com todas as situações e origens.
- [ ] T013 [P] [US1] Criar os testes unitários dos portões e do prompt em `tests/unit/geracao/test_validacao.py` e `tests/unit/geracao/test_agentes.py` (DTEC 042 e 047):
  - **Estrutura:** limites da 003 e explicação obrigatória.
  - **Vínculo:** rótulo inexistente.
  - **Citação:** literal com espaços, caixa e aspas tipográficas diferentes; inventada; `trecho[inicio:fim]` normalizado igual à citação.
  - **Cobertura:** no limiar, abaixo dele, com números e com uma resposta de uma palavra; aplicada ao verso e à explicação, e não à frente.
  - **Excedente:** a partir do 11º aprovado.
  - **Prompt:** *nonce* diferente a cada chamada; trechos só dentro dos delimitadores; rótulos `T1` a `Tn`; nenhum id do banco; frentes vizinhas incluídas (no máximo 30).
- [ ] T014 [P] [US1] Criar os testes unitários da revisão em `tests/unit/geracao/test_revisao.py` (DTEC 045):
  - tabela completa situação × ação × corpo, com os `409 cartao_ja_decidido`;
  - "editar e aceitar" com `origem_apos_edicao` da 003 (com e sem mudança efetiva);
  - motivo só em `recusado` e troca do motivo;
  - deslocamentos de microssegundos do "Aceitar todos" na ordem de exibição;
  - `verificado` e `fonteApagada` derivados.
- [ ] T015 [P] [US1] Criar os testes do aviso em `tests/unit/ia/test_aviso.py` e `tests/functional/ia/test_aviso.py` (RF-002, DTEC 039):
  - `GET /ia/aviso` com a versão, o provedor e os parágrafos;
  - `POST /ia/aviso/ciencia` idempotente;
  - versão antiga recebe `409 aviso_desatualizado`;
  - trocar o provedor na configuração faz `cienciaRegistrada` voltar a `false`.
- [ ] T016 [P] [US1] Criar os testes de integração da tarefa em `tests/integration/geracao/test_tarefa_gerar_cartoes.py` (DTEC 043), com o `FunctionModel`:
  - do `pendente` ao `concluida`: provedor, modelo, versão e trechos registrados (RF-017); cartões em `aguardando_revisao` com o estado de `fsrs.Card()`, `geracao_id`, evidências com cópias e deslocamentos; descartados com o motivo (RF-007);
  - reexecução depois de uma morte simulada entre as transações A e B: sem duplicar cartões nem `geracoes_trechos`;
  - geração inexistente ou já `concluida`: termina sem efeito;
  - fonte apagada entre A e B: nada é publicado;
  - exclusão da fonte em paralelo à transação B, numa conexão separada: ou os cartões nascem antes e entram no impacto, ou nada é publicado (DTEC 031);
  - duas gerações de fontes diferentes da mesma matéria propondo o mesmo cartão: um só é publicado.
- [ ] T017 [P] [US1] Criar os testes de integração do pedido em `tests/integration/geracao/test_pedido_concorrencia.py` (DTEC 044):
  - 20 pedidos simultâneos de fontes diferentes, com 19 gerações no dia: só 1 recebe `202`;
  - 2 pedidos simultâneos para a mesma fonte: uma geração só;
  - a mesma chave em paralelo: uma geração só;
  - geração `falhou` não conta no limite (D-010);
  - virada das 4h no fuso do estudante.
- [ ] T018 [P] [US1] Criar os testes do participante em `tests/integration/geracao/test_participante.py` (DTEC 027, 038 e 046):
  - `contar_por_materia` com `cartoes_aguardando_revisao`;
  - `impacto_fonte` com os aguardando revisão e os aceitos (inclusive editados e suspensos) das gerações da fonte;
  - `ao_excluir_fonte`:
    - nos dois modos, apaga os aguardando revisão, os recusados e os descartados;
    - no modo `excluir`, apaga os aceitos;
    - no modo `manter`, os aceitos ficam com evidência sem `trecho_id` e com as cópias;
    - gerações em andamento viram `falhou/fonte_excluida`;
    - os cartões manuais de outra fonte não são tocados;
  - `apagar_dados_usuario` das gerações, na ordem certa;
  - o teste de catálogo da 001 (`tests/security/identidade/test_exclusao_completa.py`) verde com todas as tabelas novas preenchidas.
- [ ] T019 [P] [US1] Criar os testes funcionais em `tests/functional/geracao/test_us1_gerar_revisar.py`, de ponta a ponta pela API, com o worker executado no teste:
  - cenários 1 a 9 da US1 e o teste independente (4 aceitos ativos, com origem e evidência corretas). A entrada como cartão novo é verificada pelo estado gravado (`ativo`, `entrada_estudo_em` na ordem de aceitação);
  - casos de borda:
    - clique duplo com a mesma chave;
    - novo pedido com geração em andamento;
    - fonte `pendente`, `processando` e `falhou` (`409 fonte_nao_concluida`);
    - limite atingido (`429` com `Retry-After` até a virada);
    - nova geração com cartões aguardando revisão;
    - "Aceitar todos" duas vezes;
    - editar e aceitar com a frente vazia (`422`, nada muda);
  - `GET /geracoes/uso` antes e depois;
  - `GET /materias/{id}/geracoes` com as gerações relevantes.
- [ ] T020 [US1] Reexecutar com dados reais da 004 (DTEC 027 e 038):
  - **003, US2-2:** parametrizar `tests/functional/cartoes/test_us2_editar.py::test_gerado_vira_editado` para usar um cartão aceito de uma geração real. Depois da edição, `GET /cartoes/{id}/evidencias` continua devolvendo o trecho;
  - **003, caso de borda "aguardando revisão fora da lista":** `tests/security/cartoes/test_editar_seguranca.py::test_aguardando_revisao_404` com um cartão de geração real, sem a fixture que cria o valor de enum, que é removida;
  - **002, US2 e US3:** parametrizar `tests/functional/fontes/test_us2_exclusao_fonte.py` e `tests/functional/materias/test_us3_organizar.py` para rodarem com o participante da 004. As contagens exibidas são iguais às apagadas (CS-004 da 002), e no modo `manter` os aceitos ficam com "Fonte apagada" e sem selo.
- [ ] T021 [P] [US1] Criar os testes de segurança em `tests/security/geracao/test_geracao_seguranca.py`:
  - **Tabela de isolamento:** acrescentar a `tests/security/test_isolamento_rotas.py` as 7 rotas com identificador desta história (`POST /fontes/{id}/geracoes`, `GET /materias/{id}/geracoes`, `GET /geracoes/{id}`, `GET /geracoes/{id}/cartoes`, `POST /geracoes/{id}/aceitacao`, `POST /cartoes/{id}/aceitacao` e `POST /cartoes/{id}/recusa`), com `404` idêntico ao de inexistente;
  - **Fonte alheia:** geração recusada com `404`, e nenhum trecho alheio entra na janela;
  - **Ciência:** sem ela, `409 ciencia_aviso_pendente`, e o contador do provedor simulado fica em zero;
  - **Logs e consumo:** sem texto de trechos, cartões, citações nem instruções, verificados com captura;
  - **Rotas da 003:** cartão `aguardando_revisao` ou `recusado` responde `404` em todas elas;
  - **Proteções herdadas:** `401` sem sessão e `403` sem CSRF nas rotas novas.
- [ ] T022 [P] [US1] Criar os testes adversariais em `tests/adversarial/geracao/test_revisao_adversarial.py`:
  - **Entradas:** chave de idempotência que não é UUID; chave reutilizada para outra fonte (`409 idempotencia_divergente`); motivo fora do enum; campos extras na aceitação e na recusa (`extra="forbid"`); corpo acima de 64 KiB (`413`); marcação e script no "editar e aceitar", devolvidos literalmente.
  - **Concorrência:**
    - aceitar e recusar o mesmo cartão em paralelo: um efeito só, e o outro recebe `409`;
    - "Aceitar todos" em paralelo com uma recusa: o recusado não é aceito;
    - aceitar durante a exclusão da fonte no modo `excluir`: ou o aceito entra no impacto e é apagado, ou a aceitação recebe `404`.
- [ ] T023 [US1] Implementar `app/cartoes/geracao/dominio.py` (janela, assinatura, repetição, transições, ordem e catálogo de falhas), `validacao.py` (portões 1 a 4) e `dados/palavras_vazias.txt`, até que as T012 a T014 passem.
- [ ] T024 [US1] Implementar `app/ia/aviso.py`, `servicos.py`, `dtos.py`, `mapeadores.py` e `rotas.py` (`GET /ia/aviso` e `POST /ia/aviso/ciencia`), até que a T015 passe.
- [ ] T025 [US1] Implementar `app/cartoes/geracao/agentes.py` (gerador com a saída `SaidaGeracao`, temperatura 0,2 e `output_retries=1`; prompt com *nonce*) e `instrucoes/gerador_v1.md`. Implementar `tarefas.py` (`gerar_cartoes` com as transações A e B, `queueing_lock`, `lock` e o *advisory lock* da publicação) e registrar a tarefa em `app/worker.py`, até que a T016 passe. Nesta história, a juíza fica desligada: ela entra na T036.
- [ ] T026 [US1] Implementar o pedido e o acompanhamento em `app/cartoes/geracao/servicos.py`, `repositorios.py`, `dtos.py`, `mapeadores.py` e `rotas.py`, até que as T017 e T019 passem nos pontos do pedido:
  - `POST /fontes/{id}/geracoes`, na ordem da DTEC 044;
  - `GET /geracoes/uso`, `GET /materias/{id}/geracoes` e `GET /geracoes/{id}`, com `no-store`.
- [ ] T027 [US1] Implementar a revisão, até que as T019, T021 e T022 passem:
  - `GET /geracoes/{id}/cartoes`, `POST /cartoes/{id}/aceitacao` (reutilizando `normalizar_texto_cartao`, `validar_limites`, `houve_mudanca` e `origem_apos_edicao` da 003), `POST /cartoes/{id}/recusa` e `POST /geracoes/{id}/aceitacao`;
  - na 003, `app/cartoes/repositorios.py` e `mapeadores.py` passam a derivar `verificado` e o campo `geracao` pelo *left join* com `geracoes` (DTEC 045). Os testes da 003 continuam verdes.
- [ ] T028 [US1] Implementar `app/cartoes/geracao/registros.py` (participante `geracoes_cartoes` e `apagar_dados_usuario` das gerações), importado pela composição, até que as T018 e T020 passem.
- [ ] T029 [US1] Ampliar `tests/integration/test_contrato_openapi.py` para verificar também `docs/specs/004-geracao-cartoes/contracts/openapi.yaml`, incluindo os 8 códigos novos do enum de `Erro` e o campo `geracao` em `Cartao`. Regenerar e versionar `backend/openapi.json` e rodar `npm run gerar:api`.
- [ ] T030 [P] [US1] Criar os testes de componente em `frontend/src/funcionalidades/geracao/`, todos com axe sem violações:
  - **Aviso:** só aparece sem ciência; foco preso; "Entendi e gerar" registra e pede; "Cancelar" não pede; `409 aviso_desatualizado` recarrega o aviso.
  - **Pedir cartões:** só em fonte `concluido`; desabilitado com a explicação e o horário quando o limite ou o orçamento acabaram; a chave é gerada uma vez por intenção, e o clique duplo e a nova tentativa de rede reenviam a mesma.
  - **Acompanhamento:** estados anunciados por `aria-live`; o *polling* para no estado final; aviso "N cartões aguardando revisão" na matéria.
  - **Revisão:** frente, verso, explicação e "Ver trecho" (`PainelEvidencia`); aceitar; "Editar e aceitar" com o painel da 003 e o erro do `422` junto do campo; recusar e escolher um dos quatro motivos com um clique; foco no próximo cartão depois de cada decisão; "Aceitar todos" depois da lista; sem atalhos de uma letra.
- [ ] T031 [US1] Implementar as telas, até que a T030 passe:
  - a rota `frontend/src/rotas/_autenticado/materias/$materiaId.geracoes.$geracaoId.tsx`;
  - o botão "Pedir cartões" e o estado da geração em cada fonte, e o aviso de pendentes na página da matéria ([design, 9.4 e 9.6](../../base-specs/design.md#96-revisão-dos-cartões-gerados));
  - o diálogo do aviso, a revisão, o motivo da recusa e as consultas e mutações em `frontend/src/funcionalidades/geracao/`, com o intervalo de `api/acompanhamento.ts`;
  - o modo "editar e aceitar" no painel de `frontend/src/funcionalidades/cartoes/`.

  Depois de cada decisão, invalidar a revisão, a lista de cartões e a de matérias.
- [ ] T032 [US1] Executar os passos 1 a 10 da US1 no quickstart com o provedor simulado e os testes `functional`, `security` e `adversarial` da US1. Registrar a evidência.

## Fase 4 História de usuário 4 Falhas na geração sem conteúdo inventado (P1)

**Objetivo:** nenhuma falha do provedor, saída malformada, cartão sem trecho ou fora da fonte, instrução embutida ou contradição chega ao estudante. Cada falha aparece com o estado e a mensagem certos. Faz parte do critério de pronto da US1.  
**Teste independente:** com o provedor simulado devolvendo erro, resposta malformada, cartões sem trecho ou sobre um assunto ausente da fonte, confirmar que nenhum desses cartões fica visível e que a geração mostra o estado correto.

- [ ] T033 [P] [US4] Criar os testes funcionais em `tests/functional/geracao/test_us4_falhas.py`, um por cenário da US4 com o cenário da T006:
  - **Cenário 1:** erro, timeout e 429, com `falhou` e a mensagem do catálogo, sem detalhe do provedor (RQ-005), sem cartão e sem contar no limite. "Tentar de novo" é um novo pedido que funciona.
  - **Cenários 2 e 3:** cartão sem trecho, com rótulo inexistente, com citação inventada ou fora do assunto. Os descartados ficam com o motivo, e os válidos do mesmo lote são publicados.
  - **Cenário 4:** instrução obedecida, com nenhum cartão sobre o assunto da instrução.
  - **Cenário 5:** lados de uma contradição, reprovados pela juíza (`contradicao`) e com `pontos_contraditorios` contado.
  - **Cenário 6:** todos descartados, com `concluida`, `semCartoesSustentados = true` e a mensagem distinta da falha técnica.
  - **Casos de borda:** 15 cartões devolvidos, com só os 10 primeiros aprovados mantidos (`excedente`); fonte com um parágrafo, com menos de 10 cartões ou nenhum; orçamento esgotado no pedido (`429 orcamento_ia_esgotado`).
- [ ] T034 [P] [US4] Criar os testes adversariais em `tests/adversarial/geracao/test_injecao.py` (CB-15, DTEC 047):
  - trechos que mandam mudar de assunto, revelar as instruções, inventar página e fechar o delimitador, com o provedor simulado "obedecendo": nenhum cartão publicado, e o *nonce* nunca aparece nos trechos;
  - saídas extremas: campos com 50 mil caracteres, citação vazia, rótulo `T999` e script nos campos (publicado como texto, se passar nos portões).
- [ ] T035 [P] [US4] Criar os testes de integração das falhas em `tests/integration/geracao/test_falhas.py` (DTEC 040 e 043):
  - provedor fora do ar: 2 novas tentativas pela fila e depois `falhou/provedor_indisponivel`, nada publicado;
  - cota diária do provedor: `limite_provedor`, sem nova tentativa;
  - resposta malformada depois da correção: `resposta_invalida`;
  - banco indisponível na transação B: nova tentativa, sem duplicar;
  - orçamento esgotado entre o gerador e a juíza: `orcamento_esgotado`, e a juíza não é chamada;
  - falha da juíza: a geração falha, sem publicar nada sem verificação;
  - juíza que omite um índice: o cartão é reprovado;
  - a juíza nunca aprova um cartão que um portão reprovou;
  - a tarefa `reenfileirar_tarefas_travadas` devolve à fila um `gerar_cartoes` travado (DTEC 030).
- [ ] T036 [US4] Implementar a juíza (portão 5) em `app/cartoes/geracao/agentes.py`, com `instrucoes/juiza_v1.md`, temperatura 0 e `GERACAO_VERIFICADOR_IA`. Implementar também o `RetryStrategy(max_attempts=2, exponential_wait=5)` de `gerar_cartoes`, a gravação de `falhou` com o código na última tentativa, `pontos_contraditorios` e as mensagens do catálogo em `mensagemFalha` e `semCartoesSustentados`, até que as T033 a T035 passem.
- [ ] T037 [P] [US4] Criar os testes de componente das falhas em `frontend/src/funcionalidades/geracao/`:
  - mensagens distintas para falha técnica (com "Tentar de novo"), sem cartões sustentados e orçamento esgotado;
  - "Tentar de novo" gera uma chave nova;
  - nenhum detalhe do provedor na tela;
  - axe sem violações.
- [ ] T038 [US4] Implementar os estados de falha e a ação "Tentar de novo" na fonte e na tela da geração, até que a T037 passe.
- [ ] T039 [US4] Executar a verificação da US4 no quickstart: chave inválida com `IA_PROVEDOR=gemini`, depois `adversarial_instrucao.txt` e `contradicao.txt` com o provedor real. Executar também os testes `functional`, `adversarial` e `integration` da US4. Registrar a evidência.

## Fase 5 História de usuário 3 Conferir a origem e a explicação de um cartão gerado (P2)

**Objetivo:** o estudante consulta a evidência de qualquer cartão gerado (na revisão e na aba Cartões), inclusive depois da exclusão da fonte.  
**Teste independente:** abrir a evidência de um cartão gerado e conferir fonte, trecho e página; excluir a fonte mantendo os cartões e conferir "Fonte apagada" com a descrição da origem, sem o trecho.

- [ ] T040 [P] [US3] Criar os testes funcionais em `tests/functional/geracao/test_us3_evidencia.py`:
  - **Cenário 1:** fonte, trecho, deslocamentos da citação e página só quando conhecida (TXT sem página).
  - **Cenário 2:** "Fonte apagada" depois da exclusão no modo `manter`, com título, arquivo, página e data, `trecho` nulo e `verificado = false` no `Cartao`.
  - **Cenário 3:** a explicação acompanha a evidência da mesma resposta, e a citação está no trecho.
  - **Situações:** cartão `recusado` responde `404`; cartão manual devolve `evidencias` vazia; cartão aguardando revisão, ativo e suspenso respondem.
- [ ] T041 [P] [US3] Acrescentar à tabela de isolamento `GET /cartoes/{id}/evidencias`, com `404` idêntico para cartão alheio, e verificar nos logs a ausência do texto do trecho.
- [ ] T042 [US3] Implementar `GET /cartoes/{id}/evidencias` em `app/cartoes/geracao/servicos.py`, `repositorios.py`, `mapeadores.py` e `rotas.py`, até que as T040 e T041 passem.
- [ ] T043 [P] [US3] Criar os testes de componente: "Ver origem" num cartão gerado da aba Cartões abre o `PainelEvidencia`, com "Fonte apagada" sem trecho e sem selo; explicação junto da evidência; axe sem violações.
- [ ] T044 [US3] Implementar "Ver origem" na lista de cartões da 003 e na revisão, até que a T043 passe.
- [ ] T045 [US3] Executar o teste independente da US3 e a verificação complementar do quickstart (evidência e "Fonte apagada") e registrar a evidência.

## Fase 6 História de usuário 2 Ver o resumo e gerar mais (P2)

**Objetivo:** ao terminar a revisão, o estudante vê o resumo e pede mais cartões, sem repetição. Numa fonte esgotada, recebe a mensagem de que não há conteúdo novo.  
**Teste independente:** terminar a revisão de uma geração, conferir o resumo e pedir "Gerar mais"; confirmar com o provedor simulado que nenhum novo cartão repete um existente ou um recusado da matéria.

- [ ] T046 [P] [US2] Criar os testes funcionais em `tests/functional/geracao/test_us2_gerar_mais.py`:
  - **Cenário 1:** resumo com publicados, aceitos (inclusive editados) e recusados, e `aguardandoRevisao = 0`.
  - **Cenário 2:** três "Gerar mais" seguidos, com o provedor simulado propondo repetições de cartões existentes, aguardando revisão, recusados e de outra fonte da matéria. Todos são descartados como `repetido`, e as janelas não se sobrepõem.
  - **Cenário 3:** fonte esgotada, com `409 sem_conteudo_novo`, sem criar geração, sem contar no limite e com o contador do provedor em zero (CB-26).
  - **Janela liberada:** uma geração `falhou` libera a janela para a próxima.
- [ ] T047 [P] [US2] Criar os testes de integração em `tests/integration/geracao/test_cobertura.py`: a consulta de cobertura só considera gerações `concluida`, e as frentes dos cartões ligados aos trechos vizinhos entram no prompt.
- [ ] T048 [US2] Implementar a verificação de trechos não cobertos no pedido (`409 sem_conteudo_novo`), as frentes vizinhas no prompt e os campos do resumo em `GET /geracoes/{id}`, até que as T046 e T047 passem.
- [ ] T049 [P] [US2] Criar os testes de componente `ResumoGeracao.test.tsx`:
  - o resumo aparece quando não resta cartão aguardando;
  - "Gerar mais" cria uma geração nova com uma nova chave e vai para ela;
  - "Não há novos cartões a gerar desta fonte" no `409`;
  - "Gerar mais" desabilitado com o limite atingido;
  - axe sem violações.
- [ ] T050 [US2] Implementar o cartão de resumo e "Gerar mais" na tela da geração, até que a T049 passe.
- [ ] T051 [US2] Executar a verificação complementar da US2 no quickstart (resumo, dois "Gerar mais" e fonte esgotada) e registrar a evidência.

## Fase 7 Conjunto de avaliação da IA

**Objetivo:** medir a geração com o provedor real e a revisão humana (D-003, D-006, D-011, RQ-006, RQ-007), cumprindo os CS-001 a CS-005 e o CS-007. Executado fora da suíte que bloqueia o merge (DTEC 011).

- [ ] T052 [P] Escrever os dados e os casos em `tests/avaliacao_ia/dados/` e `tests/avaliacao_ia/casos.py`, todos fictícios e escritos pela equipe (regra 10), com no mínimo 15 casos:
  - 6 regulares (PDF e TXT, com e sem página);
  - 2 ambíguos;
  - 2 sem evidência;
  - 2 com contradição;
  - 3 adversariais (mudar de assunto, revelar as instruções, inventar página);
  - 1 caso de três "Gerar mais" seguidos (CS-007).

  A pessoa responsável (T001) revisa os casos antes da primeira execução.
- [ ] T053 Implementar a avaliação:
  - **`app/cartoes/geracao/analise.py`:** taxa de aceitação por geração, por fonte e no total, e a distribuição dos motivos de recusa por modelo e versão das instruções (CS-005), com testes em `tests/integration/geracao/test_analise.py`;
  - **`tests/avaliacao_ia/test_avaliacao.py`:** marcador `avaliacao_ia`, `Dataset` do pydantic-evals, execução com e sem a juíza, e o CS-001 calculado automaticamente;
  - **Relatório:** gravado em `docs/specs/004-geracao-cartoes/avaliacao/AAAA-MM-DD-<modelo>-<versao>.md`, com o provedor, o modelo, a versão e, por caso, os publicados, os descartados com o motivo e as citações;
  - **`tests/avaliacao_ia/calcular.py`:** recalcula os CS-002 a CS-004 e o CS-007 a partir das marcações do revisor.

  **Verificação:** `pytest -m avaliacao_ia` com `IA_PROVEDOR=teste` gera um relatório de exemplo sem rede.
- [ ] T054 Executar o conjunto com o provedor real. A pessoa responsável revisa e marca cada cartão publicado, roda o cálculo e versiona o relatório. **Pronto quando:**
  - o CS-001 é de 100%;
  - nenhum cartão traz afirmação ausente da fonte (CS-002) nem toma partido numa contradição (CS-003);
  - pelo menos 90% dos publicados são sustentados (CS-004, D-006);
  - nenhuma repetição aparece no caso do CS-007;
  - o relatório mostra a precisão com e sem a juíza (DTEC 042).

  Se algum critério falhar, ajustar as instruções ou os limiares (com uma nova versão das instruções) e executar de novo (RQ-006).

## Fase final Qualidade transversal

- [ ] T055 Executar nos contêineres as suítes completas do backend e do frontend, a qualidade estática e a verificação do contrato, e confirmar a integração contínua aprovada na `develop`. Registrar as contagens de testes e a cobertura.
- [ ] T056 Revisar e registrar as evidências:
  - **Logs:** `api` e `worker` sem texto de trechos, cartões, citações nem instruções; `consumo_ia` sem conteúdo.
  - **Repositório:** sem chaves nem segredos; `.env.example` com as chaves vazias (regras 9 e 10).
  - **Acessibilidade (RQ-004):** teclado e leitor de tela no aviso, na revisão, no motivo da recusa, no resumo e na evidência; "Aceitar todos" depois da lista; uso em 320 px sem rolagem horizontal; contraste.
- [ ] T057 Medir e registrar, no ambiente local:
  - **CS-006:** geração de 10 cartões da fonte de 2 MB da fábrica com o provedor real, em até 2 minutos;
  - pedido e ações da revisão: percentil 95 até 200 ms;
  - filtro de repetição numa matéria com 3 mil cartões: abaixo de 100 ms.
- [ ] T058 Atualizar a documentação:
  - o [quickstart](quickstart.md), com os comandos realmente verificados e o modelo registrado;
  - `docs/skills/padroes-implementacao.md`, com o uso de `ia/cliente.py`, o provedor simulado e o marcador `avaliacao_ia`;
  - o "Mapa do repositório" do `.agents/AGENTS.md`, com o domínio `ia` e o subpacote `cartoes/geracao`.
- [ ] T059 Atualizar o [traceability.md](traceability.md) com os nomes reais dos testes e corrigir requisitos sem teste ou tarefa.

## Dependências

- **Specs anteriores:**
  - as T001 a T045 da 001, as T001 a T031 da 002 e as T001 a T027 da 003 bloqueiam toda esta lista;
  - a T020 também depende das T032 a T046 da 002.
- **Preparação e base:**
  - a T001 vem antes de tudo;
  - as T002 e T003 bloqueiam a Fase 2, e a Fase 2 (T004 a T011) bloqueia todas as histórias;
  - a T004 bloqueia as T005, T006 e T008 e todos os testes de integração;
  - a T009 depende da T008, e a T010 bloqueia a T030.
- **US1:** T012 a T019, T021 e T022 sem dependência entre si → T023 → T024 → T025 → T026 → T027 → T028 → T020 → T029 → T031 (usa os tipos gerados) → T032. A T030 pode ser escrita em paralelo ao backend.
- **US4:** depende da US1 (T025 e T026). T033 a T035 em paralelo → T036; T037 → T038 → T039. A T039 usa o provedor real e a T001.
- **US3:** depende da US1 (T027). Pode ser feita em paralelo à US4, por pessoas diferentes, porque altera rotas e telas distintas.
- **US2:** depende da US1 (T026) e da US4 (o filtro de repetição já está na T023, e a juíza na T036).
- **Avaliação:** a T052 pode começar depois da T001. A T053 depende da T036, e a T054 depende da T053 e da US2 (CS-007).
- **Specs seguintes:** a 005 monta lições só com `ativo`, exibe a explicação ao errar com `GET /cartoes/{id}/evidencias` e reverifica a US1-4 com lições reais. A 010 e a 014 reutilizam a janela, os portões e o `ia/cliente.py` ([obrigações no plano](plan.md#obrigações-registradas-para-as-próximas-specs)).
- **Fase final:** depende de todas as histórias e da Fase 7.

## Pontos de paralelismo

- **Base:** T005, T006, T007, T008 e T010 alteram arquivos distintos.
- **Histórias:** em cada uma, as tarefas de teste marcadas com `[P]` podem ser escritas em paralelo. O frontend (T030 e T031; T037 e T038; T043 e T044; T049 e T050) avança em paralelo ao backend depois da T029.
- **Entre histórias:** depois da US1, a US4 e a US3 podem seguir com pessoas diferentes. A escrita dos casos de avaliação (T052) corre em paralelo a tudo.

## Estratégia de incremento

1. **Base completa:** a T011 prova que a migração, o domínio `ia` e o provedor simulado funcionam e que a integração contínua passa.
2. **P1 demonstrável:** entregar a US1 e a US4 juntas. Uma geração real com a juíza e as falhas tratadas é o critério de pronto da US1.
3. **Histórias seguintes:** acrescentar a US3 e a US2 sem quebrar a P1. A suíte completa passa a cada commit.
4. **Avaliação e verificação final:** executar o conjunto de avaliação com o provedor real, a fase final e atualizar os artefatos afetados. Nenhum merge na `main` acontece sem todos os testes passando (regra 17).
