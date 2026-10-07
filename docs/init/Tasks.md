# Tarefas — Plataforma de Estudos Gamificada

## 1. Objetivo

Definir a ordem e as dependências de implementação do sistema especificado em `SPEC.md`, `DESIGN.md`, `PLAN.md` e `SKILL.md`.

Este documento determina **o que implementar e em qual ordem**, referenciando os documentos responsáveis pelos requisitos, arquitetura, interface e instruções permanentes sem duplicá-los.

---

## 2. Regras de execução

Utilizar:

- `[ ]` pendente;
- `[~]` em andamento;
- `[x]` concluída;
- `[!]` bloqueada.

Uma tarefa somente pode ser marcada como concluída quando seu critério de conclusão tiver sido atendido e sua implementação necessária estiver funcional, não apenas simulada.

Tarefas cujas dependências estejam satisfeitas podem avançar em paralelo.

Quando uma tarefa depender de decisão técnica aberta (`TD-*`), resolver somente a decisão necessária e registrá-la no `PLAN.md` antes da implementação correspondente.

Não inventar decisões técnicas apenas para desbloquear desenvolvimento.

---

# Fase 0 — Decisões técnicas iniciais

Objetivo: resolver somente as decisões necessárias para criar a fundação do projeto.

### T-001 — Definir ORM e migrations

- [ ] Resolver `TD-01` e `TD-02`.
- [ ] Registrar as decisões no `PLAN.md`.

**Depende de:** nenhuma.

**Concluída quando:** ORM e mecanismo de migrations estiverem definidos e compatíveis com a stack do projeto.

---

# Fase 1 — Fundação

Objetivo: criar uma aplicação executável com banco, contratos e estrutura base.

### T-010 — Inicializar backend

- [ ] Criar projeto Python + FastAPI.
- [ ] Configurar dependências e ambientes.
- [ ] Conectar PostgreSQL.
- [ ] Configurar ORM e migrations definidos em `T-001`.
- [ ] Criar estrutura arquitetural definida no `PLAN.md`.
- [ ] Disponibilizar OpenAPI/Swagger.

**Depende de:** T-001.

**Concluída quando:** API inicia, conecta ao PostgreSQL e executa a migration inicial.

---

### T-011 — Inicializar frontend

- [ ] Criar aplicação React JS + Vite com Material UI.
- [ ] Criar estrutura inicial do frontend conforme `PLAN.md` e `SKILL.md`.
- [ ] Configurar tema claro/escuro.
- [ ] Implementar presets independentes de paleta e tipografia conforme `DESIGN.md`.
- [ ] Criar navegação e componentes fundamentais.

**Depende de:** nenhuma.

**Cobre:** `UI-02`, `UI-03`.

**Concluída quando:** aplicação inicia, estrutura base funciona em desktop e mobile e os presets de paleta e tipografia podem ser avaliados independentemente.

---

### T-012 — Implementar autenticação

- [ ] Resolver `TD-11` e registrar a decisão no `PLAN.md`.
- [ ] Implementar cadastro, login, refresh e logout no backend.
- [ ] Implementar hash de senha, JWT e autorização por usuário.
- [ ] Implementar fluxo de Login e Cadastro conforme `DESIGN.md`.
- [ ] Manter Access Token em memória e implementar renovação da sessão.
- [ ] Proteger áreas autenticadas no frontend.
- [ ] Implementar `/auth/me` ou contrato equivalente para recuperação do estudante autenticado.
- [ ] Garantir funcionamento em desktop e mobile.

**Depende de:** T-010, T-011.

**Cobre:** `RF-01`, `RF-02`, `HU-01`, `RN-01`.

**Concluída quando:** estudante consegue cadastrar-se, autenticar-se, recuperar e renovar sua sessão e acessar somente recursos autorizados.

---

### T-013 — Padronizar contratos e erros

- [ ] Implementar formato uniforme de erro conforme `PLAN.md`.
- [ ] Criar tratamento central de exceções.
- [ ] Implementar `idRequisicao`.
- [ ] Padronizar validações e códigos HTTP.
- [ ] Aplicar convenções de datas conforme `RN-15`.
- [ ] Garantir representação dos contratos no OpenAPI.

**Depende de:** T-010.

**Cobre:** `RF-18`, `RN-15`.

**Concluída quando:** erros, validações e convenções transversais da API estão padronizados e representados no OpenAPI.

---

# Fase 2 — Materiais

Objetivo: completar o fluxo de envio e gerenciamento de materiais antes de introduzir IA.

### T-020 — Implementar modelo de materiais

- [ ] Implementar Material e Versão do material.
- [ ] Relacionar materiais ao estudante proprietário.
- [ ] Criar persistência e relacionamentos necessários.
- [ ] Aplicar integridade e isolamento conforme `RN-01`.

**Depende de:** T-010, T-012.

**Cobre:** `RF-02`, `RF-03`.

**Concluída quando:** materiais e suas versões podem ser persistidos e relacionados ao estudante proprietário com integridade e isolamento.

---

### T-021 — Implementar armazenamento de arquivos

