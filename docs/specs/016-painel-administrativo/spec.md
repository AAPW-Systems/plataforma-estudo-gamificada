# Especificação: painel administrativo simples

**Identificador:** 016-painel-administrativo
**Estágio:** Final acadêmico
**Funcionalidade do backlog:** [F-17](../../produto/backlog.md#funcionalidades-candidatas)
**Criada em:** 12/10/2026
**Status:** Rascunho
**Origem:** backlog, [base de especificação](../../base-specs/spec.md) (HU-20, RF-29, RN-01, RN-27), [QA-32](../../produto/pendencias.md#qa-32-escopo-do-painel-administrativo), [PO-06](../../produto/pauta-po.md#po-06-painel-administrativo) (retirado da pauta em 12/10/2026) e [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** pessoa da equipe que opera a plataforma publicada (administrador).
**Situação:** com a plataforma na VPS, a equipe precisa saber se ela está sendo usada, se a IA está falhando ou perto do limite gratuito e se há fontes travadas.
**Problema observável:** sem um painel, a equipe só descobre problemas pelos logs do servidor ou quando um estudante reclama.
**Resultado esperado:** um administrador entra com a mesma conta e o mesmo login dos estudantes e vê indicadores agregados de uso, de consumo e falhas da IA e do processamento, e executa poucas ações operacionais, sem acesso ao conteúdo dos estudantes.
**Alternativa atual:** consultas diretas ao banco e leitura de logs no servidor.

## Escopo

### Incluído

As capacidades abaixo são a **proposta da equipe** para QA-32, a confirmar na revisão desta spec (Q-002 e Q-003):

- Acesso restrito ao papel administrador (RN-27).
- Concessão do papel por comando executado no servidor, nunca por uma rota da aplicação.
- Indicadores agregados: estudantes cadastrados e ativos, matérias, fontes, cartões, revisões e gerações, por período.
- Consumo e falhas dos provedores de IA: chamadas, tokens, falhas por tipo e consumo do dia em relação ao limite configurado.
- Estado do processamento em segundo plano: fontes e gerações pendentes, em processamento e com falha.
- Ações: desativar e reativar uma conta de estudante; pedir nova tentativa de uma fonte ou geração com falha técnica.
- Registro de auditoria das ações administrativas.

### Fora do escopo

- Ver o conteúdo de fontes, trechos, cartões, conversas ou perguntas de qualquer estudante.
- Entrar na conta de um estudante ("acessar como").
- Editar dados ou progresso de estudantes, conceder XP ou alterar sequência.
- Criar administradores pela interface.
- Painel administrativo completo (fora dos estágios acadêmicos).

## Cenários de usuário e testes

### História de usuário 1 Acompanhar o uso e a saúde da plataforma P1

Como administrador, quero ver indicadores agregados de uso, de IA e de processamento, para operar a plataforma publicada (HU-20).

**Motivo da prioridade:** é o motivo do painel e não altera dados.
**Teste independente:** com dados fictícios de 3 estudantes e consumo simulado da IA, entrar como administrador, conferir os indicadores com os calculados à mão e confirmar que nenhum conteúdo de estudante aparece; entrar como estudante e confirmar que o painel não existe para ele.

**Cenários de aceitação**

1. **Dado** uma conta com papel administrador, **quando** ela entra, **então** tem acesso ao painel, além das áreas de estudante (Q-002).
2. **Dado** uma conta com papel estudante, **quando** ela tenta acessar o painel ou qualquer operação administrativa, **então** recebe a mesma resposta de um recurso inexistente.
3. **Dado** o painel aberto, **quando** o administrador escolhe um período, **então** vê os indicadores de uso, de IA e de processamento desse período, todos agregados.
4. **Dado** fontes e gerações com falha, **quando** o administrador abre o processamento, **então** vê a quantidade e o tipo de falha de cada uma, sem o título, o nome do arquivo ou o conteúdo.

### História de usuário 2 Executar ações operacionais P2

Como administrador, quero desativar uma conta abusiva e tentar de novo um processamento com falha técnica, para manter a plataforma funcionando.

**Motivo da prioridade:** ações raras; a US1 já entrega a visibilidade.
**Teste independente:** desativar uma conta fictícia e confirmar que as sessões dela foram encerradas e que ela não entra mais; pedir nova tentativa de uma fonte com falha técnica e confirmar o reprocessamento; conferir o registro de auditoria das duas ações.

**Cenários de aceitação**

1. **Dado** uma conta de estudante, **quando** o administrador a desativa e confirma, **então** todas as sessões dela são encerradas, ela não consegue mais entrar, e seus dados são preservados.
2. **Dado** uma conta desativada, **quando** o administrador a reativa, **então** ela volta a entrar, com todos os dados.
3. **Dado** uma fonte ou geração com falha técnica, **quando** o administrador pede nova tentativa, **então** o processamento recomeça com as mesmas garantias de não duplicação, sem que o administrador veja o conteúdo.
4. **Dado** qualquer ação administrativa, **quando** ela é executada, **então** fica registrada com o administrador, a ação, o alvo e o instante.

## Casos de borda

- Administrador tenta desativar a própria conta ou a de outro administrador: recusado.
- Conta desativada tenta recuperar a senha: resposta neutra, sem envio ([008](../008-recuperacao-senha/spec.md)).
- Período sem dados: indicadores em zero, com o período indicado.
- Grupos muito pequenos (por exemplo, um único estudante ativo no período): os indicadores continuam agregados, sem identificar a pessoa.

## Requisitos funcionais

- **RF-001:** O painel e todas as operações administrativas deverão estar disponíveis somente a contas com papel administrador; para as demais, deverão se comportar como inexistentes (deriva de RN-27 e RF-29 da base).
- **RF-002:** O papel de administrador só deverá ser concedido por um comando executado no servidor (deriva de RN-27 da base).
- **RF-003:** O painel deverá exibir apenas dados agregados de uso, de consumo e falhas da IA e do processamento, nunca o conteúdo de fontes, trechos, cartões, conversas ou perguntas, nem o título e o nome dos arquivos (deriva de RN-01 e RN-27 da base).
- **RF-004:** O administrador deverá conseguir desativar e reativar contas de estudante. A desativação encerra todas as sessões da conta e preserva os dados.
- **RF-005:** O administrador deverá conseguir pedir nova tentativa de uma fonte ou geração com falha técnica, sem acesso ao conteúdo.
- **RF-006:** Toda ação administrativa deverá ser registrada com o administrador, a ação, o alvo e o instante, num registro que não pode ser alterado pela interface.

## Entidades principais

- **Conta:** passa a ter a situação ativa ou desativada.
- **Registro de auditoria:** administrador, ação, alvo e instante.
- **Consumo dos provedores:** registros de cada chamada, já existentes ([004](../004-geracao-cartoes/spec.md)).

## Critérios de sucesso

- **CS-001:** Em 100% das operações administrativas, uma conta com papel estudante recebe a resposta de recurso inexistente.
- **CS-002:** Em revisão das respostas do painel, nenhum campo contém conteúdo, título ou nome de arquivo de um estudante.
- **CS-003:** Para os dados fictícios, todos os indicadores coincidem com os calculados à mão.

## Requisitos de qualidade

- **RQ-001:** O painel atende WCAG 2.2 AA e funciona a partir de 320 px.
- **RQ-002:** As ações destrutivas ou de impacto exigem confirmação explícita (Princípio III).
- **RQ-003:** Os indicadores de consumo usam os mesmos limites configurados no servidor.

## Suposições e dependências

- **Dependência:** [001-conta-acesso](../001-conta-acesso/spec.md) (papel e sessão), [002-materias-fontes](../002-materias-fontes/spec.md) e [004-geracao-cartoes](../004-geracao-cartoes/spec.md) (processamento, geração e consumo).
- **Dependência:** resposta da equipe em [QA-32](../../produto/pendencias.md#qa-32-escopo-do-painel-administrativo).

## Questões abertas

- **Q-001:** ~~O PO espera o painel no final acadêmico?~~ **Removida em 12/10/2026:** o item saiu da pauta com o PO ([PO-06](../../produto/pauta-po.md#po-06-painel-administrativo)) e foi resolvido pela equipe (D-002).
- **Q-002:** Um administrador também estuda com a mesma conta, ou a conta de administrador é só operacional? **Recomendação:** também estuda, porque a [RN-27](../../base-specs/spec.md#rn-27-papéis) usa o mesmo login e a equipe também usa o produto; o isolamento do conteúdo continua valendo. — **Responsável:** equipe — **Prazo:** 31/10/2026
- **Q-003:** O painel pode listar estudantes individualmente (e-mail, data de cadastro, última atividade), para viabilizar a desativação, ou só agregados? **Recomendação:** listar só e-mail, data de cadastro, última atividade e situação, sem dados de estudo, com a busca por e-mail. — **Responsável:** equipe — **Prazo:** 31/10/2026

## Decisões confirmadas

- **D-001:** Estudantes e administradores usam a mesma conta e o mesmo login, distinguidos pelo papel; o cadastro público cria só estudantes; o MVP não tem funcionalidade de administrador (RN-27 da base). — **Confirmada por:** Artur Lins (equipe), [registro](../../prompts/2026-10-12-esquema-inicial-banco.md) — **Data:** 12/10/2026
- **D-002:** O painel administrativo simples entra no final acadêmico como decisão da equipe, sem depender do PO ([PO-06](../../produto/pauta-po.md#po-06-painel-administrativo), retirado da pauta). — **Confirmada por:** Artur Lins (equipe), [registro](../../prompts/2026-10-12-specs-funcionalidades.md) — **Data:** 12/10/2026

## Exigências do PO

Nenhuma exigência (EX-01 a EX-05) toca esta funcionalidade.

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | Não se aplica |
| II Proteção e isolamento | RF-001 a RF-003; CS-001 e CS-002; o papel não suspende o isolamento |
| III Verificação humana | Escopo decidido pela equipe (D-002, Q-002, Q-003); confirmação nas ações (RQ-002) |
| IV Servidor autoritativo | Autorização e indicadores no servidor |
| V Qualidade verificável | CS-001 a CS-003 |
| VI Entrega incremental | US1 sem alteração de dados; a US2 amplia |
| VII Rastreabilidade | Auditoria (RF-006); IDs da base citados; sessão registrada |
