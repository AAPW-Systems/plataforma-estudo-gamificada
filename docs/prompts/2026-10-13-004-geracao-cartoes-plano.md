# Plano, tarefas e rastreabilidade da spec 004-geracao-cartoes

**Data:** 2026-10-13
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** planejar (etapa 5); tarefas e rastreabilidade (etapas 6 e 7) depois do portão "Plano aprovado"
**Funcionalidade:** 004-geracao-cartoes

## Contexto fornecido

- `docs/skills/fluxo-sdd.md`, `docs/skills/padroes-implementacao.md`, `docs/skills/registrar-prompt.md`
- `docs/specs/004-geracao-cartoes/spec.md` (aprovada em 12/10/2026) e `checklists/requirements.md`
- Artefatos das specs 001, 002 e 003: `plan.md`, `research.md` (DTEC 019 a 023, 028 a 032 e 035 a 038), `data-model.md`, `contracts/openapi.yaml`, `tasks.md`
- `docs/research.md` (DTEC 001 a 018, 024 a 027, 033 e 034), `docs/arquitetura/README.md`, `docs/arquitetura/esquema-inicial.dbml`
- `docs/base-specs/spec.md` (RN-04, RN-05, RN-10, RN-16, RN-20, RN-22, RQ-03 a RQ-05, RQ-10, CB-09, CB-14 a CB-16, CB-26) e `docs/base-specs/design.md` (seções 9.4 a 9.9)
- `docs/produto/exigencias_po.md`, `docs/produto/pauta-po.md`, `docs/produto/pendencias.md` (QA-04)

## Prompts

### Prompt 1

```text
Prompt para a nova sessão (spec 004)

Vamos para a etapa 5 (planejar) da spec 004-geracao-cartoes, aprovada em 12/10/2026.
Siga docs/skills/fluxo-sdd.md e as guidelines à risca: produza plan.md, research.md (só
dúvidas técnicas novas), data-model.md, contracts/openapi.yaml e quickstart.md; depois da
minha aprovação do plano, tasks.md (etapa 6) e traceability.md com análise de consistência
(etapa 7). Não imple/10/2026 é documentar
3.
- Implementação da 003 adiada até a documentação das sp
ecs do MVP ficar completa (decisão de 13/10/2026).
- Plano da spec 004 em nova sessão, com o prompt entreg
ue ao fim d
- `git pushommits desta se
ssão estão só no repositório local.

A spec 003 está fechada: registrei a aprovação das tarefas e da
rastreabilidade em f em 512d228. A 003aparece como Tarefas aprovadas no índice e no estado atual do
AGENTS.md, com a impo de 13/10.

A develop está 12 commits à frente do origin. Não fiz o git push; diga se quer que eu envie.

Prompt da spec 004 (para uma nova sessão)

Prompt para a nova sessão (spec 004)

Vamos para a etapa 5 (planejar) da spec 004-geracao-cartoes, aprovada em 12/10/2026.
Siga docs/skills/fluxo-sdd.md e as guidelines à risca: produza plan.md, research.md (só
dúvidas técnicas novas), data-model.md, contracts/openapi.yaml e quickstart.md; depois da
minha aprovação do plano, tasks.md (etapa 6) e traceability.md com análise de consistência
(etapa 7). Não implemente código: a decisão de 13/10/2026 é documentar todas as specs do
MVP antes de impleme

Use como referência obrigatória o que as specs 001, 002 e 003 já definiram e não redefina:
- Estrutura base, camadas do backend (DTO, mapeador, serviço, domínio,
repositório,
  exceções), hierarquia ErroAplicacao (com ConteudoMuitoGrande 413 da 002), formato de erro,
  camelCase, /api/v1, CSRF e sessão: docs/specs/001-conta-acesso/plan.md e DTEC 015 a 018.
- Stack aprovada (docs/arquitetura/README.md e DTEC 001 a 038), com psycopg 3, Python 3.13 +
  uv, Node 24 LTS + npm, PydanticAI com Gemini (Groq alternativo) (DTEC 007), observabilidade
  da IA (DTEC 011) e Procrastinate (DTEC 006, emenda da DTEC 002: enfileirar na mesma
  transação). Tecnologia nova só com nova DTEC; a numeração continua na DTEC 039.
