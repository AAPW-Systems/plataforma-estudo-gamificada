# Plano, tarefas e rastreabilidade da spec 002-materias-fontes

**Data:** 2026-10-13
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** planejar (etapa 5); tarefas e rastreabilidade (etapas 6 e 7) depois do portão "Plano aprovado"
**Funcionalidade:** 002-materias-fontes

## Contexto fornecido

- `docs/skills/fluxo-sdd.md`, `docs/skills/padroes-implementacao.md`, `docs/skills/registrar-prompt.md`
- `docs/specs/002-materias-fontes/spec.md` (aprovada em 12/10/2026) e `checklists/requirements.md`
- Artefatos da spec 001: `plan.md` (estrutura base e camadas), `research.md` (DTEC 019 a 023), `data-model.md`, `contracts/openapi.yaml`, `tasks.md`
- `docs/research.md` (DTEC 001 a 018), `docs/arquitetura/README.md`, `docs/arquitetura/esquema-inicial.dbml`
- `docs/base-specs/spec.md` e `docs/base-specs/plan.md`; specs 003 e 004 (cartões que citam fontes)
- `docs/produto/exigencias_po.md`, `docs/produto/pauta-po.md`, `docs/produto/pendencias.md`
- Modelos de `docs/sdd_guidelines/modelos/`

## Prompts

### Prompt 1

```text
Prompt para a nova sessão (spec 002)

Vamos para a etapa 5 (planejar) da spec 002-materias-fontes, aprovada em 12/10/2026.
Siga docs/skills/fluxo-sdd.md e as guidelines à risca: produza plan.md, research.md (só
dúvidas técnicas novas), data-model.md, contracts/openapi.yaml e quickstart.md; depois da
minha aprovação do plano, tasks.md (etapa 6) e traceability.md com análise de consistência
(etapa 7). Não implemente código: a decisão de 13/10/2026 é documentar todas as specs do
MVP antes de implementar.

Use como referência obrigatória o que a spec 001 já definiu e não redefina:
- Estrutura base do repositório, camadas do backend (DTO, mapeador, serviço, domínio,
  repositório, exceções), hierarquia ErroAplicacao, formato de erro, camelCase, /api/v1,
  CSRF e sessão: docs/specs/001-conta-acesso/plan.md e DTEC 015 a 018 de docs/research.md.
- Stack aprovada (docs/arquitetura/README.md e DTEC 001 a 023), com psycopg 3, Python 3.13 +
  uv e Node 24 LTS + npm. Tecnologia nova só com nova DTEC; a numeração continua na DTEC 024.
- Esquema inicial (docs/arquitetura/esquema-inicial.dbml): atualize-o se o plano mudar algo.
- Heranças que a 002 precisa cumprir (DTEC 019 e 021 em docs/specs/001-conta-acesso/research.md):
  chaves de objeto em usuarios/{public_id}/fontes/{uuid}; adaptadores de armazenamento de
  disco e em memória atrás da interface (DTEC 010); tarefas do Procrastinate idempotentes,
  enfileiradas na mesma transação e que terminam sem efeito se o registro não existir mais;
  rotas com identificador na tabela do teste de isolamento; função apagar_dados_usuario no
  registro de exclusão; exclusão de fonte isolada apaga os objetos antes das linhas.
- Confira as exigências do PO (docs/produto/exigencias_po.md e pauta-po.md) que tocam a 002.

Alinhe comigo em rodadas as decisões técnicas que não estiverem nas DTEC (perguntas
numeradas, opções e recomendação; consolidado antes de editar). Registre a sessão em
docs/prompts/ desde o início, faça commits atômicos separados na develop (decisões
transversais, esquema, artefatos da spec, registro) e, ao final de cada etapa, pare no
portão humano. Ao terminar a 002, gere o prompt da 003 para uma nova sessão.
O MVP tem apresentação prevista para 15/10/2026.
```

### Resposta a esclarecimento 1

