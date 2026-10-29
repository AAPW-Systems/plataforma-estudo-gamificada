# Implementação da spec 004 (geração de cartões): base, T001 a T011

**Data:** 2026-10-29
**Autor:** Artur Lins (condução); implementação pelo agente
**Agente e modelo:** agente de programação (o identificador do modelo não é registrado em artefatos do repositório)
**Etapa SDD:** implementar
**Funcionalidade:** 004-geracao-cartoes
**Responsável pela implementação e revisor do conjunto de avaliação (T001):** Artur Lins

## Contexto fornecido

- A 003 está `Convergida` (29/10/2026). Esta sessão cobre só a base da 004 (Fases 1 e 2, T001 a T011); a US1 (T012 em diante) não começa.
- Contêiner de nuvem Linux sem Docker; PostgreSQL do sistema ligado com `pg_ctlcluster 16 main start`. A T011 (Compose) é verificada por Artur Lins no Docker Desktop.

## Prompts

### Prompt 1

```text
Implemente a base da spec 004 (docs/specs/004-geracao-cartoes): tarefas T001 a T011 (Fases 1 e 2), na branch `develop`, seguindo o AGENTS.md e o SDD à risca. Não comece a US1 (T012 em diante).

Antes de agir:
- Leia o AGENTS.md, a constituição, `docs/skills/contexto-tecnico.md`, `docs/skills/padroes-implementacao.md` (inclusive a seção da 003), `docs/skills/padroes-interface.md`, `docs/skills/registrar-prompt.md` e todos os artefatos de `docs/specs/004-geracao-cartoes/` (spec, plan, research com as DTEC 039 a 047, data-model, contracts, quickstart, tasks e traceability).
- Atualize a `develop` (`git pull --rebase origin develop`) e confira se o CI está verde.
- Crie o registro da sessão em `docs/prompts/AAAA-MM-DD-004-geracao-cartoes-implementacao.md`, com este prompt literal, adicione-o ao índice e vá acrescentando a evidência de cada tarefa.

T001 vem primeiro e depende de mim: pergunte-me quem é a pessoa responsável pela implementação e revisora do conjunto de avaliação. Não faça nenhuma outra tarefa antes da minha resposta e da minha aprovação. Depois, registre o nome no plan.md e no registro da sessão.

Autoria dos commits:
- Configure `git config --local user.name "Artur Lins"` e `git config --local user.email "artur.olins@gmail.com"`, e confira com `git log -1 --format='%an <%ae>'`.
- Nenhum `Co-Authored-By` em nenhum commit, e nenhuma menção a modelo ou ferramenta de IA nos commits, no código, na documentação ou nos registros.
- O rodapé `Claude-Session: ...` também não entra.
- Nunca reescreva o histórico publicado (regra 14): sem amend, rebase de commits publicados nem force-push, mesmo que algum hook peça.

Fluxo de trabalho:
- Testes antes do código: mostre o vermelho antes do verde e registre os dois.
- Para cada regra importante, quebre a implementação de propósito (mutação) e confira que algum teste cai; depois restaure o código.
- Um commit atômico por tarefa ou por par teste e implementação, em Conventional Commits em português, citando o ID (ex.: `feat(ia): núcleo do cliente de IA [T008-T009]`).
- Todo commit que marca tarefa `[x]` inclui o `README.md` regenerado por `python scripts/atualizar_readme_progresso.py`. O hook `.githooks/pre-commit` não executa no clone de nuvem, então rode o script à mão.
- Só marque `[x]` com evidência registrada no registro da sessão.

Antes de cada push:
- `git pull --rebase origin develop`;
- backend completo duas vezes seguidas, verde, com `ruff format --check`, `ruff check` e `mypy` limpos;
- frontend com `eslint`, `tsc`, `prettier --check`, `vitest` e `vite build` limpos;
- depois do push, confira o CI.

Restrições:
- Sem dependência fora da stack aprovada. As da T002 (`pydantic-ai-slim` com os extras `google` e `groq`, e `pydantic-evals`) estão nas DTEC 007 e 011; fixe as versões no `uv.lock`.
- Nenhuma chamada real a provedor de IA: `models.ALLOW_MODEL_REQUESTS = False` e `IA_PROVEDOR=teste` nos testes.
- Sem segredos: as chaves ficam vazias no `.env.example`. Preserve o `.env` local e nunca imprima os valores dele.
- Sem dados pessoais reais: só contas `@exemplo.com`.
- Dúvida de produto vira questão Q-xxx na spec e pergunta para mim; não decida.

Pontos já conhecidos da 003 que afetam esta base:
- A migração `0005` acrescenta `aguardando_revisao` e `recusado` a `situacao_cartao`, então o teste `tests/integration/cartoes/test_restricoes.py::test_situacoes_da_004_ainda_nao_existem_no_enum` vai falhar, e o fixture `situacoes_da_004` de `tests/conftest.py` deixa de ser necessário. Trate isso na T004 de forma explícita: troque o teste por um que confira os quatro valores, troque o fixture por cartões reais nessas situações e registre a mudança. Os testes da 003 que usavam o fixture continuam cobrindo o mesmo caso ("aguardando revisão ou recusado responde 404 e fica fora da lista").
- Fixtures que recriam um tipo do banco precisam de `await engine.dispose()` depois. O defeito (`cache lookup failed for type`) só aparece na suíte completa.
- O participante falso dos cartões gerados (`tests/participantes_falsos.py`) segue nos testes da 002 até a 004 ter o participante real; não o remova nesta base.
- No ambiente de nuvem não há serviço do Docker, nem há PostgreSQL rodando por padrão; ligue-o com `pg_ctlcluster 16 main start`. A T011 (`docker compose up --build` com a `0005` e `\dT+ situacao_cartao` mostrando quatro valores) é verificada por mim no Docker Desktop: deixe-a aberta com o comando pronto e só a marque depois que eu colar a saída. A parte do CI verde da T011 você confere.
- O teste com leitor de tela fica para a rodada final do projeto (decisão de 15/10/2026).

Ao terminar, relate o que foi feito, como foi verificado, o que ficou pendente e o que depende de mim, sem declarar como verificado algo que não foi executado. Atualize o registro, as tarefas, o README da spec, o "Estado atual" do AGENTS.md e o `contexto-tecnico.md`.
```

