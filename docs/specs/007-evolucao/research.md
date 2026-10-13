# Pesquisa e decisões técnicas

**Funcionalidade:** 007-evolucao (evolução mínima)  
**Data:** 13/10/2026 ([registro](../../prompts/2026-10-13-007-evolucao-plano.md))  
**Status:** DTEC 064 a 067 em revisão, junto com o plano

Este arquivo registra só as dúvidas técnicas **novas** da spec 007. As decisões já tomadas não são reabertas:

- de [`../../research.md`](../../research.md): camadas (DTEC 018), dia de estudo num único ponto (DTEC 048) e disponibilidade no núcleo (DTEC 057);
- da [spec 001](../001-conta-acesso/research.md): isolamento (DTEC 019);
- da [spec 005](../005-licao-trilha/research.md): dominado com regras versionadas (DTEC 055);
- da [spec 006](../006-xp-meta-sequencia/research.md): liquidação preguiçosa, dia neutro e sequência (DTEC 061), mudança de fuso (DTEC 062) e `ResumoGamificacao` (DTEC 063).

Nenhuma decisão deste planejamento é transversal: todas valem só para o domínio `evolucao` e para as consultas que ele lê. A numeração das DTEC é única no projeto.

| Decisão | Título |
|---|---|
| [DTEC 064](#decisão-dtec-064-leitura-consolidada-da-evolução) | Leitura consolidada da evolução |
| [DTEC 065](#decisão-dtec-065-período-e-situações-do-calendário) | Período e situações do calendário |
| [DTEC 066](#decisão-dtec-066-cartões-dominados-atuais) | Cartões dominados atuais |
| [DTEC 067](#decisão-dtec-067-calendário-acessível-e-responsivo) | Calendário acessível e responsivo |

## Decisão DTEC 064 Leitura consolidada da evolução

**Questão:** como entregar o calendário, o XP, a sequência e os dominados (RF-001 a RF-004) com os mesmos valores da 006 (RF-002), em até 1 s no percentil 95 (CS-002), sem recalcular a sequência nem ler `dias_estudo` diretamente (obrigação da 006) e sem efeito colateral (DTEC 061)?  
**Critérios:** valores idênticos aos da trilha; uma tela, uma ida e volta; leituras coerentes entre si; nenhuma escrita; nenhuma dependência nova.  
**Alternativas consideradas:**

1. **Uma rota `GET /api/v1/evolucao`**, cuja resposta inclui `gamificacao: ResumoGamificacao` (o mesmo esquema e a mesma função `resumo` da 006), o calendário e os dominados, lidos numa transação própria `REPEATABLE READ, READ ONLY`.
2. **Três rotas** (calendário, resumo e dominados): três idas e voltas, e os valores podem vir de instantes diferentes.
3. **Campos novos em `GET /trilha`:** pesa a rota mais usada com 182 dias e a lista de matérias, e mistura duas telas.

**Decisão:** alternativa 1.  
**Justificativa:** o RF-002 fica satisfeito por construção, porque a evolução e a trilha chamam a mesma `gamificacao.consultas.resumo`. A transação `REPEATABLE READ` dá um único *snapshot* às quatro leituras (resumo, dias, dominados e existência de revisão), de modo que uma revisão feita em outra aba não aparece no XP sem aparecer no calendário.  
**Consequências:**

- **Transação de leitura própria:** a validação da sessão (001) renova `ultimo_uso_em` na transação da requisição, que por isso não pode ser `READ ONLY`. O serviço da evolução abre uma segunda transação por `transacao_leitura_consistente()`, acrescentada a `nucleo/banco.py` (engine da 001), com `isolation_level="REPEATABLE READ"` e `postgresql_readonly=True`. Se o dialeto do psycopg 3 não aplicar a opção, vale um `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY` explícito como primeira instrução, coberto pelo mesmo teste. Uma escrita acidental numa leitura falha no banco (`read-only transaction`), o que reforça a DTEC 061.
- **Dependências do domínio `evolucao`** (folha: nenhum domínio a importa):
  - `gamificacao/consultas.py`: `resumo` e `dias_no_intervalo`;
  - `revisao/consultas.py`: `dominados_por_materia` e `existe_revisao` (DTEC 066). É a primeira exceção à regra "nenhum domínio importa `revisao`" (DTEC 057), sem ciclo, porque `revisao` não importa `evolucao`;
  - `materias/consultas.py`: nomes e `public_id` das matérias do estudante.

  `evolucao` não tem modelos, repositórios nem migração, e não importa modelos ORM de outros domínios. Um teste de arquitetura vigia isso.
- **Erros:** nenhum código novo. Sem sessão, `401 nao_autenticado`; falha do banco, `500 erro_interno`.
- **Estado vazio (RF-005):** `possuiRevisoes` vem de `existe_revisao`. Ele não é derivado de `xp_total = 0`, embora os dois sejam equivalentes pelo invariante da 006: a regra fica explícita e não depende da regra de XP.
- **XP por dia:** `xp_por_dia` (006) não é usado no MVP. O calendário anuncia só a data e a situação, como a spec pede. A consulta fica disponível para a [013](../013-evolucao-completa/spec.md).

**Condição para revisão:** a 013 (filtros e períodos) acrescentar parâmetros à rota, ou um p95 acima do orçamento que exija cache.

## Decisão DTEC 065 Período e situações do calendário

**Questão:** como transformar as situações da 006 (`pendente`, `estudado`, `nao_estudado`, `neutro`, com `data_pulada`) nas quatro situações exibidas (estudado, não estudado, neutro, em andamento; RF-001), qual é exatamente o período de "26 semanas" (D-002) e o que fazer com os dias anteriores à conta e posteriores a hoje?  
**Critérios:** nenhum dia de hoje como não estudado; nenhum dia anterior à conta como não estudado; o mesmo dia de estudo da 006 (DTEC 048 e 062); função pura e testável.  
**Alternativas consideradas:**

1. **Grade de 26 semanas de domingo a sábado**, cuja última é a semana corrente. A API devolve só as datas do estudante até hoje. Hoje aparece como `estudado` se a meta já foi cumprida, e senão como `em_andamento`. `data_pulada` aparece como `neutro`.
2. **Exatamente 182 dias terminando hoje:** a primeira coluna fica parcial e a semana corrente não aparece inteira, o que dificulta a leitura por semana.
3. **Hoje sempre `em_andamento`:** esconde um fato definitivo (RF-006 da 006) e diverge de `sequencia.hojeCumprido`, mostrado na mesma tela.
4. **Uma situação `antes_da_conta` anunciada:** acrescenta ao leitor de tela dezenas de células sem informação.

**Decisão:** alternativa 1.  
**Justificativa:** as semanas completas com o domingo como primeiro dia seguem o calendário brasileiro. O período tem entre 176 e 182 dias passados ou correntes, e o total de dias estudados conta só esses dias. Mostrar hoje como estudado quando a meta foi cumprida coincide com a 006.  
**Consequências:**

- **Período** (função pura `periodo(hoje)` em `evolucao/dominio.py`):
  - `fim` é o sábado da semana de `hoje`;
  - `inicio` é o domingo de 25 semanas antes da semana de `hoje`;
  - `hoje` é `ResumoGamificacao.diaEstudo`, calculado pela 006 com `nucleo/dia_estudo.py`, e a evolução não calcula o dia de estudo de novo.
- **Datas devolvidas:** de `max(inicio, primeiro dia do estudante)` até `hoje`, contíguas e em ordem crescente. O primeiro dia do estudante é o dia de estudo de `criado_em`, já definido pela DTEC 061. O recorte é feito por `dias_no_intervalo` da 006 (esclarecimento da T036 da 006, abaixo). As datas depois de hoje e as anteriores à conta não vêm na resposta, e o frontend as desenha como células vazias, fora do foco.
- **Mapeamento** (função pura `situacao_exibida(data, hoje, situacao)`):

  | Data | Situação da 006 | Situação exibida |
  |---|---|---|
  | passada | `estudado` | `estudado` |
  | passada | `nao_estudado` (gravada ou calculada sem gravar) | `nao_estudado` |
  | passada | `neutro`, com ou sem `data_pulada` | `neutro` |
  | passada | `pendente` | impossível: `dias_no_intervalo` liquida em memória; a função lança erro de invariante |
  | hoje | `estudado` | `estudado` |
  | hoje | `pendente` ou sem linha | `em_andamento` |

- **Mudança de fuso:** as datas são as que a 006 atribuiu (`dias_estudo.dia` e a liquidação), sem recálculo. Uma data repetida aparece uma vez e uma data pulada aparece como neutra (DTEC 062).
- **Total de dias estudados:** contagem de `estudado` nas datas devolvidas, hoje incluído quando cumprido.
- **Esclarecimento da T036 da 006** (sem mudança de comportamento): `dias_no_intervalo(sessao, usuario_id, inicio, fim, agora)`
  - devolve uma entrada por data de `max(inicio, primeiro dia)` até `min(fim, hoje)`;
  - nas datas passadas, a situação vem gravada ou calculada em memória por `liquidar`;
  - em hoje, `estudado`, `pendente` ou ausente (sem linha);
  - traz `data_pulada`;
  - não grava nada.

**Condição para revisão:** a 013 (períodos e filtros) ou o congelamento da sequência (incremento de F-10), que acrescentaria uma situação de dia.

## Decisão DTEC 066 Cartões dominados atuais

**Questão:** como contar os dominados "atuais" (ativos ou suspensos, com estabilidade no limiar de domínio; RF-003), distintos de `cartoes.dominado_em` (marco único do bônus da 006), sem duplicar o limiar de `revisao/regras.py` (DTEC 055)?  
**Critérios:** uma única fonte do limiar; cartão que perdeu estabilidade deixa de contar; suspenso conta; excluído não conta; consulta agregada rápida.  
**Alternativas consideradas:**

1. **`revisao/consultas.py` expõe `dominados_por_materia(sessao, usuario_id)`**, que aplica `LIMIAR_DOMINADO_DIAS` da versão vigente e delega a contagem agrupada a `cartoes/consultas.py` (`contar_dominados_por_materia(sessao, usuario_id, limiar)`).
2. **`evolucao` importa a constante de `revisao/regras.py` e chama `cartoes` diretamente:** a regra "o que é dominado" fica espalhada em dois domínios.
3. **Contar `dominado_em is not null`:** viola o caso de borda "perdeu estabilidade depois de um Errei".

**Decisão:** alternativa 1.  
**Justificativa:** o domínio que define o limiar (`revisao`) também define a consulta, e `revisao` já depende de `cartoes/consultas.py`.  
**Consequências:**

- **Regra:** `situacao in ('ativo', 'suspenso') and estabilidade >= LIMIAR_DOMINADO_DIAS`, com a `estabilidade` gravada pela última revisão (`Card.stability`), sem decaimento por tempo. Um cartão nunca revisado tem estabilidade nula e não conta. `aguardando_revisao` e `recusado` não contam.
- **Limiar vigente:** uma mudança de limiar (nova `VERSAO_REGRAS`) muda os dominados atuais na hora, porque é leitura, e não altera `dominado_em` nem o XP concedido. A resposta traz `limiarDias` para que a interface explique o critério.
- **Por matéria:** a resposta traz todas as matérias do estudante, inclusive as com 0, ordenadas por nome como na lista da 002 (no máximo `COTA_MATERIAS = 50`). O total é a soma das matérias. Matéria excluída não aparece, e o XP dos cartões dela continua no total (RN-14, US1-4 da 006).
- **Índice:** a consulta usa o prefixo `(usuario_id, situacao)` de `cartoes_devidos` e filtra a estabilidade na linha. Com 3 mil cartões por estudante, isso fica dentro do orçamento. Um índice parcial por estabilidade foi rejeitado porque ficaria preso a um limiar versionado. Por isso **não há migração `0008`**.
- **Rótulo:** "cartões dominados", distinto de "domínio da matéria" da [012](../012-filtro-dominio-materia/spec.md), como pede o checklist da spec.

**Condição para revisão:** limiar por estudante (condição da DTEC 055) ou um volume de cartões que reprove o teste de desempenho.

## Decisão DTEC 067 Calendário acessível e responsivo

**Questão:** como tornar o calendário de 26 semanas navegável por teclado e legível por leitor de tela (cada dia anuncia data e situação), com contraste de 3:1 e marcação que não depende só de cor (RQ-001), e utilizável em 320 px sem rolagem horizontal da página (RQ-002)?  
**Critérios:** WCAG 2.2 AA; uma única parada de Tab; semântica de consulta, não de seleção; componentes da stack (DTEC 016).  
**Alternativas consideradas:**

1. **Semanas em linhas** (7 colunas de domingo a sábado, 26 linhas), com o padrão *grid* do WAI-ARIA, *roving tabindex* e um componente próprio `CalendarioEstudo`, usando os utilitários de foco e teclado do `react-aria`.
2. **Semanas em colunas** (26 × 7, o mapa de calor tradicional), com rolagem horizontal interna no celular: a leitura por linha anuncia o mesmo dia da semana de 26 semanas seguidas, e as células ficam pequenas demais.
3. **Colunas no desktop e linhas no celular:** a semântica de teclado muda com a largura.
4. **O `Calendar` do React Aria Components:** é um seletor de data e anuncia seleção, o que não serve a uma consulta.

**Decisão:** alternativa 1.  
**Justificativa:** cabe em 320 px com células de cerca de 32 px (7 × 32 px mais os espaços, menos que os 288 px úteis), lê-se como um calendário comum e tem um único modelo de teclado.  
**Consequências:**

- **Ordem:** a semana corrente fica na primeira linha e as anteriores seguem abaixo, para que hoje apareça sem rolar. Dentro da linha, a ordem é de domingo a sábado.
- **Semântica:**
  - `role="grid"`, com o rótulo "Dias de estudo das últimas 26 semanas";
  - cabeçalhos de coluna com os dias da semana;
  - cabeçalho de linha visualmente oculto ("Semana de 12 a 18 de outubro");
  - cada célula com dado tem `role="gridcell"` e um `aria-label` como "domingo, 12 de outubro de 2026: estudado", formatado com `Intl.DateTimeFormat('pt-BR')` a partir da data em texto, sem conversão de fuso;
  - as células vazias (antes da conta ou depois de hoje) ficam com `aria-hidden` e fora do foco.
- **Teclado:**
  - uma parada de Tab, com foco inicial em hoje;
  - setas esquerda e direita mudam de dia, e setas acima e abaixo mudam de semana;
  - Home e End vão ao início e ao fim da semana, e Ctrl+Home e Ctrl+End ao dia mais recente e ao mais antigo;
  - o movimento para em células vazias e nas bordas.
- **Marcação sem depender de cor:** cada situação tem cor e forma.

  | Situação | Forma |
  |---|---|
  | estudado | célula preenchida com ✓ |
  | não estudado | contorno com × |
  | neutro | célula hachurada com "–" |
  | em andamento | contorno tracejado com ponto central |

  A legenda fica visível, e o total aparece em texto ("42 dias estudados nas últimas 26 semanas").
- **Contraste (interpretação do RQ-001, verificável):** quatro situações não podem ter 3:1 entre todos os pares só pela luminância. A distinção entre as situações é garantida pela forma, e o contraste é medido assim:
  - (a) o indicador de cada situação (preenchimento, contorno ou glifo) tem pelo menos 3:1 contra o fundo da página (WCAG 1.4.11);
  - (b) o preenchimento de estudado tem pelo menos 3:1 contra o fundo das células não preenchidas;
  - (c) o glifo tem pelo menos 3:1 contra o preenchimento da própria célula.

  Os tokens `dia-estudado`, `dia-nao-estudado`, `dia-neutro` e `dia-andamento`, nos temas claro e escuro, ficam em `estilos/`, e um teste unitário calcula essas razões.
- **Layout:** os indicadores (XP total, sequência atual, recorde e dominados) são números em destaque com rótulo em texto (D-003). A lista por matéria é uma lista simples, que quebra nomes longos sem rolagem horizontal.

**Condição para revisão:** a paleta final (QA-19, UI-01 a UI-03) reprovar alguma razão, ou o Playwright do final acadêmico apontar problema de leitura.

## Fontes consultadas

- WAI-ARIA Authoring Practices Guide, padrão *Grid* (navegação por teclado em grades de dados).
- WCAG 2.2, critérios 1.4.1 (uso de cor), 1.4.11 (contraste de elementos não textuais) e 1.4.10 (refluxo em 320 px).
- Documentação do SQLAlchemy 2: opções de execução `isolation_level` e `postgresql_readonly`.
- Documentação do PostgreSQL: `SET TRANSACTION ... REPEATABLE READ, READ ONLY`.
- Artefatos das specs [005](../005-licao-trilha/research.md#decisão-dtec-055-dominado-e-fatos-entregues-à-gamificação) e [006](../006-xp-meta-sequencia/research.md#decisão-dtec-061-liquidação-dos-dias-passados-dia-neutro-e-sequência).
