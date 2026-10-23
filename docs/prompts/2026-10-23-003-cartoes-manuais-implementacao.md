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

Escopo desta rodada: **T001 a T003** concluídas com evidência. A 003 passa a **Implementando**; T004 a T045 seguem pendentes.

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
- **Frontend:** não houve mudança de código; `npm run lint` passa e falha com o arquivo temporário da T002.


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

## Pendências

- **T004 a T045** (fábrica de cartões, testes de arquitetura, `CampoTextoLongo` e `SeloOrigem`, histórias US1 a US4 e fase final): não iniciadas nesta rodada, por decisão do pedido ("tasks 1 a 3").
- **Rodada final com leitor de tela (decisão de 15/10/2026):** painel, lista, filtros e diálogo de exclusão da 003 entram na rodada única do fim do projeto, junto com os da 001 e da 002 (T042 da 003).
- **Caso de falha da migração sem permissão para `CREATE EXTENSION`:** não reproduzido aqui (papel de teste superusuário e `unaccent` *trusted*).
- T007 (verificar a base com `docker compose up -d --build --wait`) depende de Artur Lins no Docker Desktop.