### Prompt 2 (resposta à pergunta da T001)

```text
Artur Lins
```

## Evidência por tarefa

- **Base antes da sessão:** `develop` em `ed85999`, CI verde (execução 38). Suíte do backend no ambiente local: 2344 aprovados e 1 pulado (`test_saude.py:138`, pulado porque o banco local roda como superusuário), em 7 min 18 s.
- **T001:** nome "Artur Lins" registrado no campo do `plan.md` (linha 10) e no cabeçalho deste registro. Aprovado por Artur Lins em 29/10/2026 ("Aprovado, pode seguir").

- **T002:** `pydantic-ai-slim[google,groq]==2.63.0` nas dependências e `pydantic-evals==2.63.0` no grupo `dev`, fixados no `uv.lock`. O lock só acrescentou pacotes (`google-genai` 2.34.0, `groq` 1.7.0, `pydantic-graph`, `genai-prices`, `logfire-api`, `httpx2` e dependências de transporte); nenhuma versão existente mudou (`pydantic` segue 2.14.1). Marcador `avaliacao_ia` registrado e excluído por `addopts = [..., "-m", "not avaliacao_ia"]`. Verificação no ambiente local (sem Docker): `uv run python -c "import pydantic_ai, pydantic_evals"` em Python 3.13.17 e `pytest --markers` lista `@pytest.mark.avaliacao_ia`. O mesmo comando dentro da imagem (`docker compose run --rm api ...`) fica coberto pelo CI, que constrói a imagem com o `uv.lock`.
- **T003:**
  - **Vermelho:** `tests/unit/ia/test_configuracao.py` não coletava (`ModuleNotFoundError: No module named 'app.ia'`), e `tests/unit/nucleo/test_configuracao.py` tinha 18 falhas e 72 aprovados (campos `GERACAO_*` ausentes). Depois de criar `app/ia/configuracao.py`, os três testes de partida (API sem chave, worker com `teste` em produção, `ALLOW_MODEL_REQUESTS`) falharam (3 falhas, 18 aprovados) até a validação entrar em `criar_aplicacao` e em `worker.validar_configuracao` e o `conftest` ganhar o bloqueio.
  - **Verde:** 21 testes em `tests/unit/ia/test_configuracao.py` e 90 em `tests/unit/nucleo/test_configuracao.py` (111 aprovados).
  - **Mutações (cada uma restaurada depois):** sem a regra da janela, com `GERACAO_CARTOES_MAX` até 11, com limiar de cobertura aceitando 0, com limiar de repetição até 1,5, sem a recusa de `teste` em produção, aceitando chave só com espaços, lendo a chave errada do Groq, sem `ALLOW_MODEL_REQUESTS = False`, sem a validação da IA em `criar_aplicacao` e sem ela no worker: em todas, de 1 a 3 testes caem.
  - **Decisões:** a versão e os parágrafos do aviso de cada provedor (`gemini-v1`, `groq-v1`, `teste-v1`) ficam em `app/ia/configuracao.py`, com o nome do provedor, a finalidade (só os trechos da fonte pedida), o uso que o provedor pode fazer do conteúdo e a recomendação de não enviar dados pessoais ou confidenciais (DTEC 039). Com `IA_MODELO_*` vazios, valem os padrões do provedor (`gemini-2.5-flash` e `llama-3.3-70b-versatile`); a conferência deles contra a camada gratuita vigente é registrada no relatório de avaliação, que fica fora desta base. O `.env.example` traz `IA_PROVEDOR=teste`, as chaves vazias e os padrões do plano; o `compose.yaml` não muda, porque `api` e `worker` já leem o `.env`.