- [ ] Configurar armazenamento de desenvolvimento conforme `PLAN.md`.
- [ ] Gerar identificadores internos para os arquivos.
- [ ] Associar arquivos aos respectivos materiais e proprietários.
- [ ] Proteger o acesso aos arquivos.

**Depende de:** T-020.

**Cobre:** `RN-01`.

**Concluída quando:** arquivos podem ser armazenados e recuperados de forma controlada, sem utilizar o nome original como identidade física e respeitando a propriedade do estudante.

---

### T-022 — Implementar API de materiais

- [ ] Implementar upload, listagem e detalhe.
- [ ] Implementar arquivamento e restauração.
- [ ] Validar formato, tamanho, quantidade e integridade conforme `RN-02`.
- [ ] Aplicar propriedade e autorização nas operações.
- [ ] Documentar os contratos no OpenAPI.

**Depende de:** T-020, T-021.

**Cobre:** `RF-03`, `RF-04`, `RN-01`, `RN-02`, `RN-14`.

**Concluída quando:** materiais válidos podem ser enviados, consultados, arquivados e restaurados por seu proprietário conforme as regras aplicáveis.

---

### T-024 — Implementar exclusão segura de materiais

- [ ] Implementar exclusão definitiva conforme `RN-14`.
- [ ] Validar propriedade e dependências no backend.
- [ ] Retornar erro estruturado quando a exclusão estiver bloqueada.
- [ ] Remover de forma consistente os dados associados já existentes.
- [ ] Evitar referências ou dados órfãos.
- [ ] Permitir extensão das verificações conforme novas dependências forem introduzidas.

**Depende de:** T-020, T-021, T-022.

**Cobre:** `RF-04`, `RN-14`.

**Concluída quando:** materiais elegíveis podem ser excluídos definitivamente, materiais com dependências conhecidas têm a exclusão bloqueada e nenhuma operação deixa dados órfãos.

---

### T-023 — Implementar interface de materiais

- [ ] Implementar upload, listagem e detalhe conforme `DESIGN.md`.
- [ ] Implementar arquivamento e restauração.
- [ ] Implementar solicitação e confirmação de exclusão.
- [ ] Apresentar corretamente exclusão bloqueada por dependências.
- [ ] Implementar estados vazios, carregamento e erros.

**Depende de:** T-011, T-022, T-024.

**Cobre:** `HU-02`, `HU-12`.

**Concluída quando:** o estudante consegue enviar e gerenciar materiais pela interface utilizando a API real, incluindo arquivamento, restauração e os estados de exclusão permitida ou bloqueada.

---

# Fase 3 — Base RAG

Objetivo: transformar materiais em uma base de conhecimento vetorial rastreável.

### T-030 — Implementar extração

- [ ] Resolver `TD-07` e registrar a decisão no `PLAN.md`.
- [ ] Implementar adaptadores para PDF, TXT e DOCX.
- [ ] Preservar texto e metadados de origem disponíveis.
- [ ] Não inventar metadados ausentes.
- [ ] Validar extração com fixtures dos três formatos.

**Depende de:** T-022.

**Cobre:** `RF-06`, `RN-04`, `RN-05`.

**Concluída quando:** os três formatos suportados podem ser extraídos preservando texto e rastreabilidade até material e versão, incluindo localização quando disponível.

---

### T-031 — Implementar chunking

- [ ] Implementar estratégia inicial e configurável de fragmentação.
- [ ] Preservar vínculo e metadados de origem.
- [ ] Evitar perda desnecessária de contexto semântico.
- [ ] Permitir ajuste dos parâmetros necessários à avaliação.

**Depende de:** T-030.

**Cobre:** `RF-06`, `RN-04`, `RN-05`.

**Concluída quando:** chunks rastreáveis podem ser produzidos e seus parâmetros podem ser ajustados para avaliação.

---

### T-032 — Implementar embeddings

- [ ] Resolver `TD-05` e registrar a decisão no `PLAN.md`.
- [ ] Implementar adaptador substituível de embeddings.
- [ ] Gerar representação vetorial para chunks elegíveis.
- [ ] Registrar modelo e versão utilizados.
- [ ] Tratar falhas e limites da integração.

**Depende de:** T-031.

**Cobre:** `RF-06`.

**Concluída quando:** chunks elegíveis podem gerar embeddings rastreáveis utilizando o adaptador configurado.

---

### T-033 — Implementar armazenamento vetorial

- [ ] Resolver `TD-04` e registrar a decisão no `PLAN.md`.
- [ ] Configurar a tecnologia escolhida.
- [ ] Persistir embeddings vinculados aos chunks.
- [ ] Implementar filtros obrigatórios de autorização e contexto.
- [ ] Validar isolamento entre usuários.

**Depende de:** T-032.

**Cobre:** `RF-06`, `RN-01`, `RN-04`.

**Concluída quando:** embeddings podem ser armazenados e recuperados com vínculo aos chunks sem permitir acesso vetorial cruzado entre usuários.

---

### T-034 — Implementar retrieval

