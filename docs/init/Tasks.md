# Tarefas da plataforma de estudos gamificada

Versão 0.1, 25/09/2026. 
Base: [Spec.md](Spec.md), [Plan.md](Plan.md), [SKILL.md](SKILL.md) e [DESIGN.md](DESIGN.md).

## Como executar e acompanhar

As caixas abaixo representam trabalho futuro, a criação destes documentos não conclui tarefas de implementação. Marcar `[x]` somente com a evidência indicada. 
Cada tarefa lista dependências obrigatórias, tarefas sem dependência entre si podem avançar simultaneamente após seus pré-requisitos. 
Paralelismo é uma possibilidade de planejamento, não uma instrução para criar agentes ou executar trabalho agora.

Resolver questões QA em Spec.md e registrar as escolhas técnicas correspondentes em Plan.md. Preservar IDs e atualizar vínculos quando o escopo mudar. Não alterar SKILL.md ou DESIGN.md sem autorização prévia. Manter a estrutura dos três documentos; solicitar antes qualquer mudança nessa estrutura.

## Fase 0 — Refinamento e decisões

Objetivo: converter lacunas em decisões testáveis. As tarefas T-001 a T-006 podem ser discutidas em paralelo; T-007 consolida a consistência.

- [ ] **T-001 — Definir stack e ferramentas.** Resolver QA-01: linguagem/versões, framework, banco, persistência, frontend, biblioteca visual, build e testes. Registrar compatibilidade e motivos em Plan.md. **Depende de:** nenhuma. **Pronto quando:** escolhas e versões estão registradas, sem confundir React preferido com backend definido.
- [ ] **T-002 — Definir identidade e admissão.** Resolver QA-02 e QA-03 com método de acesso, formatos, cotas, campos e limites exatos. **Depende de:** nenhuma. **Pronto quando:** contrato de usuário e tabela de limites permitem escrever testes de fronteira. **Cobre:** RF-01/02/03, HU-01/02.
- [ ] **T-003 — Definir conteúdo e ciclo de vida.** Resolver as partes restantes de QA-04, QA-05 e QA-10: modelo/provedor, extração, corpus, critério de qualidade, publicação, relações, reprocessamento, exclusão e acesso a flashcards. A geração por IA com fontes exclusivamente enviadas já está decidida. Definir vínculo de material complementar e política para conflitos. **Depende de:** nenhuma para refinamento; compatibilizar formatos com T-002 antes de concluir. **Pronto quando:** políticas têm exemplos de sucesso, falha, repetição e exclusão com histórico. **Cobre:** RF-03/04/05/08, CB-01/04/05/06/11/12.
- [ ] **T-004 — Definir estudo e gamificação.** Resolver QA-06 a QA-09: fórmulas, versões, idempotência, retentativas, conquistas, fuso e continuação. **Depende de:** nenhuma. **Pronto quando:** exemplos numéricos aprovados cobrem primeira tentativa, erro, acerto, repetição, trilha vazia e mudança de conteúdo. **Cobre:** RF-06/07/09/10/11/12.
- [ ] **T-006 — Definir metas e operação.** Resolver QA-11: ambiente, escala, latência, processamento, custo, RPO/RTO e responsáveis. **Depende de:** nenhuma para refinamento; alinhar viabilidade com T-001/T-003. **Pronto quando:** metas incluem valor, unidade, carga e método de medição. **Cobre:** RQ-04/06/08, CS-07.
- [ ] **T-007 — Consolidar baseline.** Atualizar Spec e Plan com decisões; conferir escopo e matriz de aceitação. **Depende de:** T-001, T-002, T-003, T-004, T-006. **Pronto quando:** não há QA bloqueante para o incremento a iniciar; eventual mudança nos originais foi apresentada e autorizada antes da edição. Uma decisão sem impacto nos originais não exige editá-los.

## Fase 1 — Fundação técnica e contratos

Objetivo: uma base executável com princípios verificáveis. T-011, T-012 e T-013 podem avançar em paralelo após T-010; T-014 integra contratos e erros.