- **T004:**
  - **Entidades:** `app/ia/modelos.py` (`ConsumoIa`, `CienciaAvisoIa`), `app/cartoes/geracao/modelos.py` (`Geracao`, `GeracaoTrecho`, `Evidencia`, `CartaoDescartado`, com `EstadoGeracao`, `CodigoFalhaGeracao` e `MotivoDescarte`) e, em `app/cartoes/modelos.py`, `geracao_id`, `motivo_recusa`, `MotivoRecusa` e os dois valores novos de `SituacaoCartao`.
  - **Migração `0005_geracao_cartoes`:** `ADD VALUE IF NOT EXISTS` num `autocommit_block` antes de tudo (o `IF NOT EXISTS` permite subir de novo depois de descer, porque os valores ficam); quatro enums, seis tabelas com PK `generated always as identity` (as de chave composta, `geracoes_trechos` e `ciencias_aviso_ia`, sem identidade), FK composta da geração para a fonte com `ON DELETE SET NULL (fonte_id)`, índice único parcial `geracoes_fonte_em_andamento`, `CHECK` de coerência (`codigo_falha` só em `falhou`, `concluida_em` só no estado final, quantidades, citação com `0 ≤ inicio < fim`, página ≥ 1, tetos dos descartados, tokens e latência não negativos) e os quatro `CHECK` novos de `cartoes`. A descida recusa com `RAISE EXCEPTION` se houver cartão `aguardando_revisao` ou `recusado`.
  - **Vermelho:** 20 falhas, 109 aprovados e 68 erros nos testes novos e nos ajustados (tabelas e colunas inexistentes).
  - **Verde:** `tests/integration/geracao/test_restricoes.py` (79 casos), `test_migracoes.py` (a `0005` sobe, desce e sobe de novo; a descida é recusada com cartão aguardando revisão e com cartão recusado) e os testes da 003 afetados.
  - **Mutações (cada uma restaurada):** sem o `CHECK` situação × origem (4 falhas), sem o de `motivo_recusa` (3), sem o da explicação obrigatória (1), sem o de `geracao_id` em `criado` (1), FK simples para a fonte (a migração não sobe), índice único sem o `WHERE` (5), sem o `CHECK` de `codigo_falha` (4), citação aceitando `inicio ≥ fim` (2), consumo apagado em cascata com a geração (2), descida sem a recusa (2), `ADD VALUE` fora do bloco autocommit (a migração não sobe), DTO da API com os quatro valores (3).
  - **Mudanças nos testes da 003, como o prompt pediu:**
    - `test_situacoes_da_004_ainda_nao_existem_no_enum` deu lugar a `test_situacao_cartao_tem_os_quatro_valores`; o teste da `0004` em `test_migracoes.py` passou a esperar os quatro valores com a `0005` aplicada.
    - O fixture `situacoes_da_004` saiu do `conftest.py`. Os quatro testes que o usavam (lista e total na US1, repositório, consulta e edição, suspender, reativar e excluir) agora semeiam cartões gerados reais com `semear_cartao_gerado` (`tests/apoio_cartoes.py`): uma geração `concluida` de uma fonte da matéria e o cartão nela, com explicação, nas situações `aguardando_revisao` e `recusado`. Continuam cobrindo o mesmo caso: `404` nas rotas da 003 e fora da lista e do total.
    - A fábrica da 003 inseria cartões `gerado_verificado` sem explicação, que o `CHECK` novo recusa: `fabricas_cartoes.inserir` passou a completar a explicação do gerado (`EXPLICACAO_GERADO`), e `test_as_tres_origens_sao_aceitas_sem_referencia[gerado_verificado]` passou a informá-la. Os testes que comparavam com `set(SituacaoCartao)` passaram a comparar com as duas situações visíveis.
  - **Contrato preservado:** com o enum do banco com quatro valores, o filtro `?situacao=` e o `CartaoDTO` da 003 passariam a anunciar os quatro no OpenAPI, contra o contrato (`SituacaoCartao: [ativo, suspenso]`). O DTO ganhou o próprio `SituacaoCartao` com os dois valores, e o mapeador converte; o `backend/openapi.json` não mudou. Teste novo: `test_filtro_da_lista_nao_aceita_as_situacoes_da_revisao` (`422`).