- [ ] Implementar vetorização da consulta e busca vetorial.
- [ ] Aplicar filtros obrigatórios de autorização e contexto.
- [ ] Recuperar chunks com seus metadados.
- [ ] Implementar tratamento para recuperação insuficiente.
- [ ] Tornar parâmetros experimentais configuráveis.

**Depende de:** T-033.

**Cobre:** `RN-01`, `RN-04`, `RN-06`.

**Concluída quando:** consultas recuperam somente chunks autorizados e rastreáveis e o sistema consegue identificar ausência de sustentação suficiente.

---

### T-035 — Avaliar chunking e retrieval

- [ ] Criar corpus controlado com respostas e evidências conhecidas.
- [ ] Avaliar recuperação correta, ausência de resposta, cobertura insuficiente, irrelevância, contradições e isolamento.
- [ ] Avaliar os parâmetros experimentais de chunking e retrieval definidos no `PLAN.md`.
- [ ] Registrar a configuração inicial justificada.
- [ ] Atualizar `TD-09` e `TD-10` no `PLAN.md` conforme os resultados.

**Depende de:** T-034.

**Concluída quando:** existe configuração inicial de chunking e retrieval sustentada por avaliação reproduzível, sem valores escolhidos arbitrariamente.

---

# Fase 4 — Processamento e geração

Objetivo: transformar a base RAG em conteúdo de estudo validado.

### T-040 — Implementar processamento assíncrono

- [ ] Resolver `TD-03` e `TD-13` e registrar as decisões no `PLAN.md`.
- [ ] Implementar execução fora da requisição HTTP.
- [ ] Persistir e atualizar os estados definidos em `RN-03`.
- [ ] Tratar falhas e recuperação de execuções.
- [ ] Implementar reprocessamento controlado e idempotência.
- [ ] Impedir publicação duplicada.

**Depende de:** T-020, T-022.

**Cobre:** `RF-05`, `RN-03`, `RN-10`.

**Concluída quando:** processamentos podem ser executados fora da requisição, acompanhados por estado e repetidos de forma controlada sem duplicar efeitos.

---

### T-041 — Implementar adaptador de IA

- [ ] Resolver `TD-06` e registrar a decisão no `PLAN.md`.
- [ ] Implementar abstração de IA independente de provedor.
- [ ] Implementar o adaptador do provedor/modelo escolhido.
- [ ] Suportar saída estruturada.
- [ ] Tratar falhas, limites e indisponibilidade da integração.

**Depende de:** T-010.

**Cobre:** `RQ-05`.

**Concluída quando:** o backend consegue utilizar o provedor escolhido através de uma abstração substituível sem acoplamento do domínio.

---

### T-042 — Implementar construção do contexto RAG

- [ ] Recuperar chunks autorizados para a necessidade de geração.
- [ ] Construir contexto somente com evidências recuperadas.
- [ ] Separar instruções do sistema e conteúdo dos materiais.
- [ ] Tratar materiais como dados, nunca como instruções.
- [ ] Interromper geração quando a sustentação for insuficiente.

**Depende de:** T-034.

**Cobre:** `RN-04`, `RN-06`.

**Concluída quando:** uma necessidade de geração produz contexto rastreável e autorizado ou é rejeitada por sustentação insuficiente.

---

### T-043 — Implementar geração de trilhas

- [ ] Identificar assuntos e cobertura a partir dos materiais.
- [ ] Criar trilhas e etapas ordenadas.
- [ ] Identificar conteúdo insuficiente.
- [ ] Marcar assuntos sem cobertura como aguardando material.

**Depende de:** T-041, T-042.

**Cobre:** `RF-07`, `RF-08`, `RN-06`.

**Concluída quando:** o sistema consegue criar trilhas sustentadas pelos materiais e representar explicitamente assuntos sem cobertura suficiente.

---

### T-044 — Implementar geração de questões e flashcards

- [ ] Gerar questões conforme os tipos e restrições de `RN-07`.
- [ ] Gerar resposta correta, dificuldade e explicação didática.
- [ ] Vincular questões às evidências recuperadas.
- [ ] Gerar flashcards conforme `RN-08`.
- [ ] Gerar flashcards a partir das evidências, sem utilizar apenas a questão como fonte.
- [ ] Persistir conteúdo gerado como candidato à validação, sem publicá-lo antecipadamente.

**Depende de:** T-041, T-042, T-043.

**Cobre:** `RF-09`, `RF-11`, `RN-05`, `RN-07`, `RN-08`.

**Concluída quando:** questões e flashcards rastreáveis podem ser gerados em estrutura compatível com suas regras e encaminhados à validação antes da publicação.

---

### T-045 — Implementar validação de conteúdo

- [ ] Implementar validação estrutural conforme `RN-07` e `RN-08`.
- [ ] Validar existência, autorização e rastreabilidade das evidências.
- [ ] Validar sustentação de questão, resposta, explicação e flashcard.
- [ ] Rejeitar conteúdo contraditório ou insuficientemente sustentado.
- [ ] Impedir publicação de conteúdo inválido.

**Depende de:** T-044.

**Cobre:** `RN-05`, `RN-07`, `RN-08`, `RQ-03`.

