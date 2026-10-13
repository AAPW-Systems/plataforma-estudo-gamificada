# Specs das funcionalidades do MVP e do final acadêmico

**Data:** 2026-10-12
**Autor:** Artur Lins
**Agente e modelo:** Claude Code / claude-opus-5-5
**Etapa SDD:** especificar
**Funcionalidade:** 001 a 016 (MVP e final acadêmico)

## Contexto fornecido

- [`.agents/AGENTS.md`](../../.agents/AGENTS.md), [constituição](../constitution.md), [visão](../produto/visao.md), [backlog](../produto/backlog.md), [pendências](../produto/pendencias.md), [exigências do PO](../produto/exigencias_po.md) e [pauta com o PO](../produto/pauta-po.md)
- [Base de especificação](../base-specs/spec.md) e [esquema inicial do banco](../arquitetura/esquema-inicial.dbml)
- Guidelines em [`sdd_guidelines/`](../sdd_guidelines/00_COMECE_AQUI.md): modelo de spec, checklist de requisitos, exemplo `001-consulta-prazos`, prompts e roteiro

## Prompts

### Prompt 1

```text
vamos criar as specs em  "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\docs\\specs" seguindo as guidelines
```

### Resposta a esclarecimento 1

O agente fez nove perguntas, cada uma com uma recomendação:

- Q1: escrever nesta sessão só a etapa 1 (`spec.md` e `README.md`) de todas as specs do MVP.
- Q2: agrupar em sete pastas (conta; matérias e fontes; cartões manuais; geração de cartões; lição e trilha; XP, meta e sequência; evolução).
- Q3: deixar os incrementos do final acadêmico fora das specs do MVP.
- Q4: valores da gamificação: meta de 20, lição de 10, 20 novos por dia (global), 10 de XP por cartão distinto, bônus de 25, dominado com estabilidade de pelo menos 21 dias, teto de 60 s.
- Q5: exclusão de matéria definitiva em cascata, com o impacto exibido e confirmação digitando o nome.
- Q6: cotas de 50 matérias, 30 fontes por matéria e 100 MB por estudante.
- Q7: geração por fonte no MVP, até 10 cartões por pedido, reprovados descartados e registrados, pelo menos 15 casos de avaliação, sem cartão sobre ponto contraditório.
- Q8: senha de 8 a 128 caracteres, recusando senhas comuns, limite de tentativas, mensagem neutra; exclusão da conta como questão aberta.
- Q9: EX-05 como questão ligada a PO-01; EX-01 fora do escopo.

```text
pode seguir com suas recomendações, mas acho importante gerar agora também as specs da versão final acadêmica, sendo separado em cada spec de qual escopo ela pertence, se mvp ou versão final acadêmica
```

### Prompt 2

```text
uma observação importante, que acredito que não está nos documentos de arquiterura, o backend e frontend serão desenvolvidos separadamente, com as pastas respectivas
```

### Prompt 3

```text
vamos precisar ajustar algumas coisas, não teremos tempo de discutir com o professor o escopo do mvp em sua totalidade. Das funcionalidades que já discutimos anteriormente, já foi aprovado. Só estaria pendente mesmo discutir com ele alguns critérios das exigências que consideramos ser incompatível com o projeto, faça esses ajustes nos documentos respectivos
```

Interpretação aplicada pelo agente: PO-03 (recorte do MVP) encerrado como aprovado, o que encerra VAL-01; PO-04, PO-05 e PO-06 retirados da pauta e mantidos como decisões da equipe; só PO-01 (EX-05) e PO-02 (EX-01) continuam aguardando o PO.

### Prompt 4

```text
antes dos commits, adicionei em   "D:\\Workspaces\\Python\\plataforma-estudo-gamificada\\docs\\reunioes\\2026-10-01.md" uma ata de reunião de alinhamento da equipe, faça o commit dela também além dos demais
```

A ata foi escrita pela equipe, não pelo agente. O agente a leu antes do commit (sem segredos nem dados pessoais) e registrou a pasta `docs/reunioes/` no mapa do repositório. Ela não foi alterada.

## Saída aceita

