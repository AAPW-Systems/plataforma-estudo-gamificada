# Base de especificação: Plataforma de Estudos Gamificada

**Atualizado em:** 12/10/2026 ([registro da sessão](../prompts/2026-10-12-alinhamento-produto-arquitetura.md); sincronizado com as specs 001 a 007 aprovadas, [registro](../prompts/2026-10-12-revisao-requisitos-specs-mvp.md))
**Status:** rascunho de apoio às specs. Não é uma spec aprovada: o comportamento verificável de cada funcionalidade é definido em `docs/specs/NNN-nome-curto/spec.md`.

## 1. Objetivo

Reunir, em um só lugar, as regras de negócio, os requisitos, as histórias e os casos de borda do produto inteiro, para que cada spec de funcionalidade parta deles sem reinventá-los. O "o quê e por quê" do produto está na [visão](../produto/visao.md); a lista de funcionalidades e o recorte estão no [backlog](../produto/backlog.md); este documento diz **quais regras** valem.

A plataforma combina **repetição espaçada** com uma **trilha visual de progressão**. O estudante organiza seus estudos em matérias, guarda nelas suas fontes, cria cartões manualmente ou pede à IA que os gere a partir das fontes, e revisa tudo numa trilha unificada cujas lições são montadas pelo algoritmo FSRS (*Free Spaced Repetition Scheduler*). XP, meta diária e sequência incentivam a constância.

### IDs

Os IDs desta base (RN, RF, HU, CB, RQ, CS) são **estáveis desde 07/10/2026**. Nunca renumere: um item obsoleto é marcado como **removido**, com o motivo, e itens novos recebem o próximo número livre. As specs citam estes IDs na coluna de origem.

## 2. Estágios e escopo

O produto é apresentado em três estágios. A [arquitetura](../arquitetura/README.md) segue os mesmos estágios.

| Estágio | Prazo | Onde roda | O que entrega |
|---|---|---|---|
| **MVP** | 15/10, 20/10 ou 22/10/2026 (meta da equipe: 15/10) | Localmente (Docker Compose) | Matérias, fontes (PDF com texto, TXT, MD), cartões manuais e gerados pela IA com revisão do estudante, trilha unificada com FSRS, XP, meta diária, sequência e evolução mínima |
| **Final acadêmico** | Novembro de 2026 | VPS com HTTPS (deploy obrigatório) | MVP + chat com as fontes da matéria (RAG com busca híbrida e citações), tira-dúvidas do cartão, cartão com imagem, filtro da trilha por matéria e domínio por matéria, formatos SRT, VTT e DOCX, painel administrativo simples |
| **Referência pós-acadêmica** | Sem prazo | — | Evolução documentada, não implementada: ver [referência](../arquitetura/referencia-pos-academica.md) |

### 2.1 Fora de todos os estágios acadêmicos

- Ranking, ligas, rede social, equipes e compartilhamento público de materiais ou cartões.
- Pagamentos e assinaturas.
- Aplicativos nativos e funcionamento offline.
- Quizzes e questões de múltipla escolha (absorvidos pelos flashcards, QA-17).
- OCR de PDF digitalizado, XLSX e PPTX (referência pós-acadêmica, por custo de VPS).
- Painel administrativo completo. Um painel **simples** entra no final acadêmico (F-17, RN-27), com escopo definido na spec dele.
- Pesquisa externa (EX-01): **em pauta com o PO** ([pauta](../produto/pauta-po.md)); até a resposta, fora.

## 3. Glossário