- **T005:** `app/fontes/consultas.py` com `fonte_do_dono` (`FOR SHARE` por padrão, `travar=False` sem trava) e `trechos_da_fonte` (em `ordem`, com `tamanho` em code points pelo `char_length`, filtro opcional por ids), sempre com o dono na consulta. Vermelho: a coleta falha (`app.fontes.consultas` inexistente). Verde: 6 testes em `tests/integration/fontes/test_consultas.py`, inclusive o da trava (uma segunda conexão com `lock_timeout` não consegue `FOR UPDATE` na fonte enquanto a leitura travada está aberta, e consegue sem a trava). Mutações: sem o dono em cada consulta, ordem por `id`, sem o `FOR SHARE` e sem o filtro por ids: todas derrubam 1 ou 2 testes. Uma mutação sobreviveu (sem o retorno antecipado para lista de ids vazia): o código era redundante, porque o `IN` vazio já não devolve nada, e saiu.
- **T007:** `tests/arquitetura/test_camadas.py` passou a vigiar: `app.ia` fora dos domínios que conhecem `cartoes`; `app.ia` sem importar nenhum domínio de negócio; `pydantic_ai` só em `app/ia/` e em `app/cartoes/geracao/agentes.py`, percorrendo também o núcleo e a composição; os nomes das chaves e do provedor (`GEMINI_API_KEY`, `GROQ_API_KEY`, `IA_PROVEDOR`, `chave_api` e os atributos) só em `app/ia/`; `cartoes/geracao/dominio.py` e `validacao.py` sem FastAPI, Starlette, SQLAlchemy nem PydanticAI. O detector recusa 19 importações e 4 leituras proibidas de exemplo (`test_detector_recusa_*`), o que prova que uma violação futura derruba o teste.
- **Suíte completa depois da T004, T005 e T007:** 2490 aprovados e 1 pulado (o mesmo de antes), em 8 min 44 s.
- **T008 e T009:**
  - **Implementação:** `app/ia/excecoes.py` (`ErroIA` com o `codigo` da falha; `ProvedorIndisponivel`, sua subclasse `ErroTransitorioIA`, `LimiteProvedor`, `RespostaInvalida` e `OrcamentoEsgotado`), `orcamento.py`, `provedores.py` (`GoogleModel`, `GroqModel` ou `TestModel`), `cliente.py` (`ClienteIa.executar` e `classificar_erro`), `repositorios.py` e `registros.py` (ordem 600, importado em `principal.py`). O dia de estudo ficou em `app/nucleo/dia_estudo.py` (`dia_estudo`, `inicio_dia` e `proxima_virada`), como a DTEC 048 manda: a 004 é a primeira a precisar dele, então cria o módulo e os testes.
  - **Decisões de implementação:** o teto da execução (`UsageLimits`) é o que resta do orçamento do dia (`total_tokens_limit`), com no máximo 3 requisições (a resposta e o pedido de correção da saída, com folga); estourar o teto vira `OrcamentoEsgotado`. A classificação usa a hierarquia de erros do PydanticAI 2.63: `ModelQuotaExceededError` e os 429 cujo corpo traz cota diária (`PerDay`, `per day`, `daily`, `TPD`, `RPD`) viram `LimiteProvedor`; os demais 429, os 5xx, timeout, conexão e sobrecarga viram `ErroTransitorioIA`; recusas definitivas (credencial, modelo inexistente, outros 4xx) viram `ProvedorIndisponivel`, sem nova tentativa; saída fora do esquema vira `RespostaInvalida`. Um erro que não é do provedor (defeito de programação) volta como veio. O consumo é registrado numa transação própria, com sucesso ou falha, e o log `chamada_ia` leva só os identificadores públicos.
  - **Ajuste à API do PydanticAI 2.63:** `Agent(retries={"output": 1})` no lugar de `output_retries`, `run(..., timeout=...)` e `resultado.usage` como atributo.
  - **Vermelho:** sem os módulos, as 6 coletas falham (`tests/unit/nucleo/test_dia_estudo.py`, `tests/unit/ia/test_classificacao_erros.py`, `test_orcamento.py`, `test_provedores.py`, `tests/integration/ia/test_cliente.py` e `test_registros.py`). Com os módulos, 9 falhas (API do PydanticAI) até os ajustes acima.
  - **Verde:** 85 testes (dia de estudo com Hypothesis, orçamento, classificação, provedores, cliente e registros).
  - **Mutações (cada uma restaurada):** sem a conferência do orçamento antes da chamada, sem o registro da falha, sem o tempo limite, sem o teto da execução, 429 de cota diária tratado como transitório, sem `ModelQuotaExceededError`, 4xx tratado como transitório, sem `RespostaInvalida`, sem a geração no consumo, erro desconhecido convertido em falha do provedor, soma sem o filtro do usuário, soma de tokens sem o `coalesce` da entrada, exclusão sem as ciências, só os tokens de entrada no orçamento, sem a virada das 4h, um único modelo para gerador e verificador, sem a busca da hora inexistente: todas derrubam de 1 a 9 testes. Duas sobreviveram na primeira rodada (o `coalesce` da entrada e a busca da hora inexistente) e ganharam testes: um consumo com só os tokens de saída e o dia 30/12/2011, que não existiu em `Pacific/Apia`.
