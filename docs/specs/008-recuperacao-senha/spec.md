# Especificação: recuperação de senha por e-mail

**Identificador:** 008-recuperacao-senha
**Estágio:** Final acadêmico
**Funcionalidade do backlog:** [F-01](../../produto/backlog.md#funcionalidades-candidatas), incremento do final acadêmico (a parte do MVP está em [001-conta-acesso](../001-conta-acesso/spec.md))
**Criada em:** 12/10/2026
**Status:** Rascunho
**Origem:** backlog ("recuperação de senha no Final"), [base de especificação](../../base-specs/spec.md) (RF-01), [DTEC 003](../../research.md#decisão-dtec-003-autenticação) e [sessão de 12/10/2026](../../prompts/2026-10-12-specs-funcionalidades.md)

## Problema e resultado esperado

**Usuário prioritário:** estudante que esqueceu a senha.
**Situação:** o estudante volta à plataforma depois de alguns dias e não lembra a senha.
**Problema observável:** sem recuperação, ele perde o acesso a todo o histórico de estudo.
**Resultado esperado:** o estudante pede a recuperação, recebe por e-mail um link de uso único e define uma nova senha, sem que a plataforma revele se um e-mail tem conta.
**Alternativa atual:** no MVP, nenhuma: a conta fica inacessível.

## Escopo

### Incluído

- Pedido de recuperação pelo e-mail, com resposta neutra.
- Envio de um link de uso único e com validade curta.
- Definição de nova senha com a política de [001](../001-conta-acesso/spec.md) (D-002).
- Encerramento de todas as sessões da conta depois da troca.
- Aviso por e-mail de que a senha foi alterada.

### Fora do escopo

- Recuperação por SMS, perguntas secretas ou atendimento humano.
- Verificação de e-mail no cadastro: estágio em discussão em [QA-33](../../produto/pendencias.md#qa-33-confirmação-de-e-mail-no-cadastro).
- Troca de e-mail.

## Cenários de usuário e testes

### História de usuário 1 Redefinir a senha pelo e-mail P1

Como estudante, quero redefinir minha senha pelo e-mail, para recuperar o acesso aos meus estudos.

**Motivo da prioridade:** é a única história desta spec.
**Teste independente:** com um serviço de e-mail simulado, pedir a recuperação para uma conta fictícia, usar o link, definir nova senha, confirmar que a sessão antiga deixou de valer e que o link não funciona uma segunda vez; pedir para um e-mail inexistente e confirmar a mesma resposta, sem envio.

**Cenários de aceitação**

1. **Dado** qualquer e-mail, **quando** o estudante pede a recuperação, **então** a resposta é sempre a mesma: "Se houver uma conta com este e-mail, enviamos as instruções", em tempo semelhante, exista a conta ou não.
2. **Dado** uma conta existente, **quando** a recuperação é pedida, **então** um e-mail com um link de uso único, válido por 30 minutos, é enviado ao endereço da conta.
3. **Dado** um link válido, **quando** o estudante define uma nova senha que atende à política, **então** a senha é trocada, todas as sessões da conta são encerradas, o link deixa de valer, e um e-mail avisa da alteração.
4. **Dado** um link expirado, já usado ou adulterado, **quando** o estudante o abre, **então** vê que o link não é mais válido e pode pedir outro, sem dados da conta.
5. **Dado** vários pedidos para a mesma conta, **quando** um novo link é emitido, **então** os anteriores deixam de valer.

## Casos de borda

- Mais de 3 pedidos por conta em 1 hora, ou mais de 10 por endereço de rede em 1 hora: novos pedidos recebem a mesma resposta neutra, sem envio.
- Serviço de e-mail indisponível: a resposta ao estudante continua neutra, a falha é registrada para a operação e o envio é tentado de novo em segundo plano.
- Nova senha igual à atual: aceita, desde que atenda à política.
- Link aberto num navegador com outra conta conectada: a troca vale para a conta do link, e a sessão aberta é encerrada se for da mesma conta.
- Conta desativada pelo administrador ([016](../016-painel-administrativo/spec.md)): a resposta é neutra, e nenhum e-mail é enviado.

## Requisitos funcionais

- **RF-001:** O pedido de recuperação deverá ter sempre a mesma resposta e um tempo de resposta semelhante, exista ou não uma conta com o e-mail.
- **RF-002:** O link de recuperação deverá ser de uso único, válido por 30 minutos, e invalidar os links anteriores da mesma conta.
- **RF-003:** O sistema deverá guardar apenas um resumo irreversível do código do link, nunca o código em si.
- **RF-004:** A nova senha deverá seguir a política de [001](../001-conta-acesso/spec.md), RF-002.
- **RF-005:** A troca de senha deverá encerrar todas as sessões da conta e enviar um aviso ao e-mail da conta.
- **RF-006:** O sistema deverá limitar os pedidos por conta e por endereço de rede, mantendo a resposta neutra.

## Entidades principais

- **Pedido de recuperação:** conta, resumo do código, emissão, validade e uso.

## Critérios de sucesso

- **CS-001:** Em teste guiado com três pessoas, cada uma recupera a conta em até 3 minutos, contando a leitura do e-mail simulado.
- **CS-002:** Em 100% dos testes, a resposta ao pedido não permite distinguir um e-mail cadastrado de um não cadastrado (conteúdo e diferença de tempo inferior a 100 ms em média).

## Requisitos de qualidade

- **RQ-001:** O link e o código nunca aparecem em logs.
- **RQ-002:** O e-mail não contém dados de estudo do estudante, só o link e as instruções.
- **RQ-003:** As telas de pedido e de nova senha atendem WCAG 2.2 AA.
- **RQ-004:** O serviço de envio de e-mail é configurado por variáveis de ambiente, sem credenciais no repositório.

## Suposições e dependências

- **Dependência:** [001-conta-acesso](../001-conta-acesso/spec.md).
- **Dependência:** um serviço de envio de e-mail, a escolher no plano, com uma nova DTEC no [`research.md`](../../research.md) ([DTEC 003](../../research.md#decisão-dtec-003-autenticação), consequências).
- **Dependência:** domínio próprio para o remetente ([QA-11](../../produto/pendencias.md#qa-11-vps-e-operação-do-deploy)).
- **Suposição:** a validade de 30 minutos e os limites de pedidos são propostos pelo agente, configuráveis por ambiente.

## Questões abertas

- **Q-001:** O aviso de senha alterada deve trazer um caminho para o estudante informar que não foi ele? **Recomendação:** sim, com um link que encerra todas as sessões e inicia uma nova recuperação. — **Responsável:** equipe — **Prazo:** 31/10/2026
- **Q-002:** ~~Com o envio de e-mail disponível, o cadastro passa a exigir a confirmação do e-mail?~~ Movida em 12/10/2026 para [QA-33](../../produto/pendencias.md#qa-33-confirmação-de-e-mail-no-cadastro), que decide se a confirmação entra no final acadêmico ou na referência pós-acadêmica ([esclarecimento da 001](../001-conta-acesso/spec.md#esclarecimentos), E3).

## Decisões confirmadas

- **D-001:** A recuperação de senha por e-mail entra no final acadêmico. — **Confirmada por:** equipe, no [backlog](../../produto/backlog.md#final-acadêmico) — **Data:** 12/10/2026

## Exigências do PO

Nenhuma exigência (EX-01 a EX-05) toca esta funcionalidade.

## Verificação da constituição

| Princípio | Como a spec atende |
|---|---|
| I Fontes exclusivas | Não se aplica |
| II Proteção e isolamento | RF-001, RF-003, RQ-001, RQ-002, RQ-004 |
| III Verificação humana | Q-001 e Q-002 ficam com a equipe |
| IV Servidor autoritativo | Validade e uso único controlados no servidor |
| V Qualidade verificável | CS-001 e CS-002 |
| VI Entrega incremental | História única, sobre 001 |
| VII Rastreabilidade | Sessão registrada |