- [ ] **T-010 — Inicializar aplicação e verificações.** Criar estrutura MVC, configuração por ambiente, dependências fixadas e comandos reais de build, test e run. **Depende de:** T-007. **Pronto quando:** aplicação inicia e build/verificações executam em ambiente limpo; dependências entre camadas estão documentadas. **Cobre:** DC-02/03, RQ-05.
- [ ] **T-011 — Implementar identidade e autorização.** Implementar o mecanismo aprovado, contexto de usuário e proteção de recursos. **Depende de:** T-010. **Pronto quando:** usuário sem sessão e usuário de outro recurso não conseguem ler/alterar dados; testes executados. **Cobre:** RF-01, HU-01, RQ-01.
- [ ] **T-012 — Criar base visual.** Implementar tema, navegação, campos, botões, diálogos, avisos e estados acessíveis. **Depende de:** T-010. **Pronto quando:** componentes funcionam por teclado, têm estados e respeitam DESIGN.md em celular/desktop. **Cobre:** RQ-03/05.
- [ ] **T-013 — Criar modelo e políticas transversais.** Implementar esquema inicial, migrações, normalização, datas e validações comuns; preparar relações/versões das entidades aprovadas. **Depende de:** T-010. **Pronto quando:** migração funciona e testes cobrem Unicode, datas, referências e limites. **Cobre:** RN-01/04/10, entidades de Spec.md.
- [ ] **T-014 — Firmar contratos e erros.** Criar contratos de operações por módulo, formato uniforme de erro, correlação, OpenAPI e Swagger UI. **Depende de:** T-011, T-013. **Pronto quando:** contratos refletem limites aprovados, autenticação e separação entre questão e correção; exemplos de sucesso/erro validados. **Cobre:** RF-13, HU-12, RQ-06.

## Fase 2 — Materiais de ponta a ponta

Objetivo: enviar e gerenciar material com isolamento e falhas tratadas. T-020 e T-021 podem avançar em paralelo com contratos estáveis; T-023 pode usar respostas simuladas do contrato antes da integração T-024.

- [ ] **T-020 — Implementar armazenamento.** Receber/finalizar arquivos com identificadores internos, acesso controlado e tratamento de upload interrompido. **Depende de:** T-011, T-013, T-014. **Pronto quando:** arquivo incompleto não entra em processamento e acesso cruzado é negado. **Cobre:** RN-01/02, CB-03.
- [ ] **T-021 — Implementar admissão e consulta.** Criar API de envio, listagem e detalhe; validar formato real, campos, cotas e paginação. **Depende de:** T-011, T-013, T-014. **Pronto quando:** testes de contratos e limites passam com adaptador de armazenamento; integração real é verificada em T-024. **Cobre:** RF-02/03, HU-02, CB-01/02.
- [ ] **T-022 — Implementar gerenciamento e exclusão.** Aplicar edição/arquivamento/exclusão permitidos e proteger derivados e histórico. **Depende de:** T-020, T-021. **Pronto quando:** política aprovada é executada e casos com referências existentes são testados. **Cobre:** RF-03, RN-09, HU-10.
- [ ] **T-023 — Implementar interface de materiais.** Criar envio, lista, detalhe, erros, vazios e diálogo de impacto. **Depende de:** T-012, T-014. **Pronto quando:** limites e estados funcionam com contratos simulados, sem declarar integração concluída. **Cobre:** RF-02/03, HU-02/10, CB-13.
- [ ] **T-024 — Integrar e aceitar materiais.** Conectar UI, API e arquivo real de teste. **Depende de:** T-020, T-021, T-022, T-023. **Pronto quando:** HU-01/02 e gerenciamento de HU-10 passam, incluindo upload interrompido e fronteiras. **Cobre:** CS-03/05 parcialmente; processamento ainda é fase seguinte.

## Fase 3 — Processamento e trilhas

Objetivo: transformar material válido em conteúdo disponível e rastreável. T-030 e T-031 podem avançar em paralelo após T-024 por adaptadores contratados; T-033 pode trabalhar com contratos simulados em paralelo.

- [ ] **T-030 — Implementar extração e geração.** Criar adaptadores aprovados, extração por seções com trechos versionados, geração estruturada de questão/flashcard a partir das mesmas fontes, validação de estrutura e sustentação semântica. Proibir ferramentas de pesquisa externa e filtrar evidências por proprietário/trilha. Registrar modelo e versão das instruções. **Depende de:** T-024. **Pronto quando:** corpus aprovado atende estrutura e patamar semântico com revisão humana de referência; conteúdo inválido, sem evidência ou contraditório é recusado. A simples aprovação por outra IA não encerra a validação. **Cobre:** RF-04/05/08, RN-04, RQ-07, CB-01/05/14.
- [ ] **T-031 — Implementar execução durável.** Criar estados, agendamento recuperável, limites de repetição e idempotência de execução/publicação. **Depende de:** T-024. **Pronto quando:** interrupção e reentrega não perdem execução nem duplicam conteúdo ativo. **Cobre:** RF-04, RN-03, CB-03/04/06.
- [ ] **T-032 — Persistir e publicar trilhas.** Integrar geração e execução a versões, etapas ordenadas e consultas de conteúdo disponível. **Depende de:** T-030, T-031. **Pronto quando:** só conjuntos válidos são publicados conforme política e histórico não é substituído silenciosamente. **Cobre:** RF-05, RN-03/04/09.
- [ ] **T-033 — Implementar acompanhamento e trilhas na UI.** Exibir estado real, falha/recuperação, etapas e origem, distinguindo assuntos aguardando material de apoio do estado da execução. Oferecer envio de complemento, sem busca externa, conforme vínculo aprovado. **Depende de:** T-012, T-014, T-024. **Pronto quando:** estados e navegação correspondem ao contrato; integração completa em T-034. **Cobre:** RF-04/05, HU-03/04.
- [ ] **T-034 — Aceitar material até trilha.** Executar caminho completo, reprocessamento e falhas com persistência real. **Depende de:** T-032, T-033. **Pronto quando:** HU-03/04 e CB-01/04/05/06 passam, inclusive recuperação após falha. **Cobre:** CS-02 e RQ-07 no fluxo de conteúdo.