| Termo | Significado |
|---|---|
| **Matéria** | Contêiner criado pelo estudante (ex.: Matemática, Biologia). Reúne fontes, cartões e, no final acadêmico, o chat |
| **Fonte** | Arquivo enviado a uma matéria. Fica **arquivada** na matéria (acervo) e alimenta a geração de cartões e o chat |
| **Trecho** | Parte de uma fonte extraída e delimitada (com página, quando conhecida), usada como evidência |
| **Cartão** | Flashcard: frente (pergunta, com imagem opcional no final acadêmico), verso (resposta) e explicação curta. Não é quiz: é sempre respondido pela autoavaliação |
| **Origem do cartão** | *Gerado e verificado* (IA, sustentado por trechos), *editado por você* ou *criado por você* |
| **Aguardando revisão** | Estado de um cartão gerado que o estudante ainda não aceitou nem recusou. Não entra na trilha |
| **Revisão** | Evento em que o estudante revela o verso e se autoavalia com um dos quatro botões |
| **Lição** | Sessão de estudo curta montada pelo servidor a partir do FSRS (devidos primeiro, depois novos). Um cartão marcado Errei volta na mesma lição quando o passo curto do FSRS vence, se a lição ainda estiver em andamento (RN-26) |
| **Cartão novo** | Cartão ativo que nunca foi revisado |
| **Cartão devido** | Cartão ativo cujo vencimento calculado pelo FSRS é anterior à próxima virada do dia de estudo (4h locais) |
| **Cartão disponível** | Cartão devido, ou cartão novo dentro do limite diário de novos (RN-20) |
| **Trilha** | Caminho visual de progressão. Cada nó é uma lição; o nó concluído permanece como marco |
| **Cartão dominado** | Cartão cuja estabilidade no FSRS atingiu o limiar definido (QA-24) |
| **Dia de estudo** | Dia no fuso do estudante, que vira às 4h locais |
| **Meta efetiva** | O menor valor entre a meta diária e a quantidade de cartões disponíveis no dia |

## 4. Regras de negócio

### RN-01 Propriedade e isolamento

Matérias, fontes, trechos, cartões, revisões, XP, sequência e conversas pertencem a um único estudante. Conhecer um identificador não concede acesso. Nenhum estudante consulta, altera ou usa como fonte recursos de outro, inclusive na busca do RAG.

### RN-02 Admissão de fontes

| Estágio | Formatos | Tamanho | Por envio |
|---|---|---|---|
| MVP | PDF com camada de texto, TXT e MD | até 2 MB | 1 arquivo |
| Final acadêmico | + SRT, VTT e DOCX | a definir pela equipe | 1 ou mais, a definir |
| Referência | + PDF digitalizado (OCR), XLSX e PPTX | — | — |

O backend valida extensão, tipo real do conteúdo, tamanho e integridade antes do processamento. Arquivos inválidos, vazios, corrompidos ou sem texto extraível são recusados com explicação e não geram conteúdo. Os limites são configuráveis por ambiente.

### RN-03 Processamento

O processamento de uma fonte tem os estados `pendente`, `processando`, `concluido` e `falhou`, visíveis ao estudante. `concluido` significa que o texto foi extraído e dividido em trechos persistidos (e, no final acadêmico, indexados para busca). Falha técnica e conteúdo insuficiente para gerar cartões são situações distintas. Reprocessamentos respeitam RN-10.

### RN-04 Fontes exclusivas

Todo conteúdo gerado pela IA (cartões, explicações, respostas do chat) usa **somente** as fontes do próprio estudante. É proibido completar lacunas com conhecimento geral do modelo, bases externas ou conteúdo de outros usuários. Trocar de provedor de IA não altera esta regra (Princípio I da [constituição](../constitution.md)). A exceção da consulta externa (EX-01) está em pauta com o PO.

### RN-05 Evidência e referência da origem

Todo cartão gerado fica vinculado aos trechos que o sustentam. Cada evidência identifica a fonte, o trecho e, **somente quando conhecida**, a página; o sistema nunca inventa página ou localização.

Desde a criação, o cartão guarda uma **cópia da descrição da origem**: título da fonte, nome do arquivo, página (quando conhecida) e data do envio. Essa descrição sobrevive à exclusão da fonte (RN-14). O texto do trecho **não** é copiado.

### RN-06 Cobertura e lacunas

**Fora dos estágios acadêmicos** (F-13). Quando existir: a menção a um assunto não implica cobertura suficiente; assuntos sem evidência ficam como "aguardando material de apoio", sem geração por conhecimento externo.

### RN-07 Questões

**Removida em 12/10/2026.** Questões de múltipla escolha e verdadeiro ou falso corrigidas automaticamente foram absorvidas pelos flashcards (QA-17). Uma pergunta no formato "verdadeiro ou falso" é apenas uma forma de escrever a frente de um cartão.

