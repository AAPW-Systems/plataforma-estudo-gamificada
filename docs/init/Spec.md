# Especificação — Plataforma de Estudos Gamificada

## 1. Objetivo

Construir uma plataforma web de estudos gamificada que transforme materiais enviados pelo estudante em trilhas de aprendizagem, questões e flashcards, permitindo acompanhar estudo, desempenho, progresso, pontos e conquistas.

A geração de conteúdo deve utilizar **RAG (Retrieval-Augmented Generation)** exclusivamente sobre materiais autorizados do próprio estudante.

Este documento é a fonte de verdade para requisitos e regras de negócio. Interface, arquitetura, ordem de implementação e instruções para agentes pertencem, respectivamente, a `DESIGN.md`, `PLAN.md`, `TASKS.md` e `SKILL.md`.

---

## 2. Escopo

### 2.1 Incluído no MVP

- Cadastro, autenticação e isolamento por estudante.
- Materiais PDF, TXT e DOCX: envio, gerenciamento, processamento e ciclo de vida.
- Pipeline RAG com conteúdo rastreável, embeddings, recuperação vetorial e evidências.
- Identificação de assuntos e geração de trilhas de aprendizagem.
- Questões de múltipla escolha com resposta única e verdadeiro ou falso, com tentativas, correção e explicação.
- Flashcards vinculados ao conteúdo estudado.
- Pontuação, progresso, conquistas, histórico e evolução.
- Interface web responsiva em português e API documentada.

### 2.2 Fora do MVP

- Ranking, rede social, equipes, competição e compartilhamento público.
- Pagamentos e assinaturas.
- Aplicativos nativos e funcionamento offline.
- Questões discursivas ou com múltiplas respostas corretas.
- Repetição espaçada e sequências diárias.
- Notificações persistentes, push, e-mail ou central de notificações.
- Tutoria conversacional e edição manual do conteúdo gerado.
- Pesquisa externa para complementar materiais.
- Painel administrativo.

---

## 3. Regras de negócio

### RN-01 — Propriedade e isolamento

Dados e recursos de estudo pertencem ao respectivo estudante e devem permanecer isolados entre usuários.

Conhecer o identificador de um recurso não concede acesso. Nenhum usuário pode consultar, alterar ou utilizar como fonte recursos pertencentes a outro usuário.

---

### RN-02 — Admissão de materiais

São aceitos arquivos **PDF, TXT e DOCX**, com máximo de **5 MB por arquivo** e **3 arquivos por envio**.

O backend deve validar formato, tamanho e integridade antes do processamento. Arquivos inválidos, vazios, corrompidos ou incompatíveis não podem gerar conteúdo ativo.

---

### RN-03 — Processamento

O processamento possui os estados `pendente`, `processando`, `concluido` e `falhou`.

`concluido` significa que o conteúdo esperado foi extraído e persistido de forma válida. Falha técnica e insuficiência de conteúdo pedagógico são situações distintas.

Reprocessamentos devem respeitar a idempotência definida em `RN-10`.

---

### RN-04 — RAG e fontes exclusivas

Todo conteúdo pedagógico gerado por IA deve utilizar RAG exclusivamente sobre materiais autorizados do estudante e vinculados ao contexto correspondente.

É proibido utilizar pesquisa externa, bases externas, conhecimento geral do modelo ou conteúdo de outros usuários para suprir informações ausentes.

A escolha ou troca do provedor de IA não altera esta regra.

---

### RN-05 — Evidências e rastreabilidade

Questões, explicações e flashcards gerados devem permanecer vinculados às evidências que os sustentam.

Cada evidência deve permitir identificar o material e o trecho de origem e, quando conhecido, a página. O sistema nunca deve inventar localização ou número de página.

Os vínculos devem ser preservados após processamento e publicação, permitindo ao estudante consultar, após a resposta, as evidências que sustentam o conteúdo apresentado.

---

### RN-06 — Cobertura e lacunas

