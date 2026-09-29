# Plano de implementação da plataforma de estudos gamificada

Versão 0.1, 25/09/2026. 

Plano técnico condicionado às questões QA de [Spec.md](Spec.md). 
Referências: [SKILL.md](SKILL.md), [DESIGN.md](DESIGN.md) e [Tasks.md](Tasks.md).

## 1. Resumo técnico

Implementar aplicação web com View em React JSX, API com Controllers e Model contendo regras e persistência. Separar processamento demorado do atendimento HTTP. Organizar módulos de identidade, materiais, processamento, trilhas, estudos e evolução. Manter correção e efeitos de gamificação autoritativos no servidor.

Proposta de partida, ainda dependente de QA-01/11: uma aplicação modular com API e executor de tarefas compartilhando regras de domínio. Usar IA restrita aos materiais enviados, com modelo e provedor ainda a selecionar. Não pressupor microserviços ou broker externo. Escolher mecanismos após confirmar infraestrutura e capacidade.

Executar por incrementos verificáveis: fundação → materiais → processamento e trilhas → estudo → evolução → operação. Não substituir decisões de negócio por escolhas incidentais de implementação.

## 2. Contexto técnico

| Aspecto | Contexto atual | Decisão necessária |
| --- | --- | --- |
| Linguagem/backend | Não definida | QA-01: linguagem, runtime e versões suportadas |
| Frontend | JavaScript e JSX; React como preferência | QA-01: confirmar stack, versões e build |
| Dependências | Sem pacotes ou versões selecionados | Escolher validação, acesso a dados, autenticação, testes, OpenAPI e biblioteca visual segundo QA-01/02 |
| Persistência | Entidades e invariantes de Spec.md; tecnologia aberta | QA-01: banco, migrações, transações, unicidade e estratégia de concorrência |
| Arquivos | Referência interna, propriedade e acesso controlado | QA-03/05/11: armazenamento, limites, retenção e limpeza |
| Processamento | Assíncrono; IA com fontes restritas aos materiais enviados | QA-04/11: extrator, gerador, executor, timeout e eventual fila |
| Testes | Regras unitárias, integração real de persistência, contrato, E2E e operação | QA-01: ferramentas e execução em integração contínua |
| Plataforma | Web responsiva; navegador em desktop e celular | QA-11: hospedagem, ambientes e matriz de navegadores |
| Desempenho | Nenhum SLA ou tempo quantitativo aprovado | QA-11: p95 de operações interativas e duração de processamento por faixa de arquivo |
| Escala | Nenhum volume confirmado | QA-11: concorrência, arquivos/dia, bytes, crescimento e retenção |
| Datas | UTC para instantes; fuso de negócio pendente | QA-09: fuso e períodos |

Não preencher lacunas com versões “mais recentes” ou comandos presumidos. Ao selecionar tecnologias, verificar compatibilidade nas fontes oficiais e registrar versões fixadas, diretórios e comandos efetivamente disponíveis.

## 3. Verificação da constituição

“Constituição” refere-se aos princípios já presentes em SKILL.md e DESIGN.md; a tabela não cria outro documento nem altera os originais. A evidência abaixo é prevista, ainda não produzida.

| principio | como o plano atende | a evidencia prevista |
| --- | --- | --- |
| MVC obrigatório | View, Controller e Model com limites explícitos e módulos de domínio | Mapa de camadas e revisão de dependências em T-010/T-013 |
| Código limpo e português | Identificadores próprios claros, convenção da linguagem e comentários apenas de motivo | Configuração de estilo e revisão em T-010 e T-092 |
| Normalização de textos | Utilitários por finalidade sem destruir conteúdo original | Testes Unicode e espaços em T-013 |
| Datas consistentes | UTC, formato ISO e agregação no fuso aprovado | Testes de fronteira em T-013/T-042 |
| Validação nas duas pontas | Contratos de limite compartilhados ou derivados e validação autoritativa | Testes de fronteira de API e UI em T-021/T-023 |
| Exceções uniformes | Conversão central para erros documentados com correlação | Testes de contrato e logs em T-014/T-090 |
| Histórico e idempotência | Versão de questão, identidade de tentativa e efeitos consistentes | Testes concorrentes e de recuperação em T-040/T-041 |
| Conteúdo completo e rastreável | Validar estrutura e sustentação nos trechos enviados; bloquear atividades sem apoio e não pesquisar fontes externas | Corpus de referência e falhas de geração em T-030/T-031 |
| Swagger/OpenAPI | Contratos atualizados por incremento e verificação automatizada | Especificação e Swagger UI em T-014/T-092 |
| Interface limpa e consistente | Tema e componentes reutilizados conforme DESIGN.md | Revisão visual de T-012/T-091 |
| Acessibilidade e estados | Teclado, foco, contraste e estados vazios/erro/carregamento | Cenários E2E e revisão manual em T-091 |
| Isolamento de usuário | Autorização também em arquivo e tarefas assíncronas | Testes negativos em T-011/T-024/T-090 |
| Comandos verificáveis | Registrar e executar build, test e run da stack escolhida | Execução reproduzível em T-010/T-092; atualização dos originais somente se autorizada |