**Concluída quando:** somente conteúdo estruturalmente válido, autorizado e sustentado pelas evidências pode ser publicado.

---

### T-046 — Integrar pipeline de processamento e geração

Integrar o fluxo definido no `PLAN.md`, do material persistido até a publicação do conteúdo validado.

**Depende de:** T-035, T-040, T-045.

**Cobre:** `RF-05` a `RF-09`, `HU-03`.

**Concluída quando:** um material real válido percorre o pipeline assíncrono, possui estados observáveis e produz somente conteúdo validado e rastreável.

---

# Fase 5 — Interface de trilhas

### T-050 — Implementar acompanhamento de processamento

- [ ] Integrar a interface de materiais aos estados reais de processamento conforme `RN-03`.
- [ ] Atualizar o estado apresentado durante a execução.
- [ ] Apresentar falhas de forma compreensível.
- [ ] Disponibilizar recuperação/reprocessamento quando permitido.

**Depende de:** T-023, T-046.

**Cobre:** `RF-05`, `HU-03`, `RN-03`.

**Concluída quando:** o estudante consegue acompanhar pela interface o processamento real de seus materiais, incluindo conclusão, falha e recuperação quando aplicável.

---

### T-051 — Implementar interface de trilhas

- [ ] Exibir trilhas e etapas conforme `DESIGN.md`.
- [ ] Representar ordem, disponibilidade e estado das etapas.
- [ ] Permitir acesso às etapas disponíveis.
- [ ] Representar assuntos aguardando material conforme `RN-06`.
- [ ] Disponibilizar ação para envio de material complementar.
- [ ] Garantir funcionamento em desktop e mobile.

**Depende de:** T-011, T-043, T-050.

**Cobre:** `HU-04`, `HU-10`, `RN-06`, `UI-05`.

**Concluída quando:** o estudante consegue visualizar a estrutura da trilha, acessar etapas disponíveis e identificar assuntos que aguardam material complementar.

---

### T-052 — Integrar material complementar

- [ ] Permitir envio complementar a partir do assunto sem cobertura.
- [ ] Relacionar o material ao contexto que motivou o envio.
- [ ] Integrar o novo material ao pipeline conforme a estratégia de reprocessamento definida em `TD-13`.
- [ ] Reavaliar a cobertura após processamento válido.
- [ ] Atualizar a disponibilidade das etapas conforme o novo conteúdo sustentado.

**Depende de:** T-046, T-051.

**Cobre:** `RF-16`, `RN-06`.

**Concluída quando:** material complementar válido pode ser enviado para um assunto sem cobertura, processado pelo pipeline e refletido na cobertura da trilha sem gerar conteúdo não sustentado.

---

# Fase 6 — Estudo

Objetivo: permitir estudar conteúdo já publicado sem depender da IA durante a resposta.

### T-060 — Implementar consulta de questões

- [ ] Disponibilizar questões publicadas ao estudante autorizado.
- [ ] Aplicar o contrato pré-resposta definido em `RN-09`.
- [ ] Preservar vínculo com a versão publicada da questão.

**Depende de:** T-046.

**Cobre:** `RF-09`, `RN-09`.

**Concluída quando:** o estudante autorizado consegue consultar uma questão sem receber gabarito, explicação ou outros dados restritos ao pós-resposta.

---

### T-061 — Implementar tentativas e correção

- [ ] Registrar tentativa e resposta do estudante.
- [ ] Corrigir utilizando o gabarito persistido, sem nova chamada à IA.
- [ ] Suportar os tipos de questão definidos em `RN-07`.
- [ ] Persistir e retornar o resultado pós-resposta conforme `RN-09` e `RN-16`.
- [ ] Garantir idempotência conforme `RN-10`.
- [ ] Disponibilizar o resultado persistido para os efeitos posteriores de gamificação.

**Depende de:** T-060.

**Cobre:** `RF-10`, `RN-07`, `RN-09`, `RN-10`, `RN-16`.

**Concluída quando:** tentativas são registradas e corrigidas de forma idempotente utilizando o gabarito persistido, e o estudante recebe o conteúdo pós-resposta permitido.

---

### T-062 — Implementar pontuação

- [ ] Implementar concessão de pontos conforme `RN-11`.
- [ ] Registrar origem e valor da pontuação.
- [ ] Garantir idempotência e impedir pontuação duplicada.

**Depende de:** T-061.

**Cobre:** `RF-12`, `RN-11`.

**Concluída quando:** tentativas elegíveis geram exatamente os efeitos de pontuação definidos em `RN-11`, sem duplicação.

---

### T-063 — Implementar progresso

- [ ] Calcular e persistir progresso conforme `RN-12`.
- [ ] Manter acurácia e conclusão como métricas distintas.
- [ ] Disponibilizar o progresso para trilhas e evolução.
- [ ] Integrar o progresso real aos estados apresentados na interface de trilhas.

**Depende de:** T-051, T-061.

**Cobre:** `RF-13`, `RN-12`.

**Concluída quando:** progresso de questões, etapas e trilhas é calculado a partir dos dados persistidos e refletido corretamente na interface de trilhas.

---

### T-064 — Implementar conquistas

