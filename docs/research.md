# Pesquisa e decisões técnicas do projeto

**Funcionalidade:** projeto (decisões transversais, válidas para todas as specs)  
**Data:** 29/09/2026 (DTEC 001); 12/10/2026 (DTEC 002 a 014, [registro](prompts/2026-10-12-alinhamento-produto-arquitetura.md))

Este arquivo registra as decisões técnicas que valem para o projeto inteiro, no formato do [modelo de `research.md`](sdd_guidelines/modelos/research.md). Decisões específicas de uma funcionalidade ficam no `research.md` da pasta da spec correspondente (`docs/specs/NNN-nome-curto/`). As questões técnicas ainda abertas estão em [`produto/pendencias.md`](produto/pendencias.md) e, quando decididas, entram aqui como novas decisões `DTEC`.

A visão de conjunto das decisões, por estágio (MVP, final acadêmico e referência pós-acadêmica), está em [`arquitetura/README.md`](arquitetura/README.md). As alternativas mais robustas não adotadas, com custo e gatilho de adoção, estão em [`arquitetura/referencia-pos-academica.md`](arquitetura/referencia-pos-academica.md).

**Critério comum às DTEC 002 a 014:** o deploy do final acadêmico é obrigatório e pago pela equipe, numa VPS de 2 a 4 GB de RAM (RQ-09 da [base de especificação](base-specs/spec.md)). Entre alternativas tecnicamente equivalentes, vence a que não acrescenta serviço residente na VPS.