## 4. Arquitetura e fluxo

### Responsabilidades

- **View:** páginas, componentes, estado de interação, validação de entrada e apresentação de estados. Recebe métricas calculadas, não as redefine.
- **Controller:** autenticação/contexto, leitura e validação de requisição, chamada do caso de uso e resposta HTTP. Sem extração de livros ou concessão de pontos embutidas.
- **Model:** entidades, regras, correção, elegibilidade, conclusão e invariantes; persistência isolada conforme convenção da stack.
- **Serviços de aplicação, quando úteis:** coordenam casos de uso e transações. Adaptadores de arquivo, extração e geração isolam dependências externas. Executor reutiliza regras do Model.

### Módulos e contratos

| Módulo | Entrada/saída principal | Requisitos |
| --- | --- | --- |
| Identidade | Contexto autenticado e autorização de proprietário | RF-01 |
| Materiais | Metadados e arquivo → material admitido; consultas e gerenciamento | RF-02/03 |
| Processamento | Identidade da execução → estado e conteúdo validado | RF-04 |
| Trilhas | Material/versão → trilha, etapas e referências | RF-05 |
| Estudos | Questão sem gabarito; tentativa → correção; flashcard → frente/verso autorizado | RF-06/07/08 |
| Evolução | Tentativas e eventos elegíveis → pontos, progresso e concessões | RF-09/10/11/12 |
| Documentação | Contratos reais → OpenAPI/Swagger UI | RF-13 |

Detalhar caminhos HTTP após QA-01. Usar contratos diferentes para apresentação da questão e correção; não serializar a entidade de persistência diretamente. Definir paginação, enumerações e erros uniformes. Estado assíncrono retorna identidade consultável; transporte por polling ou outro mecanismo fica condicionado ao ambiente.

### Fluxo de material e publicação

1. Validar identidade, campos e limites antes de admitir processamento; finalizar arquivo de forma verificável.
2. Persistir material e intenção de processamento. Garantir que falha entre persistência e agendamento seja recuperável por mecanismo durável escolhido na stack.
3. Executor obtém execução e valida propriedade/referências. Extrai texto por seções preservando material, versão, trechos e localização. OCR/análise visual dependem do formato aprovado. Identifica tópicos do edital e cobertura pelos materiais; distingue lacuna pedagógica de falha técnica. Seleciona somente trechos dos materiais autorizados para a trilha, sem pesquisa externa. Gera questão e flashcard a partir desses trechos em saída estruturada, com limites de tempo e tamanho definidos.
4. Validar estrutura pelo código e sustentação semântica da resposta/explicação nos trechos; identificar ambiguidade e contradição. Verificar referências, não apenas aceitar citações emitidas pelo modelo. Separar conteúdo em preparação de conteúdo publicável. Se insuficiente, registrar assunto aguardando apoio; não forçar quantidade nem usar conhecimento externo. A revisão por IA é auxiliar; medir qualidade com corpus revisado por pessoa responsável.
5. Publicar a versão aprovada de forma consistente e concluir execução. Falha mantém conteúdo inválido fora do estudo e registra diagnóstico sanitizado.
6. Guardar modelo, versão das instruções e vínculos de evidência. Persistir atividades aprovadas para reutilização e corrigir tentativas pelo gabarito salvo, sem chamar IA a cada resposta. Reexecução técnica usa identidade estável; nova geração segue política QA-04. Se houver fila, assumir possibilidade de entrega repetida, sem prometer execução exatamente uma vez.