- [ ] Implementar concessão das conquistas definidas em `RN-13`.
- [ ] Garantir concessão única por estudante e conquista.
- [ ] Persistir as concessões.
- [ ] Disponibilizar o evento ou resultado necessário para comunicar uma nova conquista à interface.
- [ ] Integrar notificação global de conquista desbloqueada conforme `DESIGN.md`.

**Depende de:** T-011, T-061, T-063.

**Cobre:** `RF-14`, `RN-13`.

**Concluída quando:** os marcos definidos em `RN-13` concedem suas respectivas conquistas uma única vez e uma nova concessão é comunicada ao estudante conforme a experiência definida no `DESIGN.md`.

---

### T-065 — Implementar revisão por flashcards

- [ ] Disponibilizar flashcard após a resposta da questão relacionada conforme `RN-08`.
- [ ] Implementar frente, revelação explícita do verso, explicação e evidência quando aplicável.
- [ ] Utilizar somente conteúdo previamente validado e persistido.
- [ ] Garantir que a revisão não produza efeitos avaliativos ou de gamificação.

**Depende de:** T-061.

**Cobre:** `RF-11`, `RF-17`, `RN-08`, `HU-07`.

**Concluída quando:** o estudante consegue revisar por flashcards e consultar suas evidências sem gerar tentativa, pontuação, acurácia, progresso ou conquistas.

---

### T-066 — Implementar interface de estudo

- [ ] Implementar apresentação e resposta dos tipos de questão conforme `DESIGN.md`.
- [ ] Exigir resposta válida antes da confirmação e impedir envio técnico duplicado.
- [ ] Apresentar feedback pós-resposta conforme `RN-09` e `RN-16`.
- [ ] Permitir consulta à evidência vinculada.
- [ ] Apresentar pontuação recebida quando aplicável.
- [ ] Disponibilizar revisão por flashcard após a resposta.
- [ ] Manter navegação sob ação explícita do estudante.
- [ ] Garantir suporte a conteúdo longo e funcionamento responsivo.

**Depende de:** T-011, T-061, T-062, T-063, T-065.

**Cobre:** `RF-10`, `RF-11`, `RF-17`, `HU-05`, `HU-06`, `HU-07`, `HU-11`, `RN-08`, `RN-09`, `RN-16`.

**Concluída quando:** a jornada de estudo funciona integrada à API real, sem exposição antecipada do gabarito e com correção, feedback, evidência, pontuação e revisão disponíveis conforme as regras aplicáveis.

---

# Fase 7 — Experiência e acompanhamento

Objetivo: apresentar ao estudante informações úteis sobre sua evolução, facilitar a continuidade dos estudos e concentrar informações pessoais e conquistas no Perfil.

### T-070 — Implementar API de evolução

- [ ] Consolidar as métricas definidas em `RF-15` a partir dos dados persistidos.
- [ ] Manter acurácia e conclusão como métricas distintas.
- [ ] Restringir os dados ao estudante autenticado.
- [ ] Representar corretamente ausência de atividade.

**Depende de:** T-062, T-063.

**Cobre:** `RF-15`, `HU-08`, `RN-12`.

**Concluída quando:** o estudante autenticado consegue consultar sua evolução com métricas derivadas dos dados persistidos, sem valores fictícios.

---

### T-071 — Implementar tela de evolução

- [ ] Apresentar as métricas de evolução conforme `DESIGN.md`.
- [ ] Diferenciar claramente acurácia de conclusão.
- [ ] Representar progresso das trilhas.
- [ ] Implementar estado sem atividade.
- [ ] Utilizar visualizações que preservem compreensão e acessibilidade.

**Depende de:** T-011, T-070.

**Cobre:** `RF-15`, `HU-08`.

**Concluída quando:** o estudante consegue compreender seu desempenho e progresso a partir dos dados reais de evolução, incluindo o estado sem atividade.

---

### T-072 — Implementar Início

- [ ] Implementar os estados de estudante novo e estudante com atividade conforme `DESIGN.md`.
- [ ] Apresentar próxima ação coerente com o estado atual.
- [ ] Utilizar somente dados reais disponíveis.
- [ ] Integrar acesso a materiais, continuidade de estudo e resumo de evolução quando aplicável.

**Depende de:** T-023, T-051, T-070.

**Concluída quando:** a tela inicial apresenta uma próxima ação coerente com o estado do estudante e não utiliza informações fictícias.

---

### T-073 — Implementar Perfil e conquistas

- [ ] Disponibilizar os contratos necessários para consulta do perfil e das conquistas.
- [ ] Compor informações de identidade e gamificação conforme `PLAN.md`.
- [ ] Implementar a interface de Perfil conforme `DESIGN.md`.
- [ ] Apresentar as conquistas definidas em `RN-13`.
- [ ] Diferenciar conquistas obtidas e pendentes e apresentar os dados aplicáveis de concessão.
- [ ] Não introduzir conquistas além das definidas para o MVP.

**Depende de:** T-011, T-012, T-064.

**Cobre:** `RF-14`, `RF-19`, `HU-09`, `RN-13`.