A identificação ou menção de um assunto não implica cobertura suficiente para gerar atividades.

Quando não houver evidências suficientes, o assunto deve permanecer como `aguardando material de apoio`, sem geração por conhecimento externo nem conclusão, permitindo ao estudante enviar material complementar.

Lacunas pedagógicas não impedem que o processamento tecnicamente válido seja considerado concluído.

---

### RN-07 — Questões

Toda questão deve possuir enunciado, resposta correta, dificuldade, explicação e evidência, ser sustentada conforme `RN-04` e `RN-05` e validada antes da publicação.

O MVP suporta:

- **múltipla escolha:** exatamente 4 alternativas e 1 correta;
- **verdadeiro ou falso:** opções `Verdadeiro` e `Falso`, com 1 resposta correta.

Questões podem utilizar contextualização sustentada pelas evidências, sem introduzir informações externas.

---

### RN-08 — Flashcards

Flashcards são recursos de revisão, não atividades avaliativas, e devem ser gerados e validados a partir das evidências conforme `RN-04` e `RN-05`.

Cada flashcard deve possuir frente, resposta no verso e evidência vinculada, podendo incluir explicação curta.

O flashcard é liberado após o estudante responder à questão relacionada, e seu verso somente é revelado após ação explícita do estudante.

Flashcards não possuem envio de resposta nem produzem tentativas, pontos, acurácia, progresso, conclusão ou conquistas.

A evidência deve permanecer consultável após a revelação da resposta.

---

### RN-09 — Tentativas

Antes da confirmação da resposta, a API não pode expor o gabarito nem conteúdo que revele a resposta correta.

Após a confirmação, o servidor deve registrar e corrigir a tentativa utilizando o gabarito persistido da versão da questão, sem nova chamada à IA, aplicar os efeitos elegíveis e retornar o resultado conforme `RN-16`.

O histórico deve preservar o resultado original da tentativa mesmo que o conteúdo seja alterado futuramente.

---

### RN-10 — Idempotência

Repetições técnicas da mesma tentativa não podem duplicar tentativas nem efeitos de negócio.

Uma repetição intencional da questão constitui nova tentativa, respeitando as regras de pontuação e conquistas aplicáveis.

---

### RN-11 — Pontuação

Somente o primeiro acerto de cada questão concede pontos, conforme a dificuldade:

- fácil: 1 ponto;
- médio: 2 pontos;
- difícil: 3 pontos.

A dificuldade interfere somente na pontuação.

Respostas incorretas não removem pontos. Toda concessão deve ser rastreável à questão que a originou.

Repetições devem respeitar `RN-10`, e flashcards não concedem pontos conforme `RN-08`.

---

### RN-12 — Progresso

Percentual de acertos e percentual de conclusão são métricas distintas.

Uma questão é concluída ao ser acertada. Etapas e trilhas são concluídas quando todas as questões disponíveis que as compõem forem acertadas.

Assuntos `aguardando material de apoio` devem permanecer identificados como lacunas de cobertura, sem impedir a conclusão do conteúdo efetivamente disponível.

---

### RN-13 — Conquistas

O MVP possui exatamente três conquistas:

| Conquista | Critério |
| --- | --- |
| Primeira resposta | Registrar a primeira resposta válida |
| 10 acertos | Acertar 10 questões distintas |
| Primeira trilha | Concluir a primeira trilha |

Cada conquista pode ser concedida apenas uma vez por estudante. Repetições não aumentam o número de questões distintas acertadas.

---

### RN-14 — Arquivamento e exclusão de materiais

Arquivamento e exclusão definitiva são operações distintas.

O arquivamento retira o material da visualização ativa sem excluí-lo, preservando histórico, versões, evidências e dependências e permitindo restauração.

A exclusão definitiva somente é permitida quando o material não possuir dependências necessárias à consistência, rastreabilidade ou preservação do histórico. Caso existam, a operação deve ser bloqueada.

