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

Em andamento. Escopo desta rodada: T001 a T003 (Fase 1 e o início da Fase 2); T004 a T007 e as histórias ficam para as próximas rodadas.

## Alterações humanas

Pendente de revisão.

## Verificação

Em andamento.

### Evidência da T001 (limites dos cartões)

`tests/unit/nucleo/test_configuracao.py` ganhou 15 casos novos (padrões 1000/2000/1000, aceitação de 1 e do teto, recusa de 0, -1 e teto + 1 nos três campos, leitura das variáveis `CARTAO_*` do ambiente e conferência do `.env.example`). **Vermelho antes:** 15 falhas (campos inexistentes). **Verde depois:** 73 passed no arquivo; `ruff format --check`, `ruff check` e `mypy` limpos. Os tetos (4.000, 8.000 e 4.000) ficaram em constantes do módulo (`CARTAO_FRENTE_TETO` etc.) para o DTO, o domínio e o `CHECK` reutilizarem.

## Pendências

- T007 (verificar a base com `docker compose up -d --build --wait`) depende de Artur Lins no Docker Desktop.