**Concluída quando:** o estudante consegue consultar seu perfil e todas as conquistas do MVP, distinguindo as obtidas das pendentes a partir dos dados persistidos.

---

# Fase 8 — Validação integrada

Objetivo: validar de forma integrada os requisitos, riscos e jornadas críticas do sistema completo.

### T-080 — Validar segurança e isolamento

- [ ] Validar isolamento entre usuários na API e persistência relacional.
- [ ] Validar proteção de arquivos e conteúdo processado.
- [ ] Validar isolamento de chunks e recuperação vetorial.
- [ ] Validar autorização sobre trilhas, questões, tentativas e demais recursos pertencentes ao estudante.
- [ ] Validar cenários de acesso cruzado definidos no `SPEC.md`.

**Depende de:** T-046, T-061.

**Cobre:** `RN-01`, `RQ-01`, `CS-02`.

**Concluída quando:** os testes de acesso cruzado não permitem consultar, recuperar ou modificar dados pertencentes a outro estudante.

---

### T-081 — Validar RAG e qualidade do conteúdo

- [ ] Executar avaliação integrada utilizando corpus controlado.
- [ ] Validar cobertura suficiente e insuficiente.
- [ ] Validar relevância e sustentação das evidências.
- [ ] Validar tratamento de conteúdo contraditório e referências inválidas.
- [ ] Validar tratamento de instruções maliciosas presentes nos materiais.
- [ ] Validar isolamento durante a recuperação.
- [ ] Validar que conteúdo sem sustentação suficiente não seja publicado.
- [ ] Validar qualidade da geração a partir das evidências recuperadas.

**Depende de:** T-035, T-045, T-046.

**Cobre:** `RN-04`, `RN-05`, `RN-06`, `RN-07`, `RN-08`, `RQ-03`, `RQ-04`.

**Concluída quando:** o pipeline recupera evidências adequadas, rejeita conteúdo insuficiente ou inválido e publica somente conteúdo rastreável e sustentado pelos materiais autorizados.

---

### T-082 — Validar tentativas e gamificação

- [ ] Validar idempotência de tentativas e seus efeitos.
- [ ] Validar pontuação conforme `RN-11`.
- [ ] Validar progresso conforme `RN-12`.
- [ ] Validar concessão única das conquistas conforme `RN-13`.
- [ ] Validar repetição de questões e primeiro acerto.
- [ ] Validar consistência entre tentativa, pontuação, progresso e conquistas.
- [ ] Validar que flashcards não produzam efeitos avaliativos ou de gamificação.

**Depende de:** T-061, T-062, T-063, T-064, T-065.

**Cobre:** `RN-08`, `RN-10`, `RN-11`, `RN-12`, `RN-13`, `RQ-02`.

**Concluída quando:** tentativas e seus efeitos permanecem consistentes sob acertos, erros, repetições e reenvios técnicos, sem duplicação de pontuação, progresso ou conquistas.

---

### T-083 — Validar ciclo de vida de materiais

- [ ] Validar arquivamento e restauração preservando histórico e dependências.
- [ ] Validar exclusão definitiva de materiais elegíveis.
- [ ] Validar bloqueio da exclusão diante das dependências definidas em `RN-14`.
- [ ] Validar propriedade antes das operações de ciclo de vida.
- [ ] Validar remoção consistente dos dados associados quando a exclusão for permitida.
- [ ] Validar ausência de dados órfãos entre PostgreSQL, armazenamento de arquivos e armazenamento vetorial.
- [ ] Validar envio de material complementar.
- [ ] Validar reprocessamento e reindexação conforme a estratégia definida.

**Depende de:** T-024, T-046, T-052, T-061.

**Cobre:** `RN-14`, `CS-04`, `PLAN.md §23`.

**Concluída quando:** arquivamento e restauração preservam os dados necessários, exclusões respeitam as dependências existentes e as operações de ciclo de vida mantêm consistência entre os mecanismos de persistência.

---

### T-084 — Validar interface e experiência

- [ ] Validar responsividade e acessibilidade conforme `RQ-06` e `DESIGN.md`.
- [ ] Validar navegação por teclado, foco, contraste e conteúdo longo.
- [ ] Validar temas e presets ainda ativos de paleta e tipografia.
- [ ] Validar estados de carregamento, vazio, erro, acesso negado e ações indisponíveis.
- [ ] Validar as jornadas principais de autenticação, materiais, trilhas, estudo, evolução e Perfil.
- [ ] Validar feedback, evidências e revisão por flashcards.
- [ ] Validar notificações transitórias e confirmações de ações destrutivas.
- [ ] Validar funcionamento a partir de 320 px até desktop.

**Depende de:** T-023, T-050, T-051, T-066, T-071, T-072, T-073.

**Cobre:** `RQ-06`, `UI-02`, `UI-03`, `UI-05`, `CS-04`.

**Concluída quando:** as jornadas e estados principais da interface permanecem utilizáveis, acessíveis, responsivos e coerentes com o `DESIGN.md`.

---

### T-085 — Validar contratos, arquitetura e documentação