### RN-08 Cartão

- Modelo único: **frente** (texto; imagem opcional no final acadêmico, até 3 MB, JPEG, PNG ou WebP), **verso**, **explicação curta** (RN-16) e **origem**.
- O verso só é revelado por ação explícita do estudante.
- Todos os cartões são respondidos da mesma forma (RN-17). Não há tipo de cartão com correção automática.
- O estudante pode criar, editar, suspender e excluir cartões. Editar um cartão gerado muda a origem para *editado por você*, mantém o vínculo com o trecho e remove o selo de verificado.
- Cartão suspenso não entra em lições até ser reativado; seu estado no FSRS é preservado.

### RN-09 Tentativas

**Removida em 12/10/2026.** Substituída por RN-17 (revisão com FSRS).

### RN-10 Idempotência

Toda revisão enviada carrega um identificador gerado no cliente. O reenvio com o mesmo identificador e o mesmo conteúdo devolve o resultado original, sem duplicar revisão, XP ou efeitos na sequência. O mesmo identificador com conteúdo diferente gera conflito. Pedidos de geração e de processamento também são protegidos contra execução duplicada. A proteção é persistente (restrições de unicidade e transações), nunca apenas em memória.

### RN-11 Pontuação

**Removida em 12/10/2026.** Pontos por dificuldade da questão foram substituídos por XP (RN-18).

### RN-12 Progresso

**Removida em 12/10/2026.** O progresso por conclusão de questões foi substituído pela trilha de lições (RN-19), pela sequência (RN-21) e pela evolução (RN-25).

### RN-13 Conquistas

**Fora do MVP** (F-11). Os critérios do brainstorming, baseados em questões, não valem mais e serão redefinidos com base em revisões, cartões dominados e sequência (QA-08). Cada conquista será concedida uma única vez por estudante.

### RN-14 Ciclo de vida das fontes

- As fontes ficam **arquivadas na matéria** (acervo da matéria) enquanto o estudante quiser. Elas são a base da geração de cartões e, no final acadêmico, do chat.
- A **exclusão é definitiva**: remove o arquivo, os trechos e, quando houver, os embeddings. Exige confirmação explícita, com o impacto exibido antes (quantidade de cartões aceitos e de cartões aguardando revisão).
- No diálogo de confirmação, o estudante escolhe entre **manter** os cartões aceitos ou **excluí-los junto**.
  - Cartões mantidos exibem "fonte apagada" junto da descrição da origem (RN-05), perdem o selo de verificado e preservam o histórico do FSRS.
  - Cartões aguardando revisão daquela fonte são sempre excluídos.
- Revisões registradas, XP e sequência já conquistados nunca são removidos. A única exceção é a exclusão da conta pelo próprio estudante, que apaga todos os dados ([spec 001](../specs/001-conta-acesso/spec.md), RF-015).
- No final acadêmico, citações do chat a uma fonte apagada passam a exibir "fonte apagada".
- Não há arquivamento com restauração: "arquivar" significa guardar a fonte no acervo, não ocultá-la.

### RN-15 Datas e dia de estudo

Instantes são persistidos em UTC e transportados em ISO 8601 com fuso explícito. A exibição segue o padrão brasileiro, no fuso do estudante (configurável no perfil, detectado no cadastro, padrão `America/Sao_Paulo`). O dia de estudo vira às **4h** no horário local, para que quem estuda de madrugada não perca o dia.

### RN-16 Explicação do erro

Exigência EX-03. Todo cartão gerado pela IA traz, criada junto com ele, uma explicação curta e didática sustentada pelo trecho de origem, com a citação. A explicação é exibida quando o estudante marca **Errei**, junto do acesso à evidência. Em cartões criados pelo estudante, a explicação é opcional. Exibir a explicação não faz nova chamada à IA.

### RN-17 Revisão com FSRS

