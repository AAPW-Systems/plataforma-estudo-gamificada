# Sistemas inteligentes aplicados 



## Conteúdos previstos: aulas 1 a 5 

- 01 Sistemas inteligentes, LLMs e contexto 

- 02 Specs, critérios de aceitação e SDD 

- 03 RAG com respostas fundamentadas 

- 04 Busca híbrida e qualidade do RAG 

- 05 Agentes, ferramentas e memória 

3 

## Conteúdos previstos: aulas 6 a 10 

- 06 MCP e integração com sistemas 

- 07 Agent Skills e procedimentos reutilizáveis 

- 08 Sistemas multiagentes e visão de A2A 

- 09 Evals, segurança e observabilidade 

- 10 Demonstração e defesa dos projetos 

4 

## Como os conceitos se conectam 

RAG 

Agentes 

Busca evidências nos dados para apoiar a resposta. 

Escolhem passos e ferramentas dentro de limites definidos. 

MCP e skills MCP conecta capacidades. Skills orientam procedimentos reutilizáveis. 

Specs e evals 

Specs descrevem o esperado. Evals verificam o comportamento. 

5 

## Escolha de IA com justificativa 

### Possibilidades 

LLM com RAG, classificação, recomendação, visão computacional ou previsão. 

A IA deve resolver uma necessidade observável do usuário. 

### Evidência esperada 

Uma solução de referência simples, casos de teste e comparação dos resultados. 

Custo, qualidade e limitações orientam a escolha. 

6 

## Projeto integrador: um web app em produção 

Produto de escopo controlado 

Uma jornada completa que o usuário consiga executar. 

Interface utilizável 

Backend e persistência 

O grupo negocia o MVP com o professor/PO e demonstra incrementos ao longo do projeto. 

IA no fluxo principal 

Testes e documentação 

URL publicada e operação 

7 

## Professor como cliente e Product Owner 

Professor / PO Define a visão do produto e ordena o backlog. 

Grupo de estudantes 

Planeja e executa o trabalho técnico. 

Esclarece requisitos e participa das reviews. Decide prioridades com base no que o grupo demonstra. 

Designa um Scrum Master para facilitar o processo. 

Assume qualidade, documentação e entrega. 

9 

## Lean Inception adaptada ao curso 

Visão e problema Quem enfrenta o problema e qual resultado deseja? 

Personas e jornada 

Quais etapas e dificuldades orientam o produto? 

Funcionalidades e riscos O que tem valor, o que é viável e o que precisamos validar? 

MVP e experimentos Qual entrega pequena permite aprender com usuários? 

10 

## Acordo do MVP com o PO 

Escopo incluído 

Uma persona, uma jornada principal e até três capacidades essenciais. 

Hipótese de valor Uma melhoria observável, com forma de medição definida. 

### Escopo adiado 

Ideias para depois, com justificativa e registro no backlog. 

Critérios de sucesso Comportamento esperado, dados de teste e limites de operação. 

11 

## Scrum na rotina dos grupos 

Sprint Planning 

Objetivo da sprint e seleção do trabalho pelo grupo. 

Sprint Review com o PO Produto em funcionamento, feedback e atualização do backlog. 

### Daily Scrum 

Até 15 minutos para inspecionar o avanço e ajustar o plano. 

Retrospectiva 

Uma melhoria concreta de processo para a próxima sprint. 

12 

## Reuniões de acompanhamento com o PO 

### Incrementos e decisões 

Cada grupo chega com uma versão executável e perguntas objetivas. 

Objetivo e demonstração 

Critérios atendidos e pendências 

As decisões da reunião orientam o próximo ciclo. 

Feedback registrado Prioridades atualizadas 

Responsáveis e próximos passos 

13 

## Documentação como parte do trabalho 

### Produto e processo 

Visão, Lean Inception e Canvas MVP. Backlog, objetivos e registros das sprints. Atas com o PO e feedback de usuários. Decisões estratégicas e riscos. 

Engenharia e operação Specs, registro de decisão arquitetural e diagramas. Prompts, uso de IA e avaliações. Testes, PRs e releases. 

Deploy, monitoramento e recuperação. 

15 

## Registro do uso de IA e dos prompts 

### Identificação 

Entrada 

Data, autor, ferramenta, modelo e tarefa ou issue relacionada. 

Prompt, contexto, anexos e versão da spec utilizada. 

Resultado 

Verificação 

Saída relevante, alterações humanas e decisão de aceitar ou rejeitar. 

Testes executados, falhas encontradas e link para commit ou PR. 

16 

## Specs que orientam implementação e testes 

### Exemplo de requisito 

Como estudante, quero consultar um prazo e verificar sua fonte. 

