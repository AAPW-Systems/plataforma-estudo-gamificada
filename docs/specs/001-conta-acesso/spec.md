# Especificação: conta, sessão, isolamento e preferências

**Identificador:** 001-conta-acesso
**Estágio:** MVP
**Funcionalidade do backlog:** [F-01](../../produto/backlog.md#funcionalidades-candidatas), parte do MVP (a recuperação de senha do final acadêmico está em [008-recuperacao-senha](../008-recuperacao-senha/spec.md))
**Criada em:** 12/10/2026
**Status:** Aprovada para planejamento em 12/10/2026 por Artur Lins (equipe)
**Origem:** backlog, [base de especificação](../../base-specs/spec.md) (HU-01, RF-01, RF-02, RF-19, RN-01, RN-15, RN-26, RN-27) e decisões da [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante individual, com fontes próprias de várias matérias.
**Situação:** o estudante vai guardar fontes, cartões e um histórico de revisões que leva semanas para construir.
**Problema observável:** sem uma conta própria, o progresso não sobrevive à troca de dispositivo e os materiais de um estudante podem ficar ao alcance de outro.
**Resultado esperado:** o estudante cria a conta, entra e sai com segurança, só enxerga os próprios dados e ajusta o ritmo de estudo (meta, tamanho da lição, novos cartões por dia, retenção desejada e fuso).
**Alternativa atual:** anotações e arquivos soltos no próprio dispositivo, sem histórico de revisão.

## Escopo

### Incluído

- Cadastro com nome, e-mail e senha. Toda conta criada pelo cadastro público tem o papel **estudante** (RN-27).
- Entrada (login) com e-mail e senha, saída (logout) e expiração da sessão.
- Isolamento: cada estudante acessa somente os próprios recursos (RN-01).
- Consulta e alteração do perfil e das preferências: nome, fuso, meta diária, tamanho da lição, limite de novos cartões por dia e retenção desejada (RF-19).
- Valores padrão das preferências para quem acaba de se cadastrar.
- Aviso curto de privacidade no cadastro (D-007).
- Alteração da senha com a sessão aberta (D-004).
- Exclusão da própria conta, com todos os dados (D-003).

### Fora do escopo

- Recuperação de senha por e-mail: final acadêmico, em [008-recuperacao-senha](../008-recuperacao-senha/spec.md).
- Login social, autenticação em dois fatores e login institucional.
- Funcionalidades de administrador: final acadêmico, em [016-painel-administrativo](../016-painel-administrativo/spec.md). O MVP só registra o papel.
- Troca de e-mail.
- Confirmação do e-mail no cadastro: fora do MVP; o estágio (final acadêmico ou referência pós-acadêmica) está em discussão na equipe ([QA-33](../../produto/pendencias.md#qa-33-confirmação-de-e-mail-no-cadastro)).

## Cenários de usuário e testes

### História de usuário 1 Criar conta e entrar P1

Como estudante, quero criar minha conta e entrar nela, para guardar meus estudos num lugar só meu.

**Motivo da prioridade:** nenhuma outra funcionalidade existe sem conta (não há uso anônimo).
**Teste independente:** cadastrar uma conta fictícia, sair, entrar de novo e confirmar que a sessão dá acesso à área do estudante; tentar entrar com a senha errada e confirmar a recusa com mensagem neutra.

**Cenários de aceitação**

1. **Dado** um e-mail ainda não cadastrado, **quando** o estudante informa nome, e-mail e uma senha válida, **então** a conta é criada com o papel estudante, as preferências padrão e o fuso detectado no navegador (ou `America/Sao_Paulo`, se não for possível detectar), e o estudante já entra na plataforma.
2. **Dado** uma senha com menos de 8 caracteres ou presente na lista de senhas comuns, **quando** o estudante tenta se cadastrar, **então** o cadastro é recusado com a explicação junto do campo, e os demais valores digitados são preservados.
3. **Dado** uma conta existente, **quando** o estudante entra com e-mail e senha corretos, **então** uma sessão é iniciada e ele chega à trilha.
4. **Dado** uma senha errada ou um e-mail inexistente, **quando** o estudante tenta entrar, **então** a mensagem é a mesma nos dois casos e não revela se o e-mail tem conta.
5. **Dado** uma sessão aberta, **quando** o estudante sai, **então** a sessão deixa de valer no servidor, e uma requisição posterior com ela é tratada como não autenticada.
6. **Dado** cinco tentativas de entrada malsucedidas para a mesma conta em 15 minutos, **quando** chega a sexta tentativa, **então** ela é recusada temporariamente, com a indicação de tentar mais tarde, mesmo que a senha esteja correta.
7. **Dado** um e-mail que já tem conta (sem diferenciar maiúsculas e minúsculas), **quando** alguém tenta se cadastrar com ele, **então** o cadastro é recusado com a mensagem de que o e-mail já está em uso, e nenhuma conta é criada (D-005).
8. **Dado** a tela de cadastro, **quando** o estudante a abre, **então** vê um aviso curto de privacidade: quais dados a plataforma guarda e que, ao pedir cartões gerados pela IA, trechos das fontes são enviados a um provedor externo.

### História de usuário 2 Acessar somente meus dados P1

Como estudante, quero que somente eu acesse minhas matérias, fontes, cartões e progresso, para estudar com privacidade.

**Motivo da prioridade:** um vazamento entre estudantes compromete o produto inteiro (Princípio II).
**Teste independente:** com duas contas fictícias, A e B, usar na conta B os identificadores de recursos da conta A em todas as operações expostas e confirmar que nenhuma devolve, altera ou confirma a existência do recurso.

**Cenários de aceitação**

1. **Dado** um recurso da conta A, **quando** a conta B tenta consultá-lo, alterá-lo ou excluí-lo pelo identificador, **então** a resposta é idêntica à de um recurso inexistente.
2. **Dado** uma requisição sem sessão válida, **quando** ela tenta acessar qualquer recurso de estudante, **então** é recusada como não autenticada, sem dados do recurso.
3. **Dado** uma requisição que altera dados, **quando** ela vem de outra origem sem a proteção contra falsificação de requisição, **então** é recusada.

### História de usuário 3 Ajustar perfil e preferências P2

Como estudante, quero ajustar meu fuso e meu ritmo de estudo, para que a meta e as lições caibam na minha rotina.

**Motivo da prioridade:** os padrões já permitem estudar; o ajuste melhora a constância, mas não bloqueia a jornada.
**Teste independente:** alterar cada preferência para um valor válido e um inválido e confirmar que só os válidos são salvos; alterar a retenção desejada e confirmar que a próxima revisão usa a nova versão dos parâmetros.

**Cenários de aceitação**

1. **Dado** um estudante autenticado, **quando** ele abre o perfil, **então** vê nome, e-mail, fuso e as preferências atuais, com a explicação, em linguagem simples, do efeito de aumentar ou reduzir a retenção desejada.
2. **Dado** um valor fora dos limites, **quando** o estudante tenta salvar, **então** nada é alterado e o erro aparece junto do campo.
3. **Dado** uma nova retenção desejada, **quando** o estudante salva, **então** uma nova versão dos parâmetros de agendamento passa a valer a partir da próxima revisão, e as revisões anteriores mantêm a versão que usaram (CB-29 da base).
4. **Dado** um novo fuso, **quando** o estudante salva, **então** os próximos dias de estudo passam a virar às 4h no novo fuso, e os dias já registrados não mudam.

### História de usuário 4 Proteger e encerrar a conta P3

Como estudante, quero trocar minha senha e, se quiser, excluir minha conta com todos os meus dados, para manter o controle sobre eles.

**Motivo da prioridade:** proteção e direito previsto na LGPD; não bloqueiam a jornada principal.
**Teste independente:** trocar a senha de uma conta fictícia com duas sessões abertas e confirmar que só a sessão atual continua válida; excluir outra conta fictícia com matérias, fontes e cartões e confirmar que nenhum dado dela permanece e que o e-mail pode ser usado num novo cadastro.

**Cenários de aceitação**

1. **Dado** uma sessão aberta, **quando** o estudante informa a senha atual e uma nova senha válida, **então** a senha é trocada, e todas as outras sessões da conta são encerradas.
2. **Dado** uma senha atual errada, **quando** o estudante tenta trocar a senha, **então** nada muda, e a tentativa conta para o limite de tentativas da conta.
3. **Dado** o pedido de exclusão da conta, **quando** o estudante abre a ação, **então** um diálogo explica que a exclusão é definitiva e apaga matérias, fontes, cartões, revisões, XP e sequência, e exige a senha atual para confirmar.
4. **Dado** a confirmação com a senha correta, **quando** a exclusão termina, **então** todos os dados e arquivos da conta são apagados, todas as sessões são encerradas e o e-mail fica livre para um novo cadastro.

## Casos de borda

- E-mail com maiúsculas, espaços nas extremidades ou já cadastrado com outra caixa: tratado como o mesmo e-mail.
- Nome vazio, só com espaços ou acima de 100 caracteres.
- Senha com mais de 128 caracteres, ou só com espaços.
- Fuso inexistente na base de fusos (nome IANA inválido).
- Duas abas: sair numa aba invalida a sessão nas duas.
- Tentativas de entrada distribuídas entre muitas contas a partir do mesmo endereço de rede.
- Requisição com identificador de outro estudante em qualquer recurso, inclusive em listagens e filtros.
- Cadastro com um e-mail já existente: recusado com a mensagem de e-mail em uso (D-005); muitas tentativas de cadastro do mesmo endereço de rede são limitadas (RQ-003).
- Exclusão da conta com fontes em processamento ou geração em andamento: os processamentos são interrompidos, e nada da conta permanece.
- Exclusão da conta pedida duas vezes (duas abas): um único efeito.

## Requisitos funcionais

- **RF-001:** O sistema deverá cadastrar estudantes com nome (1 a 100 caracteres, sem espaços nas extremidades), e-mail válido (até 254 caracteres, único sem diferenciar maiúsculas e minúsculas) e senha (deriva de RF-01 da base).
- **RF-002:** O sistema deverá aceitar senhas de 8 a 128 caracteres, recusar as que constam numa lista local de senhas comuns ou vazadas e não impor regras de composição (D-002).
- **RF-003:** Toda conta criada pelo cadastro público deverá ter o papel estudante. Nenhuma requisição do próprio usuário altera o papel (deriva de RN-27 da base).
- **RF-004:** O sistema deverá autenticar por e-mail e senha e responder com a mesma mensagem para e-mail inexistente e senha errada.
- **RF-005:** O sistema deverá limitar as tentativas de entrada malsucedidas por conta e por endereço de rede (RQ-003).
- **RF-006:** A saída deverá invalidar a sessão no servidor. A sessão também deverá expirar após 14 dias sem uso e, em qualquer caso, 30 dias após a entrada.
- **RF-007:** Toda operação sobre um recurso de estudante deverá verificar que o recurso pertence ao estudante autenticado. Um recurso de outro estudante é tratado como inexistente (deriva de RN-01 e RF-02 da base).
- **RF-008:** O estudante deverá conseguir consultar e alterar nome, fuso, meta diária, tamanho da lição, limite de novos cartões por dia e retenção desejada, dentro dos limites de D-001 (deriva de RF-19 da base).
- **RF-009:** No cadastro, o sistema deverá usar o fuso detectado no navegador quando ele for um nome IANA válido; caso contrário, `America/Sao_Paulo` (deriva de RN-15 da base).
- **RF-010:** A alteração da retenção desejada deverá criar uma nova versão dos parâmetros de agendamento, sem alterar as versões anteriores (deriva de RN-26 e CB-29 da base).
- **RF-011:** Requisições que alteram dados deverão exigir proteção contra falsificação de requisição entre sites.
- **RF-012:** No cadastro, o sistema deverá verificar se o e-mail já está em uso e, nesse caso, recusar o cadastro informando que o e-mail já está em uso (D-005).
- **RF-013:** A tela de cadastro deverá exibir um aviso curto de privacidade, sem caixa de aceite (D-007).
- **RF-014:** O estudante deverá conseguir trocar a senha informando a senha atual. A troca deverá encerrar todas as outras sessões da conta (D-004).
- **RF-015:** O estudante deverá conseguir excluir a própria conta, confirmando com a senha atual. A exclusão deverá apagar definitivamente todos os dados e arquivos da conta e encerrar todas as sessões (D-003). É a única situação em que revisões, XP e sequência são removidos (exceção a RN-14 e RN-18 da base).

## Entidades principais

- **Estudante (conta):** nome, e-mail, papel, fuso, preferências de ritmo, data de criação.
- **Sessão:** vínculo entre um navegador e uma conta, com início, último uso, expiração e revogação.
- **Parâmetros de agendamento:** versão imutável dos parâmetros do algoritmo de repetição espaçada do estudante, incluindo a retenção desejada.

## Critérios de sucesso

- **CS-001:** Em teste guiado com três pessoas, cada uma cria a conta e chega à trilha em até 2 minutos, sem ajuda.
- **CS-002:** Em 100% das operações expostas pela API, o teste com duas contas confirma que a conta B não lê, altera nem descobre recursos da conta A.
- **CS-003:** Nenhuma resposta de entrada ou de erro permite distinguir um e-mail cadastrado de um não cadastrado, exceto a recusa do cadastro por e-mail em uso, decidida em D-005.
- **CS-004:** Depois da exclusão de uma conta fictícia, nenhum registro nem arquivo ligado a ela é encontrado no banco ou no armazenamento.

## Requisitos de qualidade

- **RQ-001:** A senha nunca é armazenada nem registrada em texto legível, e a credencial da sessão não fica acessível a scripts da página.
- **RQ-002:** Logs não registram senha, credencial de sessão nem o corpo das requisições de cadastro e de entrada.
- **RQ-003:** Bloqueio temporário de 15 minutos após 5 falhas de entrada por conta em 15 minutos, e após 20 falhas por endereço de rede em 15 minutos; no máximo 10 tentativas de cadastro por endereço de rede por hora. Valores configuráveis por ambiente.
- **RQ-004:** Cadastro, entrada e perfil atendem WCAG 2.2 AA, operam por teclado e funcionam a partir de 320 px (RQ-06 da base).
- **RQ-005:** Os contratos de cadastro, entrada, saída e perfil estão documentados em OpenAPI, inclusive os erros (RQ-08 da base).

## Suposições e dependências

- **Suposição:** os limites de nome e o limite de tentativas de cadastro são propostos pelo agente, configuráveis por ambiente, e confirmados na revisão da spec.
- **Suposição:** frontend e API ficam na mesma origem ([arquitetura](../../arquitetura/README.md#52-autenticação-e-sessão)).
- **Dependência:** nenhuma funcionalidade anterior. Todas as outras specs dependem desta.

## Esclarecimentos

### Sessão de 12/10/2026 ([registro](../../prompts/2026-10-12-esclarecimento-specs-mvp.md))

- **E1:** O MVP permite excluir a própria conta? → Sim, com confirmação pela senha e apagamento definitivo (D-003).
- **E2:** O MVP permite alterar a senha com a sessão aberta? → Sim, informando a atual e encerrando as outras sessões (D-004).
- **E3:** Como o cadastro trata um e-mail já cadastrado? → Verifica no banco e informa que o e-mail está em uso; sem confirmação de conta por e-mail nem recuperação de senha no MVP (D-005). O estágio da confirmação por e-mail fica em [QA-33](../../produto/pendencias.md#qa-33-confirmação-de-e-mail-no-cadastro).
- **E4:** Qual a duração da sessão? → 14 dias sem uso e, no máximo, 30 dias após a entrada, sem "manter conectado" (D-006).
- **E5:** O cadastro exibe um aviso de privacidade? → Sim, um texto curto, sem caixa de aceite (D-007).

## Questões abertas

- **Q-001:** ~~Excluir a própria conta no MVP?~~ Resolvida em 12/10/2026 (D-003).
- **Q-002:** ~~Alterar a senha com a sessão aberta no MVP?~~ Resolvida em 12/10/2026 (D-004).
- **Q-003:** ~~Cadastro sem envio de e-mail não pode ser neutro.~~ Resolvida em 12/10/2026 (D-005).

Nenhuma questão aberta impede o planejamento.

## Decisões confirmadas

- **D-001:** Preferências padrão e limites: meta diária de 20 cartões distintos (de 1 a 200); lição de 10 cartões distintos (de 5 a 50); 20 cartões novos por dia, num limite global e não por matéria (de 0 a 100); retenção desejada de 0,90 (de 0,70 a 0,97). Os valores ficam numa configuração versionada (QA-24 e QA-23). — **Confirmada por:** Artur Lins (equipe) — **Data:** 12/10/2026
- **D-002:** Política de senha: de 8 a 128 caracteres, com recusa de senhas comuns ou vazadas e sem regras de composição; limite de tentativas; mensagem de erro de entrada neutra. — **Confirmada por:** Artur Lins (equipe) — **Data:** 12/10/2026
- **D-003:** O estudante pode excluir a própria conta no MVP, confirmando com a senha atual; a exclusão apaga definitivamente todos os dados e arquivos da conta. — **Confirmada por:** Artur Lins (equipe), esclarecimento E1 — **Data:** 12/10/2026
- **D-004:** O estudante pode alterar a senha com a sessão aberta, informando a atual; a troca encerra as outras sessões. — **Confirmada por:** Artur Lins (equipe), esclarecimento E2 — **Data:** 12/10/2026
- **D-005:** No MVP, o cadastro verifica no banco se o e-mail já está em uso e, nesse caso, informa o estudante. Não há confirmação de conta por e-mail nem recuperação de senha no MVP. O estágio da confirmação por e-mail será decidido pela equipe ([QA-33](../../produto/pendencias.md#qa-33-confirmação-de-e-mail-no-cadastro)). — **Confirmada por:** Artur Lins (equipe), esclarecimento E3 — **Data:** 12/10/2026
- **D-006:** A sessão expira após 14 dias sem uso e, em qualquer caso, 30 dias após a entrada, sem opção "manter conectado"; valores configuráveis por ambiente. — **Confirmada por:** Artur Lins (equipe), esclarecimento E4 — **Data:** 12/10/2026
- **D-007:** O cadastro exibe um aviso curto de privacidade, sem caixa de aceite: quais dados a plataforma guarda e que trechos das fontes vão a um provedor de IA externo quando o estudante pede cartões. — **Confirmada por:** Artur Lins (equipe), esclarecimento E5 — **Data:** 12/10/2026

## Exigências do PO

Nenhuma exigência (EX-01 a EX-05) toca esta funcionalidade.

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | Não se aplica: não há conteúdo gerado |
| II Proteção e isolamento | US2, US4, RF-007, RQ-001 a RQ-003; aviso de privacidade (RF-013) |
| III Verificação humana | Decisões do esclarecimento registradas pela equipe (D-003 a D-007); exclusão da conta com confirmação explícita (US4) |
| IV Servidor autoritativo | Sessão e preferências validadas e guardadas no servidor; datas em UTC com o fuso do estudante |
| V Qualidade verificável | Cenários Dado/Quando/Então, RQ-004 e RQ-005 |
| VI Entrega incremental | US1 pode ser demonstrada sozinha; a US4 amplia |
| VII Rastreabilidade | IDs da base citados; sessão registrada |