```text
Rodada 1 do agente: Q1 cartões na exclusão (registro de participantes no núcleo,
recomendado); Q2 validação do tipo real e isolamento do parser de PDF (assinaturas próprias
+ subprocesso com tempo e memória limitados, limite de 500 páginas); Q3 codificação de TXT e
MD (só UTF-8, com ou sem BOM); Q4 divisão em trechos (divisor próprio por estrutura, alvo
1.200, máximo 2.000, sobreposição 150, uma página por trecho, versao_extracao); Q5 estado
sem recarregar (polling condicional de 2 s); Q6 consistência objeto e linha (objeto antes,
compensação e reconciliação diária com listar_prefixo); Q7 contagens do diálogo
(confirmação com as contagens exibidas e 409 impacto_alterado); Q8 falhas e novas
tentativas (codigo_falha, 2 tentativas automáticas, reprocessamento só com falha técnica,
queueing_lock, jobs travados); e a lista de decisões tomadas sem perguntar (domínios
materias e fontes, rotas, limite do corpo, trava das cotas, índice único de duplicata,
página física, MD como texto puro, transação do worker, ordem das exclusões,
apagar_dados_usuario, variáveis).
-> "siga as recomendações"
```

O agente tratou a resposta como confirmação do consolidado, idêntico às recomendações da rodada 1. No detalhamento, registrou três refinamentos, sem mudar a intenção das respostas:

- A verificação de integridade do PDF na API também roda em subprocesso, e não numa *thread*, porque uma *thread* não pode ser interrompida (DTEC 024).
- As cotas são serializadas por *advisory lock* por estudante, e não por `FOR UPDATE` na linha `usuarios`, para não disputar a linha com a sessão e o perfil da 001 (DTEC 032).
- O domínio `fontes` também é participante da exclusão da matéria, o que mantém a dependência num só sentido (DTEC 027).

## Saída aceita

| Artefato | Ação |
|---|---|
| `docs/research.md` | alterado (DTEC 024 a 027, transversais; índice e fontes consultadas) |
| `docs/arquitetura/README.md` | alterado (seções 5.3, 5.6, 6 e 8) |
| `docs/skills/padroes-implementacao.md` | alterado (isolamento e consistência de arquivos, participantes, subclasse 413) |
| `docs/arquitetura/esquema-inicial.dbml` | alterado (`fontes`: `codigo_falha` no lugar de `motivo_falha`, `versao_extracao`, `total_trechos`, título com 120 caracteres, conteúdo único por matéria, índice por usuário; enum `codigo_falha_fonte`; título de 120 caracteres em `evidencias_cartoes`) |
| `docs/specs/002-materias-fontes/plan.md` | criado |
| `docs/specs/002-materias-fontes/research.md` | criado (DTEC 028 a 032) |
| `docs/specs/002-materias-fontes/data-model.md` | criado |
| `docs/specs/002-materias-fontes/contracts/openapi.yaml` | criado |
| `docs/specs/002-materias-fontes/quickstart.md` | criado |
| `docs/specs/002-materias-fontes/README.md`, `docs/specs/README.md` | alterados (status `Planejando`) |
| `.agents/AGENTS.md` | alterado (estado atual) |
| `docs/prompts/README.md` | alterado (índice) |

## Alterações humanas

Pendente: aprovação do plano (portão "Plano aprovado").

## Verificação

- `contracts/openapi.yaml` validado com `openapi-spec-validator` (OpenAPI 3.1): OK.
- Links relativos e âncoras dos arquivos Markdown alterados conferidos por script: nenhum quebrado.
- Recursos do Procrastinate citados (`RetryStrategy`, `queueing_lock` com `AlreadyEnqueued`, `get_stalled_jobs`, `retry_job`, `prune_stalled_workers`) conferidos na documentação oficial em 13/10/2026.
- Commits até o portão do plano: `031d3b2` e `3d2c150` (decisões transversais), `1618360` (esquema), `44f2852` (padrões), `6c64ede` (artefatos da 002) e o commit deste registro.
- Nenhum código foi escrito nem executado (decisão de 13/10/2026).

## Pendências

- Portão "Plano aprovado" da 002; depois, `tasks.md` (etapa 6) e `traceability.md` com análise de consistência (etapa 7).
- Obrigações registradas para as próximas specs: 003 (participante dos cartões criados à mão), 004 (participante dos cartões gerados e das gerações, `FOR SHARE` na fonte ao publicar) e 014 (participante dos índices e citações).