- [ ] **T-035 — Verificar fontes exclusivas e lacunas.** Testar edital que lista assunto sem explicação, complemento enviado, referência inventada, trecho real sem sustentação, contradição e tentativa de usar fonte de outro usuário. Conferir geração de exercício derivado verificável sem exigir cópia literal. **Depende de:** T-034. **Pronto quando:** HU-13/14 e CB-15/16 passam, questões sem fundamento não são publicadas e estado de apoio/progresso respeita a política aprovada. **Cobre:** RF-14/15, RN-11/12/13, RQ-07.

## Fase 4 — Estudo, histórico e evolução

Objetivo: registrar aprendizado e efeitos consistentes. T-040 e T-043 podem avançar em paralelo após T-035. A UI T-044 pode começar pelos contratos e integra em T-046.

- [ ] **T-040 — Implementar questão e tentativa.** Separar contrato pré-resposta, corrigir versão, preservar histórico e tratar identidade idempotente/conflito. **Depende de:** T-035. **Pronto quando:** HU-05/06 e CB-07/08 passam sem efeitos duplicados nem vazamento do gabarito pelo contrato. **Cobre:** RF-06/07, RN-05/06.
- [ ] **T-041 — Implementar pontos e conquistas.** Aplicar elegibilidade e versão de regras, registro de origem e unicidade de concessão; integrar atomicidade ou mecanismo durável escolhido. **Depende de:** T-040. **Pronto quando:** exemplos aprovados, concorrência e reenvio produzem os totais esperados. **Cobre:** RF-09/11, HU-06/09, RN-06/08.
- [ ] **T-042 — Implementar progresso e indicadores.** Aplicar fórmula e períodos aprovados, continuação de estudo e estado sem atividade. **Depende de:** T-040. **Pronto quando:** HU-08/11 e CB-09/10 conferem com dados controlados e alterações de trilha. **Cobre:** RF-10/12, RN-07/10.
- [ ] **T-043 — Implementar flashcards.** Criar consulta, frente/verso e regras de acesso/contribuição aprovadas. **Depende de:** T-035. **Pronto quando:** vínculos e política antes/depois da resposta são respeitados. **Cobre:** RF-08, HU-07, CB-11.
- [ ] **T-044 — Implementar interface de estudo e evolução.** Criar questão, feedback, flashcard, pontos, progresso e conquistas com teclado e estados. **Depende de:** T-012, T-014, T-034. **Pronto quando:** contratos simulados cobrem falhas e espera sem mostrar recompensa não confirmada; integração em T-046. **Cobre:** RF-06 a RF-12, RQ-03.
- [ ] **T-045 — Verificar ciclo de vida completo.** Exercitar exclusão/reprocessamento concorrentes com tentativas e conferir histórico e projeções. **Depende de:** T-022, T-041, T-042, T-043. **Pronto quando:** HU-10, CB-08/09/12 e CS-04 passam com dados de estudo reais de teste. **Cobre:** RN-09, RQ-02/08.
- [ ] **T-046 — Aceitar jornada integrada.** Conectar interfaces e serviços e executar estudo até evolução. **Depende de:** T-041, T-042, T-043, T-044, T-045. **Pronto quando:** HU-05 a HU-11 passam, inclusive timeout, repetição e nova sessão. **Cobre:** CS-01/02/04 no fluxo de estudo.

## Fase 5 — Qualidade, operação e aceite

Objetivo: reunir evidências do produto completo. T-090, T-091, T-092 e T-093 podem avançar em paralelo após T-046 em ambientes/dados isolados; T-094 consolida resultados.