| Artefato | Ação |
|---|---|
| `docs/specs/001-conta-acesso/` a `docs/specs/007-evolucao/` (`spec.md` e `README.md`) | criados (MVP) |
| `docs/specs/008-recuperacao-senha/` a `docs/specs/016-painel-administrativo/` (`spec.md` e `README.md`) | criados (final acadêmico) |
| `docs/specs/README.md` | alterado: índice por estágio |
| `docs/produto/backlog.md` | alterado: coluna "Spec" |
| `docs/produto/pendencias.md` | alterado: situação de QA-23, QA-24, QA-04 e QA-32; VAL-01 encerrada (prompt 3) |
| `docs/arquitetura/README.md` | alterado: backend e frontend como projetos separados em `backend/` e `frontend/` (seção 5.1) |
| `.agents/AGENTS.md` | alterado: "Estado atual" e "Mapa do repositório" (inclui `docs/reunioes/`) |
| `docs/produto/pauta-po.md` | alterado (prompt 3): pauta restrita a PO-01 e PO-02; PO-03 aprovado; PO-04 a PO-06 retirados |
| `docs/produto/visao.md`, `docs/produto/exigencias_po.md` | alterados (prompt 3): recorte do MVP aprovado |
| `docs/specs/004-geracao-cartoes/spec.md`, `docs/specs/014-chat-fontes/spec.md`, `docs/specs/016-painel-administrativo/spec.md` | alterados (prompt 3): referências a PO-03, PO-05 e PO-06; D-004 em 004, D-002 em 016, Q-001 de 016 removida |
| `docs/prompts/2026-10-12-specs-funcionalidades.md` e `docs/prompts/README.md` | criado e alterado |
| `docs/reunioes/2026-10-01.md` | commitado (prompt 4); escrito pela equipe, sem alteração do agente |

Organização das specs: cada spec pertence a um único estágio. Os incrementos do final acadêmico de funcionalidades do MVP têm pasta própria (008 a 013), e as funcionalidades exclusivas do final acadêmico ficam em 014 a 016. A indexação das fontes (F-03 no final) foi incluída na spec do chat (014), porque é o pré-requisito dele e não tem valor observável isolado.

Decisões registradas como `D-xxx` nas specs, por Artur Lins (equipe): valores padrão das preferências e da gamificação, política de senha, exclusão de matéria em cascata, cotas por estudante, geração por fonte com até 10 cartões e conjunto de avaliação com pelo menos 15 casos. Os pontos novos que surgiram durante a escrita ficaram como `Q-xxx`, com recomendação, responsável e prazo, sem serem decididos pelo agente.

## Alterações humanas

Pendente de revisão.

## Verificação

- Leitura das guidelines (`00_COMECE_AQUI.md`, modelo de spec, checklist de requisitos, exemplo `001-consulta-prazos`, prompts e roteiro) antes da escrita; as specs seguem as seções do modelo, acrescidas de "Exigências do PO" (exigido pelo `AGENTS.md`) e "Verificação da constituição" (exigida pela governança da constituição).
- Links relativos e âncoras de todos os arquivos criados e alterados conferidos por script (0 links quebrados); o script foi testado com um link e uma âncora inválidos, que foram detectados.
- Busca por nomes de produtos de terceiros nas specs (regra 13): nenhuma ocorrência.
- O checklist de requisitos (`checklists/requirements.md`) **não** foi executado: ele é a etapa 3 do fluxo e cabe a um revisor humano.

## Pendências

- Esclarecimento (até 5 perguntas por spec) e revisão pelo checklist de requisitos, começando pelas specs do MVP (001 a 007), até a aprovação pela equipe (portão humano).
- Questões `Q-xxx` das specs do MVP com prazo em 14/10/2026 e 16/10/2026; as do final acadêmico, em 31/10/2026; com o PO, só EX-05 (PO-01; Q-002 de 005 e Q-002 de 013) e EX-01 (PO-02; Q-001 de 015), na próxima review.
- Aprovação das specs depende ainda de VAL-02 (constituição v0.4). VAL-01 foi encerrada em 12/10/2026.
- A visão ainda cita 10 como ponto de partida do limite de novos cartões por dia; a spec 001 propõe 20. Atualizar a visão e a base de especificação quando a spec for aprovada (regra 12).