- Convenções transversais: acompanhamento por polling condicional (DTEC
026), paginação por
  cursor (DTEC 034),), tarefasidempotentes que terminam sem
  efeito se o registro sumiu (DTEC 021 e 030), reenfileiramento de jobs travados (DTEC 030).
- Esquema inicial (dal.dbml): atualize-ose o plano mudar algo.
  Cada spec cria só as tabelas, colunas e valores de enum que usa: a 004 cria geracoes,
  evidencias_cartoes e consumo_ia, e acrescenta a cartoes a coluna geracao_id e os valores
  aguardando_revisao e recusado de situacao_cartao (ALTER TYPE ... ADD VALUE).
- Contrato: o enum Erro.codigo é cumulativo (códigos da 001, da 002 e da 003, inclusive
  cursor_invalido, mantidos).

Heranças que a 004 p
- DTEC 027 (com a emenda de 13/10/2026) e DTEC 038 (docs/specs/003-cartoes-manuais/research.md):
  registrar o participante dos cartões gerados e das gerações. Ele
conta só
  cartoes_aguardando_revisao e cartoes_gerados_aceitos por fonte (pelas evidências), sem
  contar de novo ativos e suspensos por matéria (já contados pela 003). Aplica o modo da
  exclusão aos aceitos (manter com "Fonte apagada" e sem selo, ou apagar), apaga os aguardando
  revisão e interrompe as gerações em andamento (CB-16). Também registra o apagar_dados_usuario
  de gerações, evidências e consumo.
- DTEC 031 (docs/spech.md): a tarefa degeração trava a fonte com
  FOR SHARE ao publicar cartões, para serializar com a exclusão.
- DTEC 038: reutilizunçõesnormalizar_texto_cartao,
  validar_limites, houve_mudanca e origem_apos_edicao no "editar e aceitar" e na validação
  estrutural. Os limites de texto vêm da configuração da 003 (D-004). Manter o CHECK de
  entrada_estudo_em, que recebe o instante da aceitação (ordem dos
novos, RN-20).
- Rotas da 003 devoldo revisão ourecusados; a revisão dos
  gerados tem rotas próprias, que entram na tabela de isolamento (DTEC 019).
- Tarefas de reexecuão real (evidência
mantida depois da
  edição), o caso de borda "aguardando revisão fora da lista" com dados reais, e os testes
  funcionais da US2 e da US3 da 002 com o participante da 004.
- RQ-007 da spec: reponsável pela implementação e pela
  do conjunto de avaliação (D-012). Pergunte quem é; não presuma.