Critérios verificáveis Com fonte disponível, retornar prazo e referência. 

A spec define entrada, resposta, evidência e tratamento de ausência de informação. 

Sem evidência, informar a limitação. Com serviço indisponível, apresentar erro tratável. 

17 

## Decisões estratégicas e de arquitetura 

### Registro estratégico 

ADR técnico 

Problema e opções consideradas. Valor, prazo, custo e riscos. Decisão e justificativa. 

Contexto e alternativas. Decisão e consequências. Evidências ou experimento. 

Condição para revisitar a escolha. 

Autor, data e status. 

18 

## Arquitetura de referência 

Experiência web Aplicação e dados Interface responsiva, API, regras de negócio, validação e comunicação clara controle de acesso e de estados e erros. armazenamento persistente. 

Capacidade de IA Modelo ou serviço, contexto e ferramentas, com limites e avaliação. 

19 

## RAG e agentes no produto 

Conhecimento confiável 

Fontes autorizadas e rastreáveis. 

Estratégia de busca documentada. Referências verificáveis. 

Resposta prevista para informação ausente. 

### Ações controladas 

Ferramentas com entradas validadas. Permissões mínimas e limite de passos. Confirmação para ações relevantes. Registro dos resultados executados. 

20 

## Dados e segurança 

### Dados adequados 

Origem, licença, qualidade e separação de dados de avaliação. 

Segredos 

Chaves fora do código e do navegador. Configuração por ambiente. 

Acesso 

Autenticação quando necessária e autorização no backend. 

Uso responsável 

Minimização de dados, instruções maliciosas e aprovação de ações. 

21 

## Testes de software 

Unidade 

Regras de negócio e casos de borda com execução rápida. 

Ponta a ponta 

Jornada principal no navegador, incluindo um caminho de erro. 

### Integração 

API, banco e contratos com serviços externos. 

Qualidade adicional Acessibilidade básica, segurança e tempo de resposta. 

22 

## Avaliação da capacidade de IA 

Conjunto de casos 

Ao menos 15 casos relevantes, com respostas ou critérios de referência. 

Robustez 

Casos ambíguos, ausência de dados, entradas adversariais e repetição. 

Métricas adequadas 

Classificação: precisão e recall. RAG: evidência e correção. Agentes: sucesso da tarefa. 

Viabilidade Latência, consumo e custo por tarefa, com limites conhecidos. 

23 

## Git, revisão de código e CI/CD 

Entrega rastreável 

Cada mudança relevante se conecta ao backlog e passa por revisão. O pipeline automatiza as verificações antes de publicar. 

Issue e branch identificáveis 

Pull request revisado 

Testes no pipeline 

Build e release versionados 

Deploy com verificação 

24 

## Publicação e operação do web app 

### Ambiente acessível ao PO 

O produto precisa funcionar fora da máquina do grupo. 

A equipe demonstra publicação, atualização e recuperação. 

URL com HTTPS 

Configuração e dados persistentes 

Logs e verificação de saúde 

Backup e restauração testados 

Rollback documentado 

25 

## Containers e Kubernetes 

Requisito essencial proposto Containerização reproduzível do backend ou equivalente justificado em ADR. 

Deploy funcional, health check e procedimento de rollback. 

Aprofundamento com Kubernetes 

Deployment e Service. 

Configuração e gestão de segredos. Readiness, liveness e limites de recursos. 

Demonstração de atualização e recuperação. 

26 

## Observabilidade e continuidade 

Logs úteis 

### Métricas 

Identificação da requisição, erros e etapas críticas, sem segredos. 

Disponibilidade, latência, falhas e consumo da IA. 

Limites 

Runbook 

Timeouts, retries limitados e orçamento de chamadas. 

Como detectar, investigar e recuperar uma falha. 

27 

## Definition of Done do projeto 

Critério comum de conclusão 

O grupo combina a Definition of Done antes da primeira sprint e a revisita quando necessário. 

Critérios de aceitação atendidos 

Código revisado e testes passando 

IA avaliada e limitações registradas Docs e decisões atualizadas 

Incremento utilizável e demonstrável 

28 

## Rastreabilidade das evidências 

Origem 

Necessidade do cliente e item priorizado no backlog. 

Implementação Prompt relevante, commit, pull request e revisão humana. 

Decisão 

Spec, alternativas e ADR quando necessário. 

Resultado 

Teste, release, demonstração ao PO e feedback. 

31 

## Entrega final e demonstração 

Pacote de evidências 

O PO recebe acesso ao produto e consegue localizar as informações necessárias para avaliá-lo. 

URL e instruções de acesso Repositório e release final 

Dossiê de produto e processo Testes, evals e custos 

Runbook e defesa do grupo 

32 

