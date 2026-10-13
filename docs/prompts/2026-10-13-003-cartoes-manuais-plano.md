# Plano, tarefas e rastreabilidade da spec 003-cartoes-manuais

**Data:** 2026-10-13
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** planejar (etapa 5); tarefas e rastreabilidade (etapas 6 e 7) depois do portão "Plano aprovado"
**Funcionalidade:** 003-cartoes-manuais

## Contexto fornecido

- `docs/skills/fluxo-sdd.md`, `docs/skills/padroes-implementacao.md`, `docs/skills/registrar-prompt.md`
- `docs/specs/003-cartoes-manuais/spec.md` (aprovada em 12/10/2026) e `checklists/requirements.md`
- Artefatos das specs 001 e 002: `plan.md`, `research.md` (DTEC 019 a 023 e 028 a 032), `data-model.md`, `contracts/openapi.yaml`, `tasks.md`
- `docs/research.md` (DTEC 001 a 018 e 024 a 027), `docs/arquitetura/README.md`, `docs/arquitetura/esquema-inicial.dbml`
- `docs/base-specs/spec.md` (RN-05, RN-08, RN-14, RN-16, RN-20, RN-26) e `docs/base-specs/design.md`; specs 004 e 005 (fronteiras)
- `docs/produto/exigencias_po.md`, `docs/produto/pauta-po.md`

## Prompts

### Prompt 1

```text
Prompt da spec 003

Prompt para a nova sessão (spec 003)

Vamos para a etapa 5 (planejar) da spec 003-cartoes-manuais, aprovada em 12/10/2026.
Siga docs/skills/fluxo-sdd.md e as guidelines à risca: produza plan.md, research.md (só
dúvidas técnicas novas), data-model.md, contracts/openapi.yaml e quickstart.md; depois da
minha aprovação do plano, tasks.md (etapa 6) e traceability.md com análise de consistência
(etapa 7). Não implemente código: a decisão de 13/10/2026 é documentar todas as specs do
MVP antes de implementar.

Use como referência obrigatória o que as specs 001 e 002 já definiram e não redefina:
- Estrutura base, camadas do backend (DTO, mapeador, serviço, domínio, repositório,
  exceções), hierarquia ErroAplicacao (com ConteudoMuitoGrande 413 da 002), formato de erro,
  camelCase, /api/v1, CSRF e sessão: docs/specs/001-conta-acesso/plan.md e DTEC 015 a 018.
- Stack aprovada (docs/arquitetura/README.md e DTEC 001 a 032), com psycopg 3, Python 3.13 +
  uv e Node 24 LTS + npm. Tecnologia nova só com nova DTEC; a numeração continua na DTEC 033.
  Extensões do PostgreSQL (ex.: unaccent, pg_trgm para a busca da US4) também exigem DTEC.
- Esquema inicial (docs/arquitetura/esquema-inicial.dbml): atualize-o se o plano mudar algo.
- Estrutura base, camadas do backend (DTO, mapeador, serviço, domínio, repositório,
  exceções), hierarquia ErroAplicacao (com ConteudoMuitoGrande 413 da 002), formato de erro,
  camelCase, /api/v1, CSRF e sessão: docs/specs/001-conta-acesso/plan.md e DTEC 015 a 018.
- Stack aprovada (docs/arquitetura/README.md e DTEC 001 a 032), com psycopg 3, Python 3.13 +
  uv e Node 24 LTS + npm. Tecnologia nova só com nova DTEC; a numeração continua na DTEC 033.
  Extensões do PostgreSQL (ex.: unaccent, pg_trgm para a busca da US4) também exigem DTEC.
- Esquema inicial (docs/arquitetura/esquema-inicial.dbml): atualize-o se o plano mudar algo.
  Cada spec cria só as tabelas e colunas que usa; defina quais colunas de `cartoes` a 003
  cria (as de agendamento são necessárias para RF-003, RF-005 e CS-002) e quais ficam para
  a 004 e a 005.
- Contrato: o enum Erro.codigo é cumulativo (códigos da 001 e da 002 mantidos); o esquema
  `ContagensExclusaoMateria.cartoesAtivos` da 002 conta ativos e suspensos.

Heranças que a 003 precisa cumprir:
- DTEC 027 (docs/research.md): registrar em nucleo/participantes_acervo.py o participante
  dos cartões criados à mão, com contar_por_materia (cartoes_ativos), impacto_fonte
  (cartoes_referencia), ao_excluir_fonte (mantém sempre, marca "Fonte apagada", D-009 da 002
  e D-006 da 003) e ao_excluir_materia (apaga os cartões da matéria); e criar as tarefas que
  reexecutam com cartões reais os testes funcionais da US2 e da US3 da 002.
- DTEC 019 e 021 (docs/specs/001-conta-acesso/research.md): rotas com identificador na
  tabela do teste de isolamento; apagar_dados_usuario dos cartões no registro de exclusão.
- Ponto em aberto que o plano precisa resolver: o esquema não tem onde guardar a fonte de
  referência de um cartão manual (`cartoes` não tem coluna de fonte, e `evidencias_cartoes`
  liga a trechos). A descrição da origem copiada (título, arquivo, data) precisa sobreviver
  à exclusão da fonte, e a 002 precisa conseguir contar e marcar esses cartões.
- O enum origem_cartao (gerado_verificado, editado, criado) e a edição de cartão gerado
  (RF-006) tocam a 004: alinhe a fronteira entre as duas specs sem invadir a geração.
- Revisões e XP preservados na exclusão de cartão (RF-008) dependem de revisoes.cartao_id
  com set null (005); registre a obrigação em vez de criar a tabela.
- Confira as exigências do PO (docs/produto/exigencias_po.md e pauta-po.md) que tocam a 003
  (EX-03, explicação curta, aparece na base do cartão).

Alinhe comigo em rodadas as decisões técnicas que não estiverem nas DTEC (perguntas
numeradas, opções e recomendação; consolidado antes de editar). Registre a sessão em
docs/prompts/ desde o início, faça commits atômicos separados na develop (decisões
transversais, esquema, artefatos da spec, registro) e, ao final de cada etapa, pare no
portão humano. Ao terminar a 003, gere o prompt da 004 para uma nova sessão.
O MVP tem apresentação prevista para 15/10/2026.
```

