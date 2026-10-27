# Implementação da spec 003 (cartões manuais): T001 a T003

**Data:** 2026-10-23
**Autor:** Artur Lins (condução); implementação pelo agente
**Agente e modelo:** Claude Code (o identificador do modelo não é registrado em artefatos do repositório)
**Etapa SDD:** implementar
**Funcionalidade:** 003-cartoes-manuais

## Contexto fornecido

- A spec 002 está `Convergida` (15/10/2026) e a 001 em `Implementando` (T063 e leitor de tela são humanos). Só a 003 entra nesta sessão; a 004 não começa.
- Esta sessão rodou num contêiner de nuvem Linux novo, sem `docker compose` utilizável. O ambiente local foi refeito: PostgreSQL 16 do sistema, backend no host (`uv`, Python 3.13, `UV_PROJECT_ENVIRONMENT` fora do repositório), variáveis de ambiente num arquivo do diretório temporário da sessão (nenhum `.env` foi criado no repositório) e frontend com `npm ci`.

## Prompts

### Prompt 1

```text
Implemente a spec 003 (docs/specs/003-cartoes-manuais: cartões criados e gerenciados pelo estudante) na branch
`develop`, da T001 até a T045, seguindo o AGENTS.md e o SDD à risca. A 002 está Convergida (15/10/2026); só a 003
entra nesta sessão. Não comece a 004.

Antes de agir, leia o AGENTS.md (CLAUDE.md aponta para ele) e, nesta ordem: docs/skills/contexto-tecnico.md,
docs/skills/padroes-implementacao.md (inclusive a seção "Acervo: matérias, fontes e exclusões"),
docs/skills/padroes-interface.md, docs/skills/registrar-prompt.md e todos os artefatos de
docs/specs/003-cartoes-manuais (spec, plan, research, data-model, contracts/openapi.yaml, quickstart, tasks,
traceability). Leia também o registro docs/prompts/2026-10-15-002-materias-fontes-implementacao-2.md (decisões,
achados e pendências da 002) e as DTEC 027 (com as emendas de 13/10 e 15/10/2026), 033 a 038.

## Regras de autoria dos commits (decisão global de Artur Lins)

- Os commits saem em nome de Artur Lins, nunca de Claude. O ambiente de nuvem vem com a identidade
  `Claude <noreply@anthropic.com>`: antes do primeiro commit, rode
  `git config --local user.name "Artur Lins"` e `git config --local user.email "artur.olins@gmail.com"`
  e confira com `git log -1 --format='%an <%ae>'` depois do primeiro commit. Se sair "Claude", corrija antes do push.
- Nenhum `Co-Authored-By`, em nenhum commit, e nenhuma menção a modelo ou ferramenta de IA nos commits, no código,
  na documentação ou nos registros. O rodapé `Claude-Session: ...` também não deve entrar.
- Nunca reescreva o histórico publicado (regra 14); os commits antigos em nome de Claude ficam como estão.

### Prompt 2 (rodada 3, em 27/10/2026)

```text
[saída do `docker compose up -d --build --wait` colada duas vezes pelo usuário, no Windows com Docker Desktop: imagens `plataforma-api:dev` e `plataforma-web:dev` construídas em 247 s; contêiner `migrate` Exited; `worker`, `api`, `web` e `db` Healthy]

