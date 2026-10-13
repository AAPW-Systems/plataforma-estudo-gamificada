# Pesquisa e decisões técnicas

**Funcionalidade:** 006-xp-meta-sequencia (XP, meta diária e sequência)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-006-xp-meta-sequencia-plano.md))  
**Status:** DTEC 058 a 063 propostas em 13/10/2026; aprovação com o plano

Este arquivo registra só as dúvidas técnicas **novas** da spec 006. As decisões já tomadas não são reabertas:

- de [`../../research.md`](../../research.md): camadas (DTEC 018), participantes da exclusão (DTEC 027) e dia de estudo num único ponto (DTEC 048);
- da [spec 001](../001-conta-acesso/research.md): isolamento (DTEC 019) e exclusão da conta (DTEC 021);
- da [spec 005](../005-licao-trilha/research.md): elegibilidade (DTEC 051), avaliação idempotente (DTEC 052), dominado e evento `RevisaoRegistrada` (DTEC 055) e trilha (DTEC 056).

Vale também a DTEC transversal proposta neste planejamento: disponibilidade de cartões e ganchos de alteração no núcleo ([DTEC 057](../../research.md#decisão-dtec-057-disponibilidade-de-cartões-e-ganchos-de-alteração-no-núcleo)). A numeração das DTEC é única no projeto.

| Decisão | Título |
|---|---|
| [DTEC 058](#decisão-dtec-058-regra-de-valores-versionada) | Regra de valores versionada |
| [DTEC 059](#decisão-dtec-059-concessão-de-xp-idempotente-e-cache-do-total) | Concessão de XP idempotente e cache do total |
| [DTEC 060](#decisão-dtec-060-meta-efetiva-e-dia-estudado-sob-concorrência) | Meta efetiva e dia estudado sob concorrência |
| [DTEC 061](#decisão-dtec-061-liquidação-dos-dias-passados-dia-neutro-e-sequência) | Liquidação dos dias passados, dia neutro e sequência |
| [DTEC 062](#decisão-dtec-062-mudança-de-fuso-e-horário-de-verão) | Mudança de fuso e horário de verão |
| [DTEC 063](#decisão-dtec-063-exibição-contrato-aditivo-e-anúncio-acessível) | Exibição, contrato aditivo e anúncio acessível |

## Decisão DTEC 058 Regra de valores versionada

**Questão:** onde guardar os valores de XP (10 pela primeira revisão do cartão no dia e 25 pelo cartão dominado, D-001) e como relacioná-los com o limiar de dominado da 005 (`LIMIAR_DOMINADO_DIAS = 21` e `VERSAO_REGRAS` em `revisao/regras.py`, DTEC 055), de modo que mudar valores não altere o XP já concedido (RQ-004) e que nenhuma regra seja duplicada?  
**Critérios:** cada evento de XP rastreável até os valores e o limiar que o produziram; uma regra em um só lugar; mudança só por diff revisado; versão já usada imutável.  
**Alternativas consideradas:**

1. **Histórico imutável de valores em `gamificacao/regras.py`, com o limiar só em `revisao/regras.py`.** O evento de XP grava a versão dos valores, e a revisão de origem já grava a versão do limiar. As duas ficam ligadas por `revisao_id`.
2. **Uma única regra versionada no núcleo, com limiar e valores juntos:** exige emendar a DTEC 055 e mover o limiar para fora do domínio que o aplica. Uma mudança só de XP criaria uma versão nova também para o dominado.
3. **Tabela de regras no banco:** permite mudança sem diff revisado, que a DTEC 055 já rejeitou para o limiar.

**Decisão:** alternativa 1.  
**Justificativa:** cada regra fica no domínio que a aplica, e a "regra de valores" da spec (entidade com a versão dos valores de XP e do limiar) fica completa pelo par de versões, sem copiar nenhum número.  
**Consequências:**

- **`gamificacao/regras.py`:** `RegraXp(versao, xp_revisao, xp_dominado)`, um dicionário `PUBLICADAS = {1: RegraXp(1, 10, 25)}` e `VIGENTE = PUBLICADAS[1]`. Mudar um valor exige uma versão nova; as anteriores ficam no dicionário.
- **`eventos_xp.versao_regra`:** `smallint`, como `revisoes.versao_regras` (o `.dbml` trazia `varchar(20)`).
- **Teste de referência:** um teste fixa os valores de cada versão publicada da `RegraXp` e o par `(VERSAO_REGRAS, LIMIAR_DOMINADO_DIAS)` da 005. Alterar um número sem criar uma versão nova faz o teste falhar.
- **Auditoria:** `eventos_xp.versao_regra` com `revisoes.versao_regras` da revisão de origem respondem "com quais valores e com qual limiar este XP foi concedido".

**Condição para revisão:** valores por estudante ou por matéria, que exigiriam a regra no banco.

## Decisão DTEC 059 Concessão de XP idempotente e cache do total

**Questão:** como conceder o XP (RF-001 a RF-003) na mesma transação da revisão (RQ-002), sem duplicidade sob reenvio e concorrência (CS-001, CB-24), com o mesmo resultado para um cartão errado várias vezes e para um acertado uma vez (CS-003), e manter `usuarios.xp_total` igual à soma dos eventos?  
**Critérios:** um evento por fato; duplicidade impossível pelo banco; nenhuma divergência silenciosa; leitura do total sem agregação.  
**Alternativas consideradas:**

1. **Ouvinte de `RevisaoRegistrada` com `INSERT` simples, índice único `(revisao_id, tipo)` e cache incrementado na mesma transação.**
2. **`INSERT ... ON CONFLICT DO NOTHING`:** esconderia um defeito, como o ouvinte chamado duas vezes, e o cache poderia divergir.
3. **Sem cache, com `sum` a cada leitura:** a trilha e cada avaliação agregariam todo o histórico.

**Decisão:** alternativa 1.  
**Justificativa:** a 005 já garante um fato por revisão. O reenvio com a mesma chave devolve a revisão existente sem publicar o evento (DTEC 052), `primeira_do_dia` é única por cartão e dia (índice parcial) e `tornou_dominado` acontece uma vez por cartão (`dominado_em`). O banco repete a garantia, e uma violação desfaz a revisão inteira, em vez de passar despercebida.  
**Consequências:**

- **Eventos:** com `primeira_do_dia`, um evento `revisao` com `xp_revisao`; com `tornou_dominado`, um evento `cartao_dominado` com `xp_dominado`. Os dois são independentes, e uma revisão pode gerar os dois. A nota não entra no cálculo (RN-18, CS-003).
- **Campos copiados do evento:** `dia_estudo` e `concedido_em` vêm da revisão (`dia_estudo` e `revisada_em`), e não de `now()`, o que mantém tudo reprodutível com o relógio controlado.
- **Índices e restrições:** único `(revisao_id, tipo)`, que substitui o `(cartao_id, dia_estudo, tipo)` do `.dbml`; o antigo deixa de proteger quando `cartao_id` fica nulo e não expressa o bônus único por cartão. `CHECK (quantidade > 0)`.
- **FKs compostas:** `(revisao_id, usuario_id)` → `revisoes (id, usuario_id)`, com o índice único novo `revisoes_id_usuario`, e `(cartao_id, usuario_id)` → `cartoes (id, usuario_id)` `ON DELETE SET NULL (cartao_id)` (obrigação da 003). O XP sobrevive à exclusão do cartão (US1-5; US3-3 da 003).
- **Cache:** `UPDATE usuarios SET xp_total = xp_total + :soma` com a linha travada (DTEC 060), na mesma transação. `CHECK (xp_total >= 0)`.
- **Imutabilidade:** o repositório de eventos só insere e lê (teste de arquitetura), salvo `apagar_dados_usuario` (RF-003, DTEC 021).
- **Verificação do CS-001:** teste de propriedade (Hypothesis) com sequências aleatórias de avaliações, reenvios e abas concorrentes: `xp_total = sum(eventos_xp.quantidade)` e um evento `revisao` por cartão e dia.

**Condição para revisão:** XP que não nasça de revisão (ex.: conquistas), que exigiria `revisao_id` opcional e outra chave de idempotência.

## Decisão DTEC 060 Meta efetiva e dia estudado sob concorrência

**Questão:** como calcular a meta efetiva, que é o menor valor entre a meta diária e os revisados mais os restantes (RF-005), e marcar o dia como estudado uma única vez e de forma definitiva (RF-006)? Os cartões ficam disponíveis ao longo do dia, saem por suspensão ou exclusão, e duas abas podem avaliar ao mesmo tempo (CB-24).  
**Critérios:** decisão no servidor e na mesma transação da revisão (RQ-002); marcação que não se desfaz; a mesma regra de elegibilidade da lição.  
**Alternativas consideradas:**

1. **Linha do dia em `dias_estudo` atualizada a cada revisão e a cada alteração de disponibilidade, com a linha do estudante travada.** Os restantes vêm do provedor da DTEC 057.
2. **Calcular a meta só na leitura:** não grava o instante em que o dia foi cumprido, e uma meta reduzida depois, ou uma suspensão, poderia "descumprir" o dia.
3. **Meta efetiva fixada na primeira revisão do dia:** contraria o caso de borda dos cartões criados ou aceitos no meio do dia, que aumentam a meta efetiva.

**Decisão:** alternativa 1.  
**Justificativa:** a marcação acontece no exato momento em que a condição é satisfeita, dentro da transação que a satisfez, e a situação `estudado` nunca volta atrás.  
**Consequências:**

- **Trava:** toda escrita da gamificação começa com `SELECT ... FOR NO KEY UPDATE` na linha do estudante em `usuarios`. Isso serializa revisões, alterações de disponibilidade e mudanças de preferência do mesmo estudante. As revisões já são serializadas pela trava da lição (DTEC 052); a trava de `usuarios` cobre os ganchos e o `PATCH /perfil`.
- **Revisados:** `cartoes_revisados` soma 1 só com `primeira_do_dia`; as reapresentações não contam (US2-4).
- **Meta efetiva:** `min(usuarios.meta_diaria, revisados + restantes_hoje)`, calculada a cada revisão e a cada `depois_de_alterar`, com cópia da meta diária, da meta efetiva e do fuso na linha do dia.
- **Marcação:** a linha `pendente` passa a `estudado` quando `revisados >= 1` e `revisados >= meta_efetiva`. Grava `meta_cumprida_em` com o instante da revisão ou da alteração e atualiza a sequência (DTEC 061). Nenhuma escrita tira uma linha de `estudado` (`CHECK`: `estudado` se e somente se `meta_cumprida_em` presente).
- **Casos de borda:**
  - cartões aceitos ou criados no meio do dia aumentam os restantes na próxima avaliação;
  - uma suspensão, exclusão ou meta reduzida que complete a meta marca o dia no `depois_de_alterar`, sem esperar nova revisão;
  - depois da meta, as lições extras continuam somando revisados, e o dia continua `estudado`.
- **Leitura:** a trilha recalcula a meta efetiva com os restantes de agora, sem gravar. A resposta da avaliação usa a linha recém-gravada.

**Condição para revisão:** meta por matéria (012), que exigiria a linha do dia por matéria.

## Decisão DTEC 061 Liquidação dos dias passados, dia neutro e sequência

**Questão:** um dia sem revisões é neutro quando nenhum cartão estava disponível na virada (RF-007, CB-13), e a sequência e o recorde (RF-008) precisam estar certos mesmo que o estudante passe dias sem abrir a aplicação. Como classificar os dias passados sem tarefa periódica por estudante e sem brechas, como suspender hoje o cartão de ontem para salvar a sequência?  
**Critérios:**

- resultado exato e reprodutível com relógio controlado (CS-002);
- leitura sem efeito colateral;
- nenhuma ação do estudante altera a classificação de um dia passado;
- nenhum serviço residente novo (restrição de custo da constituição).

**Alternativas consideradas:**

1. **Liquidação preguiçosa exata.** Os dias passados são classificados na próxima escrita da gamificação: revisão, ou um dos ganchos da DTEC 057, que rodam antes de qualquer ação que altere a disponibilidade. As leituras fazem o mesmo cálculo em memória, sem gravar.
2. **Tarefa periódica que registra a disponibilidade na virada:** no MVP local a máquina fica desligada, os dias ficariam sem registro e a reconstrução seria necessária de qualquer forma.
3. **Reconstrução só pelo estado atual, sem ganchos:** é inexata. Suspender ou excluir hoje o cartão devido ontem conserta uma sequência quebrada, reativar um cartão quebra uma sequência injustamente, e uma retirada que completa a meta sem nova revisão não marca o dia.

**Decisão:** alternativa 1.  
**Justificativa:** a disponibilidade muda só por duas causas, o tempo e as ações do estudante. A passagem do tempo é determinística a partir de `vencimento` e `entrada_estudo_em`. Toda ação que retira disponibilidade, ou que devolve um cartão com vencimento antigo (reativação), passa pelo gancho `antes_de_alterar`, que liquida os dias passados com o estado ainda intacto. Entre duas liquidações nada muda além do tempo, e uma única consulta reconstrói os dias do intervalo com exatidão.  
**Consequências:**

- **Leitura literal de "disponível na virada" (decidida na sessão):** a disponibilidade de um dia sem revisões é avaliada na virada que o encerra. Exemplos: um cartão criado às 23h e não estudado deixa o dia não neutro; o único cartão devido, suspenso às 10h, deixa o dia neutro.
- **Estado do estudante em `usuarios`:**
  - `sequencia_atual`: a sequência vigente na última liquidação;
  - `sequencia_recorde`;
  - `ultimo_dia_estudado`;
  - `dias_liquidados_ate`: o último dia de estudo já classificado; nulo antes da primeira liquidação, quando o intervalo começa no dia de estudo de `criado_em`.
- **Invariante:** toda escrita da gamificação liquida antes de mudar o dia corrente. Assim, se existe uma linha `pendente` no dia X, então `dias_liquidados_ate >= X − 1`, e os dias depois de X não tiveram revisão nem ação que alterasse a disponibilidade.
- **Algoritmo** (função pura `liquidar` em `gamificacao/dominio.py`), para o intervalo `[dias_liquidados_ate + 1, hoje − 1]`:
  1. uma linha `pendente` no intervalo vira `nao_estudado`. Ela não atingiu a meta efetiva até a virada, e qualquer retirada posterior teria passado pelo `depois_de_alterar`;
  2. linhas já liquidadas (como as datas puladas da DTEC 062) ficam como estão;
  3. as datas sem linha são classificadas pelo `primeiro_instante_disponivel` do provedor: as anteriores ao dia de estudo desse instante viram `neutro`, e as demais `nao_estudado`, porque a disponibilidade só cresce com o tempo enquanto nada muda;
  4. as datas novas são aplicadas em ordem à sequência: `nao_estudado` a zera, `neutro` não a altera, e uma linha `estudado` do intervalo já foi contada quando o dia foi cumprido;
  5. `dias_liquidados_ate = hoje − 1`.
- **Marcação do dia corrente (DTEC 060):** como a liquidação vem antes, `sequencia_atual` já reflete qualquer quebra. Cumprir o dia faz `sequencia_atual += 1`, `sequencia_recorde = max(recorde, atual)` e `ultimo_dia_estudado = hoje`.
- **Datas materializadas:** cada data liquidada vira uma linha de `dias_estudo` com a situação (`estudado`, `nao_estudado` ou `neutro`). É a base do calendário da 007 e da conferência do CS-002. Uma ausência de meses gera algumas centenas de linhas pequenas, numa única inserção.
- **Leitura (`GET /trilha`):** aplica o mesmo `liquidar` em memória e exibe 0 se houver quebra não gravada. Hoje ainda não cumprido aparece como "hoje falta", e a sequência exibida é a do último dia estudado (US3-5).
- **Verificação do CS-002:** testes de propriedade (Hypothesis) comparam `liquidar` mais a marcação, aplicados a sequências aleatórias de dias (com ou sem revisões, disponibilidade, suspensões e mudanças de meta), com um oráculo que simula dia a dia de forma ingênua.

**Condição para revisão:** congelamento da sequência (incremento posterior de F-10), que acrescentaria uma situação ao dia, ou um volume de estudantes que torne relevante liquidar ausências longas fora da requisição.

## Decisão DTEC 062 Mudança de fuso e horário de verão

**Questão:** como aplicar o D-003 (cada revisão pertence ao dia de estudo do seu instante no fuso vigente; datas puladas são neutras; datas repetidas contam uma vez) e garantir a virada das 4h no horário de verão (RF-009, CS-002)?  
**Critérios:** o mesmo dia de estudo da lição (DTEC 048); nenhuma data passada reclassificada; casos testáveis com fusos reais.  
**Alternativas consideradas:**

1. **"Data pulada" é a que nunca foi o dia corrente; o gancho da mudança de fuso a grava como `neutro`. A data vivida em parte segue a regra normal, e a data repetida reaproveita a mesma linha.**
2. **Considerar neutra também a data vivida em parte:** é mais leniente, mas permitiria salvar um dia não estudado trocando o fuso no fim dele.
3. **Guardar o histórico de fusos numa tabela:** só seria necessário para reclassificar o passado, o que a liquidação já evita.

**Decisão:** alternativa 1.  
**Justificativa:** segue o texto do D-003, sem abrir brecha, e reaproveita a liquidação da DTEC 061.  
**Consequências:**

- **Mudança de fuso no `PATCH /perfil`:**
  - `antes_de_alterar` liquida com o fuso anterior;
  - `depois_de_alterar`, com `fuso_anterior`, calcula `dia_antes = dia_estudo(agora, fuso_anterior)` e `dia_depois = dia_estudo(agora, fuso_novo)`;
  - se `dia_depois > dia_antes + 1`, as datas entre os dois ficam como `neutro` com `data_pulada`. Só um salto de mais de 24 h entre os fusos produz isso;
  - em seguida liquida no fuso novo: a data `dia_antes`, já passada, segue a regra normal.
- **Data repetida (mudança para oeste):** a revisão grava o dia pelo fuso vigente (DTEC 048) e cai na linha existente da data. Uma linha já liquidada nunca muda de situação: a revisão continua registrada em `revisoes`, mas não altera a contagem nem a situação de uma data `nao_estudado` ou `neutro`. Uma linha `estudado` continua somando revisados. Uma linha `pendente` volta a ser o dia corrente.
- **Horário de verão:** é tratado só por `nucleo/dia_estudo.py` (DTEC 048). A 006 não faz aritmética de horas. Os dias são datas, e a sequência compara datas consecutivas, de modo que dias de 23 h ou 25 h contam um só.
- **Testes:** `America/Sao_Paulo` num ano com horário de verão, `America/Santiago`, mudança de `America/Sao_Paulo` para `Asia/Tokyo` (vivida em parte) e de `Pacific/Pago_Pago` para `Pacific/Kiritimati` (data pulada), e o caminho inverso (data repetida).

**Condição para revisão:** virada configurável por estudante (condição da DTEC 048).

## Decisão DTEC 063 Exibição, contrato aditivo e anúncio acessível

**Questão:** como expor XP, meta e sequência na trilha e no fechamento (RF-010), e o ganho de cada revisão para o anúncio discreto (RQ-003), sem exibir nada antes da resposta do servidor (RQ-001) e sem quebrar o contrato da 005?  
**Critérios:** sem ida e volta extra na transição de cartão (CS-004 da 005); campos aditivos (obrigação da 005); anúncio sem som e com respeito a `prefers-reduced-motion`.  
**Alternativas consideradas:**

1. **Esquema `ResumoGamificacao` como campo aditivo das respostas da 005.** O contrato da 006 redefine os caminhos afetados como superconjunto do contrato da 005.
2. **Rota própria `GET /gamificacao`:** custa uma ida e volta a mais e contraria a obrigação registrada no plano da 005.
3. **O cliente soma o XP localmente:** viola o RQ-001 e o Princípio IV.

**Decisão:** alternativa 1.  
**Justificativa:** a interface recebe na mesma resposta o cartão seguinte e o efeito da revisão, e o teste de contrato (o OpenAPI gerado contém o de cada spec) continua valendo para a 005 e para a 006.  
**Consequências:**

- **`ResumoGamificacao`:**
  - `xpTotal` e `diaEstudo`;
  - `meta`: `revisados`, `metaDiaria`, `metaEfetiva`, `cumprida` e `cumpridaEm`;
  - `sequencia`: `atual`, `recorde` e `hojeCumprido`.
- **Campos aditivos:**
  - `Trilha.gamificacao`;
  - `Fechamento.xpGanho` (soma dos eventos das revisões da lição) e `Fechamento.gamificacao`;
  - `ResultadoAvaliacao.xpGanho`, `ResultadoAvaliacao.metaCumpridaAgora` e `ResultadoAvaliacao.gamificacao`;
  - `NoTrilha.depoisDaMeta` e `Licao.depoisDaMeta`: a lição começou depois de `meta_cumprida_em` do mesmo dia (classificação "extra depois da meta", obrigação da 005), calculada na leitura.
- **Composição:** `revisao` chama `gamificacao/consultas.py` para montar os campos (direção `revisao` → `gamificacao`). `gamificacao` não importa `revisao` (DTEC 057).
- **Interface:**
  - os valores entram no cache do TanStack Query a partir da resposta do servidor, sem atualização otimista;
  - uma única região `aria-live="polite"` por página anuncia "Mais 10 de XP", "Mais 35 de XP. Cartão dominado." e "Meta de hoje cumprida. Sequência de N dias.";
  - sem som; a animação de ganho só roda sem `prefers-reduced-motion` e nunca atrasa o foco do cartão seguinte.
- **Erros:** nenhum código novo. A 006 não cria rotas, e as falhas da gamificação desfazem a transação da revisão (`500 erro_interno`, reenviável com a mesma chave).

**Condição para revisão:** um painel próprio de evolução (007), que lê as mesmas consultas sem mudar estes campos.

## Fontes consultadas

- Documentação do PostgreSQL 17 (`SELECT ... FOR NO KEY UPDATE`, índices únicos, `ON DELETE SET NULL` com lista de colunas, `generate_series` para datas), consultada em 13/10/2026 para as DTEC 059 a 061.
- Documentação da biblioteca padrão do Python (`zoneinfo` e a base IANA, fusos `Pacific/Pago_Pago`, `Pacific/Kiritimati`, `America/Santiago`), consultada em 13/10/2026 para a DTEC 062.
- Documentação do Hypothesis (estratégias com estado e comparação com oráculo), consultada em 13/10/2026 para as DTEC 059 e 061.
- WAI-ARIA 1.2 (`aria-live`, `polite`) e WCAG 2.2 (critério 2.3.3, animação por interação), consultados em 13/10/2026 para a DTEC 063.