### Fluxo de resposta e gamificação

1. Cliente obtém questão/versão sem gabarito e cria identidade de tentativa antes do primeiro envio.
2. Controller valida formato; Model verifica dono, versão, alternativa e disponibilidade conforme QA-07.
3. Consultar identidade: mesma entrada retorna resultado original; entrada divergente gera conflito.
4. Registrar tentativa e efeitos elegíveis de pontos, progresso e conquistas de forma atômica quando suportado. Se houver efeitos assíncronos, usar registro durável e consumidores idempotentes; comunicar eventual pendência na UI.
5. Retornar correção e métricas confirmadas. Timeout permite reenviar a identidade original; uma nova tentativa intencional usa outra identidade.

Preferir consistência transacional simples no primeiro incremento quando a persistência escolhida permitir. Registrar versão da regra de pontuação e de conteúdo para preservar histórico. Índices de unicidade devem proteger identidades de tentativa, origens pontuadas e concessões, além das verificações no código.

### Persistência e ciclo de vida

Traduzir entidades de Spec.md em esquema com vínculos e índices por proprietário, trilha e período de consulta. Escolher entre projeção calculada e materializada de progresso após fórmulas e carga conhecidas. Se materializar, prever reconstrução a partir dos dados de origem e verificar divergências.

Excluir/arquivar arquivos e derivados apenas segundo QA-05. Coordenar exclusão com execuções ativas e respostas em andamento. Migrações devem preservar versões históricas; não reescrever tentativas ao editar gabarito.

### Interface

Implementar Início, Materiais, Trilhas/Etapas, Questões, Flashcards e Evolução conforme DESIGN.md. Estados da API orientam mensagens e disponibilidade. Distinguir estado da execução de cobertura por assunto; exibir “aguardando material de apoio” e ação de enviar complemento. Mostrar evidências após correção e no verso do flashcard, respeitando a política de acesso para evitar gabarito prematuro. Desenvolver componentes de campo, botão, seleção, aviso, diálogo e progresso antes dos fluxos. Não criar telas de autenticação específicas até QA-02; não introduzir rankings ou edição de conteúdo fora do escopo.

## 5. Estratégias de teste

| Nível | Foco | Referências e evidência |
| --- | --- | --- |
| Unidade | Normalização, datas, validadores de questão, fórmulas e elegibilidade | RN-02/04/07/08/10; valores de fronteira e exemplos aprovados |
| Integração | Banco real de teste, transações, unicidade, propriedade e histórico | HU-01/06/09/10; CB-04/07/08/12 |
| Arquivos e processamento | Fixtures válidas, vazias, corrompidas, interrompidas e geração inválida | HU-02/03/04; CB-01 a CB-06/14 |
| Contrato | OpenAPI, erros, autenticação e ausência de gabarito pré-resposta | HU-12, CS-03/06; CB-11 |
| Interface/E2E | Fluxo principal, recuperação de erro, revisão e continuação | HU-02 a HU-11; estados visuais e navegação |
| Acessibilidade | Teclado, foco, rótulos, contraste e leitura responsiva | RQ-03, CS-05; automação mais revisão humana |
| Conteúdo | Fontes exclusivas, fidelidade, explicações, origem, edital sem apoio e evidências falsas | RQ-07, HU-13/14, CB-15/16; corpus com resposta esperada e revisão humana, além da validação de formato |
| Carga e operação | Concorrência, saturação, retomada de executor e restauração | RQ-04/08, QA-11; carga, ambiente e metas registrados |

Usar fixtures determinísticas e dados sintéticos sem informações pessoais. Substituir provedor externo por adaptador controlado em testes de falha; executar avaliação representativa separada do gerador real quando houver. Não exigir que um teste estrutural prove a verdade de uma questão gerada.

Cada tarefa de funcionalidade inclui testes de seus critérios; T-090 a T-094 verificam o sistema integrado. Não usar percentual de cobertura isolado como prova de qualidade. Documentar HU/CB executados, resultado e limitações; cenário bloqueado não equivale a aprovado.

## 6. Observabilidade e operação