Toda exclusão definitiva exige confirmação explícita e não pode deixar dados órfãos nem comprometer histórico, pontuação, progresso, conquistas ou evidências.

---

### RN-15 — Datas

Instantes devem ser persistidos em UTC e transportados em ISO 8601.

A apresentação deve seguir o padrão brasileiro, utilizando **UTC−3** para agregações por dia no MVP.

---

### RN-16 — Feedback didático

Após toda resposta confirmada, o estudante deve receber feedback informando:

- resultado da correção;
- resposta correta;
- explicação curta e didática;
- pontos recebidos, quando aplicável;
- acesso às evidências correspondentes.

O feedback deve utilizar o conteúdo validado e persistido da questão, sem nova chamada à IA.

O avanço para a próxima questão depende de ação do estudante.

---

## 4. Requisitos funcionais

| ID | Requisito |
| --- | --- |
| RF-01 | Cadastrar estudantes com nome, e-mail e senha e permitir sua autenticação; o MVP possui apenas o perfil de estudante |
| RF-02 | Restringir dados e operações ao estudante proprietário conforme `RN-01` |
| RF-03 | Enviar materiais conforme `RN-02` |
| RF-04 | Consultar, arquivar, restaurar e excluir materiais conforme `RN-14` |
| RF-05 | Processar materiais e informar seu estado conforme `RN-03` |
| RF-06 | Preparar e recuperar conteúdo dos materiais para RAG |
| RF-07 | Identificar cobertura e lacunas dos assuntos conforme `RN-06` |
| RF-08 | Criar e disponibilizar trilhas e etapas ordenadas |
| RF-09 | Gerar questões conforme `RN-07` |
| RF-10 | Registrar e corrigir tentativas com feedback conforme `RN-09` e `RN-16` |
| RF-11 | Disponibilizar flashcards conforme `RN-08` |
| RF-12 | Calcular e registrar pontos conforme `RN-11` |
| RF-13 | Calcular progresso conforme `RN-12` |
| RF-14 | Conceder e apresentar conquistas conforme `RN-13` |
| RF-15 | Exibir evolução com pontos, questões respondidas, acertos, percentual de acertos e progresso das trilhas |
| RF-16 | Permitir material complementar para assuntos sem cobertura |
| RF-17 | Permitir consulta às evidências conforme `RN-05` |
| RF-18 | Disponibilizar documentação OpenAPI/Swagger coerente com os contratos implementados, incluindo autenticação, validações e erros |
| RF-19 | Permitir consulta ao perfil e às conquistas do estudante |

---

## 5. Histórias de usuário

| ID | História |
| --- | --- |
| HU-01 | Como estudante, quero acessar somente meus dados. |
| HU-02 | Como estudante, quero enviar materiais para gerar conteúdo de estudo. |
| HU-03 | Como estudante, quero acompanhar o processamento dos meus materiais. |
| HU-04 | Como estudante, quero estudar os assuntos em uma sequência organizada. |
| HU-05 | Como estudante, quero responder questões e receber feedback didático. |
| HU-06 | Como estudante, quero que repetições técnicas não gerem efeitos duplicados. |
| HU-07 | Como estudante, quero revisar por flashcards os conteúdos relacionados às questões respondidas. |
| HU-08 | Como estudante, quero acompanhar meu desempenho e progresso. |
| HU-09 | Como estudante, quero receber conquistas pelos marcos alcançados. |
| HU-10 | Como estudante, quero identificar assuntos sem material suficiente. |
| HU-11 | Como estudante, quero consultar a origem do conteúdo gerado. |
| HU-12 | Como estudante, quero arquivar, restaurar e excluir materiais quando permitido. |

---

## 6. Casos de borda