- **T010:** `frontend/src/componentes/ui/CitacaoDestacada.tsx` (o trecho com o intervalo da citação em `<mark>`, contado em code points com `Array.from`, como o `char_length` do servidor; intervalo inválido mostra o trecho sem destaque; sempre texto puro, com as quebras de linha preservadas) e `PainelEvidencia.tsx` (`Disclosure` do React Aria, recolhido por padrão; com a fonte: título, trecho com a citação destacada e "Página N" só quando conhecida; com a fonte apagada: "Ver origem", "Fonte apagada", título, arquivo, página quando conhecida e data, sem o trecho). Estilos em `global.css`, só com os tokens. Vermelho: a coleta falha sem os componentes. Verde: 16 testes em `evidencia.test.tsx`, inclusive teclado (Tab, Enter e espaço) e `vitest-axe` sem violações, recolhido e expandido. Mutações (cada uma restaurada): contar em unidades UTF-16, sem a validação do intervalo, sem o `<mark>`, página sempre visível (nos dois ramos), painel aberto por padrão, sem o ramo da fonte apagada, sem a data: todas derrubam de 1 a 5 testes. Frontend completo: `prettier --check`, `eslint` e `tsc` limpos, `vitest` com 292 testes em 30 arquivos (eram 276) e `vite build` concluído. Teste com leitor de tela: rodada final do projeto (decisão de 15/10/2026).
- **T006:**
  - **`tests/fabricas_geracao.py`:** fontes `concluido` fictícias (biologia em PDF, uma página por trecho; história em TXT, sem página; um trecho com instrução embutida, inclusive a tentativa de fechar o delimitador; um par contraditório; uma fonte longa de até 2 MB), divididas pelo próprio divisor da 002, de modo que as invariantes da DTEC 029 valem por construção. `semear_fonte_concluida` grava a fonte e os trechos; a linha de comando `python -m tests.fabricas_geracao --email --materia --tamanho-mb` só roda com `APP_AMBIENTE=desenvolvimento` e só para contas `@exemplo.com` (reaproveita `email_de_exemplo` da fábrica da 003).
  - **`tests/cenarios_provedor.py`:** um `FunctionModel` por cenário da DTEC 047 (válidos com citação literal, sem trecho e `T999`, citação inventada, fora do assunto, instrução obedecida, lados de uma contradição, resposta malformada, timeout, 5xx, 429 por minuto e por cota diária, 15 cartões, campos com 50 mil caracteres), a juíza que aprova, reprova ou omite índices e o `ContadorChamadas`. As funções leem os trechos no formato de delimitação da DTEC 047 e devolvem os campos da `SaidaGeracao` da DTEC 042; a juíza lê `<cartao indice="N">` e devolve `avaliacoes` (`indice`, `sustentado`, `motivo`). **Ponto para a US1:** os agentes reais (`cartoes/geracao/agentes.py`, T013 em diante) precisam usar esses mesmos formatos e nomes de campos, ou os cenários são ajustados junto.
  - **Vermelho:** sem os dois módulos, as duas coletas falham.
  - **Verde:** 44 testes em `tests/unit/test_fabricas_geracao.py` e `tests/integration/geracao/test_fabricas_geracao.py`: invariantes dos trechos por tema, recusas da linha de comando (ambiente, domínio, tamanho), os cenários válidos passando nos portões 1 a 4 avaliados à mão no teste (a implementação real é da US1), cada cenário inválido falhando no portão que exercita, os lados da contradição passando nos portões (quem os reprova é a juíza), a resposta malformada esgotando o pedido de correção (2 chamadas), os erros do provedor, a juíza e o contador; no banco, cada tema grava a fonte e os trechos, o mesmo tema entra duas vezes na matéria, e a linha de comando cria a fonte longa numa conta `@exemplo.com`.
  - **Mutações (cada uma restaurada):** sem a recusa de ambiente (2 falhas), sem a recusa de domínio (4), biologia sem página (2), hash sem o sufixo aleatório (1), explicação sem apoio no trecho (5), juíza sem omitir (1), contador sem contar (2), citação invertida (7). A citação em maiúsculas sobreviveu e é equivalente: o portão da citação compara sem diferenciar caixa (DTEC 042).