- [ ] Validar OpenAPI e Swagger contra os contratos implementados.
- [ ] Validar documentação de erros, autenticação e operações da API.
- [ ] Validar build e execução dos testes.
- [ ] Validar configuração dos ambientes e exemplos necessários.
- [ ] Verificar conformidade da implementação com o `PLAN.md`.
- [ ] Verificar conformidade com as responsabilidades e convenções do `SKILL.md`.

**Depende de:** T-080, T-081, T-082, T-083, T-084.

**Cobre:** `RF-18`, `RQ-07`, `RQ-08`, `CS-04`.

**Concluída quando:** contratos, documentação, build, testes e estrutura implementada estão coerentes com os documentos oficiais do projeto.

---

# Fase 9 — Aceite do MVP

Objetivo: executar as jornadas críticas do produto e verificar formalmente se o MVP atende aos critérios de sucesso definidos no `SPEC.md`.

### T-090 — Executar jornada principal do MVP

Executar de ponta a ponta a jornada principal definida no `SPEC.md`:

```text
Cadastro
   ↓
Login
   ↓
Upload
   ↓
Processamento
   ↓
RAG
   ↓
Trilha
   ↓
Questão
   ↓
Confirmação da resposta
   ↓
Correção + Feedback didático
   ↓
Evidência
   ↓
Flashcard de revisão
   ↓
Pontos
   ↓
Progresso
   ↓
Conquista
   ↓
Evolução
   ↓
Perfil + Conquistas
```

Durante a jornada:

- [ ] utilizar dados reais e integrações implementadas;
- [ ] validar rastreabilidade do conteúdo até os materiais autorizados;
- [ ] validar separação entre os contratos pré-resposta e pós-resposta;
- [ ] validar feedback didático e acesso à evidência após a resposta;
- [ ] validar flashcard como recurso exclusivamente de revisão;
- [ ] validar os efeitos de pontuação, progresso e conquistas;
- [ ] validar atualização das informações de evolução;
- [ ] validar apresentação das informações e conquistas no Perfil.

**Depende de:** T-085.

**Cobre:** `CS-01`, `CS-03`, `CS-05`.

**Concluída quando:** a jornada principal pode ser executada de ponta a ponta com dados reais e apresenta os resultados esperados em cada etapa sem violar as regras do produto.

---

### T-091 — Executar jornada de conteúdo insuficiente

Executar de ponta a ponta o fluxo de conteúdo sem cobertura suficiente:

```text
Assunto identificado
   ↓
Conteúdo insuficiente
   ↓
Aguardando material de apoio
   ↓
Material complementar
   ↓
Processamento
   ↓
Atualização da base RAG
   ↓
Reavaliação da cobertura
   ↓
Conteúdo sustentado disponível
```

Durante a jornada:

- [ ] validar que assunto sem sustentação suficiente não produz atividade artificial;
- [ ] validar estado `Aguardando material de apoio`;
- [ ] validar envio de material complementar relacionado ao contexto;
- [ ] validar processamento do novo material conforme a estratégia definida;
- [ ] validar atualização da base de conhecimento;
- [ ] validar reavaliação da cobertura;
- [ ] validar que somente conteúdo posteriormente sustentado seja disponibilizado.

**Depende de:** T-085.

**Cobre:** `RF-16`, `RN-06`, `CS-05`.

**Concluída quando:** um assunto sem cobertura permanece indisponível até que material complementar válido forneça sustentação suficiente e o pipeline atualize corretamente sua disponibilidade.

---

### T-092 — Conferir critérios de sucesso do MVP

- [ ] Verificar `CS-01` a `CS-05` do `SPEC.md`.
- [ ] Relacionar cada critério às evidências produzidas pelas validações e jornadas executadas.
- [ ] Identificar critérios não atendidos ou sem evidência suficiente.
- [ ] Registrar pendências bloqueantes antes do aceite.
- [ ] Confirmar que nenhum critério seja considerado atendido apenas por existência de interface ou implementação parcial.

**Depende de:** T-090, T-091.

**Cobre:** `CS-01` a `CS-05`.

**Concluída quando:** todos os critérios de sucesso possuem evidência verificável de atendimento e não existe pendência bloqueante omitida para o aceite do MVP.

---

# 10. Dependências principais

Este mapa apresenta as dependências técnicas principais entre as tasks.

Não substitui o campo `Depende de` de cada tarefa.