- Após revelar o verso, o estudante se autoavalia com **Errei, Difícil, Bom ou Fácil**. Os quatro botões são os mesmos para todos os cartões.
- O servidor calcula o próximo agendamento com o FSRS (RN-26) e mantém, por cartão, o estado do algoritmo (aprendizado, revisão ou reaprendizado), o passo, a estabilidade, a dificuldade, o vencimento e a última revisão. Não existe estado "novo" no algoritmo: um cartão novo é um cartão em aprendizado que nunca foi revisado.
- Os botões correspondem às notas do FSRS: Errei (*Again*), Difícil (*Hard*), Bom (*Good*) e Fácil (*Easy*).
- Cada revisão é um evento imutável, com nota, instante, duração, o estado do cartão antes e depois e a versão dos parâmetros do FSRS usada, o que permite reproduzir o agendamento.
- Não há desfazer revisão no MVP (incremento posterior de F-05).

### RN-26 Soberania do FSRS

Decidida em 12/10/2026 ([registro](../prompts/2026-10-12-esquema-inicial-banco.md)). O FSRS é o centro do produto, e as demais regras se adaptam a ele, nunca o contrário.

- O vencimento de cada cartão é calculado **exclusivamente** pelo FSRS. Nenhuma regra do produto (lição, meta, XP, sequência, filtro por matéria, exibição da dificuldade) antecipa, adia ou altera esse cálculo.
- **Passos curtos:** em aprendizado e reaprendizado, o FSRS agenda o cartão em minutos (padrão: 1 e 10 minutos no aprendizado; 10 minutos no reaprendizado). A lição reapresenta o cartão quando o passo vence. Se a lição for interrompida, ou terminar antes do vencimento do passo, o cartão vence no instante calculado e entra na próxima lição.
- **Dia de estudo:** o FSRS agenda instantes em UTC; um cartão é devido no dia de estudo se vencer antes da próxima virada das 4h no fuso do estudante (RN-15).
- **Sem revisão antecipada:** cartões que ainda não venceram não entram em lições, nem nas extras.
- **Intervalos com variação aleatória leve** (*fuzzing*) ficam ligados, para que cartões criados juntos não vençam sempre juntos.
- **Parâmetros por estudante:** os parâmetros do FSRS (pesos, retenção desejada, passos, intervalo máximo) são versionados por estudante e nunca alterados no lugar. A **retenção desejada** é uma preferência do perfil (padrão 0,90). No MVP, todos usam os pesos padrão da biblioteca; a otimização dos pesos pelo histórico do estudante fica para depois e não exige mudança de esquema.
- **Edição:** editar o texto de um cartão não reinicia seu estado no FSRS. Uma ação explícita de "reiniciar aprendizado" é incremento posterior de F-05.
- **Filtro por matéria** (final acadêmico): restringe quais cartões disponíveis entram na lição, sem alterar o agendamento.
- A **dificuldade** exibida ao estudante, se aprovada (PO-01), é uma leitura da dificuldade calculada pelo FSRS, nunca uma escolha.

### RN-18 XP

