# Guia: padrões de implementação

**Origem:** seções agnósticas de stack do brainstorming inicial (`docs/init/SKILL.md`, hoje [`../base-specs/`](../base-specs/README.md)), migradas em 29/09/2026; revisto em 12/10/2026.
**Stack:** [arquitetura](../arquitetura/README.md) e DTEC 002 a 014 do [`research.md`](../research.md), aprovadas em 12/10/2026, mais as DTEC 015 a 018, propostas no [plano da spec 001](../specs/001-conta-acesso/plan.md). A estrutura de pastas está planejada nesse plano. Os comandos e os endereços do OpenAPI e do Swagger UI são acrescentados aqui quando a estrutura base do código for criada; até lá, valem os do [quickstart da 001](../specs/001-conta-acesso/quickstart.md).

## Arquitetura MVC

| Camada | Responsabilidade | Limite |
|---|---|---|
| Model | Entidades, invariantes, regras de domínio e acesso aos dados | Não depende de componentes visuais nem de detalhes HTTP |
| View | Interface, apresentação, interação e validações de experiência | Não acessa o banco nem decide pontuação, agendamento ou autorização |
| Controller | Recebe requisições, valida a entrada, aciona casos de uso e devolve respostas | Não concentra processamento de arquivos nem regras de negócio |

