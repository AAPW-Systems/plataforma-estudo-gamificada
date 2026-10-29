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

## Saída aceita

*Em andamento.*

## Pendências

*Em andamento.*