| ID | Situação | Comportamento esperado |
| --- | --- | --- |
| CB-04 | Upload interrompido | Não processar arquivo incompleto |
| CB-09 | Materiais contraditórios | Não gerar atividade afetada até resolução |
| CB-13 | Trilha sem questões disponíveis | Não apresentar conclusão fictícia |
| CB-14 | Provedor de IA indisponível | Falhar de forma controlada sem publicar conteúdo parcial inválido |
| CB-15 | Material contém instruções direcionadas à IA | Tratar como conteúdo, nunca como instrução |
| CB-16 | Material arquivado durante processamento | Preservar consistência e impedir publicação indevida |
| CB-22 | Confirmação sem resposta selecionada | Não registrar tentativa |

---

## 7. Entidades conceituais

As entidades centrais do domínio são:

- **Estudante:** proprietário dos dados e recursos de estudo;
- **Material:** conteúdo enviado para estudo;
- **Trilha:** sequência organizada de etapas;
- **Etapa:** unidade temática da trilha;
- **Questão:** atividade avaliativa vinculada a evidências;
- **Flashcard:** recurso de revisão vinculado a evidências;
- **Tentativa:** resposta registrada do estudante;
- **Evidência:** origem rastreável que sustenta conteúdo gerado;
- **Conquista:** marco obtido pelo estudante.

Modelagem, persistência e entidades técnicas pertencem ao `PLAN.md`.

---

## 8. Requisitos de qualidade

### RQ-01 — Segurança

Garantir autenticação, autorização e isolamento entre usuários em todos os recursos e fluxos.

Segredos não podem ser expostos em código, logs ou respostas.

### RQ-02 — Consistência

Tentativas e seus efeitos devem permanecer consistentes sob repetição, concorrência e falhas recuperáveis.

### RQ-03 — Qualidade do conteúdo

Conteúdo pedagógico somente pode ser publicado quando possuir evidência autorizada e sustentação suficiente; validade estrutural isolada não comprova qualidade.

### RQ-04 — Rastreabilidade

Conteúdo gerado deve permanecer rastreável às evidências que o sustentam.

### RQ-05 — Substituição da IA

Regras de negócio não podem depender de provedor ou modelo específico de IA.

### RQ-06 — Acessibilidade e responsividade

Os fluxos principais devem funcionar por teclado e permanecer utilizáveis a partir de 320 px até desktop, conforme `DESIGN.md`.

### RQ-07 — Manutenibilidade

A implementação deve seguir a arquitetura do `PLAN.md` e as convenções do `SKILL.md`.

### RQ-08 — API

Os contratos da API devem permanecer coerentes e documentados em OpenAPI/Swagger.

---

## 9. Critérios de sucesso

- **CS-01:** a jornada principal do estudante funciona de ponta a ponta, do cadastro ao acompanhamento de evolução e conquistas.
- **CS-02:** dados e recursos permanecem isolados entre estudantes.
- **CS-03:** conteúdo pedagógico é gerado exclusivamente a partir dos materiais autorizados, com sustentação e rastreabilidade.
- **CS-04:** tentativas, feedback, pontuação, progresso, conquistas e flashcards respeitam as regras de negócio aplicáveis.
- **CS-05:** os fluxos principais funcionam em desktop e mobile, atendem aos requisitos de acessibilidade e possuem contratos de API coerentes.

---

## 10. Fluxo principal

```text
Cadastro e autenticação
    ↓
Envio e processamento de materiais
    ↓
Identificação de cobertura
    ↓
RAG e geração de conteúdo sustentado
    ↓
Trilha e questões
    ↓
Correção + feedback + evidências
    ↓
Flashcards de revisão
    ↓
Pontos + progresso + conquistas
    ↓
Evolução
```

Lacunas de cobertura seguem `RN-06`. Demais comportamentos do fluxo seguem as regras de negócio aplicáveis.

---

## 11. Regra de documentação

Este `SPEC.md` é a fonte de verdade para escopo, requisitos e regras de negócio.

Os demais documentos devem referenciar seus `RF` e `RN` quando necessário, sem duplicar sua especificação.

Mudanças no comportamento do produto devem ser registradas primeiro neste documento e refletidas nos demais somente quando necessário.