- Organize por domínio (os domínios estão na [arquitetura](../arquitetura/README.md#51-organização-mvc-por-domínio)) mantendo as camadas identificáveis em cada módulo.
- Serviços e repositórios são permitidos quando reduzem acoplamento. Eles complementam o MVC, não o substituem.
- Com front e backend separados, o frontend é a View. Não crie páginas de servidor só para cumprir o MVC.
- Registre no `plan.md` o mapeamento das camadas para diretórios reais.

### Camadas de cada domínio do backend ([DTEC 018](../research.md#decisão-dtec-018-camadas-do-backend-dto-mapper-repositório-e-exceções))

A estrutura de pastas completa está no [plano da spec 001](../specs/001-conta-acesso/plan.md#estrutura-do-repositório). Cada domínio em `backend/src/app/<dominio>/` usa os mesmos arquivos:

| Arquivo | Camada MVC | Responsabilidade | Não pode importar |
|---|---|---|---|
| `rotas.py` | Controller | Router fino: recebe o DTO, chama um serviço e devolve o DTO | `modelos`, `repositorios`, SQLAlchemy |
| `dtos.py` | (transporte) | DTOs Pydantic de entrada e saída, camelCase no JSON, `extra="forbid"` na entrada | `modelos`, FastAPI |
| `mapeadores.py` | (conversão) | Funções puras: DTO → comando de domínio; entidade → DTO | FastAPI, sessão do banco |
| `servicos.py` | Model | Casos de uso; controlam a transação e o enfileiramento | FastAPI, `dtos` |
| `dominio.py` | Model | Regras puras, testáveis sem banco e sem HTTP | SQLAlchemy, FastAPI |
| `repositorios.py` | Model | Consultas; todo método de recurso de estudante exige `usuario_id` | FastAPI, `dtos` |
| `modelos.py` | Model | Entidades SQLAlchemy | todo o resto |
| `excecoes.py` | (erros) | Exceções do domínio, subclasses de `ErroAplicacao` | — |

- Nenhuma entidade do ORM sai pela API: a resposta é sempre um DTO produzido por um mapeador.
- Um recurso de outro estudante é buscado com o dono na própria consulta e, se não existir, vira `RecursoNaoEncontrado` (404 idêntico ao de inexistente, [DTEC 019](../specs/001-conta-acesso/research.md#decisão-dtec-019-garantia-do-isolamento-entre-estudantes)).
- Toda rota com identificador no caminho entra na tabela do teste de isolamento (`tests/security/test_isolamento_rotas.py`); sem isso, a integração contínua falha.
- Todo domínio com dados de estudante registra sua função `apagar_dados_usuario` no registro de exclusão do núcleo ([DTEC 021](../specs/001-conta-acesso/research.md#decisão-dtec-021-exclusão-da-conta-e-chaves-de-armazenamento-por-usuário)).
- Toda chave de objeto no armazenamento começa por `usuarios/{public_id_usuario}/`.
- Um teste de arquitetura (`tests/arquitetura/`) verifica as importações proibidas.

## Nomenclatura e código

- Identificadores do domínio em português, sem acentos, na convenção de caixa da linguagem (ex.: `enviarMaterial`, `agendarRevisao`, `calcularSequencia`).
- Nomes curtos que revelam a intenção. Evite abreviações obscuras e nomes genéricos (`dados`, `info`, `util`).
- Preserve os nomes exigidos por bibliotecas, protocolos e contratos externos. Não traduza APIs de terceiros.
- Mantenha funções coesas, dependências explícitas e cada regra de negócio em um único lugar. Não crie abstração sem uso concreto.
- Comente apenas decisões não evidentes, invariantes delicadas ou limitações externas. O comentário explica o motivo, não narra o código.

## Textos

- Use UTF-8 com normalização Unicode NFC.
- Remova espaços nas extremidades dos campos simples. Preserve parágrafos, acentos, fórmulas e formatação relevante dos materiais e dos flashcards.
- Comparação sem diferença de caixa ou acento só em chaves de busca. Nunca normalize senhas.
- Busca por texto sem diferenciar maiúsculas e acentos: `lower(unaccent(coluna)) LIKE` com o termo escapado (`%`, `_`, `\`) e sempre como parâmetro, numa única função do repositório ([DTEC 033](../research.md#decisão-dtec-033-busca-sem-diferenciar-maiúsculas-e-acentos)).
- O conteúdo dos materiais é dado, nunca instrução (Princípio II).

## Datas

- Persista instantes em UTC e transporte em ISO 8601 com fuso explícito. Datas sem horário usam `YYYY-MM-DD`.
- Exiba no padrão brasileiro, no fuso do usuário.
- Sequência diária, meta diária e agendamento de revisões são calculados no fuso do usuário, **com testes de fronteira** (virada do dia, mudança de fuso, horário de verão).

## Validações e limites

- O backend valida obrigatoriedade, tipo, comprimento, intervalo e vínculo entre entidades. A interface replica os limites relevantes, e os valores ficam centralizados em um único ponto.
- Verifique propriedade e autorização em **cada** operação.
- Valide arquivos por extensão, tipo real do conteúdo, tamanho e quantidade. Não confie no navegador. Armazene com identificador interno e acesso controlado.
- Abra e extraia arquivos enviados pelo estudante **somente** por `nucleo/isolamento.executar_isolado`, em subprocesso com tempo limite e teto de memória ([DTEC 024](../research.md#decisão-dtec-024-execução-isolada-do-processamento-de-arquivos-não-confiáveis)). No envio, grave o objeto antes da linha e apague-o se a transação falhar; na exclusão de um item isolado, apague o objeto antes das linhas ([DTEC 025](../research.md#decisão-dtec-025-consistência-entre-o-armazenamento-de-objetos-e-o-banco)).
- Um domínio que tenha dados ligados a fontes ou matérias registra um participante da exclusão em `nucleo/participantes_acervo.py` ([DTEC 027](../research.md#decisão-dtec-027-participantes-da-exclusão-de-fontes-e-matérias)), além da função `apagar_dados_usuario` do registro de exclusão da conta (DTEC 021).
- Nenhum limite pendente vira número arbitrário no código: registre-o como questão aberta.

## Erros e respostas da API

- Converta as exceções em respostas HTTP em um ponto central. O corpo de erro é consistente: `codigo`, `mensagem`, `campos` (quando aplicável) e `idRequisicao`.
- Os códigos seguem a semântica HTTP: 400 (requisição malformada), 401 (não autenticado), 403 (acesso negado), 404 (não encontrado), 409 (conflito, incluindo idempotência divergente), 422 (entrada semanticamente inválida) e 500 (falha inesperada).
- Nunca retorne stack trace, credenciais ou detalhes internos. Nunca esconda uma falha retornando sucesso vazio.
- **Hierarquia única** em `backend/src/app/nucleo/erros.py` ([DTEC 018](../research.md#decisão-dtec-018-camadas-do-backend-dto-mapper-repositório-e-exceções)): `ErroAplicacao(codigo, mensagem, status, campos)` e as subclasses `RequisicaoMalformada` (400), `NaoAutenticado` (401), `AcessoNegado` (403), `RecursoNaoEncontrado` (404), `Conflito` (409), `EntradaInvalida` (422) e `LimiteExcedido` (429, com `Retry-After`). A spec 002 acrescenta `ConteudoMuitoGrande` (413), para arquivos acima do limite ([DTEC 028](../specs/002-materias-fontes/research.md#decisão-dtec-028-validação-do-arquivo-no-envio)).
- **Quem lança o quê:** domínio e serviços lançam só essas exceções. O repositório converte os erros do banco (ex.: violação de unicidade) em `Conflito`. Os handlers centrais convertem `ErroAplicacao`, erros de validação do Pydantic e exceções inesperadas (500, com a pilha só no log) no corpo padrão.
- **Códigos estáveis:** o `codigo` é estável e em snake_case (ex.: `email_em_uso`). As specs acrescentam códigos, mas não renomeiam nem removem os existentes.
- **Sem `except` vazio:** toda exceção capturada é convertida ou registrada e relançada.
- **JSON em camelCase** (`idRequisicao`, `metaDiaria`); o Python continua em snake_case, e a conversão fica nos DTOs.

## IA: geração e chat

- As credenciais e a integração com o provedor ficam somente no backend.
- A saída é estruturada e validada pelo código antes da publicação. A sustentação é verificada contra os trechos de origem (Princípio I).
- Flashcards e questões derivadas usam os mesmos trechos originais como fonte. Um flashcard não é gerado a partir de outro conteúdo gerado.
- Registre o modelo, a versão das instruções (*prompt* do sistema) e os trechos usados em cada geração.
- O chat recupera trechos apenas dos materiais do próprio usuário, cita os trechos usados e declara quando não há evidência.
- Timeouts, indisponibilidade do provedor e respostas malformadas falham de forma controlada e visível ao usuário.
- Trabalhos longos (extração, indexação, geração) rodam em segundo plano, com estados observáveis (pendente, processando, concluído, falhou).

## Gamificação e revisão

- Correção, XP, sequência, agendamento de revisões, progresso e conquistas são calculados no servidor (Princípio IV).
- Todo evento que gera efeito (resposta, revisão, conclusão) carrega uma identidade idempotente. Registre o evento e seus efeitos na mesma transação.
- Uma conquista nunca é concedida duas vezes no mesmo contexto.
- Nenhum gabarito ou verso de cartão é enviado ao cliente antes do momento permitido.

## API e OpenAPI

- Mantenha a especificação OpenAPI coerente com as respostas reais, com Swagger UI. Prefira gerá-la a partir dos contratos do código.
- Documente autenticação, upload multipart, paginação, enumerações, limites, exemplos, erros e consulta de tarefas assíncronas.
- Listagens sem limite natural usam paginação por cursor opaco: resposta `{itens, proximoCursor, total}`, parâmetros `cursor` e `limite` (padrão 50, de 1 a 100), ordem total com o `id` como desempate e `422 cursor_invalido` para cursor adulterado ([DTEC 034](../research.md#decisão-dtec-034-paginação-das-listagens-por-cursor)). Listagens limitadas por cota (ex.: matérias e fontes) dispensam paginação.
- Separe o contrato "antes da resposta" do contrato "correção".

## Testes

- Os testes do backend usam pytest ([DTEC 001](../research.md#decisão-dtec-001-ferramenta-de-testes-do-backend)), classificados pelos marcadores `unit`, `integration`, `functional`, `security` e `adversarial`, conforme a regra 17 do [`AGENTS.md`](../../.agents/AGENTS.md).
- Teste regras e invariantes de negócio, não a implementação.
- São obrigatórios os testes negativos de isolamento entre usuários, de reenvio idempotente, de fronteira de datas e de falha do provedor de IA.
- O comportamento da IA é avaliado com um conjunto de casos revisado por pessoa responsável (Princípio V).

## Dependências

- Antes de adicionar uma dependência, confirme que a stack aprovada não resolve o problema e avalie necessidade, manutenção, licença e sobreposição de responsabilidades.
- Não adicione frameworks, bancos, filas ou serviços residentes por conveniência: cada serviço novo na VPS precisa de uma DTEC (restrição de custo da [constituição](../constitution.md)).
- Fixe as versões no arquivo de dependências e registre licenças restritivas (ex.: AGPL do PyMuPDF, [DTEC 009](../research.md#decisão-dtec-009-extração-de-texto)).

## Docker

- Todo serviço tem imagem própria e sobe via orquestração declarativa (ex.: arquivo Compose), com um comando documentado no `quickstart.md`.
- As imagens não contêm segredos. A configuração vem de variáveis de ambiente, documentadas em `.env.example`.

### Comandos e endereços (verificados na spec 001)

Copie `.env.example` para `.env` e preencha `POSTGRES_PASSWORD` e `SEGREDO_APLICACAO` (no mínimo 32 bytes). O `.env` é ignorado pelo git.

| O quê | Comando |
|---|---|
| Subir tudo | `docker compose up -d --build --wait` (o `migrate` roda uma vez e termina; `db`, `api`, `worker` e `web` ficam saudáveis) |
| Testes do backend | `docker compose up -d --wait db` e `docker compose run --rm --no-deps api uv run --frozen pytest` (acrescente `-m security` para um marcador, `--cov` para a cobertura) |
| Qualidade do backend | `docker compose run --rm --no-deps api uv run --frozen ruff format --check .`, `... ruff check .` e `... mypy` |
| Contrato do backend | `docker compose run --rm --no-deps api uv run --frozen python -m app.exportar_openapi`, depois `git diff --exit-code backend/openapi.json` |
| Frontend | `docker compose run --rm --no-deps web npm run format:check`, `lint`, `typecheck` e `test:cobertura` |
| Tipos da API | `docker compose run --rm --no-deps --user root web npm run gerar:api`, depois `git diff --exit-code frontend/src/api/` |

- Os mesmos comandos rodam na integração contínua ([`ci.yml`](../../.github/workflows/ci.yml)); o `--user root` existe porque, no runner, o diretório montado pertence a outro usuário.
- Endereços: interface em `http://localhost:5173` (o Vite repassa `/api` para a API), API e Swagger UI em `http://localhost:8000` (`/health/ready`, `/api/docs` só em desenvolvimento). O banco não publica porta; use `docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"`.
- A suíte do backend cria e migra o banco `plataforma_teste` no mesmo Postgres; os testes de contrato leem `docs/specs/NNN/contracts/openapi.yaml` pelo volume `./docs:/docs:ro`.
- O `worker` precisa carregar as tarefas dos domínios (`carregar_tarefas()` em `app/worker.py`, lista em `nucleo/fila.py`): sem isso ele sobe saudável e não executa nenhuma tarefa de domínio.