obs: deu um conflito no repositório local ao fazer o pull, fiz a correção e dei o push, atualize antes de fazer outras coisas
```

## Estado de partida

- Spec 002 Convergida; 001 em Implementando (T063 e o leitor de tela são humanos). Backend: 1629 testes (1 pulado,
  superusuário); frontend: 206 testes (rode também no Node 24, o do CI). CI da `develop` verde na execução 26.
- Primeiro confira o CI da cabeça da `develop` (`git pull origin develop`) e corrija o que estiver vermelho.
- A próxima migração é a `0004_cartoes` (T003), com a extensão `unaccent` (DTEC 033).

## Regras de trabalho

- Ordem do tasks.md: Fase 1 (T001, T002), Fase 2 (T003 a T007), US1 (T008 a T019), US2 (T020 a T027),
  US3 (T028 a T033), US4 (T034 a T040), fase final (T041 a T045). Em cada história, testes antes do código, e
  mostre o vermelho antes do verde.
- Um commit atômico por tarefa ou por par teste+implementação, em Conventional Commits em português, citando o ID
  (`feat(cartoes): ... [T015]`). Antes de cada push: `git pull --rebase origin develop`, suíte completa verde
  (rode a do backend pelo menos duas vezes seguidas) e depois confira o CI.
- Só marque `[x]` no tasks.md com evidência executada (regra 6), registrada em
  docs/prompts/AAAA-MM-DD-003-cartoes-manuais-implementacao.md, que você cria logo no início (prompt literal,
  saída aceita, verificação, pendências) e acrescenta ao docs/prompts/README.md. Crie um registro novo; não reescreva
  os registros anteriores (regra 12).
- Sem dependência nova, salvo as que o plano da 003 prevê. Tecnologia fora da stack exige DTEC antes.
- Dúvida de produto vira questão Q-xxx na spec e pergunta a Artur Lins; não decida produto.
- Sem segredos e sem dados pessoais reais (contas @exemplo.com, textos fictícios das fábricas).
- Preserve o `.env` local e nunca imprima seus valores.

## O que a 002 deixa para a 003

- **Participante dos cartões (DTEC 027):** registre em `nucleo/participantes_acervo.py` o participante dos cartões
  criados à mão (contagens `cartoes_ativos`, `cartoes_suspensos` e `cartoes_referencia`, e a marcação "Fonte
  apagada" ao excluir a fonte). Faixa de prioridade 100 a 799; `fontes` roda por último (900).
- **Gancho de trava (emenda de 15/10/2026 da DTEC 027):** implemente `travar_para_exclusao_de_materia`
  (`ParticipanteComTravaDeMateria`) no participante dos cartões, travando em ordem de `id` o que a exclusão da
  matéria apaga, antes da contagem. Acrescente um teste que falhe sem a trava.
- **T011:** reexecute com cartões reais os testes funcionais da US2 e da US3 da 002
  (`tests/functional/fontes/test_us2_exclusao_fonte.py` e `tests/functional/materias/test_us3_organizar.py`), hoje
  com participantes falsos, e o CS-004 com cartões reais. A lista de matérias mostra só os ativos; o impacto da
  exclusão da matéria soma ativos e suspensos.
- **Exclusão da conta (DTEC 021):** `cartoes` entra no registro de `app/nucleo/exclusao.py` em ordem anterior a
  `materias` (500); o teste de catálogo (`security/identidade/test_exclusao_completa.py`) é a rede de segurança.
- **Isolamento e contrato:** toda rota nova com identificador entra em `CASOS_DE_ISOLAMENTO`
  (tests/security/test_isolamento_rotas.py) com o seu teste de duas contas, provando antes que a rota existe para
  o dono; use `buscar_do_dono`. Amplie o teste de contrato para o openapi.yaml da 003 (T016), regenere
  `backend/openapi.json` (`python -m app.exportar_openapi`) e os tipos (`npm run gerar:api`), sem diferença no git.
- **Cache da interface:** a lista de matérias não está montada na página da matéria; quem cria, exclui ou muda a
  situação de cartões grava o resultado no cache da lista (`setQueryData`) além de invalidar, para não piscar dado
  velho. Reaproveite `DialogoConfirmacao`, `RenomearInline` quando couber, `GrupoOpcoes` e `SeloEstado`.
- **Texto do estudante:** sempre texto puro (`pre-wrap`); `dangerouslySetInnerHTML` proibido por lint (T002, DTEC 036).
- **Participantes falsos de teste** (tests/participantes_falsos.py) continuam servindo à 002; não os quebre.

## Lições da 001 e da 002 que se aplicam

- **Ambiente de nuvem sem Compose:** se o `docker compose build` falhar por rede, rode o backend no host (uv,
  Python 3.13, `UV_PROJECT_ENVIRONMENT` fora do repositório) contra um PostgreSQL 16 local e o frontend nos Node 22
  e 24 (Node 24 via `npm install node@24` num diretório temporário); o CI é a verificação em contêiner. Se o
  PostgreSQL cair no meio da rodada (conexão recusada em massa), reinicie o cluster antes de investigar o código.
- **T007 (verificar a base):** exige `docker compose up -d --build --wait`, que só Artur Lins roda no Windows.
  Peça a saída dele; não marque a T007 sem ela, mas não pare as histórias por isso.
- **Testes de concorrência:** use `acervo`/`fabrica_real` e clientes pré-criados (não savepoints) e prove cada
  defesa por mutação. Para alargar a janela de uma corrida, use o `atraso_s` dos participantes falsos.
- **Armadilhas do shell:** `pkill -f` ou `pgrep -f` com padrão que aparece na própria linha de comando mata o
  shell; use PIDs de arquivo. Como root, `chmod 000` não bloqueia; para simular falha de permissão rode o worker
  como outro usuário (setpriv).
- **Navegador:** Playwright global (/opt/node-tools) com o Chromium em /opt/pw-browsers; axe via
  `frontend/node_modules/axe-core/axe.min.js`; o tema escuro se ativa com `data-tema="escuro"` no `<html>`.
- **Frontend:** componentes sobre o React Aria (DTEC 016), cada tela com teste e `vitest-axe`; erros junto do
  campo e foco no primeiro inválido; validar no envio, não no blur; 320 px sem rolagem horizontal; evite `autoFocus`.

## Fase final e encerramento

- T041 a T045: suítes completas, qualidade estática (inclusive a regra de lint da T002), contrato, contagens e
  cobertura; CI verde na cabeça; revisão de logs, segurança e acessibilidade com axe no navegador real em 2 temas e
  a 320 px (inclusive diálogos abertos); CS-001 cronometrado só com teclado e as medições do plano (T043);
  quickstart, padroes-implementacao.md, "Mapa do repositório" e contexto-tecnico.md atualizados; traceability.md
  com os nomes reais dos testes, conferidos por script contra os arquivos.
- Leitor de tela: por decisão de 15/10/2026, todos os testes com leitor de tela do projeto são feitos de uma vez, ao
  final; registre o que falta para essa rodada, sem marcar como feito.
- Verificação que só uma pessoa faz (Compose no Windows, teste com usuários) fica explícita e aberta.
- Ao encerrar (AGENTS.md, "Como encerrar uma sessão"): links relativos conferidos, registro completo, índices
  atualizados (docs/specs/README.md, README da 003, tasks, "Estado atual"), status da 003 em `Implementando` (ou
  `Convergida` somente se todas as tarefas tiverem evidência). Relate o que foi feito, como foi verificado e o que
  ficou pendente, sem declarar verificado o que não foi executado, e repita o pedido a Artur sobre a T007.

inicie as tasks 1 a 3 da spec 003
```

## Estado de partida

- CI da `develop`: execução 26 (`e2bc949`, cabeça) **verde**. Nada a corrigir.
- Linha de base no host: backend com **1629 passed e 1 skipped** (permissão de escrita, pulado como superusuário), em 300 s.

## Saída aceita

Rodada 1: **T001 a T003** concluídas com evidência; a 003 passou a **Implementando**. Rodada 2: **T004 a T006, T008 a T013 e T015** (pedido: T004 a T015) e, por necessidade do CI, a **T016**; a **T007 fica aberta** (depende de Artur Lins no Compose). T017 em diante seguem pendentes.

| Artefato | Ação |
|---|---|
| `.env.example`, `backend/src/app/nucleo/configuracao.py`, `backend/tests/unit/nucleo/test_configuracao.py` | alterados: `CARTAO_FRENTE_MAX`, `CARTAO_VERSO_MAX`, `CARTAO_EXPLICACAO_MAX` e os tetos (T001) |
| `frontend/eslint.config.js` | sem alteração: a regra contra `dangerouslySetInnerHTML` já existia; verificação registrada (T002) |
| `backend/migracoes/versions/0004_cartoes.py`, `backend/src/app/cartoes/{__init__,modelos}.py`, `backend/src/app/{modelos,fontes/modelos}.py` | criados e alterados: migração, entidade e índice único de `fontes` (T003) |
| `backend/tests/integration/cartoes/test_restricoes.py`, `backend/tests/integration/test_migracoes.py` | criados e alterados: restrições no banco e subida e descida da `0004` (T003) |
| `docs/specs/003-cartoes-manuais/{tasks,data-model,README}.md`, `docs/specs/README.md`, `docs/arquitetura/esquema-inicial.dbml`, `docs/skills/contexto-tecnico.md`, `.agents/AGENTS.md`, `docs/prompts/README.md` | alterados: T001 a T003 marcadas, `CHECK` da dificuldade, status e índices |