- **T011:** aberta. A parte do Compose é verificada por Artur Lins no Docker Desktop (o contêiner de nuvem não tem Docker), com os comandos da seção "Verificação da base (T011)" do [quickstart](../specs/004-geracao-cartoes/quickstart.md); a tarefa só é marcada depois que a saída for colada aqui. A parte do CI é conferida depois do push (abaixo).

- **Antes do push:** `git pull --rebase origin develop` sem mudança; backend completo, execução 1: 2598 aprovados e 1 pulado em 7 min 48 s.

## Saída aceita

- Base da spec 004 (Fases 1 e 2) na `develop`: T001 a T010 concluídas, cada uma com vermelho, verde e mutações registrados acima, em commits atômicos de autoria de Artur Lins.
- Documentação atualizada: tarefas, README da spec, índice das specs, "Estado atual" e mapa do `AGENTS.md`, `contexto-tecnico.md` (estado, base da 004 e obrigações), `padroes-implementacao.md` (seção da base da 004) e quickstart (verificação da T011).

## Pendências

- **T011 (depende de Artur Lins):** `docker compose up -d --build --wait` e `\dT+ situacao_cartao` no Docker Desktop, com a saída colada neste registro.
- **US1 (T012 em diante):** só começa por decisão de Artur Lins. Pontos levantados nesta base para ela:
  - os agentes reais precisam seguir o formato de delimitação e os nomes de campos simulados em `tests/cenarios_provedor.py` (ou os cenários mudam junto);
  - o quickstart diz que o provedor simulado (`IA_PROVEDOR=teste`) "devolve cartões fictícios sustentados pelos trechos"; hoje `teste` usa o `TestModel` do PydanticAI, que gera saídas de acordo com o esquema mas sem relação com os trechos (seriam descartadas pelos portões). Fazer o modo de desenvolvimento devolver cartões sustentados é trabalho da US1;
  - os modelos padrão (`gemini-2.5-flash` e `llama-3.3-70b-versatile`) ainda não foram conferidos contra a camada gratuita vigente; isso é registrado no relatório de avaliação, antes da primeira execução do conjunto.
- **Leitor de tela:** rodada final do projeto (decisão de 15/10/2026).
- **Ambiente local:** o teste `tests/integration/test_saude.py:138` é pulado aqui porque o banco local roda como superusuário; no CI ele roda.