### Resposta a esclarecimento 1

```text
Rodada 1 do agente: Q1 referência da fonte (colunas em cartoes com fonte_id e cópias,
FK composta restrict, recomendado); Q2 contagem de cartões ativos na lista de matérias e na
exclusão (emenda aditiva da DTEC 027 com cartoes_suspensos, recomendado); Q3 busca sem
acentos (unaccent sem índice, recomendado); Q4 paginação da lista (keyset com cursor opaco,
50 por página, total filtrado, recomendado); Q5 limites configuráveis (validação no domínio,
tetos no DTO e no banco, GET /cartoes/limites, recomendado); Q6 fronteira com a 004
(origem_cartao completo, situacao_cartao com ativo e suspenso, colunas exceto geracao_id,
chave_imagem e dominado_em, recomendado); Q7 criação por teclado (painel lateral com
"Salvar e criar outro", recomendado); e a lista de decisões tomadas sem perguntar (rotas,
normalização do texto, edição sem escrita no FSRS, estado inicial de fsrs.Card(),
entrada_estudo_em no lugar de aceito_em, regras da referência, divisão do participante,
exclusão com DELETE, segurança do texto, interface, migração 0004_cartoes, EX-03).
-> "siga as recomendações"
```

O agente tratou a resposta como confirmação do consolidado, idêntico às recomendações da rodada 1. No detalhamento, registrou três refinamentos, sem mudar a intenção das respostas:

- Para não acrescentar dependência ao frontend, a proibição de `dangerouslySetInnerHTML` usa a regra nativa `no-restricted-syntax` do ESLint, e não um plugin novo.
- As decisões específicas ficaram em quatro DTEC (035 a 038), e não em três, separando o estado e a edição do cartão (DTEC 037) da fronteira com a 004 (DTEC 038). O intervalo foi corrigido em `docs/research.md` num commit próprio.
- `GET /cartoes/limites` também devolve o teto da busca (`buscaMax`), para que a interface não repita o número.

### Prompt 2

```text
continue
```

O agente não tratou "continue" como aprovação do plano (regra 1): apresentou o resumo da etapa 5 e pediu a aprovação explícita.