## Alterações humanas

Pendente de revisão.

## Verificação

**Ambiente da sessão.** Contêiner de nuvem Linux sem Compose utilizável: backend no host (`uv`, Python 3.13) contra o PostgreSQL 16 do sistema, frontend no Node 22. O CI do GitHub é a verificação em contêiner. As evidências por tarefa estão abaixo.

- **Backend no host, depois da correção do CI:** `ruff format --check`, `ruff check` e `mypy` limpos; **1701 passed e 1 skipped** (permissão de escrita, pulado como superusuário) em duas execuções completas seguidas (303 s e 317 s). Linha de base de partida: 1629.
- **CI da `develop`:** a execução 26 (`e2bc949`) estava verde na partida; a execução 27 (`9804ec1`, T001 a T003) falhou só pelo teste do `.env.example` (ver "Achado do CI"); a execução **28 (`ab3cce4`, cabeça) passou nos dois jobs**. O commit seguinte, só de documentação, não teve o CI aguardado.
- **Frontend (rodada 1):** não houve mudança de código; `npm run lint` passa e falha com o arquivo temporário da T002.

### Verificação da rodada 2 (T004 a T016)

- **Backend no host:** `ruff format --check`, `ruff check` e `mypy` limpos; **2063 passed e 1 skipped** em duas execuções completas seguidas (418 s e 414 s); linha de base da rodada: 1701.
- **Frontend:** **234 passed** (Node 22), `eslint`, `tsc` e `prettier --check` limpos; baseline 206. O Node 24 (o do CI) não foi instalado nesta rodada; o job `frontend` do CI roda nele.
- **CI da `develop`:** a execução **30 (`4ecd02b`, cabeça do código) passou nos dois jobs** (backend: formatação, lint, tipos, 7 min de testes com migrações, contrato OpenAPI e imagem prod; frontend: formatação, lint, tipos, testes, tipos da API e imagem prod). O commit seguinte, só de documentação, não teve o CI aguardado.


### Evidência da T001 (limites dos cartões)

`tests/unit/nucleo/test_configuracao.py` ganhou 14 casos novos (padrões 1000/2000/1000, aceitação de 1 e do teto, recusa de 0, -1 e teto + 1 nos três campos e leitura das variáveis `CARTAO_*` do ambiente). **Vermelho antes:** 15 falhas, contando um 15º teste que lia o `.env.example` e foi retirado depois (ver "Achado do CI"). **Verde depois:** 72 passed no arquivo; `ruff format --check`, `ruff check` e `mypy` limpos. Os tetos (4.000, 8.000 e 4.000) ficaram em constantes do módulo (`CARTAO_FRENTE_TETO` etc.) para o DTO, o domínio e o `CHECK` reutilizarem.

### Evidência da T002 (regra de lint contra `dangerouslySetInnerHTML`)

A regra `no-restricted-syntax` com o seletor `JSXAttribute[name.name='dangerouslySetInnerHTML']` **já estava** em `frontend/eslint.config.js` desde o commit `a236a0e` (001, T057/T058); a T002 não exigiu alteração de código. Verificação executada no host (sem Compose), `npm run lint` com Node 22: o código atual passa (saída limpa); com o arquivo temporário `src/temporario_t002.tsx` contendo `<div dangerouslySetInnerHTML={{ __html: html }} />`, o lint **falha** (`2:15 error dangerouslySetInnerHTML é proibido: exiba o texto como texto puro (DTEC 036)  no-restricted-syntax`, saída 1); removido o arquivo, volta a passar. A forma `docker compose run --rm web npm run lint` do tasks.md não pôde ser usada neste ambiente; o CI roda o mesmo `npm run lint`.

### Evidência da T003 (entidade e migração `0004_cartoes`)

Arquivos: `backend/migracoes/versions/0004_cartoes.py`, `backend/src/app/cartoes/{__init__,modelos}.py` (`Cartao`, `OrigemCartao`, `SituacaoCartao` só com `ativo` e `suspenso`, `EstadoFsrs`), `app/modelos.py` (registro) e o índice único `fontes_id_materia_usuario` também no modelo `Fonte`. A migração cria `unaccent`, os três enums, o índice em `fontes`, a tabela (PK `generated always as identity`, `public_id` com `gen_random_uuid()`, FKs compostas `restrict`, os `CHECK` e os índices `cartoes_devidos`, `cartoes_novos`, `cartoes_materia` e `cartoes_fonte_id_idx`), e a descida remove tudo menos a extensão.

- **Testes novos (58):** `tests/integration/cartoes/test_restricoes.py` (57: extensão, padrões do FSRS, `id` sempre gerado pelo banco, tetos de texto em caracteres e não em bytes, obrigatoriedade, dificuldade, cópias da referência, referência só em `criado`, entrada no estudo, enums, FK composta da matéria, FK composta da fonte (outra matéria, outro dono, inexistente), `restrict` ao apagar a fonte citada, `fonte_id` nulo com as cópias, índices) e `test_migracoes.py::test_migracao_0004_dos_cartoes_sobe_e_desce` (sobe, desce até a `0003` sem resíduos de tabela, enums e índice, mantém a extensão e sobe de novo).
- **Vermelho antes do verde:** 58 falhas com a migração ausente (os 14 que passavam eram os testes antigos de `test_migracoes`).
- **Verde depois:** 72 passed nos dois arquivos, e `test_modelos_concordam_com_migracao` continua verde (modelo e migração sem diferença). `ruff format --check`, `ruff check` e `mypy` limpos. Suíte completa do backend no host: **1702 passed, 1 skipped** (1629 de partida + 15 da T001 + 58 da T003, antes de retirar o teste do `.env.example`), 308 s e 300 s em duas execuções seguidas.
- **Mutações verificadas (cada uma derrubou o teste esperado, migração restaurada depois):** sem o `CHECK` `fonte_id` só com cópias; sem o `CHECK` referência só em `criado`; sem o `CHECK` da entrada no estudo; FK da fonte só por `id` (sem dono e matéria); FK da fonte com `SET NULL` no lugar de `restrict`; FK da matéria só por `id`; teto da frente em 5.000.
- **Decisão pequena (a confirmar):** a migração inclui o `CHECK` `dificuldade BETWEEN 1 AND 10`, que a descrição da coluna já pedia (data-model) mas a lista de `CHECK` da tarefa não citava. Acrescentei a linha ao `data-model.md` e ao comentário do `esquema-inicial.dbml`; nada mais mudou nos artefatos aprovados.
- **Não verificado aqui:** o caso de falha "migração sem permissão para `CREATE EXTENSION`" do plano (a `unaccent` é *trusted* no PostgreSQL 13+, e o papel de teste é superusuário); a mensagem vem do próprio PostgreSQL.