- **Logs:** eventos estruturados de upload, transição de execução, publicação, tentativa, pontuação e erro. Correlacionar requisição e processamento com identificadores; não registrar texto integral de livros, senhas, tokens ou gabaritos em logs de rotina.
- **Métricas:** latência e falhas por operação, execuções pendentes/ativas/falhas, tempo de processamento por faixa de arquivo, armazenamento, conflitos idempotentes e falhas de consistência. Se houver serviço pago, medir uso/custo conforme orçamento aprovado.
- **Alertas:** definir limiares e responsável em QA-11 para tarefas paradas, aumento de erro, capacidade e falha de backup. Não fixar limiares sem linha de base.
- **Recuperação:** registrar timeouts, tentativas automáticas limitadas, atraso entre tentativas e tratamento de execução irrecuperável. Só repetir falhas transitórias; entrada inválida requer correção.
- **Ambientes:** separar desenvolvimento, teste e produção; segredos por configuração externa. Fornecer exemplo de variáveis sem valores secretos e comandos reproduzíveis da stack.
- **Dados:** planejar backup de banco e arquivos, retenção, restauração e consistência entre ambos. Confirmar RPO e RTO antes do teste operacional.
- **Entrega:** aplicar migrações controladas, verificar saúde da API e executor e definir reversão compatível com dados existentes. Não pressupor que reverter código desfaz migração destrutiva.
- **Rotina de operação:** documentar como localizar falhas, reprocessar sem duplicar, restaurar backup, limpar arquivos órfãos e verificar divergência de progresso. Definir responsáveis e acesso à documentação em QA-11.

## 7. Riscos técnicos

| ID | Risco | Impacto | Mitigação/verificação prevista | Dependência |
| --- | --- | --- | --- | --- |
| RT-01 | Stack e infraestrutura indefinidas | Retrabalho e comandos inválidos | Resolver decisões antes de inicializar aplicação | QA-01/11; T-001/006 |
| RT-02 | Extração ruim ou geração incorreta | Conteúdo pedagógico inadequado | Corpus representativo, avaliação semântica e política de publicação | QA-03/04; T-003/030 |
| RT-03 | Reentrega/concorrência | Pontos, trilhas ou conquistas duplicadas | Identidades, unicidade e testes de interrupção | T-031/040/041 |
| RT-04 | Edição/exclusão altera histórico | Resultados inconsistentes | Versionamento, política de ciclo de vida e testes concorrentes | QA-05/07; T-022/040 |
| RT-05 | Falha entre banco, arquivo e executor | Tarefas perdidas e arquivos órfãos | Intenção durável, reconciliação e limpeza controlada | T-020/031/093 |
| RT-06 | Gabarito ou dados de outro usuário expostos | Perda de confiança e isolamento | Contratos separados e autorização em todos os caminhos | QA-10; T-011/040/090 |
| RT-07 | Progresso/recompensas ambíguos | Métricas incoerentes e abuso de repetição | Exemplos numéricos aprovados antes do código | QA-06/07/08/09; T-004 |
| RT-08 | Processamento excede capacidade/orçamento | Fila crescente e indisponibilidade | Limites, métricas e carga com metas aprovadas | QA-11; T-006/093 |
| RT-09 | UI parece pronta sem tratar falhas | Fluxo incompleto para o estudante | Estados de erro, limites e E2E com falhas | T-023/033/044/091 |
| RT-11 | IA usa conhecimento externo ou cita trecho que não sustenta a resposta | Atividades sem fundamento | Desabilitar busca externa, filtrar materiais por usuário/trilha e validar sustentação; testar lacunas e citações enganosas | RN-11/13; T-030/035/090 |
| RT-10 | Documentos divergem do código | Desenvolvimento perde rastreabilidade | Atualizar Spec/Plan/Tasks e contratos por decisão; pedir autorização para originais | T-007/094 |

## 8. Condições para execução e aceite

Decisões independentes podem avançar em paralelo, conforme Tasks.md. Tarefas bloqueadas por QA não devem ser encerradas com valores inventados. Uma prova técnica pode usar hipótese identificada e descartável, sem promovê-la a decisão definitiva.

O aceite requer CS-01 a CS-07 de Spec.md, evidências reais e resolução das pendências incidentes no escopo entregue. Nesta revisão, a solicitação do usuário autoriza adequar SKILL.md e DESIGN.md à política de IA e fontes exclusivas. Outras mudanças continuam sujeitas à autorização pertinente. Caso uma escolha futura conflite com eles, interromper apenas a mudança dependente e solicitar autorização explícita para a edição.
