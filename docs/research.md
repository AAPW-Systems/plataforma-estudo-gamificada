# Pesquisa e decisões técnicas do projeto

**Funcionalidade:** projeto (decisões transversais, válidas para todas as specs)  
**Data:** 29/09/2026 (DTEC 001); 12/10/2026 (DTEC 002 a 014, [registro](prompts/2026-10-12-alinhamento-produto-arquitetura.md))

Este arquivo registra as decisões técnicas que valem para o projeto inteiro, no formato do [modelo de `research.md`](sdd_guidelines/modelos/research.md). Decisões específicas de uma funcionalidade ficam no `research.md` da pasta da spec correspondente (`docs/specs/NNN-nome-curto/`). As questões técnicas ainda abertas estão em [`produto/pendencias.md`](produto/pendencias.md) e, quando decididas, entram aqui como novas decisões `DTEC`.

A visão de conjunto das decisões, por estágio (MVP, final acadêmico e referência pós-acadêmica), está em [`arquitetura/README.md`](arquitetura/README.md). As alternativas mais robustas não adotadas, com custo e gatilho de adoção, estão em [`arquitetura/referencia-pos-academica.md`](arquitetura/referencia-pos-academica.md).

**Critério comum às DTEC 002 a 014:** o deploy do final acadêmico é obrigatório e pago pela equipe, numa VPS de 2 a 4 GB de RAM (RQ-09 da [base de especificação](base-specs/spec.md)). Entre alternativas tecnicamente equivalentes, vence a que não acrescenta serviço residente na VPS.

| Decisão | Título | Status |
|---|---|---|
| [DTEC 001](#decisão-dtec-001-ferramenta-de-testes-do-backend) | Ferramenta de testes do backend | Decidida por Artur Lins em 29/09/2026; aprovação da equipe pendente ([VAL-05](produto/pendencias.md#val-05-aprovação-das-regras-de-git-e-testes)) |
| [DTEC 002](#decisão-dtec-002-framework-do-backend) | Framework do backend | Aprovada em 12/10/2026; encerra QA-18 ([VAL-06](produto/pendencias.md#val-06-aprovação-da-arquitetura-e-das-dtec-002-a-014)) |
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

## Fontes consultadas

- Documentação oficial do pytest (fixtures, parametrização, marcadores e plugins).
- Documentação oficial do `unittest` da biblioteca padrão do Python.
- Índice de pacotes do Python (PyPI), consultado em 29/09/2026 para a versão estável mais recente do pytest.
- [`produto/pendencias.md`](produto/pendencias.md), QA-18, para a comparação entre os frameworks do backend.
- Página de preços do Workers AI da Cloudflare (`developers.cloudflare.com/workers-ai/platform/pricing/`) e página do modelo `bge-reranker-base`, consultadas em 12/10/2026.
- Página de preços do R2 da Cloudflare (`developers.cloudflare.com/r2/pricing/`), consultada em 12/10/2026.
- Página de limites da API do Gemini (`ai.google.dev/gemini-api/docs/rate-limits`) e fontes secundárias sobre a camada gratuita, consultadas em 12/10/2026 (os limites gratuitos são exibidos por projeto no painel do provedor).
- Esboço de arquitetura de 12/10/2026, hoje [`arquitetura/referencia-pos-academica.md`](arquitetura/referencia-pos-academica.md).