- Confira as exigências do PO (docs/produto/exigencias_po.md e pauta-po.md) que tocam a 004:                                             EX-02 ("Gerar maiscação obrigatória comcitação).

Pontos que o plano precisa resolver (alinhe comigo):                    - Registro da ciêncio (RF-002): onde ecomo guardar.
- Não repetição de conteúdo no "Gerar mais" (RF-013, D-008, CS-007): critério e mecanismo.
- Validação de sustentação (RF-006, CS-004): como verificar antes de publicar.
- Limite diário de gerações (D-005, D-010) e orçamento por estudante (RQ-002), sob concorrência.
- Motivo de recusa opcional (RF-020, D-007): onde guardar e como        alimenta a análise.

Alinhe comigo em rodadas as decisões técnicas que não estiverem nas     DTEC (perguntas
numeradas, opções e recomendação; consolidado antes de editar). Registre a sessão em
docs/prompts/ desde o início, faça commits atômicos separados na develop (decisões
transversais, esquema, artefatos da spec, registro) e, ao final de cada etapa, pare no
portão humano. Ao terminar a 004, gere o prompt da 005 para uma novasessão.
O MVP tem apresentação prevista para 15/10/2026.
```

### Resposta a esclarecimento 1

```text
Rodada 1 de alinhamento: (1) responsável pelo conjunto de avaliação (RQ-007); (2) ciência do
aviso em tabela versionada por provedor; (3) passada única pela fonte com cobertura registrada e
filtro determinístico de repetição; (4) portões determinísticos (citação literal e cobertura
lexical) seguidos de juíza de IA que só reprova; (5) idempotência, índice único parcial por
fonte, advisory lock e orçamento de tokens por dia de estudo; (6) coluna motivo_recusa;
(7) tabela de descartados com texto, apagada em toda exclusão; (8) recusados apagados na
exclusão da fonte. Observação: fonte de 2 MB tem ~1.700 trechos e exige janela por geração.
-> siga com as recomendações, sobre o tamanho, vamos privilegiar pdf's pequenos na demonstração e explicar para o professor sobre a limitação
```

### Resposta a esclarecimento 2

```text
Rodada 2 de alinhamento (pergunta 1 reaberta): (9) revisão por geração; (10) rotas, idempotência
pelo estado e ordem de aceitação com microssegundos; (11) pipeline em duas transações, novas
tentativas, códigos de falha, 409 sem_conteudo_novo e "tentar de novo" como nova geração;
(12) delimitação com nonce, pontos_contraditorios e juíza; (13) provedor simulado do PydanticAI e
pydantic-evals fora do merge; (14) interface da revisão sem atalhos de uma letra.
-> sobre a 1, qualquer membro da equipe poderá fazer a implementação. nessa fase de documentação, eu farei as aprovações necessárias. nas demais, pode seguir as recomendações
```

## Saída aceita

Etapa 5 (planejar), aguardando o portão "Plano aprovado":

| Artefato | Ação |
|---|---|
| `docs/research.md` | alterado: DTEC 039 (aviso e ciência do provedor de IA) e DTEC 040 (consumo, orçamento e limites da IA), propostas |
| `docs/arquitetura/README.md` | alterado: tarefa `gerar_cartoes` e seção 5.4 (juíza, orçamento em *tokens*, *nonce*, ciência versionada) |
| `docs/arquitetura/esquema-inicial.dbml` | alterado: `geracoes` (código de falha, FK composta, índice parcial), `geracoes_trechos`, `cartoes_descartados`, `ciencias_aviso_ia`, `motivo_recusa`, deslocamentos da citação, enums novos |
| `docs/specs/004-geracao-cartoes/research.md` | criado: DTEC 041 a 047 |
| `docs/specs/004-geracao-cartoes/plan.md` | criado |
| `docs/specs/004-geracao-cartoes/data-model.md` | criado |
| `docs/specs/004-geracao-cartoes/contracts/openapi.yaml` | criado |
| `docs/specs/004-geracao-cartoes/quickstart.md` | criado |
| `docs/specs/004-geracao-cartoes/README.md` | alterado: status e ordem de leitura |
| `docs/specs/003-cartoes-manuais/README.md`, `data-model.md` | alterados: propagação da DTEC 045 (selo derivado da fonte da geração), com registro no histórico |

## Alterações humanas

Pendente de revisão.

## Verificação

- Contrato validado com `openapi-spec-validator` (`OK`).
- Links relativos e âncoras dos arquivos alterados conferidos por script (0 problemas).
- Documentação do PydanticAI (`UsageLimits`, `RunUsage`, `FunctionModel`, `TestModel`, `ALLOW_MODEL_REQUESTS`) e do pydantic-evals (`Dataset`, `Case`, avaliadores) consultada pelo Context7 em 13/10/2026.
- Semântica de `max_attempts` do Procrastinate conferida contra a DTEC 030 (`max_attempts=2` = até 2 novas tentativas).

## Pendências

- Portão "Plano aprovado" (Artur Lins).
- Depois do portão: `tasks.md` (etapa 6) e `traceability.md` com análise de consistência (etapa 7).
- Nome da pessoa responsável pela implementação e revisora do conjunto de avaliação (RQ-007), registrado no plano no início da implementação.
- Modelo padrão do provedor conferido na implementação contra a camada gratuita vigente.