| Decisão | Título | Status |
|---|---|---|
| [DTEC 001](#decisão-dtec-001-ferramenta-de-testes-do-backend) | Ferramenta de testes do backend | Decidida por Artur Lins em 29/09/2026; aprovação da equipe pendente ([VAL-05](produto/pendencias.md#val-05-aprovação-das-regras-de-git-e-testes)) |
| [DTEC 002](#decisão-dtec-002-framework-do-backend) | Framework do backend | Aprovada em 12/10/2026; encerra QA-18 ([VAL-06](produto/pendencias.md#val-06-aprovação-da-arquitetura-e-das-dtec-002-a-014)); emenda do driver (psycopg 3) aprovada em 12/10/2026 com o plano da 001 |
| [DTEC 003](#decisão-dtec-003-autenticação) | Autenticação | Aprovada em 12/10/2026; substitui a direção anterior (Keycloak) e encerra QA-25 |
| [DTEC 004](#decisão-dtec-004-frontend) | Frontend | Aprovada em 12/10/2026; encerra QA-29 |
| [DTEC 005](#decisão-dtec-005-banco-de-dados-único) | Banco de dados único | Aprovada em 12/10/2026 |
| [DTEC 006](#decisão-dtec-006-fila-e-processamento-assíncrono) | Fila e processamento assíncrono | Aprovada em 12/10/2026 |
| [DTEC 007](#decisão-dtec-007-llm-e-framework-de-agentes) | LLM e framework de agentes | Aprovada em 12/10/2026; framework do final acadêmico em reavaliação (QA-31) |
| [DTEC 008](#decisão-dtec-008-embeddings-e-reranking) | Embeddings e reranking | Aprovada em 12/10/2026; com DTEC 007, encerra QA-22 |
| [DTEC 009](#decisão-dtec-009-extração-de-texto) | Extração de texto | Aprovada em 12/10/2026 |
| [DTEC 010](#decisão-dtec-010-armazenamento-de-arquivos) | Armazenamento de arquivos | Aprovada em 12/10/2026; revisada no mesmo dia (adaptador por ambiente: disco local no MVP, R2 no final) |
| [DTEC 011](#decisão-dtec-011-observabilidade-e-avaliação-da-ia) | Observabilidade e avaliação da IA | Aprovada em 12/10/2026 |
| [DTEC 012](#decisão-dtec-012-algoritmo-de-repetição-espaçada) | Algoritmo de repetição espaçada | Aprovada em 12/10/2026 |
| [DTEC 013](#decisão-dtec-013-hospedagem-e-operação) | Hospedagem e operação | Aprovada em 12/10/2026; VPS e domínio pendentes (QA-11) |
| [DTEC 014](#decisão-dtec-014-complementos-de-teste) | Complementos de teste | Aprovada em 12/10/2026; encerra QA-28 |
| [DTEC 015](#decisão-dtec-015-roteamento-e-estado-do-servidor-no-frontend) | Roteamento e estado do servidor no frontend | Aprovada em 12/10/2026 com o plano da 001 |
| [DTEC 016](#decisão-dtec-016-primitivas-acessíveis-da-interface) | Primitivas acessíveis da interface | Aprovada em 12/10/2026 com o plano da 001 |
| [DTEC 017](#decisão-dtec-017-integração-contínua-e-verificação-local) | Integração contínua e verificação local | Aprovada em 12/10/2026 com o plano da 001 |
| [DTEC 018](#decisão-dtec-018-camadas-do-backend-dto-mapper-repositório-e-exceções) | Camadas do backend: DTO, mapper, repositório e exceções | Aprovada em 12/10/2026 com o plano da 001 |
| [DTEC 024](#decisão-dtec-024-execução-isolada-do-processamento-de-arquivos-não-confiáveis) | Execução isolada do processamento de arquivos não confiáveis | Aprovada em 13/10/2026 com o plano da 002 |
| [DTEC 025](#decisão-dtec-025-consistência-entre-o-armazenamento-de-objetos-e-o-banco) | Consistência entre o armazenamento de objetos e o banco | Aprovada em 13/10/2026 com o plano da 002 |
| [DTEC 026](#decisão-dtec-026-acompanhamento-de-processamentos-assíncronos-na-interface) | Acompanhamento de processamentos assíncronos na interface | Aprovada em 13/10/2026 com o plano da 002 |
| [DTEC 027](#decisão-dtec-027-participantes-da-exclusão-de-fontes-e-matérias) | Participantes da exclusão de fontes e matérias | Aprovada em 13/10/2026 com o plano da 002; emenda de 13/10/2026 (`cartoes_suspensos`) proposta com o plano da 003 |
| [DTEC 033](#decisão-dtec-033-busca-sem-diferenciar-maiúsculas-e-acentos) | Busca sem diferenciar maiúsculas e acentos | Proposta em 13/10/2026 com o plano da 003 |
| [DTEC 034](#decisão-dtec-034-paginação-das-listagens-por-cursor) | Paginação das listagens por cursor | Proposta em 13/10/2026 com o plano da 003 |

A DTEC 002 tem uma emenda de 12/10/2026 (driver psycopg 3), e a DTEC 027, uma de 13/10/2026 (contagem dos suspensos). As decisões específicas da spec 001 (DTEC 019 a 023) estão no [`research.md` da spec](specs/001-conta-acesso/research.md), as da spec 002 (DTEC 028 a 032), no [`research.md` dela](specs/002-materias-fontes/research.md), e as da spec 003 (DTEC 035 a 038), no [`research.md` da 003](specs/003-cartoes-manuais/research.md). A numeração das DTEC é única no projeto, inclusive entre arquivos.

## Decisão DTEC 001 Ferramenta de testes do backend

**Questão:** qual ferramenta executa os testes automatizados do backend em Python, exigidos para toda spec implementada (regra 17 do [`AGENTS.md`](../.agents/AGENTS.md)), cobrindo testes unitários, de integração, funcionais, de segurança e adversariais?  
**Critérios:** suporte aos cinco tipos de teste na mesma suíte; independência do framework do backend, ainda pendente (QA-18); clareza das falhas; reuso de preparação de ambiente (banco, usuários, provedor de IA simulado); execução em contêiner e em integração contínua; maturidade e documentação; curva de aprendizado da equipe.  
**Alternativas consideradas:**

1. **pytest:** asserts simples com mensagens detalhadas de falha, fixtures com escopo e injeção por nome, parametrização de casos, marcadores para classificar e filtrar testes e um ecossistema amplo de plugins (cobertura, execução paralela, testes assíncronos, integração com os dois frameworks avaliados em QA-18). Executa também testes escritos com `unittest`. Consequência: é uma dependência externa, e o uso excessivo de fixtures implícitas pode dificultar a leitura se não houver convenção.
2. **unittest (biblioteca padrão):** não exige dependência, mas requer classes e métodos de assert específicos, a preparação de ambiente é por herança (`setUp`/`tearDown`), não há parametrização nativa equivalente e o ecossistema de extensões é restrito. Consequência: mais código repetitivo por teste e menos recursos para organizar os cinco tipos de teste.
3. **Test runner do framework (ex.: `manage.py test` do Django):** integrado ao framework, mas baseado em `unittest` e amarrado a uma escolha ainda pendente (QA-18). Consequência: a decisão de testes ficaria bloqueada por QA-18 e mudaria se o framework mudasse.

**Decisão:** usar **pytest** como ferramenta única de execução dos testes do backend e de qualquer outro código Python do projeto (versão estável mais recente na data desta decisão: 9.1.1, a ser fixada no arquivo de dependências do backend).  
**Justificativa:** é a única alternativa que atende a todos os critérios sem depender de QA-18. As fixtures resolvem a preparação reutilizável de banco, usuários e IA simulada; a parametrização concentra os casos adversariais e de fronteira em tabelas legíveis; os marcadores permitem separar e executar por tipo os cinco grupos exigidos pela regra 17; e existe integração mantida para FastAPI e para Django, qualquer que seja o resultado de QA-18.  
**Consequências:**

- Os testes são classificados por marcadores registrados (`unit`, `integration`, `functional`, `security`, `adversarial`), com marcadores desconhecidos tratados como erro, para que nenhum teste fique sem tipo.
- A suíte roda dentro do contêiner do backend, com os serviços reais do ambiente (ex.: PostgreSQL) nos testes de integração, conforme a regra 11 do `AGENTS.md`. O comando único de execução é documentado no `quickstart.md` da spec.
- Os complementos dependem de QA-18 e são decididos no primeiro `plan.md`: cliente HTTP de teste e plugin de integração com o framework, plugin de testes assíncronos, medição de cobertura e, como candidato para os testes adversariais, geração de entradas por propriedades.
- O pytest não cobre o frontend em React. A ferramenta de testes do frontend é uma decisão separada, a registrar quando o frontend for planejado.
- Nenhum merge na `main` acontece sem a suíte completa passando na `develop` (regra 17). A automação dessa verificação (integração contínua e proteção da `main`) é trabalho futuro.

**Condição para revisão:** incompatibilidade comprovada entre o pytest e o framework escolhido em QA-18, ou tempo de execução da suíte que inviabilize rodá-la completa antes de cada merge mesmo com execução paralela.

## Decisão DTEC 002 Framework do backend

**Questão:** com qual framework, ORM e ferramentas o backend em Python é construído (QA-18)?  
**Critérios:** OpenAPI gerado dos contratos (Princípio V); chamadas assíncronas a provedores de IA e streaming do chat; MVC identificável; maturidade; integração com pytest; leveza em memória.  
**Alternativas consideradas:**

1. **FastAPI + SQLAlchemy 2 (assíncrono, asyncpg) + Alembic + Pydantic + pydantic-settings, com uv:** OpenAPI nativo a partir dos tipos, assincronia nativa e SSE simples, Pydantic compartilhado com o PydanticAI (DTEC 007). Consequência: ORM e migrações são duas bibliotecas a aprender, e o MVC é montado pela equipe (routers como Controller).
2. **Django + Django Ninja:** ORM, migrações e admin integrados, MTV fácil de apontar. Consequência: assincronia e streaming menos naturais, e o ORM assíncrono é parcial.
3. **Litestar:** semelhante ao FastAPI, com ecossistema e material de estudo menores.

**Decisão:** alternativa 1.  
**Justificativa:** é a única que atende, sem adaptações, ao OpenAPI exigido, ao chat em streaming e às chamadas assíncronas de IA, e compartilha o Pydantic com a camada de agentes. A mesma escolha vale para a referência pós-acadêmica.  
**Consequências:** Ruff e mypy como qualidade estática; routers finos, regras em serviços e no domínio; migrações revisadas manualmente (índices HNSW, DTEC 005).  
**Condição para revisão:** a equipe não conseguir produzir no prazo com o par SQLAlchemy e Alembic.

**Emenda de 12/10/2026: driver psycopg 3 no lugar do asyncpg** ([registro](prompts/2026-10-12-001-conta-acesso-plano.md)). No planejamento da [spec 001](specs/001-conta-acesso/plan.md), a documentação do Procrastinate (DTEC 006) mostrou que ele não tem conector para asyncpg. Ele oferece `PsycopgConnector` (psycopg 3, assíncrono), `AiopgConnector` e conectores síncronos. Para enfileirar uma tarefa **na mesma transação** que grava o registro de processamento, como exige a DTEC 006, a tarefa precisa ser criada com `configure(connection=...)` numa `psycopg.AsyncConnection`.

- **Alternativas:** (1) psycopg 3 como driver único: o SQLAlchemy usa `postgresql+psycopg` assíncrono, e a conexão bruta da transação do ORM é entregue ao Procrastinate; (2) asyncpg no ORM e psycopg 3 só na fila: dois drivers e dois *pools*, sem atomicidade entre o registro e a tarefa; (3) asyncpg e enfileiramento depois do commit: janela em que o registro existe sem a tarefa, contrária à RN-03.
- **Decisão:** alternativa 1. O asyncpg sai da stack.
- **Consequências:** um único driver e um único *pool*; o enfileiramento e a gravação do registro são atômicos; a URL do banco usa o esquema `postgresql+psycopg://`.
- **Condição para revisão:** o Procrastinate passar a oferecer conector asyncpg com conexão externa, sem ganho comprovado que justifique a troca.

## Decisão DTEC 003 Autenticação

**Questão:** como o estudante se cadastra e mantém a sessão, considerando o custo da VPS e a segurança no navegador (QA-25)?  
**Critérios:** nenhum token acessível ao JavaScript; revogação no servidor; custo de memória; superfície a implementar e testar; prazo.  
**Alternativas consideradas:**

1. **Keycloak (OIDC + PKCE, JWT via JWKS):** recursos completos (MFA, login social, papéis). Consequência: JVM de 0,5 a 1 GB, realm e tema para configurar, e o token no navegador exigiria ainda a migração para BFF (QA-25). Era a direção anterior.
2. **Autenticação própria com JWT de acesso em memória e *refresh* em cookie** (esboço de 07/10/2026): dispensa serviço extra. Consequência: coordenação de renovação, rotação e revogação de tokens no cliente.
3. **Autenticação própria com sessão opaca:** senha com Argon2id, identificador de sessão aleatório guardado com hash no Postgres, cookie `HttpOnly`, `Secure`, `SameSite=Lax`, proteção anti-CSRF por *double submit* e limite de tentativas.
4. **Provedor de identidade gerenciado:** dispensa servidor, mas acopla o produto a um terceiro e envia dados pessoais para fora.

**Decisão:** alternativa 3 no MVP e no final acadêmico; Keycloak fica na [referência](arquitetura/referencia-pos-academica.md).  
**Justificativa:** o produto tem um único papel (estudante) e uma única aplicação; sessão no servidor é o modelo mais simples e seguro para isso, revoga na hora e não expõe token ao JavaScript, o que encerra QA-25 sem trabalho extra. Keycloak seria excessivo para o contexto acadêmico e caro na VPS.  
**Consequências:** recuperação de senha por e-mail no final acadêmico (serviço de envio a escolher); testes de segurança cobrem enumeração de contas, força bruta, fixação de sessão e CSRF; frontend e API na mesma origem.  
**Condição para revisão:** papéis além do estudante, MFA ou login institucional.

## Decisão DTEC 004 Frontend

**Questão:** com quais tecnologias a View (frontend React) é construída e testada (QA-29)?  
**Critérios:** contrato tipado com o backend; liberdade visual para a trilha e a identidade própria; acessibilidade; desempenho; testes.  
**Alternativas consideradas:**

1. **React + TypeScript (strict) + Vite + Tailwind CSS + `openapi-typescript`:** tipos derivados do OpenAPI, tokens de design centralizados, sem aparência imposta.
2. **React + JavaScript + Vite + Material UI** (esboço de 07/10/2026): componentes acessíveis prontos, mas aparência reconhecível de biblioteca e sem contrato tipado.
3. **React + TypeScript + Material UI:** contrato tipado, mas a mesma aparência genérica, salvo com tema extenso.

**Decisão:** alternativa 1, com Zod e React Hook Form nos formulários e ESLint (`typescript-eslint`, `react-hooks`, `jsx-a11y`) e Prettier.  
**Justificativa:** a trilha de progressão e a identidade visual são componentes sob medida que nenhuma biblioteca entrega; o contrato tipado evita divergência entre front e back.  
**Consequências:** componentes de acessibilidade (diálogo, menu) são escritos com cuidado ou vêm de primitivas sem estilo; testes com Vitest, Testing Library e MSW, e Playwright na jornada principal (DTEC 014).  
**Condição para revisão:** prazo comprometido pela construção de componentes básicos.

## Decisão DTEC 005 Banco de dados único

**Questão:** onde ficam os dados relacionais, a fila, os vetores e o índice textual?  
**Critérios:** consistência transacional entre trechos e embeddings; número de serviços; busca híbrida (aula 04).  
**Alternativas consideradas:**

1. **PostgreSQL com pgvector (imagem `pgvector/pgvector` desde o MVP):** HNSW com distância de cosseno, `tsvector` com configuração `portuguese`, fusão por RRF.
2. **PostgreSQL + banco vetorial dedicado (ex.: Qdrant):** mais um contêiner e mais memória; só se justifica em volumes muito maiores.

**Decisão:** alternativa 1. A extensão é criada na primeira migração do final acadêmico, mas a imagem já é a mesma no MVP, para não trocar o banco no meio do caminho.  
**Justificativa:** um único banco mantém trechos, embeddings e cartões na mesma transação e evita um serviço residente.  
**Consequências:** cada embedding registra modelo e versão; o filtro por estudante e matéria é aplicado na consulta; backup único.  
**Condição para revisão:** latência de busca inaceitável com o volume real.

## Decisão DTEC 006 Fila e processamento assíncrono

**Questão:** como extração, geração e indexação rodam fora da requisição HTTP?  
**Critérios:** sem serviço extra; tarefas persistentes e retomáveis; estados visíveis; idempotência.  
**Alternativas consideradas:**

1. **Procrastinate:** fila no próprio PostgreSQL, assíncrona, com novas tentativas e tarefas periódicas.
2. **Celery + Redis:** padrão de mercado para volume alto; exige Redis residente.
3. **Tarefas em segundo plano do próprio FastAPI:** sem persistência; uma reinicialização perde o trabalho.

**Decisão:** alternativa 1, num contêiner `worker` com o mesmo código da API.  
**Justificativa:** atende à persistência e à retomada sem acrescentar serviço; a transação que cria o registro de processamento também enfileira a tarefa.  
**Consequências:** tarefas idempotentes (RN-10); o backup diário também é uma tarefa periódica.  
**Condição para revisão:** fila competindo com o banco por recursos (gatilho da referência).

## Decisão DTEC 007 LLM e framework de agentes

**Questão:** qual provedor de LLM e qual framework de agentes geram os cartões no MVP e sustentam o chat no final acadêmico (QA-22)?  
**Critérios:** custo zero ou baixo; saída estruturada confiável; qualidade em português; troca de provedor por configuração (RQ-05); suporte a agentes, ferramentas, MCP e avaliação (aulas 05 a 09); leveza.  
**Alternativas consideradas (provedor):**

1. **Gemini, camada gratuita:** boa qualidade em português e saída estruturada por esquema. Consequência: limites por projeto visíveis apenas no painel do provedor, e o conteúdo enviado pode ser usado para melhorar os produtos do provedor.
2. **Groq, camada gratuita:** baixa latência e modelos abertos. Consequência: limites por minuto e por dia que podem estourar na geração em lote.
3. **API paga:** maior estabilidade, com custo por token.
4. **Modelo local:** inviável numa VPS de 2 a 4 GB.

**Alternativas consideradas (framework):**

1. **PydanticAI:** agentes com saída tipada em Pydantic (mesmo ecossistema do FastAPI), vários provedores, ferramentas, MCP, delegação entre agentes e pydantic-evals.
2. **Agno:** agentes e times prontos, com base de conhecimento e pgvector embutidos. A busca híbrida fica dentro do framework, menos controlável e menos demonstrável.
3. **LangGraph:** grafos de estado explícitos, retomada e aprovação humana. Curva maior; há experiência prévia na equipe.
4. **Sem framework:** chamadas diretas ao SDK. Menos dependências, mas a equipe reescreveria validação de saída, ferramentas e novas tentativas.

**Decisão:** Gemini na camada gratuita como provedor principal e Groq como alternativa configurável; **PydanticAI desde o MVP**, com um agente gerador de cartões.  
**Justificativa:** o PydanticAI resolve a saída estruturada validada já no MVP, cresce sem reescrita para os agentes do chat e do tira-dúvidas, e deixa a busca híbrida sob controle da equipe, que é justamente o que a disciplina avalia.  
**Consequências:** interface própria por capacidade, com o provedor configurado por ambiente; limites de timeout, novas tentativas e orçamento diário por estudante; consumo registrado por chamada; o estudante é avisado do uso de provedor externo e, no Gemini gratuito, da possibilidade de uso do conteúdo pelo provedor. O conjunto de avaliação registra provedor, modelo e versão; trocar de modelo exige reexecutá-lo.  
**Condição para revisão:** antes do final acadêmico, comparar PydanticAI e LangGraph para os agentes do chat ([QA-31](produto/pendencias.md#qa-31-framework-de-agentes-do-final-acadêmico)); trocar de provedor se a camada gratuita não comportar a demonstração ou se a política de uso de dados for inaceitável.

## Decisão DTEC 008 Embeddings e reranking

**Questão:** de onde vêm os embeddings e o reranking do RAG do final acadêmico, sem modelo local na VPS?  
**Critérios:** custo; RAM na VPS; qualidade em português; dimensão estável; caminho de migração para execução local.  
**Alternativas consideradas:**

1. **bge-m3 no Workers AI da Cloudflare:** multilíngue, dimensão 1024, 10 mil *neurons* gratuitos por dia e US$ 0,012 por milhão de tokens acima disso (preços consultados em 12/10/2026). O **mesmo modelo** pode rodar localmente depois, sem reindexar.
2. **Embeddings do Gemini, camada gratuita:** boa qualidade, mas os limites gratuitos não são publicados, o conteúdo pode ser usado pelo provedor e o espaço vetorial difere do bge-m3 (migrar exige reindexar).
3. **Modelo local pequeno (multilingual-e5-small):** dados não saem do servidor, mas consome 0,5 a 1 GB de RAM, e a indexação em CPU é lenta.
4. **bge-m3 local:** 2 a 3 GB de RAM (referência pós-acadêmica).

**Decisão:** alternativa 1 para embeddings, e reranking com o reranker disponível no Workers AI (`@cf/baai/bge-reranker-base`, US$ 0,00311 por milhão de tokens).  
**Justificativa:** zero de RAM na VPS, custo zero no volume acadêmico e continuidade total com a arquitetura de referência.  
**Consequências:** cada embedding registra modelo e versão; trechos são enviados a um terceiro, o que é informado ao estudante; dependência de rede e de conta na Cloudflare.  
**Condição para revisão:** o reranker é otimizado para inglês e chinês. Se o conjunto de casos não mostrar ganho em português sobre a fusão RRF, o reranking é retirado ou trocado por um reranker multilíngue.

## Decisão DTEC 009 Extração de texto

**Questão:** como extrair texto das fontes, com página quando conhecida?  
**Critérios:** qualidade em PDF com texto; página e posição; leveza; licença.  
**Alternativas consideradas:**

1. **PyMuPDF:** extração rápida e de boa qualidade, com página e blocos. Licença **AGPL-3.0**.
2. **pypdf ou pdfplumber:** licenças permissivas, com texto um pouco pior em layouts complexos.
3. **Docling:** OCR, tabelas e layout, mas com modelos pesados (referência pós-acadêmica).

**Decisão:** PyMuPDF para PDF; leitura direta de TXT e MD no MVP; no final acadêmico, SRT e VTT por *parser* de legendas (texto com marcação de tempo no lugar da página) e DOCX por `python-docx`. Divisão em trechos por estrutura (página e seção) com sobreposição; tamanho e sobreposição são parâmetros experimentais, ajustados pela avaliação.  
**Justificativa:** melhor qualidade em PDF com texto entre as opções leves. O uso acadêmico não comercial é compatível com a AGPL.  
**Consequências:** PDF sem texto é recusado (CB-23).  
**Condição para revisão:** **qualquer evolução comercial do produto** exige a licença comercial do PyMuPDF ou a troca por biblioteca permissiva ou pelo Docling (MIT). Esse ponto está registrado na [referência](arquitetura/referencia-pos-academica.md).

## Decisão DTEC 010 Armazenamento de arquivos

**Questão:** onde ficam as fontes enviadas e as imagens dos cartões?  
**Critérios:** custo; backup; privacidade; simplicidade.  
**Alternativas consideradas:**

1. **Volume Docker** para tudo: simples, mas imagens servidas pela API consomem banda e memória da VPS.
2. **Cloudflare R2** para tudo: camada gratuita de 10 GB, 1 milhão de escritas e 10 milhões de leituras por mês, saída sem custo; exige conta e rede.
3. **Volume para as fontes e R2 para as imagens.**
4. **Interface de armazenamento com adaptador por ambiente:** disco local (pasta montada no contêiner) no MVP e no desenvolvimento; R2 no final acadêmico. A mesma chave de objeto vale nos dois.
5. **Emulador do protocolo S3 num contêiner local (ex.: MinIO) no MVP:** mesmo código do R2 em todo ambiente, mas mais um serviço no Compose e tecnologia fora da stack.
6. **Só arquivo temporário, apagado após o processamento:** descartada, porque perde o original e impede o acervo (RN-14), o reprocessamento (RN-03) e a indexação do final acadêmico.

**Decisão (revisada em 12/10/2026, [registro](prompts/2026-10-12-esquema-inicial-banco.md)):** alternativa 4. Fontes e imagens dos cartões ficam atrás de uma **interface própria de armazenamento**, com o adaptador escolhido por variável de ambiente:

| Ambiente | Adaptador |
|---|---|
| MVP e desenvolvimento local | **Disco local**: pasta montada no contêiner (volume), sem rede nem conta externa |
| Final acadêmico (VPS) | **Cloudflare R2**, via API compatível com S3, com buckets separados por ambiente e um bucket próprio para os backups |
| Testes unitários | **Em memória** |
| Testes de integração | **Disco local**, numa pasta temporária por execução |

Imagens com limite de **3 MB** (JPEG, PNG ou WebP); fontes com os limites da RN-02. O backend valida o tipo real antes de gravar. O banco guarda a **chave do objeto**, nunca a URL ou o caminho absoluto.  
*Decisões anteriores (12/10/2026):* alternativa 3 (fontes no volume, imagens no R2) e, em seguida, alternativa 2 (tudo no R2 desde o MVP).  
**Justificativa:** o MVP roda sem rede e sem conta externa, e os testes não dependem do R2. Na VPS, as fontes crescem sem limite com o uso e lotariam o disco: com o R2, API e worker ficam sem estado, o backup da VPS se reduz ao banco e a camada gratuita cobre o volume acadêmico sem custo de saída. Como a chave é a mesma, trocar de adaptador não muda o banco nem o domínio.  
**Consequências:**

- Nomes internos (UUID) para tudo; o nome enviado pelo usuário nunca compõe a chave. O adaptador de disco resolve a chave dentro da pasta raiz e recusa qualquer chave que escape dela (*path traversal*).
- Exclusão de cartão ou de fonte remove os objetos correspondentes; a aplicação exclui os objetos antes das linhas.
- O worker lê a fonte para um arquivo temporário antes da extração e o apaga em seguida, com qualquer adaptador.
- Leitura pelo navegador: no R2, URL assinada de curta duração; no disco local, uma rota autenticada da API que verifica o dono antes de entregar o arquivo. No MVP, o navegador não lê arquivos: a evidência mostra o texto do trecho, que está no banco, e imagens só existem no final acadêmico.
- Uma suíte de contrato roda os mesmos testes contra os adaptadores em memória e de disco e, opcionalmente, contra um bucket de teste do R2 antes do deploy.
- Variáveis previstas para o `.env.example` (sem valores): `ARMAZENAMENTO_ADAPTADOR` (`local` ou `r2`), `ARMAZENAMENTO_DIRETORIO`, `ARMAZENAMENTO_URL_ASSINADA_SEGUNDOS`, `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` e `R2_BUCKET_BACKUP`.

**Condição para revisão:** uso acima da camada gratuita do R2.

## Decisão DTEC 011 Observabilidade e avaliação da IA

**Questão:** como observar o sistema e avaliar a IA (aula 09) sem serviços pesados?  
**Critérios:** exigências das guidelines (logs úteis, saúde, consumo da IA, runbook); privacidade; custo.  
**Alternativas consideradas:**

1. **Logs JSON com id de correlação, `/health` e `/health/ready`, e tabela de consumo da IA:** sem serviço extra.
2. **Langfuse Cloud, camada gratuita:** rastros de agentes sem custo de VPS; envia metadados a um terceiro.
3. **Langfuse self-hosted e OpenTelemetry:** controle total, mas vários GB (referência).

**Decisão:** alternativa 1 no MVP; alternativas 1 e 2 no final acadêmico, com o **conteúdo das fontes, perguntas e respostas desligado ou mascarado** nos rastros. As avaliações da IA usam pydantic-evals executado pelo pytest, num grupo separado da suíte que bloqueia o merge, porque chamam o modelo real. A **taxa de aceitação** dos cartões gerados (RN-22) é a métrica humana de qualidade da geração.  
**Justificativa:** cobre o que a disciplina avalia sem enviar o conteúdo do estudante a mais um terceiro.  
**Consequências:** o relatório de avaliação registra provedor, modelo e versão das instruções.  
**Condição para revisão:** necessidade de rastrear conteúdo, que exigiria a versão self-hosted.

## Decisão DTEC 012 Algoritmo de repetição espaçada

**Questão:** qual implementação do agendamento de revisões o servidor usa (QA-13)?  
**Critérios:** algoritmo decidido pelo produto (FSRS); implementação mantida; testes; reprodutibilidade.  
**Alternativas consideradas:**

1. **Biblioteca `fsrs`** (implementação oficial em Python mantida pelo projeto do algoritmo, licença MIT).
2. **Implementação própria do FSRS:** controle total, com risco de erro nas fórmulas.
3. **SM-2:** mais simples, porém inferior e contrário à decisão de produto.

**Decisão:** alternativa 1, com a versão fixada e os parâmetros registrados por revisão (RN-17).  
**Justificativa:** reduz risco e mantém o agendamento idêntico ao de referência do algoritmo.  
**Consequências:** a lógica de domínio (lição, novos por dia, dia de estudo) fica no código do projeto; só o cálculo do agendamento vem da biblioteca.  
**Atualização de 12/10/2026 (FSRS soberano, [RN-26](base-specs/spec.md#rn-26-soberania-do-fsrs)):** a leitura do código da biblioteca mostrou consequências que o produto passa a seguir:

- O `Card` tem os estados *Learning*, *Review* e *Relearning*, além de `step`, `stability`, `difficulty`, `due` e `last_review`. Não há estado "novo": cartão novo é *Learning* sem `last_review`. O [esquema](arquitetura/esquema-inicial.dbml) espelha esses campos em `cartoes`.
- Os passos curtos (padrão: 1 e 10 minutos no aprendizado, 10 minutos no reaprendizado) exigem que a lição reapresente o cartão na mesma sessão.
- O `Scheduler` recebe 21 pesos, retenção desejada (padrão 0,9), passos, intervalo máximo e *fuzzing*. Esses parâmetros ficam versionados por estudante (`parametros_fsrs`), e cada revisão aponta a versão usada.
- A biblioteca trabalha só em UTC; a conversão para o dia de estudo (virada às 4h locais) é do domínio.
- A biblioteca inclui um otimizador de pesos a partir do histórico de revisões. Ele fica fora do MVP; as revisões guardam o necessário para usá-lo depois.

**Condição para revisão:** mudança incompatível da biblioteca.

## Decisão DTEC 013 Hospedagem e operação

**Questão:** como o final acadêmico é publicado e operado (QA-11)?  
**Critérios:** HTTPS; health check, logs, backup com restauração testada, rollback e runbook (guidelines); custo mensal; simplicidade.  
**Alternativas consideradas:**

1. **VPS com Docker Compose e Caddy:** HTTPS automático, poucos componentes.
2. **VPS com Coolify:** painel de deploy, mas consome memória própria.
3. **Kubernetes (k3s):** aprofundamento opcional das guidelines; mais componentes e memória.

**Decisão:** alternativa 1, numa VPS de 2 a 4 GB (provável Hetzner). Imagens construídas na integração contínua e publicadas num registro; o deploy atualiza as *tags* no Compose. Backup diário (`pg_dump`) copiado para um bucket de backup no R2, com restauração ensaiada; as fontes já ficam no R2 (DTEC 010). MVP apenas local.  
**Justificativa:** atende a todas as exigências de operação das guidelines com o menor número de peças.  
**Consequências:** escolha da VPS, do domínio e do custo mensal registrada quando decidida (QA-11); Kubernetes fica como aprofundamento opcional.  
**Condição para revisão:** necessidade de alta disponibilidade ou de mais de uma VPS.

## Decisão DTEC 014 Complementos de teste

**Questão:** quais ferramentas complementam o pytest (DTEC 001) no backend e quais testam o frontend (QA-28 e QA-29)?  
**Critérios:** testes assíncronos; integração com serviços reais (regra 17 do [`AGENTS.md`](../.agents/AGENTS.md)); execução em contêiner e na integração contínua.  
**Alternativas consideradas:**

1. **pytest-asyncio + httpx (`AsyncClient`) + Postgres real do Compose + pytest-cov + Hypothesis** para entradas adversariais por propriedades.
2. **Testcontainers** para subir um Postgres por suíte: isolamento maior, mas exige Docker dentro do executor (referência).

**Decisão:** alternativa 1 no backend; IA simulada por adaptador falso nos testes da suíte principal. No frontend, **Vitest + Testing Library + MSW** e **Playwright** na jornada principal, com verificação automática de acessibilidade (axe) nas telas principais.  
**Justificativa:** cobre os cinco tipos de teste exigidos com o menor custo de infraestrutura.  
**Consequências:** a cobertura é medida, mas sem mínimo obrigatório no MVP; os testes do frontend também bloqueiam o merge na `main`.  
**Condição para revisão:** testes interferindo entre si ou suíte lenta demais para rodar antes de cada merge.

## Decisão DTEC 015 Roteamento e estado do servidor no frontend

**Data:** 12/10/2026 ([registro](prompts/2026-10-12-001-conta-acesso-plano.md))  
**Questão:** como o frontend organiza as rotas (inclusive as protegidas por sessão), consulta a API e mantém o estado vindo do servidor, já que a DTEC 004 não decide isso?  
**Critérios:** tipagem de ponta a ponta com o contrato OpenAPI; proteção de rota antes da renderização; cache e invalidação do estado do servidor sem código manual; Princípio IV (o frontend só exibe o que o servidor confirma); maturidade.  
**Alternativas consideradas:**

1. **TanStack Router + TanStack Query + `openapi-fetch`:** rotas e parâmetros tipados, proteção de rota em `beforeLoad` integrada ao cache do Query, invalidação declarativa após mutações; o `openapi-fetch` usa diretamente os tipos do `openapi-typescript` (DTEC 004), sem gerar código de cliente.
2. **React Router + TanStack Query:** roteador mais conhecido, com rotas e parâmetros menos tipados.
3. **React Router + `fetch` manual e estado em contexto:** menos dependências, mas cache, repetição, invalidação e estados de carregamento seriam reescritos pela equipe.

**Decisão:** alternativa 1.  
**Justificativa:** é a única que mantém o tipo do contrato da rota até o componente, o que evita divergência entre front e back (critério da DTEC 004). Proteger a rota antes de renderizar evita piscar conteúdo de área autenticada.  
**Consequências:** o estado do servidor vive só no cache do TanStack Query; não há biblioteca de estado global. Um *middleware* do `openapi-fetch` envia o cabeçalho anti-CSRF e converte o corpo de erro padronizado. As rotas usam o roteamento por arquivos do plugin do TanStack Router para o Vite.  
**Condição para revisão:** o roteador atrasar a equipe a ponto de comprometer o prazo do MVP.

## Decisão DTEC 016 Primitivas acessíveis da interface

**Data:** 12/10/2026 ([registro](prompts/2026-10-12-001-conta-acesso-plano.md))  
**Questão:** de onde vêm os componentes com comportamento de acessibilidade difícil (diálogo, campos com erro, menus, controles deslizantes), que a DTEC 004 manda escrever com cuidado ou tirar de primitivas sem estilo?  
**Critérios:** WCAG 2.2 AA (RQ-06 da base), com foco, teclado e anúncio a leitores de tela; nenhuma aparência imposta; manutenção; integração com Tailwind.  
**Alternativas consideradas:**

1. **React Aria Components:** primitivas sem estilo, com comportamento de acessibilidade testado em leitores de tela, internacionalização e estilização por atributos de estado que combinam com o Tailwind.
2. **Radix Primitives:** primitivas sem estilo e populares, com cobertura menor de campos de formulário e validação.
3. **Elementos nativos (`<dialog>`) e componentes escritos à mão:** sem dependência, mas com o risco de errar foco, anúncios e teclado em cada componente.

**Decisão:** alternativa 1, encapsulada em `frontend/src/componentes/ui/`. As telas não importam o React Aria diretamente.  
**Justificativa:** é a opção com o comportamento de acessibilidade mais completo sem impor aparência, o que preserva a identidade própria da trilha (DTEC 004).  
**Consequências:** os componentes de `ui/` aplicam os tokens de design e são o único ponto de troca da biblioteca; os testes de acessibilidade (axe, DTEC 014) rodam sobre eles.  
**Condição para revisão:** limitação que impeça um componente exigido pelo design.

## Decisão DTEC 017 Integração contínua e verificação local

**Data:** 12/10/2026 ([registro](prompts/2026-10-12-001-conta-acesso-plano.md)); atende à parte técnica da [QA-30](produto/pendencias.md#qa-30-branch-develop-e-verificação-automática-antes-do-merge)  
**Questão:** como garantir, sem depender da disciplina de cada integrante, que nenhum merge na `main` aconteça sem lint, checagem de tipos e as suítes completas passando (regra 17)?  
**Critérios:** execução nos mesmos contêineres do ambiente local (regra 11 e DTEC 001); custo zero; visibilidade da verificação na avaliação.  
**Alternativas consideradas:**

1. **GitHub Actions + pre-commit opcional:** o repositório já está no GitHub; a camada gratuita cobre o uso acadêmico. O fluxo constrói as imagens `dev` e roda tudo pelo Compose. O pre-commit local antecipa as falhas de formatação e lint.
2. **Só verificação local:** sem custo nem configuração, mas depende de cada pessoa.
3. **Serviço de integração contínua externo ao GitHub:** mais um terceiro, sem ganho.

**Decisão:** alternativa 1. O fluxo `.github/workflows/ci.yml` roda a cada push na `develop` e em todo pull request para a `main`: lint, formatação, checagem de tipos, migrações, as duas suítes, a comparação do OpenAPI gerado com o versionado e a construção das imagens.  
**Justificativa:** torna a regra 17 verificável e deixa a evidência registrada em cada pull request.  
**Consequências:** a proteção da `main` (exigir a verificação aprovada) é configurada por quem administra o repositório; as decisões de processo da QA-30 (revisão obrigatória, documentação pela `develop`) continuam com a equipe. O pre-commit exige Python no computador e é opcional: a integração contínua é a verificação que vale.  
**Condição para revisão:** limite de minutos da camada gratuita ou tempo de execução que atrase os merges.

## Decisão DTEC 018 Camadas do backend: DTO, mapper, repositório e exceções

**Data:** 12/10/2026 ([registro](prompts/2026-10-12-001-conta-acesso-plano.md)), por pedido de Artur Lins  
**Questão:** como cada domínio do backend separa transporte, conversão, regras, acesso a dados e erros, de modo que o MVC fique identificável (constituição) e nenhuma entidade do banco vaze pela API?  
**Critérios:** routers finos (DTEC 002); contrato OpenAPI estável e independente do esquema do banco; regras testáveis sem HTTP nem banco; isolamento por estudante num único ponto (RN-01); corpo de erro uniforme (`padroes-implementacao.md`).  
**Alternativas consideradas:**

1. **Camadas explícitas por domínio:** DTOs Pydantic de entrada e saída, mapeadores como funções puras, serviços de caso de uso, regras puras de domínio, repositórios SQLAlchemy sempre filtrados pelo dono, entidades do ORM e uma hierarquia única de exceções da aplicação convertida em HTTP num único ponto.
2. **Router acessando o ORM e devolvendo a entidade com `from_attributes`:** menos arquivos, mas acopla o contrato ao esquema do banco e espalha regras e filtros de dono pelos routers.
3. **Arquitetura hexagonal completa (portas e adaptadores para tudo):** isola mais, porém com abstrações sem uso concreto no prazo do MVP (contrário a `padroes-implementacao.md`).

**Decisão:** alternativa 1, com a estrutura de arquivos definida no [plano da spec 001](specs/001-conta-acesso/plan.md#camadas-do-backend) e reproduzida em [`skills/padroes-implementacao.md`](skills/padroes-implementacao.md). Portas e adaptadores ficam restritos ao que já tem mais de uma implementação (armazenamento, DTEC 010, e provedores de IA, DTEC 007).  
**Justificativa:** o contrato muda só quando o DTO muda; o filtro de dono fica num único lugar; as regras são testadas como funções puras; e o tratamento de erros é central e verificável.  
**Consequências:**

- **Model:** entidades SQLAlchemy, regras de domínio, serviços e repositórios. **Controller:** routers. **View:** o frontend.
- Serviços e domínio não importam FastAPI; routers não importam o ORM nem repositórios.
- Domínio e serviços lançam apenas subclasses de `ErroAplicacao`; o repositório converte erros do banco (ex.: violação de unicidade) em `Conflito`; nenhum `except` engole erro sem convertê-lo ou registrá-lo.
- Um teste de arquitetura verifica as dependências proibidas entre camadas.

**Condição para revisão:** camadas que só repassam dados sem acrescentar regra em mais da metade dos casos de uso, o que indicaria abstração em excesso.

## Decisão DTEC 024 Execução isolada do processamento de arquivos não confiáveis

**Data:** 13/10/2026 ([registro](prompts/2026-10-13-002-materias-fontes-plano.md))  
**Questão:** como abrir e extrair arquivos enviados pelo estudante (PDF na spec 002; SRT, VTT e DOCX na 009; imagens na 011) sem que um arquivo malicioso ou patológico trave, esgote a memória ou derrube a API ou o worker? O PyMuPDF (DTEC 009) é uma biblioteca em C: um laço infinito ou uma explosão de memória dentro dela não é interrompível por uma *thread* Python.  
**Critérios:** Princípio II (proteção); disponibilidade da API e do worker; memória previsível na VPS de 2 a 4 GB; nenhuma tecnologia nova; custo de latência aceitável num envio de até 2 MB.  
**Alternativas consideradas:**

1. **Subprocesso por chamada, com tempo limite e limite de memória:** a função de leitura roda num processo filho criado pelo contexto `spawn` do `multiprocessing`, que aplica `resource.setrlimit(RLIMIT_AS)` antes de abrir o arquivo; o pai espera até o tempo limite e mata o filho (`kill`) se ele não terminar. A concorrência é limitada por um semáforo por processo. Custo: cerca de 0,2 a 0,5 s de criação do processo por chamada.
2. **Mesma chamada numa *thread* com tempo limite:** o tempo limite só abandona a espera; a *thread* continua consumindo CPU e memória, e o processo não pode matá-la.
3. **Contêiner ou serviço de conversão separado (sandbox dedicado):** isolamento mais forte, mas é um serviço residente a mais, contrário ao critério comum das DTEC 002 a 014.

**Decisão:** alternativa 1, num utilitário único do núcleo (`nucleo/isolamento.py`, `executar_isolado(funcao, argumentos, tempo_limite_s, memoria_max_mb)`), usado tanto na verificação de integridade feita na requisição quanto na extração feita no worker.  
**Justificativa:** é a única alternativa sem serviço novo que garante a interrupção de verdade e um teto de memória por arquivo. A latência adicional é irrelevante diante do tempo de envio e da meta de 60 s do processamento (CS-003 da 002).  
**Consequências:**

- O filho recebe o **caminho de um arquivo temporário** (nunca o conteúdo pela fila de mensagens) e devolve só dados simples e serializáveis (contagens, textos por página, código de erro).
- Estouro do tempo ou da memória vira um resultado tipado (`tempo_esgotado`, `memoria_esgotada`), que cada spec traduz para a sua mensagem ao estudante. Nenhum desses casos derruba o processo pai.
- Valores padrão configuráveis por ambiente: na API, 10 s, 256 MiB e no máximo 2 verificações simultâneas (`VALIDACAO_ARQUIVO_*`); no worker, 30 s e 512 MiB (`EXTRACAO_*`).
- O `RLIMIT_AS` só existe em Linux. Como todo serviço roda em contêiner Linux (regra 11), os testes que dependem dele são marcados para rodar somente nesse ambiente.

**Condição para revisão:** um formato que exija ferramenta externa pesada (ex.: OCR na referência pós-acadêmica), o que pode justificar um contêiner de conversão separado.

## Decisão DTEC 025 Consistência entre o armazenamento de objetos e o banco

**Data:** 13/10/2026 ([registro](prompts/2026-10-13-002-materias-fontes-plano.md))  
**Questão:** o arquivo vai para o armazenamento (DTEC 010) e o registro vai para o PostgreSQL, sem transação comum. Como evitar linhas sem objeto e objetos sem linha no envio (fontes na 002, imagens na 011) e na exclusão?  
**Critérios:** nenhuma linha visível ao estudante aponta para um objeto inexistente; nenhum objeto fica para sempre sem dono (custo e privacidade, Princípio II); idempotência; regra do esquema "objetos antes das linhas" na exclusão de um item isolado; exceção da DTEC 021 na exclusão da conta.  
**Alternativas consideradas:**

1. **Objeto primeiro, linha depois, com compensação e reconciliação:** no envio, grava o objeto, abre a transação, insere a linha (e enfileira o processamento) e confirma; se a transação falhar, apaga o objeto. Uma tarefa periódica apaga objetos sem linha mais antigos que uma margem de segurança, o que cobre a queda do processo entre a gravação e a confirmação.
2. **Só compensação:** uma queda do processo no meio deixa o objeto órfão para sempre.
3. **Linha primeiro, num estado "recebendo", e objeto depois:** exige um estado a mais visível nas consultas e a limpeza de linhas presas, com o mesmo problema invertido.

**Decisão:** alternativa 1.  
**Justificativa:** a linha só existe depois que o objeto existe, então a API nunca mostra um registro sem arquivo; a compensação resolve a falha comum, e a reconciliação resolve a falha rara (queda do processo) sem estado extra no domínio.  
**Consequências:**

- **A interface de armazenamento ganha `listar_prefixo(prefixo) -> iterável de (chave, criado_em)`**, ao lado de `gravar`, `ler_para_arquivo`, `apagar` (idempotente) e `apagar_prefixo` (DTEC 021). Os adaptadores de disco e em memória a implementam, e a suíte de contrato dos adaptadores a cobre.
- **Reconciliação:** a tarefa periódica `reconciliar_objetos` (diária, às 3h30 UTC) percorre `usuarios/*/fontes/` (e, na 011, `usuarios/*/imagens/`) e apaga as chaves sem linha correspondente criadas há mais de 1 hora (`RECONCILIACAO_MARGEM_MIN`). A margem impede que ela apague o objeto de um envio ainda em curso.
- **Exclusão de um item isolado:** trava a linha (`FOR UPDATE`), apaga o objeto (operação idempotente) e só então apaga as linhas, na mesma transação. Se a transação falhar depois de apagar o objeto, a linha continua existindo sem arquivo; repetir a exclusão conclui o trabalho, e um reprocessamento falha como erro técnico. Esse estado é raro e recuperável pelo próprio estudante.
- **Exclusão da conta:** continua como na DTEC 021 (linhas primeiro, objetos por tarefa).

**Condição para revisão:** um armazenamento que ofereça gravação condicional ligada ao banco, ou um volume de objetos em que listar o prefixo diariamente fique caro (gatilho para um índice de objetos no banco).

## Decisão DTEC 026 Acompanhamento de processamentos assíncronos na interface

**Data:** 13/10/2026 ([registro](prompts/2026-10-13-002-materias-fontes-plano.md))  
**Questão:** como a interface mostra a mudança de estado de um trabalho em segundo plano (processamento de fonte na 002, geração de cartões na 004, indexação na 014) sem que o estudante recarregue a página (RF-005 da 002)?  
**Critérios:** Princípio IV (o estado vem do servidor); nenhuma tecnologia ou serviço novo; funcionamento através do proxy do Vite e do Caddy; custo de requisições desprezível; simplicidade de teste.  
**Alternativas consideradas:**

1. ***Polling* condicional com o TanStack Query (DTEC 015):** a consulta da lista usa `refetchInterval` de 2 s **somente enquanto** algum item da tela estiver num estado não final (`pendente` ou `processando`) e para sozinha quando todos chegam a um estado final. Também consulta ao voltar o foco à aba.
2. **Server-Sent Events alimentados por `LISTEN/NOTIFY` do PostgreSQL:** atualização imediata, mas com conexões longas no proxy, reconexão, autenticação do fluxo e mais testes.
3. **WebSocket:** bidirecional sem necessidade, e com o mesmo custo de infraestrutura da alternativa 2.

**Decisão:** alternativa 1, com o intervalo configurado num único ponto do frontend (`api/acompanhamento.ts`).  
**Justificativa:** os processamentos duram de segundos a um minuto (CS-003 da 002); 2 s de latência são imperceptíveis nesse contexto, e o *polling* só existe enquanto há trabalho em andamento.  
**Consequências:** as rotas de listagem devolvem o estado de cada item e não têm cache no navegador (`Cache-Control: no-store`); o anúncio da mudança de estado a leitores de tela é feito por uma região `aria-live="polite"` (WCAG 2.2 AA); a interface nunca mostra um estado que o servidor não confirmou.  
**Condição para revisão:** o chat em *streaming* do final acadêmico (spec 014), que pode justificar SSE para aquela funcionalidade, sem mudar esta decisão para os processamentos.

## Decisão DTEC 027 Participantes da exclusão de fontes e matérias

**Data:** 13/10/2026 ([registro](prompts/2026-10-13-002-materias-fontes-plano.md))  
**Questão:** a exclusão de uma fonte ou de uma matéria (spec 002) precisa contar e tratar cartões, evidências e gerações, que pertencem aos domínios `cartoes` (specs 003 e 004) e, no final acadêmico, `busca` e `chat` (spec 014). A lista de matérias também mostra contagens de cartões (RF-002 da 002). Como fazer isso sem que o domínio `fontes` dependa das tabelas de outros domínios (DTEC 018)?  
**Critérios:** domínios desacoplados; cada spec é dona das tabelas que cria; atomicidade da exclusão; contagens exibidas iguais às efetivamente apagadas (CS-004 da 002); a 002 testável antes da 003.  
**Alternativas consideradas:**

1. **Registro de participantes no núcleo:** cada domínio registra, em `nucleo/participantes_acervo.py`, um participante com quatro operações, todas executadas **na transação de quem chama**: `contar_por_materia(sessao, usuario_id) -> {materia_id: contagens}`, `impacto_fonte(sessao, usuario_id, fonte_id) -> contagens`, `ao_excluir_fonte(sessao, usuario_id, fonte_id, modo)` e `ao_excluir_materia(sessao, usuario_id, materia_id)`. O serviço de `fontes` ou de `materias` organiza a exclusão e soma as contagens dos participantes. É o mesmo padrão do registro `apagar_dados_usuario` (DTEC 021).
2. **A 002 cria agora as tabelas mínimas de cartões:** quebra a regra de que cada spec é dona das colunas que usa e obriga a 002 a carregar regras da 003 e da 004 sem testes.
3. **O serviço de fontes consulta e altera diretamente as tabelas de cartões:** acopla os domínios e viola a DTEC 018.

**Decisão:** alternativa 1.  
**Justificativa:** a 002 entrega o mecanismo, as próprias contagens (fontes e trechos) e testes com um participante falso; cada spec seguinte só registra o seu participante, e a exclusão continua sendo uma única transação.  
**Consequências:**

- **Sentido das dependências:** o serviço de `materias` organiza a exclusão da matéria, e o de `fontes`, a da fonte. O próprio domínio `fontes` é **participante** da matéria: conta as fontes e, na exclusão da matéria, apaga os objetos e as linhas das fontes. Assim `fontes` depende de `materias` (para verificar o dono), e `materias` não importa nada de `fontes`.
- **Contagens padronizadas** (`ContagensAcervo`): `fontes`, `cartoes_ativos`, `cartoes_aguardando_revisao`, `cartoes_gerados_aceitos` (afetados pela escolha "Manter" ou "Excluir"), `cartoes_referencia` (criados pelo estudante e sempre mantidos, D-009 da 002). Campos ausentes valem zero; antes da 003, todas as contagens de cartões são zero.
- **Obrigações das próximas specs:**
  - A **003** registra o participante dos cartões criados à mão (contagem e marcação "Fonte apagada" dos que citam a fonte).
  - A **004** registra o participante dos cartões gerados e das gerações: apaga os aguardando revisão, aplica o modo escolhido aos aceitos (manter com "Fonte apagada" e sem selo de verificado, ou apagar) e interrompe as gerações em andamento da fonte (CB-16).
  - A **014** registra o participante dos índices e das citações.
- **Ordem:** cada participante declara uma prioridade. Os de cartões e gerações rodam primeiro e o de `fontes` por último, todos antes de a matéria ou a fonte ter as linhas apagadas, porque as FKs de cartões e de fontes para matérias usam `restrict`.
- **Testes:** um participante falso cobre o mecanismo na 002. Cada spec seguinte acrescenta testes do seu participante e reexecuta os testes funcionais da exclusão (US2 e US3 da 002) com dados reais.

**Condição para revisão:** um participante que precise de efeito fora do banco (ex.: apagar imagens dos cartões na 011), que seguirá a DTEC 025: objetos antes das linhas, na mesma transação.

**Emenda de 13/10/2026: contagem separada dos cartões suspensos** ([registro](prompts/2026-10-13-003-cartoes-manuais-plano.md)). No planejamento da [spec 003](specs/003-cartoes-manuais/plan.md), apareceu um conflito. A lista de matérias mostra a quantidade de "cartões ativos" (RF-002 da 002), e o impacto da exclusão da matéria conta "ativos e suspensos" (`ContagensExclusaoMateria.cartoesAtivos` no contrato da 002). Os dois números saíam do mesmo campo `cartoes_ativos` de `contar_por_materia`.

- **Alternativas:**
  1. Acrescentar o campo `cartoes_suspensos` a `ContagensAcervo`. A lista mostra só `cartoes_ativos`, e o impacto da matéria soma `cartoes_ativos + cartoes_suspensos`.
  2. Fazer `cartoes_ativos` contar ativos e suspensos nos dois lugares. A 002 não muda, mas a lista mostraria cartões suspensos como ativos, contra a RF-002 da 002.
- **Decisão:** alternativa 1. A mudança é aditiva: campos ausentes continuam valendo zero, e o contrato da 002 não muda.
- **Consequências:** o plano e as tarefas da 002 (T005 e T043) passam a citar o campo novo, com registro no histórico da 002. O participante dos cartões (spec 003) preenche `cartoes_ativos` e `cartoes_suspensos` com cartões de qualquer origem; a 004 não os conta de novo.
- **Condição para revisão:** a mesma da decisão.

## Decisão DTEC 033 Busca sem diferenciar maiúsculas e acentos

**Data:** 13/10/2026 ([registro](prompts/2026-10-13-003-cartoes-manuais-plano.md))  
**Questão:** como buscar textos do estudante (frente e verso dos cartões na RF-010 da spec 003 e, no futuro, outras buscas por texto curto) sem diferenciar maiúsculas, minúsculas e acentos, mantendo o comportamento "contém o texto" da spec?  
**Critérios:**

- semântica de substring, sem radicalização, porque a spec pede "contém o texto";
- mesmo resultado para "célula", "Celula" e "CÉLULA";
- nenhum serviço novo;
- latência abaixo de 100 ms na escala da spec (uma matéria com centenas de cartões);
- normalização feita num único ponto;
- nenhuma coluna derivada mantida à mão por vários escritores (004 e 011 inclusive).

**Alternativas consideradas:**

1. **Extensão `unaccent` do PostgreSQL, sem índice:** `lower(unaccent(coluna)) LIKE '%' || lower(unaccent(:termo)) || '%' ESCAPE '\'`, aplicada aos cartões já recortados pelo índice `(materia_id, usuario_id)`. A extensão faz parte do *contrib* e já vem na imagem `pgvector/pgvector` (DTEC 005), sem pacote novo.
2. **`unaccent` + `pg_trgm` com índice GIN de trigramas:** busca indexada em qualquer volume. Exige duas extensões e uma função `IMMUTABLE` em volta da `unaccent`, que é `STABLE`, para que ela possa entrar num índice. É complexidade sem uso na escala atual.
3. **Coluna normalizada mantida pela aplicação** (em minúsculas e sem acentos, calculada em Python a cada escrita): dispensa a extensão, mas duplica o texto e depende de que todo escritor de cartões a atualize.
4. **Busca textual (`tsvector` com a configuração `portuguese`):** radicaliza as palavras e não encontra pedaços de palavra, o que contraria o "contém o texto" da spec. Ela continua reservada ao RAG do final acadêmico (DTEC 005).

**Decisão:** alternativa 1. A extensão é criada pela migração da spec 003 (`CREATE EXTENSION IF NOT EXISTS unaccent`).  
**Justificativa:** atende à semântica exata da spec com uma única expressão SQL, sem coluna derivada nem serviço novo. Uma matéria cabe com folga numa varredura das linhas já filtradas pelo índice.  
**Consequências:**

- **Ordem das funções:** primeiro `unaccent`, depois `lower`. Assim "É" vira "E" antes da conversão para minúscula, o que funciona mesmo que a colação do banco converta só ASCII.
- **Termo:** o termo é normalizado em NFC, sem espaços nas extremidades, com 1 a 100 caracteres. `%`, `_` e `\` são escapados antes do `LIKE`, para que o termo nunca vire padrão. Ele vai sempre como parâmetro, nunca concatenado ao SQL.
- **Ponto único:** a expressão fica numa função do repositório de cartões, coberta por testes de integração com acentos, cedilha, maiúsculas e curingas.
- **Permissão:** o papel que roda as migrações precisa poder criar a extensão. No MVP, é o próprio dono do banco.

**Condição para revisão:** uma matéria com mais de 5 mil cartões ou uma busca acima de 100 ms no percentil 95, o que justificaria a alternativa 2.

## Decisão DTEC 034 Paginação das listagens por cursor

**Data:** 13/10/2026 ([registro](prompts/2026-10-13-003-cartoes-manuais-plano.md))  
**Questão:** como paginar as listagens sem limite natural? É o caso dos cartões de uma matéria na spec 003 e, depois, das conversas e mensagens da 014. As listas da 002 dispensam paginação por causa das cotas.  
**Critérios:**

- nenhum item repetido ou pulado quando há criação ou exclusão entre as páginas;
- custo constante por página;
- contrato estável e documentado no OpenAPI;
- integração com o TanStack Query (DTEC 015);
- cursor inútil para enumerar recursos de outro estudante.

**Alternativas consideradas:**

1. ***Keyset* com cursor opaco:** a ordem é sempre total, com o `id` como desempate (ex.: `criado_em desc, id desc`). O cursor codifica, em base64url, a chave do último item da página e um resumo dos filtros. A consulta seguinte usa `(criado_em, id) < (:c, :i)`.
2. ***Offset* e limite:** simples, mas repete ou pula itens quando a lista muda entre as páginas, e o custo cresce com o *offset*.
3. **Sem paginação:** inviável numa matéria com centenas de cartões gerados.

**Decisão:** alternativa 1, como convenção da API.  
**Justificativa:** é a única alternativa estável sob escrita concorrente e com custo constante. O `useInfiniteQuery` do TanStack Query consome o cursor diretamente.  
**Consequências:**

- **Resposta:** `{itens, proximoCursor, total}`. `proximoCursor` é nulo na última página, e `total` conta todos os itens que atendem aos filtros, não só os da página. A requisição aceita `cursor` (opaco) e `limite` (padrão 50, de 1 a 100).
- **Cursor:** guarda só a chave de ordenação e um resumo dos filtros. Como toda consulta também filtra pelo dono (DTEC 019), um cursor adulterado, de outra lista ou de outro estudante não revela nada. Cursor malformado ou de filtros diferentes dos atuais responde `422 cursor_invalido`.
- **Índice:** cada listagem paginada tem um índice que cobre o filtro de dono e a ordem.

**Condição para revisão:** uma tela que precise saltar para páginas arbitrárias, o que nenhuma tela prevista exige.

## Fontes consultadas

- Documentação oficial do pytest (fixtures, parametrização, marcadores e plugins).
- Documentação oficial do `unittest` da biblioteca padrão do Python.
- Índice de pacotes do Python (PyPI), consultado em 29/09/2026 para a versão estável mais recente do pytest.
- [`produto/pendencias.md`](produto/pendencias.md), QA-18, para a comparação entre os frameworks do backend.
- Página de preços do Workers AI da Cloudflare (`developers.cloudflare.com/workers-ai/platform/pricing/`) e página do modelo `bge-reranker-base`, consultadas em 12/10/2026.
- Página de preços do R2 da Cloudflare (`developers.cloudflare.com/r2/pricing/`), consultada em 12/10/2026.
- Página de limites da API do Gemini (`ai.google.dev/gemini-api/docs/rate-limits`) e fontes secundárias sobre a camada gratuita, consultadas em 12/10/2026 (os limites gratuitos são exibidos por projeto no painel do provedor).
- Documentação do Procrastinate (`procrastinate.readthedocs.io`, páginas "Instantiate your connector" e "Using an external database connection"), consultada em 12/10/2026 para a emenda da DTEC 002.
- Documentação do Procrastinate (`procrastinate.readthedocs.io/en/stable`, páginas "Retry a task", "Queueing locks" e "Retry stalled jobs"), consultada em 13/10/2026 para as DTEC 024 a 030.
- Documentação da biblioteca padrão do Python (`multiprocessing` com o contexto `spawn` e `resource.setrlimit`), consultada em 13/10/2026 para a DTEC 024.
- Documentação do PostgreSQL 17 (módulo `unaccent`, funções `lower` e `LIKE` com `ESCAPE`, comparação de linhas), consultada em 13/10/2026 para as DTEC 033 e 034.
- Esboço de arquitetura de 12/10/2026, hoje [`arquitetura/referencia-pos-academica.md`](arquitetura/referencia-pos-academica.md).