```text
FUNDAÇÃO E AUTENTICAÇÃO

T-001 → T-010
           ├→ T-012
           └→ T-013

T-011 ────→ T-012


MATERIAIS

T-010 + T-012
       ↓
     T-020
       ↓
     T-021
       ↓
     T-022
       ↓
     T-024
       ↓
     T-023


BASE RAG

T-022
   ↓
T-030  [resolve TD-07]
   ↓
T-031
   ↓
T-032  [resolve TD-05]
   ↓
T-033  [resolve TD-04]
   ↓
T-034
   ↓
T-035


PROCESSAMENTO E GERAÇÃO

T-020 + T-022
       ↓
     T-040  [resolve TD-03 e estratégia de reprocessamento]

T-010
   ↓
T-041  [resolve TD-06]

T-034
   ↓
T-042

T-041 + T-042
       ↓
     T-043
       ↓
     T-044
       ↓
     T-045

T-035 + T-040 + T-045
          ↓
        T-046


TRILHAS E PROCESSAMENTO NA INTERFACE

T-023 + T-046
       ↓
     T-050

T-011 + T-043 + T-050
          ↓
        T-051

T-046 + T-051
       ↓
     T-052


ESTUDO

T-046
   ↓
T-060
   ↓
T-061
   ├────────→ T-062
   ├────────→ T-063
   └────────→ T-065

T-051 + T-061
       ↓
     T-063

T-011 + T-061 + T-063
          ↓
        T-064

T-011 + T-061 + T-062 + T-063 + T-065
                    ↓
                  T-066


EXPERIÊNCIA E ACOMPANHAMENTO

T-062 + T-063
       ↓
     T-070
       ↓
     T-071

T-023 + T-051 + T-070
          ↓
        T-072

T-011 + T-012 + T-064
          ↓
        T-073


VALIDAÇÃO INTEGRADA

T-046 + T-061
       ↓
     T-080

T-035 + T-045 + T-046
          ↓
        T-081

T-061 + T-062 + T-063 + T-064 + T-065
                    ↓
                  T-082

T-024 + T-046 + T-052 + T-061
                    ↓
                  T-083

T-023 + T-050 + T-051 + T-066 + T-071 + T-072 + T-073
                              ↓
                            T-084

T-080 + T-081 + T-082 + T-083 + T-084
                    ↓
                  T-085


ACEITE DO MVP

T-085
   ├────────→ T-090
   └────────→ T-091

T-090 + T-091
       ↓
     T-092
```

O frontend pode avançar em paralelo quando os contratos necessários estiverem definidos.

As dependências representam restrições técnicas, não atribuição de responsáveis.

Tasks independentes podem ser executadas em paralelo quando suas dependências já estiverem satisfeitas.

Decisões técnicas abertas devem ser resolvidas somente quando forem necessárias para a execução da task correspondente, conforme definido no `PLAN.md`.

---

# 11. Marcos

| Marco | Resultado |
| --- | --- |
| M1 — Fundação | Frontend, backend, banco, contratos base e autenticação funcionando |
| M2 — Materiais | Upload, consulta, arquivamento, restauração e exclusão segura funcionando |
| M3 — Base RAG | Materiais extraídos, fragmentados, vetorizados e recuperáveis com rastreabilidade e isolamento |
| M4 — Geração | Pipeline assíncrono produz trilhas, questões e flashcards validados e sustentados por evidências |
| M5 — Trilhas | Trilhas e estados de processamento disponíveis na interface, incluindo fluxo de material complementar |
| M6 — Estudo | Questões, tentativas, correção, feedback, evidências e flashcards funcionando |
| M7 — Gamificação | Pontuação, progresso e conquistas funcionando de forma consistente |
| M8 — Experiência | Início, Evolução e Perfil integrados aos dados reais do estudante |
| M9 — Validação | Segurança, RAG, gamificação, ciclo de vida, interface e contratos validados de forma integrada |
| M10 — MVP | Jornadas críticas executadas e critérios de sucesso do `SPEC.md` verificados |

---

# 12. Registro de conclusão

Ao concluir uma task relevante, registrar apenas:

- estado;
- implementação correspondente;
- testes executados;
- pendências reais.

Não utilizar este documento como diário de desenvolvimento.

Detalhes extensos de implementação ou investigação devem permanecer:

- no código;
- nos testes;
- no README;
- na documentação técnica apropriada.

Não registrar neste documento histórico de protótipos, experimentações ou implementações descartadas.

Uma task somente deve ser marcada como concluída quando atender ao respectivo critério `Concluída quando` e às regras de execução definidas neste documento.

---

# 13. Regra de documentação

Este `TASKS.md` é a fonte principal para **ordem, dependências e acompanhamento da implementação**.

Não duplicar:

- regras completas do `SPEC.md`;
- explicações arquiteturais do `PLAN.md`;
- especificações visuais do `DESIGN.md`;
- instruções permanentes do `SKILL.md`.

Utilizar referências curtas aos documentos proprietários quando necessário, por exemplo:


**Cobre:** RN-04, RF-06


Quando uma decisão `TD-*` for necessária, consultar o `PLAN.md` e resolvê-la somente quando bloquear a execução da task correspondente.

Quando houver dúvida sobre comportamento ou regra de negócio, consultar o `SPEC.md`.

Quando houver dúvida sobre arquitetura ou decisão técnica, consultar o `PLAN.md`.

Quando houver dúvida sobre interface ou experiência, consultar o `DESIGN.md`.

Quando houver dúvida sobre convenções e forma de execução pelo agente, consultar o `SKILL.md`.

Uma mudança deve ser realizada primeiro no documento proprietário da informação e somente depois refletida, de forma curta, nas tasks afetadas.

Referências temporárias utilizadas durante discussões ou resolução de conflitos não devem permanecer como fonte normativa depois que a decisão tiver sido incorporada ao documento proprietário.