- A **primeira revisão de cada cartão no dia de estudo** concede XP, **independentemente da nota**. Reapresentações do mesmo cartão no mesmo dia (passos curtos do FSRS, RN-26) não concedem XP, para que errar de propósito não renda pontos. Decidido em 12/10/2026 (Princípio de gamificação da [visão](../produto/visao.md#princípio-de-gamificação): nunca premiar a nota que o próprio estudante se atribui).
- Um cartão que se torna **dominado** pela primeira vez concede um bônus.
- XP é calculado no servidor, rastreável ao evento que o originou e nunca removido, exceto na exclusão da conta pelo próprio estudante ([spec 001](../specs/001-conta-acesso/spec.md), RF-015). Os valores (QA-24) ficam numa regra versionada: mudar valores não altera XP já concedido.

### RN-19 Lição e trilha

- A lição é uma sessão de estudo montada pelo servidor: primeiro os cartões devidos, depois os novos, até o tamanho da lição (em cartões distintos) e respeitando o limite diário de novos cartões (RN-20).
- Um cartão em aprendizado ou reaprendizado que recebe um passo curto (minutos) volta na mesma lição quando o passo vence. A lição termina quando todos os cartões previstos foram revisados ao menos uma vez e nenhum passo curto já vencido aguarda reapresentação; um cartão cujo passo curto ainda não venceu entra na próxima lição, no instante calculado (RN-26). Alterado em 12/10/2026 pela [spec 005](../specs/005-licao-trilha/spec.md) (D-004).
- **MVP:** a lição mistura cartões de todas as matérias (trilha unificada, sem filtro).
- **Final acadêmico:** é possível filtrar a lição por matéria, e cada matéria exibe seu domínio (cartões dominados sobre o total de cartões ativos).
- A trilha mostra as lições concluídas como nós alcançados, a lição atual e o próximo passo. Concluir uma lição acende o nó.
- Depois da meta, o estudante pode fazer lições extras enquanto houver cartões **disponíveis**. Não há revisão antecipada de cartões que ainda não venceram (RN-26).
- Sem cartões disponíveis, não há lição. A trilha mostra o próximo agendamento, sem conteúdo fictício.

### RN-20 Novos cartões por dia

O estudante configura o limite diário de cartões novos que entram nas lições (padrão de 20 por dia, global, de 0 a 100; [spec 001](../specs/001-conta-acesso/spec.md), D-001). Um cartão novo conta no limite quando é revisado pela primeira vez ([spec 005](../specs/005-licao-trilha/spec.md), D-007). Cartões aceitos além do limite aguardam os dias seguintes, na ordem de aceitação. O limite decide **quando** um cartão novo é apresentado pela primeira vez; depois disso, o agendamento é do FSRS.

### RN-21 Meta diária e sequência

- A meta diária é um número de **cartões distintos revisados** no dia, configurável. Reapresentações do mesmo cartão não contam duas vezes.
- A meta efetiva usa os cartões **disponíveis** no dia (devidos e novos dentro do limite).
- **Dia estudado:** dia em que a meta efetiva é cumprida.
- Um dia sem nenhum cartão disponível é **neutro**: não conta como estudado e não quebra a sequência.
- A sequência é o número de dias estudados consecutivos, desconsiderando os dias neutros. Lições extras não criam dias adicionais.
- Congelamento da sequência fica fora do MVP (incremento de F-10).

### RN-22 Geração e revisão dos cartões gerados

- O estudante pede cartões de uma fonte ou de uma matéria. A geração roda em segundo plano, com estados visíveis.
- Cada cartão gerado passa por **validação estrutural** (esquema, campos obrigatórios, vínculo com trechos existentes da mesma matéria e do mesmo estudante) e por **validação de sustentação** antes de ficar visível. Uma segunda chamada de IA pode auxiliar, mas não prova sustentação (Princípio V).
- Os aprovados entram como **aguardando revisão**. O estudante pode **aceitar**, **editar e aceitar**, **recusar** ou **aceitar todos**.
- Ao terminar, um **cartão de resumo** mostra quantos foram gerados, aceitos e recusados, e oferece **Gerar mais** (EX-02).
- **Gerar mais** não repete cartões existentes nem recusados da mesma matéria.
- Cartões recusados não aparecem ao estudante, mas ficam registrados para a **taxa de aceitação**, métrica de qualidade da IA.
- Após o MVP: avaliar se a quantidade gerada é coerente com o volume da fonte.
- Cada geração registra o modelo, a versão das instruções e os trechos usados.

### RN-23 Matérias

O estudante cria, renomeia e exclui matérias (nome de 1 a 60 caracteres, único por estudante). Toda fonte e todo cartão pertencem a exatamente uma matéria. A exclusão de uma matéria é definitiva e em cascata (fontes, trechos e cartões), com o impacto exibido e a confirmação pelo nome digitado; revisões, XP e sequência são preservados ([spec 002](../specs/002-materias-fontes/spec.md), D-002).

### RN-24 Chat com as fontes e tira-dúvidas

**Final acadêmico** (F-06 e F-16).
- O chat fica ao lado das fontes da matéria e responde apenas com base nelas.
- Cada resposta cita os trechos usados, com links até o trecho e a página.
- Sem evidência, o chat declara que não encontrou a informação nas fontes.
- O tira-dúvidas abre o chat com o cartão como contexto (EX-04).
- O escopo do histórico e os limites de uso estão em QA-16.

### RN-27 Papéis

Decidida em 12/10/2026 ([registro](../prompts/2026-10-12-esquema-inicial-banco.md)).

- Toda conta tem um papel: **estudante** (padrão) ou **administrador**. Os dois usam a mesma conta e o mesmo login.
- O cadastro público cria apenas estudantes. O papel de administrador nunca é atribuído por uma requisição do próprio usuário; a forma de concedê-lo é definida na spec de F-17.
- O MVP não tem funcionalidade de administrador. O painel administrativo simples entra no final acadêmico (F-17).
- O papel de administrador não suspende o isolamento (RN-01) por padrão: o que o painel pode ver dos dados dos estudantes é decidido na spec de F-17 ([QA-32](../produto/pendencias.md#qa-32-escopo-do-painel-administrativo)) e nunca inclui o conteúdo das fontes ou das conversas sem justificativa registrada.

### RN-25 Evolução

Calculados no servidor, por matéria e no total:
- dias estudados (calendário);
- tempo dedicado (soma do tempo por cartão, com teto por cartão, QA-24);
- cartões dominados;
- XP total;
- sequência atual e recorde.

No MVP, o mínimo é dias estudados, XP, sequência e cartões dominados.

## 5. Requisitos funcionais

| ID | Requisito | Estágio |
|---|---|---|
| RF-01 | Cadastrar estudantes com nome, e-mail e senha e autenticá-los. Estudantes e administradores usam a mesma conta e o mesmo login, distinguidos pelo papel (RN-27). Recuperação de senha por e-mail no final acadêmico | MVP |
| RF-02 | Restringir dados e operações ao estudante proprietário (RN-01) | MVP |
| RF-03 | Enviar fontes a uma matéria (RN-02) | MVP |
| RF-04 | Listar, consultar e excluir fontes definitivamente, com escolha sobre os cartões (RN-14) | MVP |
| RF-05 | Processar fontes e informar seu estado (RN-03) | MVP |
| RF-06 | Extrair trechos das fontes (MVP) e indexá-los para busca híbrida (final acadêmico) | MVP / Final |
| RF-07 | **Fora dos estágios acadêmicos:** identificar cobertura e lacunas (RN-06) | — |
| RF-08 | Apresentar a trilha de lições com nós alcançados, lição atual e próximo passo (RN-19) | MVP |
| RF-09 | **Removido em 12/10/2026:** gerar questões (RN-07) | — |
| RF-10 | **Removido em 12/10/2026:** registrar e corrigir tentativas (substituído por RF-21) | — |
| RF-11 | Criar, editar, suspender e excluir cartões manualmente (RN-08) | MVP |
| RF-12 | Calcular e registrar XP (RN-18) | MVP |
| RF-13 | **Removido em 12/10/2026:** calcular progresso por questões (substituído por RF-24 e RF-15) | — |
| RF-14 | Conceder e apresentar conquistas (RN-13) | Fora do MVP |
| RF-15 | Exibir a evolução (RN-25) | MVP (mínimo) |
| RF-16 | **Fora dos estágios acadêmicos:** material complementar para assuntos sem cobertura | — |
| RF-17 | Consultar a evidência e a descrição da origem de um cartão (RN-05) | MVP |
| RF-18 | Disponibilizar OpenAPI e Swagger UI coerentes com os contratos, incluindo autenticação, validações e erros | MVP |
| RF-19 | Consultar e alterar o perfil e as preferências: fuso, meta diária, tamanho da lição, limite de novos cartões e retenção desejada do FSRS (RN-26) | MVP |
| RF-20 | Criar, renomear e excluir matérias (RN-23) | MVP |
| RF-21 | Revisar cartões em lições com autoavaliação e agendamento FSRS (RN-17, RN-26, RN-10) | MVP |
| RF-22 | Gerar cartões por IA a partir de fontes, com revisão pelo estudante, resumo e "Gerar mais" (RN-22, EX-02) | MVP |
| RF-23 | Exibir a explicação curta ao marcar "Errei" (RN-16, EX-03) | MVP |
| RF-24 | Calcular meta efetiva, dia estudado e sequência (RN-21) | MVP |
| RF-25 | Conversar com as fontes de uma matéria, com citações (RN-24) | Final |
| RF-26 | Tira-dúvidas a partir de um cartão, com referência (RN-24, EX-04) | Final |
| RF-27 | Criar cartões com imagem na frente (RN-08) | Final |
| RF-28 | Filtrar a lição por matéria e exibir o domínio por matéria (RN-19) | Final |
| RF-29 | Painel administrativo simples, acessível só ao papel administrador (RN-27) | Final |

## 6. Histórias de usuário

| ID | História | Estágio |
|---|---|---|
| HU-01 | Como estudante, quero acessar somente meus dados. | MVP |
| HU-02 | Como estudante, quero enviar fontes para uma matéria. | MVP |
| HU-03 | Como estudante, quero acompanhar o processamento das minhas fontes. | MVP |
| HU-04 | Como estudante, quero estudar numa trilha que mostre de onde vim e o próximo passo. | MVP |
| HU-05 | **Removida em 12/10/2026:** responder questões com feedback (RN-07). | — |
| HU-06 | Como estudante, quero que reenvios técnicos não dupliquem revisões nem XP. | MVP |
| HU-07 | Como estudante, quero revisar meus cartões no momento certo, conforme meu desempenho em cada um. | MVP |
| HU-08 | Como estudante, quero acompanhar minha evolução. | MVP (mínimo) |
| HU-09 | Como estudante, quero receber conquistas pelos marcos alcançados. | Fora do MVP |
| HU-10 | **Fora dos estágios acadêmicos:** identificar assuntos sem material suficiente. | — |
| HU-11 | Como estudante, quero consultar de onde veio cada cartão gerado. | MVP |
| HU-12 | Como estudante, quero excluir uma fonte de vez e decidir o que acontece com os cartões dela. | MVP |
| HU-13 | Como estudante, quero organizar fontes e cartões por matéria. | MVP |
| HU-14 | Como estudante, quero que a IA gere cartões das minhas fontes e escolher quais entram no meu baralho. | MVP |
| HU-15 | Como estudante, quero criar e editar meus próprios cartões. | MVP |
| HU-16 | Como estudante, quero entender por que errei um cartão. | MVP |
| HU-17 | Como estudante, quero manter minha sequência sem ser punido em dias sem cartões. | MVP |
| HU-18 | Como estudante, quero conversar com as fontes de uma matéria e ver as citações. | Final |
| HU-19 | Como estudante, quero tirar dúvidas sobre um cartão durante a revisão. | Final |
| HU-20 | Como administrador, quero acompanhar e operar a plataforma num painel simples. | Final |

## 7. Casos de borda

| ID | Situação | Comportamento esperado |
|---|---|---|
| CB-04 | Envio interrompido | Não processar arquivo incompleto |
| CB-09 | Fontes contraditórias sobre o mesmo ponto | Não gerar cartão afirmando um dos lados como fato; a spec de F-04 define o tratamento |
| CB-13 | Nenhum cartão disponível no dia | Nenhuma lição; dia neutro (RN-21); a trilha mostra o próximo agendamento |
| CB-14 | Provedor de IA indisponível ou limite gratuito esgotado | Falha controlada e visível, sem publicar conteúdo parcial; a geração pode ser retomada |
| CB-15 | Fonte contém instruções direcionadas à IA | Tratar como conteúdo, nunca como instrução |
| CB-16 | Fonte excluída durante o processamento ou a geração | Interromper, não publicar cartões dela e manter a consistência |
| CB-22 | Avaliação enviada sem o verso ter sido revelado | Não registrar a revisão |
| CB-23 | PDF sem camada de texto | Recusar com explicação (OCR fora dos estágios acadêmicos) |
| CB-24 | Mesma revisão reenviada, ou enviada de duas abas | Um único efeito (RN-10) |
| CB-25 | Revisão perto das 4h, mudança de fuso ou horário de verão | Atribuir ao dia de estudo correto no fuso vigente no instante da revisão |
| CB-26 | "Gerar mais" sem conteúdo novo na fonte | Informar que não há novos cartões a gerar, sem repetir existentes |
| CB-27 | Exclusão de fonte com cartões em lição aberta | A lição em andamento não perde as revisões já registradas |
| CB-28 | Lição interrompida com cartão em passo curto | O cartão mantém o vencimento calculado pelo FSRS e entra na próxima lição; o nó só acende quando a lição é concluída |
| CB-29 | Estudante altera a retenção desejada | Uma nova versão dos parâmetros vale a partir da próxima revisão; revisões anteriores mantêm a versão usada |
| CB-30 | Todos os cartões disponíveis do dia já foram revisados | Nenhuma lição extra; a trilha mostra o próximo vencimento, sem revisão antecipada |

## 8. Entidades conceituais

Estudante, Matéria, Fonte, Trecho, Cartão, Estado FSRS do cartão, Parâmetros do FSRS, Revisão, Geração (pedido de geração e seus cartões), Lição, Evento de XP, Dia de estudo, Conversa e Mensagem (final acadêmico), Citação. A modelagem física está no [esquema inicial em DBML](../arquitetura/esquema-inicial.dbml) e no `data-model.md` de cada spec.

## 9. Requisitos de qualidade

| ID | Requisito |
|---|---|
| RQ-01 | **Segurança:** autenticação, autorização e isolamento em todos os recursos e fluxos, inclusive na busca do RAG. Segredos fora de código, logs e respostas |
| RQ-02 | **Consistência:** revisões e seus efeitos permanecem consistentes sob repetição, concorrência e falhas recuperáveis |
| RQ-03 | **Qualidade do conteúdo:** só vira cartão aguardando revisão o que tem evidência e sustentação; validade estrutural isolada não comprova qualidade |
| RQ-04 | **Rastreabilidade:** conteúdo gerado permanece rastreável à evidência ou, após a exclusão da fonte, à descrição da origem |
| RQ-05 | **Substituição da IA:** regras de negócio não dependem de provedor ou modelo específico |
| RQ-06 | **Acessibilidade e responsividade:** WCAG 2.2 AA, operação por teclado, a partir de 320 px ([design](design.md)) |
| RQ-07 | **Manutenibilidade:** segue a [arquitetura](../arquitetura/README.md) e os [padrões de implementação](../skills/padroes-implementacao.md) |
| RQ-08 | **API:** contratos coerentes e documentados em OpenAPI |
| RQ-09 | **Custo operacional:** o final acadêmico roda numa VPS de 2 a 4 GB de RAM, sem modelos locais, usando camadas gratuitas de serviços externos quando possível |
| RQ-10 | **Avaliação da IA:** a geração é medida pela taxa de aceitação e por um conjunto de casos revisado por pessoa; o RAG do final acadêmico é comparado a uma solução de referência só com busca textual |

## 10. Critérios de sucesso

- **CS-01:** a jornada principal funciona de ponta a ponta: cadastro, matéria, fonte, cartões gerados e aceitos, lição, XP, sequência e evolução.
- **CS-02:** dados e recursos permanecem isolados entre estudantes.
- **CS-03:** cartões gerados usam exclusivamente as fontes do estudante, com evidência e descrição da origem.
- **CS-04:** revisões, agendamento, XP, meta e sequência respeitam as regras, inclusive sob reenvio e na virada do dia.
- **CS-05:** os fluxos principais funcionam em desktop e celular, atendem à acessibilidade e têm contratos de API coerentes.
- **CS-06** (final acadêmico): o chat responde com citações corretas e declara a falta de evidência, com qualidade medida contra a solução de referência.

## 11. Fluxo principal

```text
Cadastro -> cria matéria -> envia fonte -> processamento
    -> pede cartões -> revisa os gerados (aceitar, editar, recusar) -> resumo / gerar mais
    -> trilha: lição do dia (FSRS) -> revela, autoavalia, vê explicação ao errar
    -> XP, meta, sequência -> evolução
Final acadêmico: chat ao lado das fontes da matéria e tira-dúvidas do cartão
```

## 12. Regra de documentação

- A [visão](../produto/visao.md) descreve o produto. Este documento descreve as regras. O [backlog](../produto/backlog.md) define o que entra em cada estágio.
- Em caso de divergência, corrija primeiro a visão (produto) ou a [constituição](../constitution.md) (princípios), depois esta base, e por fim as specs.
- Uma spec aprovada prevalece sobre esta base para a sua funcionalidade. Ao aprová-la, atualize aqui as regras que mudaram.