### Achado do CI (execução 27, `9804ec1`)

O job `backend` falhou com **1 failed, 1701 passed, 1 skipped**: `test_env_example_traz_os_limites_de_cartao_com_os_padroes` abria `/.env.example`, que **não existe no contêiner do backend** (só `backend/` e o volume `docs` são montados), embora existisse no clone do host. O job `frontend` passou. Correção: o teste foi retirado (é um teste que depende de arquivo fora do contêiner), e a conferência do `.env.example` fica como verificação manual: um script confirmou as três linhas `CARTAO_FRENTE_MAX=1000`, `CARTAO_VERSO_MAX=2000` e `CARTAO_EXPLICACAO_MAX=1000`. O Compose repassa o `.env` ao `api` por `env_file`, e o CI o cria a partir do `.env.example`, então as variáveis chegam sem outro ajuste. **Lição:** teste que lê arquivo da raiz do repositório só roda no host; o que precisa rodar no CI lê de `/docs` (volume) ou de dentro de `backend/`.

### Rodada 2 (T004 a T015): prompt

```text
continue com as tasks 4 a 15 da spec 003
```

### Evidência da T004 (fábrica de cartões)

`backend/tests/fabricas_cartoes.py`: `gerar(n)` determinístico (ciclo de 12 receitas: as três origens, ativos e suspensos, os três estados do FSRS, referência a fonte só em `criado`, acentos, cedilha, variação de caixa, curingas `%` `_` `\`, marcação e script, quebras de linha e emoji), `cartao_ficticio`, `cartao_no_limite`, `cartao_acima_do_limite`, `texto_com_tamanho`, `inserir` e a CLI `python -m tests.fabricas_cartoes --email --materia --quantidade`, que recusa `APP_AMBIENTE` diferente de `desenvolvimento` (saída 2) e e-mail fora de `@exemplo.com` (saída 2, inclusive `@sub.exemplo.com`, `@exemplo.com.br` e `@exemplo.com.evil.com`) **antes** de abrir o banco (o teste troca `criar_engine` por uma função que falha). **Testes (38):** `tests/unit/test_fabricas_cartoes.py` (limites e normalização dos textos, variedade, coerência com o `Card`, CLI) e `tests/integration/cartoes/test_fabrica_insercao.py` (os 120 cartões entram no banco pelos `CHECK` e FKs reais, ordem de criação crescente, limites exatos, CLI semeando e recusando conta/matéria inexistente). **Vermelho antes:** erro de importação (módulo ausente). **Verde depois:** 38 passed; `ruff` e `mypy` limpos. **Mutação:** com a receita da referência trocada para `editado`, 3 testes caem (um unitário e dois de integração, pelo `CHECK` do banco).

### Evidência da T005 (testes de arquitetura)

`tests/arquitetura/test_camadas.py` ganhou duas regras no detector (`violacoes`): `app.materias.*`, `app.fontes.*` e `app.identidade.*` não importam `app.cartoes`, e `app.cartoes.dominio` e `app.cartoes.cursor` não importam FastAPI, Starlette nem SQLAlchemy (o `cursor` não era coberto por nenhuma regra). Dez casos novos de detecção provam que uma violação futura falha. **Vermelho antes:** sem as duas regras, 9 dos 10 casos novos falham (o décimo, `dominio` importando FastAPI, já era pego pela regra antiga); **verde depois:** 26 passed no diretório. A varredura real do código passa: nenhum módulo de `materias`, `fontes` ou `identidade` importa `cartoes`. O `cursor.py` ainda não existe; a regra vale quando ele nascer (T014).

### Evidência da T006 (`CampoTextoLongo` e `SeloOrigem`)

`frontend/src/componentes/ui/CampoTextoLongo.tsx` (React Aria `TextField` + `TextArea`; rótulo persistente com "(obrigatório)" por texto; contador "N de LIMITE" em *code points* depois do NFC, com aviso por texto "(K acima do limite)" e sem cortar o que o estudante digita; contador e erro associados ao campo por `aria-describedby`; controlado ou não; `Enter` quebra a linha; exporta `contarCaracteres`) e `SeloOrigem.tsx` ("Gerado e verificado", "Editado por você", "Criado por você" e o complemento "Fonte apagada", cada um com texto e ícone próprio; só a primeira origem leva a classe de verificado), mais as classes em `estilos/global.css` (tokens existentes, nenhum valor solto). **Testes (28):** `CampoTextoLongo.test.tsx` e `SeloOrigem.test.tsx`, com `vitest-axe` sem violações (com contador, com erro, nas cinco combinações de origem), contagem de emoji e de caracteres combinados, associação por `aria-describedby`, `Enter` sem enviar o formulário, valor controlado, referência para o foco e marcação do estudante mantida como texto. **Vermelho antes:** os dois arquivos falhavam por módulo ausente. **Verde depois:** frontend com **234 passed** (206 + 28), `eslint`, `tsc` e `prettier --check` limpos (Node 22). **Mutação:** trocando a contagem por `texto.length`, 4 testes caem (emoji, acento combinante e o contador). Achado de lint: a regra `no-misused-spread` recusa `[...texto]`; usei `Array.from`, que também percorre por *code points*.

### Evidência da T008 e da T014 (testes unitários e domínio/cursor)

`backend/src/app/cartoes/dominio.py` (`normalizar_texto_cartao`, `LimitesTexto`, `TextoCartao`, `TextoInvalido`, `validar_limites`, `EstadoInicial`/`estado_inicial`, `rotulo_origem`, `verificado`, `fonte_apagada`) e `cursor.py` (`PosicaoCursor`, `codificar`, `decodificar`, `resumo_dos_filtros`, `CursorInvalido`), mais `CodigoErro.CURSOR_INVALIDO`. **Testes (143 com os de arquitetura):** `tests/unit/cartoes/test_dominio.py` e `test_cursor.py`, com Hypothesis (idempotência da normalização, nenhuma quebra interna perdida, texto aceito sempre cabe no limite, ida e volta do cursor para qualquer posição, texto qualquer nunca passa por cursor). **Vermelho antes:** erro de coleta (módulos ausentes). **Verde depois:** 143 passed em `tests/unit/cartoes` e `tests/arquitetura`; `ruff` limpo.

**Mutações verificadas (cada uma derrubou o teste esperado):** cursor sem o selo; cursor sem o resumo na chave; NFC antes de tirar os controles; contagem em bytes no lugar de *code points*; sem a checagem de texto invisível. A mutação "sem a forma canônica do base64" **sobreviveu** aos primeiros testes e motivou dois testes novos (texto diferente que decodifica aos mesmos bytes; alfabeto padrão no lugar do URL-seguro), que a derrubam.

**Decisões pequenas dentro da DTEC 036/034 (a confirmar):**

- **Cursor mascarado e autenticado.** Em vez de um cursor só em base64 da chave `(criado_em, id)`, ele leva a posição mascarada e um selo HMAC com o segredo da aplicação e o resumo da lista (conta, matéria e filtros). Motivo: a DTEC 034 diz que o cursor guarda "a chave de ordenação", e o `id` interno não pode sair pela API; assim ele também se recusa de outra conta ou lista sem depender de a chave estar em claro. Trocar o segredo invalida os cursores abertos (a interface refaz a consulta).
- **Texto sem caractere visível vale como vazio.** Frente e verso só com caracteres de largura zero, controles de direção ou outros invisíveis são recusados como vazios (e a explicação assim vira `null`), por reaproveitar `tem_caractere_visivel` do núcleo. A DTEC 036 só cita "só espaços"; o texto com caracteres invisíveis **no meio** de texto visível continua voltando literal.
- **Substitutos isolados também saem** na normalização (além dos controles C0 e C1), porque o JSON aceita `\ud800` e o PostgreSQL e o UTF-8 não: sem isso a criação responderia `500`.

### Evidência da T009 a T013, T015 e T016 (US1 no backend)

**Implementação (T015):** `backend/src/app/cartoes/{excecoes,repositorios,servicos,dtos,mapeadores,dependencias,rotas,registros}.py`, composição em `principal.py`, e as rotas `GET /api/v1/cartoes/limites`, `GET` e `POST /api/v1/materias/{materiaId}/cartoes` (com `Location` e `no-store`). O participante dos cartões (`registros.py`) conta ativos e suspensos de qualquer origem, conta e marca as referências na exclusão da fonte (`fonte_id` nulo, cópia mantida, nos dois modos), trava os cartões da matéria por `id` antes da contagem (`travar_para_exclusao_de_materia`, emenda de 15/10/2026 da DTEC 027) e os apaga com a matéria; prioridade 300 no registro do acervo (as dos participantes falsos de teste são 100, 150 e 200) e ordem 300 na exclusão da conta (antes de `fontes`, 400, e `materias`, 500). Logs: `cartao_criado` (`cartao_public_id`, `usuario_public_id`, `materia_public_id`, `com_referencia`), `cartoes_referencia_marcados` e `cartoes_materia_apagados` (só `quantidade`, e só quando maior que zero).

**Testes novos (163 na US1, mais 2 de arquitetura da T005):**

- T009: `tests/integration/cartoes/test_repositorio.py` (18) e `test_participante.py` (16): criação, dono, ordem total com desempate pelo `id`, paginação sem repetir nem pular com criação e exclusão entre as páginas, `total`, situações fora das visíveis (com a fixture `situacoes_da_004` do `conftest.py`), `FOR SHARE` na fonte provado com uma segunda conexão, contagens, impacto, anulação da referência nos dois modos, exclusão da matéria e da conta na ordem do registro, trava por `id`.
- T010: `tests/functional/cartoes/test_us1_criar.py` (33): cenários 1 a 3 da US1, estado gravado de cartão novo e `entrada_estudo_em` crescente, limites exatos e um acima (inclusive emoji e acento combinante), texto normalizado, marcação devolvida literalmente, referência em fonte `pendente`, `falhou` e `concluido`, renomear a fonte sem mudar a cópia, `GET /cartoes/limites`, paginação por cursor.
- T011: seções novas em `tests/functional/fontes/test_us2_exclusao_fonte.py` (7 testes) e `tests/functional/materias/test_us3_organizar.py` (5) que reexecutam a exclusão da fonte e da matéria **com o participante real**: impacto de referência, os dois modos mantendo os cartões com `fonteApagada = true`, CS-004 com cartões reais, suspensos que citam a fonte, `409 impacto_alterado` com cartão criado depois do diálogo, lista de matérias só com ativos e diálogo somando suspensos, exclusão da matéria apagando só os cartões dela e sem barrar por `restrict`, soma sem dupla contagem com o participante falso dos gerados. **Divergência:** a tarefa diz "parametrizar" os testes existentes; os testes antigos continuam com o participante falso porque o que ele simula (cartões gerados aceitos e aguardando revisão) é da 004 e não existe ainda. Os cartões reais entram em testes novos nos mesmos arquivos, que cobrem o que a 003 é dona.
- T012: `tests/security/cartoes/test_cartoes_seguranca.py` (15) e as duas rotas na tabela `CASOS_DE_ISOLAMENTO` (o teste da 002 que confere os nomes passou a ignorar as rotas de cartões, que têm o teste próprio): duas contas, `404` idêntico ao de inexistente, `422` idêntico para fonte alheia, de outra matéria e inexistente, cursor de outra conta, logs sem texto, título nem termo (com captura da saída real), `401`, `403` sem CSRF, origem estranha e `no-store`.
- T013: `tests/adversarial/cartoes/test_criar_adversarial.py` (79) e `test_exclusao_materia_adversarial.py` (2): teto mais um, corpo acima de 64 KiB com e sem `Content-Length`, doze campos extras (origem, verificado, situação, vencimento, estabilidade...) recusados, tipos trocados, `fonteId` que não é UUID, NUL e controles removidos, substituto isolado recusado com `422`, texto só invisível tratado como vazio, `limite` fora da faixa, cursor adulterado ou inventado, e a concorrência: criação com referência durante a exclusão da fonte (uma rodada com atraso e oito sem), cartões da matéria travados durante a contagem da exclusão e criação durante a exclusão da matéria.
- T016: `tests/contrato.py` e `test_contrato_openapi.py` passam a verificar também `docs/specs/003-cartoes-manuais/contracts/openapi.yaml` (inclusive `cursor_invalido` no enum de `Erro`); as cinco operações e o esquema `EdicaoCartaoEntrada` que chegam nas US2 e US3 estão em `OPERACOES_PENDENTES` e `ESQUEMAS_PENDENTES`, e o teste `test_pendentes_ainda_nao_existem` obriga a tirá-las quando existirem. `backend/openapi.json` e `frontend/src/api/{esquema.gerado.d.ts,limites.gerado.ts}` regenerados (o teto da busca sai como `buscaMax: {maximum: 100, minimum: 100}`). **Observação:** a T016 estava fora do pedido ("tasks 4 a 15"), mas é indispensável à T015: sem o contrato no teste e o `openapi.json` regenerado, o CI (`test_openapi_versionado_esta_atualizado` e o `git diff` dos tipos) ficaria vermelho.

**Vermelho antes do verde:** os arquivos novos falharam na coleta (módulos `app.cartoes.*` ausentes) antes da T014 e da T015; depois da T014, as suítes de domínio e cursor ficaram verdes e as de integração, funcionais, segurança e adversariais seguiram vermelhas até a T015.

**Verde depois:** backend no host com `ruff format --check`, `ruff check` e `mypy` limpos e **2063 passed, 1 skipped** em duas execuções completas seguidas (418 s e 414 s); linha de base da rodada: 1701. Frontend: 234 passed (Node 22), `eslint`, `tsc` e `prettier --check` limpos com os tipos regenerados.

**Mutações verificadas (cada uma derrubou o teste esperado, código restaurado e conferido com `cmp`):** sem `FOR SHARE` na fonte (cai o teste das duas conexões); sem o gancho de trava e sem o `FOR UPDATE` dos cartões (cai o teste adversarial dos cartões travados); `ao_excluir_fonte` sem efeito; sem a conversão da FK da matéria em `404` (cai o teste da criação durante a exclusão da matéria); listagem sem filtro de dono; listagem sem filtro de situação; suspensos contados como ativos. A corrida da criação com a exclusão da fonte tem **duas defesas independentes** (a fonte lida com `FOR SHARE` e a conversão da violação da FK composta em `422 fonteId`): cada uma sozinha mantém o resultado correto, e sem as duas a criação responde `500` (verificado). Por isso o teste adversarial só cai quando as duas somem, e o `FOR SHARE` também é provado diretamente pelo teste de integração.

**Achados:**

- O SQLAlchemy 2.1 marca `Result.tuples()` como obsoleto, e o `filterwarnings = error` do projeto transforma isso em falha: usei o desempacotamento direto da linha.
- O Pydantic recusa o substituto isolado (`\ud800`) com `422 Valor inválido.` antes do domínio; a remoção de substitutos na normalização ficou como segunda defesa para quem chamar o domínio de outro caminho. O teste adversarial registra os dois comportamentos.
- Um teste meu de segurança acusou vazamento de um termo que era só a URL do próprio cliente de teste no log do `httpx`; o log do servidor registra apenas a rota (modelo `/materias/{materiaId}/cartoes`), e o teste passou a usar um cursor sem o texto sentinela.

## Pendências

- ~~T017 a T027~~: concluídas na rodada 4 (abaixo). **T028 a T045** (US3, US4 e fase final): não iniciadas; a próxima é a T028 (testes funcionais da US3).
- **Rodada final com leitor de tela (decisão de 15/10/2026):** painel, lista, filtros e diálogo de exclusão da 003 entram na rodada única do fim do projeto, junto com os da 001 e da 002 (T042 da 003).
- **Caso de falha da migração sem permissão para `CREATE EXTENSION`:** não reproduzido aqui (papel de teste superusuário e `unaccent` *trusted*).
- ~~T007~~: resolvida na rodada 3 (abaixo).
- **Reverificações de outras specs (obrigações do plano):** a entrada do cartão novo na lição, o suspenso fora da lição e o reativado com o vencimento anterior são reverificados pela 005 com lições reais; as revisões e o XP preservados, pela 005 e pela 006.
- ~~Teste de concorrência da edição durante a revisão (T021)~~: feito na rodada 4. Os de suspender e excluir seguem para a US3.
- **US2-2 com cartão gerado de verdade:** sem a 004, coberto só pelos testes (fábrica com `gerado_verificado`), como prevê o quickstart; a 004 reexecuta com geração real.

## Rodada 3 (27/10/2026): atualização da `develop` e T007

- **Atualização:** a `develop` recebeu um merge feito por Artur Lins, que resolveu à mão um conflito no `pull` (`64a5b32`), trazendo o guia e o script do progresso no README (`scripts/atualizar_readme_progresso.py`, hook `.githooks/pre-commit`, job `readme` do CI e a regra nova no `AGENTS.md`). Puxei com `git pull --rebase`, sem conflito local; ativei o hook (`git config core.hooksPath .githooks`) e `python scripts/atualizar_readme_progresso.py --check` passou. Passo a incluir o `README.md` regenerado em todo commit que marcar tarefa.
- **Evidência da T007:** a saída colada por Artur Lins mostra o `docker compose up -d --build --wait` no Docker Desktop: imagens construídas e `migrate` terminado, com `worker`, `api`, `web` e `db` `Healthy`. No `compose.yaml`, `api` e `worker` dependem do `migrate` com `condition: service_completed_successfully`, então a `0004_cartoes` (que começa por `CREATE EXTENSION IF NOT EXISTS unaccent`) foi aplicada: se a extensão faltasse, a migração falharia e a `api` não subiria. O `\dx` literal do `psql` **não veio na saída colada**; a extensão está provada de forma indireta aqui e, no CI, pelo teste de migração e pelos testes de busca da US4 (a vir). Se Artur Lins quiser a prova direta: `docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dx"'`. A integração contínua já estava verde na execução 30.
- **Resultado:** T007 marcada `[x]`; T001 a T016 prontas. A próxima é a T017.

## Rodada 4 (27/10/2026): T017 a T027

### Prompts

```text
continue com as tasks 17 a 27 da spec 003
```

```text
continue, mudei  o modelo para o opus
```

### Evidência da T017 e da T018 (interface da US1)

- **Arquivos:** `frontend/src/api/cartoes.ts` (consultas de limites e da lista paginada com `useInfiniteQuery`, criação), `funcionalidades/cartoes/{AbaCartoes,ItemCartao,PainelCartao,esquemas,textos}.ts(x)`, a rota `rotas/_autenticado/materias/$materiaId.cartoes.tsx`, a navegação "Fontes" e "Cartões" em `$materiaId.tsx` (a área Cartões tem endereço próprio e sobrevive ao recarregamento e ao Voltar), estilos em `estilos/global.css` e `routeTree.gen.ts` regenerado. O `Botao` passou a aceitar `ref` (React 19), para o foco ir a "Continuar editando" na pergunta de descarte.
- **Comportamento:** painel lateral sobre o `Modal` do React Aria, com o foco na frente ao abrir; `Ctrl/⌘+Enter` salva e deixa o painel aberto, vazio e com o foco na frente, anunciando "Cartão criado." numa região viva; "Salvar" fecha e o foco volta ao acionador; `Enter` quebra a linha; `Esc` fecha sem perguntar se nada foi digitado e, com texto, mostra a pergunta "Descartar o que você digitou?" (`alertdialog`); validação no envio com a mesma contagem do servidor (*code points* depois de tirar as pontas) e os limites de `GET /cartoes/limites`; erros do `422` junto do campo (inclusive `fonteId` na escolha da fonte), com os valores mantidos e o foco no primeiro inválido; um único envio enquanto salva; erro de rede mantém o rascunho. A lista mostra frente e verso como texto (`pre-wrap`), o `SeloOrigem`, a situação, a referência com "Fonte apagada", o total, o estado vazio com "Criar o primeiro cartão" e "Carregar mais". Depois de criar, a lista de cartões é invalidada, e a contagem de cartões ativos é gravada no cache da lista de matérias e da matéria (`setQueryData`) antes de a rede responder.
- **Testes (23):** `PainelCartao.test.tsx` (14), `AbaCartoes.test.tsx` (7) e `AbasMateria.test.tsx` (2), com `vitest-axe` sem violações no painel aberto, com erro, na pergunta de descarte, na lista e na página com as abas. **Vermelho antes:** os dois primeiros arquivos falhavam por módulos ausentes; na primeira implementação, 3 casos falharam (foco depois de "Salvar e criar outro" e dois artefatos do próprio teste), e depois 2 casos de `Esc` falharam porque o `onKeyDown` de um campo do React Aria não deixa o evento subir: o tratador passou a chamar `continuePropagation()` para as teclas que não usa. **Verde depois:** frontend com **257 passed** (234 + 23), `eslint`, `tsc`, `prettier --check` e `vite build` limpos (Node 22).

### Evidência da T019 (US1 no navegador real e CS-001)

**Ambiente:** PostgreSQL 16 local com a `0004` aplicada, API (`uvicorn`), worker e Vite (`npm` com Node 22) no host, e o Chromium do Playwright global. Conta `@exemplo.com` e fonte fictícia "Citologia" (TXT) criadas pela própria API, na sessão do navegador. O script de verificação ficou no diretório temporário da sessão e não foi versionado.

**Passos 1 a 7 do quickstart (33 de 33 verificações):** aba Cartões vazia com "Criar o primeiro cartão" e `aria-current="page"`; painel aberto pelo teclado com o foco na frente e os contadores "0 de 1.000", "0 de 2.000" e "0 de 1.000" vindos do servidor; primeiro cartão com a explicação em duas linhas salvo com `Ctrl+Enter`, o painel aberto, vazio e com o foco na frente, e o item "Ativo" e "Criado por você" na lista; frente só com espaços e verso com 2.001 caracteres recusados junto do campo, com os valores preservados; cartão com a fonte "Citologia" mostrado como "Criado por você", com a fonte e sem "Gerado e verificado"; `<script>alert(1)</script>` e `<img onerror>` exibidos literalmente, sem nenhum diálogo aberto pelo navegador nem `img` criada; `Esc` com o painel vazio fecha sem perguntar e o foco volta ao acionador; recarregar mantém a aba. **CS-001:** cinco cartões criados só pelo teclado (`Enter` no acionador, digitação, `Tab`, `Ctrl+Enter` e `Esc` no fim) em 1,2 s na execução automatizada, com o foco de volta à frente depois das cinco gravações. A execução automatizada prova a operação só pelo teclado e o fluxo; o tempo de uma pessoa (meta de 3 minutos) fica para o teste guiado com pessoas.

**Acessibilidade (axe, WCAG 2.2 AA):** sem violações na aba vazia, na lista e no painel aberto (vazio e com erro), nos temas claro e escuro, a 1100 px e a 320 px, sem rolagem horizontal a 320 px e com "Salvar", "Salvar e criar outro" e "Cancelar" dentro da tela. **Achado e correção (`fix(cartoes)`):** a 320 px no tema claro, o axe acusou contraste de 1,59:1 e 1,89:1 em dois elementos do fim do painel; o painel esticava até a altura da tela (`align-items: stretch` do flex) e o conteúdo mais alto ficava sobre a sobreposição escura, sem o fundo. Com `align-self: flex-start`, o painel cresce com o conteúdo (altura 1.035 px contra 768 px antes) e as violações sumiram nos dois temas.

**Banco e logs:** os 8 cartões da conta estão `criado`, `ativo`, `aprendizado`, passo 0, sem última revisão e com `vencimento = entrada_estudo_em`, na ordem de criação; a explicação guardou a quebra de linha, e o cartão com a fonte guardou a cópia "Citologia". O log da API tem 24 eventos `cartao_criado` (três execuções) só com `cartao_public_id`, `usuario_public_id`, `materia_public_id` e `com_referencia`, e nenhuma ocorrência dos textos dos cartões nem do título da fonte.

**Testes da US1 no backend:** `tests/functional/cartoes`, `tests/security/cartoes` e `tests/adversarial/cartoes`: **129 passed**.

### Evidência da T020 a T024 (US2 no backend)

- **Testes (104):** `tests/unit/cartoes/test_edicao.py` (34: validação só dos campos enviados, explicação nula ou vazia removendo, `houve_mudanca` depois da normalização, `origem_apos_edicao` nas três origens); `tests/integration/cartoes/test_edicao_fsrs.py` (17: as seis colunas do FSRS iguais em cada estado e campo editado, edição sem mudança sem escrita, o `UPDATE` capturado sem coluna do FSRS, revisão simulada numa segunda conexão segurando a linha durante a edição e as duas sobrevivendo, e duas edições simultâneas de campos diferentes sem uma desfazer a outra); `tests/functional/cartoes/test_us2_editar.py` (16: cenários 1 a 3, consulta, `gerado_verificado` → `editado` só com mudança, referência mantida, CS-002 com 20 cartões de todos os estados); `tests/security/cartoes/test_editar_seguranca.py` (9) e as duas rotas novas em `CASOS_DE_ISOLAMENTO` (o teste de nomes passou a procurar em todos os módulos de `tests.security.cartoes`); `tests/adversarial/cartoes/test_editar_adversarial.py` (28: campos extras, nulos, tipos, tetos, corpo vazio, corpo que não é objeto, acima de 64 KiB).
- **Implementação:** `dominio.py` (`validar_edicao`, `houve_mudanca`, `origem_apos_edicao`, com `validar_limites` reescrita sobre os mesmos auxiliares), `repositorios.py` (`buscar` com `FOR UPDATE OF cartoes` opcional e `editar` com um único `UPDATE` de `frente`, `verso`, `explicacao`, `origem` e `atualizado_em`), `servicos.py` (`consultar` e `editar`, logs `cartao_editado` e `cartao_edicao_sem_mudanca` só com identificadores públicos), `dtos.py` (`EdicaoCartaoEntradaDTO` com `minProperties: 1` no esquema e frente e verso que podem faltar mas não ser nulos) e as rotas `GET` e `PATCH /cartoes/{cartaoId}`. As pendências do teste de contrato saíram, e `openapi.json` e os tipos do frontend foram regenerados.
- **Vermelho antes:** sem o código da T024 (`git stash` só de `app/cartoes`, contrato e `openapi.json`), os testes unitários e de integração falharam na coleta e os funcionais, de segurança e adversariais deram **50 failed, 18 passed**. Na primeira execução com o código, 5 falharam por erro dos próprios testes: "remover a explicação" de um cartão sem explicação não é mudança (a semeadura passou a garantir uma explicação) e corpo que não é objeto JSON segue a convenção da criação (`400` ou `422`, teste separado). O corpo `{}` dava `400` porque o erro de um validador de modelo não tem campo e cai em "corpo ilegível"; a verificação passou para o DTO e responde `422 dados_invalidos`.
- **Mutações (cada uma derrubou o teste esperado e o código foi restaurado):** `UPDATE` que também grava `vencimento` (19 falhas); `origem_apos_edicao` sem olhar a mudança (1); gerado nunca virando editado (4); sem o `FOR UPDATE`. **Achado:** sem o `FOR UPDATE`, todos os testes passavam, porque a edição espera a revisão no próprio `UPDATE` e as escritas são disjuntas. O que a trava protege é outra edição simultânea, que leria a frente antiga e a regravaria; o teste das duas edições simultâneas foi acrescentado e cai sem a trava.
- **Verde:** suítes da US2 e de contrato e isolamento com **510 passed**; `ruff` e `mypy` limpos.

### Evidência da T025 e da T026 (interface da US2)

- **Arquivos:** `api/cartoes.ts` (`editarCartao`), `PainelCartao.tsx` com o modo edição (prop `cartao`: título "Editar cartão", valores atuais, só os campos alterados enviados, explicação vazia como `null`, nenhuma chamada se nada mudou, `Ctrl/⌘+Enter` salva e fecha, sem "Salvar e criar outro" nem escolha de fonte, pergunta "Descartar as alterações?" só quando algo mudou, cartão trocado nas páginas carregadas com `setQueryData` e a lista invalidada), `ItemCartao.tsx` (botão "Editar" com nome acessível "Editar o cartão: <início da frente>"), `AbaCartoes.tsx` e um estilo.
- **Testes (6) em `EdicaoCartao.test.tsx`:** valores atuais e axe; `Ctrl+Enter` envia só `{verso, explicacao: null}` e fecha; selo "Gerado e verificado" trocado por "Editado por você"; salvar sem mudança sem chamada à API; `422` junto da frente com o valor mantido, o foco nela e axe; `Esc` sem mudança fecha e com mudança pergunta. **Vermelho antes:** 6 failed. **Verde depois:** **263 passed** (257 + 6), `eslint`, `tsc`, `prettier --check` e `vite build` limpos.

### Evidência da T027 (US2 no navegador real e CS-002)

**Ambiente:** o mesmo da T019, com a API reiniciada no código novo. Conta `@exemplo.com` e quatro cartões criados pela API; para o CS-002 ter estados variados, um script local gravou no banco estados do FSRS como os de depois de revisões (revisão, reaprendizado, aprendizado no passo 1), já que só a 005 escreve neles. Scripts no diretório temporário da sessão, não versionados.

**21 de 21 verificações:** editar pelo teclado (`Enter` no "Editar", foco na frente, valores atuais, sem "Salvar e criar outro" nem fonte), acrescentar texto e `Ctrl+Enter`: o painel fecha, o texto novo aparece, a origem continua "Criado por você" e o foco volta ao "Editar" do cartão; abrir e salvar sem mudar nada não altera `atualizado_em` no banco (cenário 3); remover a explicação grava `NULL`; `Esc` com alteração pergunta "Descartar as alterações?" e descartar não grava; frente com 1.001 caracteres fica marcada junto do campo com o painel aberto; axe (WCAG 2.2 AA) sem violações na lista e no painel (claro a 1100 px, com erro, e escuro a 320 px), sem rolagem horizontal a 320 px. **CS-002:** depois das 4 edições pelo navegador e de mais 20 pela API, `estado_fsrs`, `passo`, `estabilidade`, `dificuldade`, `vencimento` e `ultima_revisao` dos quatro cartões estão iguais aos de antes (100%). **Logs:** 22 eventos `cartao_editado` (2 do navegador com mudança e 20 da API) só com identificadores públicos e `origem_mudou`, e nenhuma ocorrência dos textos editados. A US2-2 (gerado → editado) fica nos testes, como prevê o quickstart.