- [ ] **T-090 — Verificar segurança, contratos sensíveis e consistência.** Testar acesso cruzado, validação server-side, gabarito, concorrência, filtragem de evidências e logs sem segredos. Verificar ausência de pesquisa externa no fluxo de geração e correção pelo gabarito salvo, sem nova geração a cada resposta. **Depende de:** T-046. **Pronto quando:** CS-02/03 e RQ-01/02/06 têm evidências sem falhas pendentes no escopo.
- [ ] **T-091 — Verificar experiência e acessibilidade.** Revisar teclado, foco, contraste, 320 px/desktop, conteúdo longo e todos os estados. **Depende de:** T-046. **Pronto quando:** CS-05 e RQ-03 atendidos com evidência manual e automatizada.
- [ ] **T-092 — Verificar build, testes e OpenAPI.** Executar comandos reais, testes de contrato, exemplos e revisão MVC/nomenclatura; manter documentação coerente. **Depende de:** T-046. **Pronto quando:** HU-12, CS-06 e RQ-05 passam em ambiente reproduzível. Não preencher SKILL.md sem autorização para editá-lo; registrar comandos em Plan.md enquanto necessário.
- [ ] **T-093 — Verificar carga e recuperação.** Medir metas QA-11, provocar falha de executor, restaurar banco/arquivos e validar procedimentos/alertas. **Depende de:** T-046. **Pronto quando:** RQ-04/08 e parte operacional de CS-07 têm resultados comparados às metas, com responsáveis e procedimentos definidos.
- [ ] **T-094 — Consolidar aceite e documentação.** Conferir todos os RF, HU, CB e CS; atualizar Spec/Plan/Tasks com decisões e evidências. **Depende de:** T-090, T-091, T-092, T-093. **Pronto quando:** CS-01 a CS-07 atendidos, incluindo avaliação de conteúdo T-030 e política de fontes T-035, sem pendências bloqueantes omitidas. Qualquer mudança necessária nos originais é solicitada antes da edição.

## Mapa de dependências e paralelismo

| Marco | Necessita | Trabalho que pode ocorrer em paralelo |
| --- | --- | --- |
| Baseline T-007 | T-001, T-002, T-003, T-004, T-006 | Refinamentos por tema; reconciliar decisões antes de concluir |
| Fundação T-014 | T-010 → T-011 e T-013 | T-012 independente após T-010 |
| Materiais T-024 | T-020, T-021, T-022, T-023 | Armazenamento/API por contrato; UI simulada após base visual |
| Trilhas T-034 | T-030/T-031 → T-032; T-033 | Gerador, executor e interface por contratos estáveis |
| Estudo T-046 | T-034 → T-035 → T-040 → T-041/T-042; T-043; T-044; T-045 | Flashcards e UI durante backend; pontos e indicadores após tentativa |
| Aceite T-094 | T-090, T-091, T-092, T-093 | Segurança, visual, contratos e operação com ambientes isolados |

Migrações compartilhadas e mudanças de contrato exigem coordenação, mesmo em tarefas marcadas como paralelizáveis. Antes de integrar, reconciliar esquemas, limites e contratos. Não executar carga sobre o mesmo ambiente usado para medir comportamento funcional sem isolamento.

## Matriz de rastreabilidade

| Requisitos | Tarefas principais | Aceitação |
| --- | --- | --- |
| RF-01 | T-002, T-011, T-024, T-090 | HU-01; CS-03 |
| RF-02/03 | T-002/003, T-020 a T-024, T-045 | HU-02/10; CB-01/02/03/12 |
| RF-04/05 | T-003, T-030 a T-034 | HU-03/04; CB-04/05/06 |
| RF-06/07 | T-004, T-040, T-044, T-046 | HU-05/06; CB-07/08/11 |
| RF-08 | T-003, T-030, T-043, T-044 | HU-07; CB-11 |
| RF-09/11 | T-004, T-041, T-044, T-046 | HU-06/09; CS-02 |
| RF-10/12 | T-004, T-042, T-044, T-046 | HU-08/11; CB-09/10 |
| RF-14/15 | T-003, T-030, T-032/033, T-035, T-090 | HU-13/14; CB-15/16 |
| RF-13 | T-014, T-092 | HU-12; CS-06 |
| RQ-01/02/06 | T-011/014/031/040/041, T-090 | CS-02/03/04 |
| RQ-03/05 | T-010/012/044, T-091/092 | CS-05/06; CB-13 |
| RQ-04/07/08 | T-003/006/030/045, T-093 | CS-07; CB-14 |

## Registro de conclusão

Ao concluir uma tarefa, registrar junto dela a data, decisão/implementação correspondente, testes executados e localização da evidência. Falhas e limitações devem permanecer visíveis. Uma implementação parcial ou teste simulado de UI não encerra uma tarefa de integração; uma QA aberta não pode ser marcada como resolvida apenas para liberar a fase seguinte.