### Prompt 3

```text
aprovado
```

O agente tratou a resposta como aprovação do plano (portão "Plano aprovado"), com as DTEC 033 a 038 e a emenda da DTEC 027. Corrigiu no plano a origem da dependência `fsrs`, que já entra na 001. Depois escreveu as tarefas e a rastreabilidade (etapas 6 e 7) e parou no portão "Tarefas aprovadas".

### Prompt 4

```text
aprovo as tarefas da 003
```

O agente registrou a aprovação (portão "Tarefas aprovadas") e entregou o prompt da spec 004 para uma nova sessão.

## Saída aceita

| Artefato | Ação |
|---|---|
| `docs/research.md` | alterado (emenda da DTEC 027 com `cartoes_suspensos`; DTEC 033 e 034; índice e fontes consultadas) |
| `docs/arquitetura/README.md` | alterado (seção 3: `unaccent`) |
| `docs/skills/padroes-implementacao.md` | alterado (busca sem acentos e paginação por cursor) |
| `docs/specs/002-materias-fontes/plan.md`, `research.md`, `tasks.md`, `README.md` | alterados (propagação da emenda da DTEC 027, com registro no histórico; contrato inalterado) |
| `docs/arquitetura/esquema-inicial.dbml` | alterado (`cartoes`: referência com cópia da origem, `entrada_estudo_em`, índices `cartoes_materia` e `fonte_id`, spec que cria cada coluna e valor de enum; `fontes`: índice `fontes_id_materia_usuario`; FK composta da referência) |
| `docs/specs/003-cartoes-manuais/plan.md` | criado |
| `docs/specs/003-cartoes-manuais/research.md` | criado (DTEC 035 a 038) |
| `docs/specs/003-cartoes-manuais/data-model.md` | criado |
| `docs/specs/003-cartoes-manuais/contracts/openapi.yaml` | criado |
| `docs/specs/003-cartoes-manuais/quickstart.md` | criado |
| `docs/specs/003-cartoes-manuais/README.md`, `docs/specs/README.md` | alterados (status `Planejando`) |
| `.agents/AGENTS.md` | alterado (estado atual) |
| `docs/prompts/README.md` | alterado (índice) |
| `docs/research.md`, `plan.md` e `research.md` da 003, READMEs e `.agents/AGENTS.md` | alterados (aprovação do plano e estado atual) |
| `docs/specs/003-cartoes-manuais/plan.md` | alterado (origem da dependência `fsrs`) |
| `docs/specs/003-cartoes-manuais/tasks.md` | criado (T001 a T045) |
| `docs/specs/003-cartoes-manuais/traceability.md` | criado (matriz e análise de consistência) |
| `tasks.md`, `traceability.md` e README da 003, `docs/specs/README.md` e `.agents/AGENTS.md` | alterados (aprovação das tarefas e estado atual) |

## Alterações humanas

- Plano aprovado por Artur Lins em 13/10/2026 sem alterações (prompt 3), com as DTEC 033 a 038 e a emenda da DTEC 027.
- Tarefas e rastreabilidade aprovadas por Artur Lins em 13/10/2026 sem alterações (prompt 4).

## Verificação

- `contracts/openapi.yaml` validado com `openapi-spec-validator` (resultado: `OK`).
- Links relativos e âncoras dos arquivos criados e alterados conferidos por script (nenhum quebrado).
- Exigências do PO conferidas: só a EX-03 toca a 003, coberta pela spec (explicação opcional aqui, obrigatória na 004 e exibida na 005); o plano garante o campo e o limite. EX-01 e EX-05 (em pauta) não tocam a 003.
- Rastreabilidade: todo RF, RQ, CS, cenário e caso de borda tem teste planejado e tarefa; as dependências de outras specs estão registradas como lacunas aceitas.
- Nenhum código foi escrito nem executado (decisão de 13/10/2026). Os testes listados no plano e nas tarefas são previstos, não verificados.

## Pendências

- Implementação da 003 adiada até a documentação das specs do MVP ficar completa (decisão de 13/10/2026).
- Plano da spec 004 em nova sessão, com o prompt entregue ao fim desta.
- `git push` da `develop` pendente: os commits desta sessão estão só no repositório local.
