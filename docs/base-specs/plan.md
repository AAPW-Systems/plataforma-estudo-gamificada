# Base técnica para os planos

**Atualizado em:** 12/10/2026 ([registro da sessão](../prompts/2026-10-12-alinhamento-produto-arquitetura.md))
**Status:** rascunho de apoio. A arquitetura vigente está em [`../arquitetura/README.md`](../arquitetura/README.md), e as decisões, com alternativas, estão em [`../research.md`](../research.md). Este arquivo **não repete** a stack: ele reúne o que todo `plan.md` de funcionalidade precisa considerar.

## 1. Como usar

Ao escrever o `plan.md` de uma spec (modelo em [`../sdd_guidelines/modelos/`](../sdd_guidelines/modelos/)):

1. Cite as DTEC aplicáveis em vez de reabrir decisões já tomadas.
2. Use os domínios e as tarefas assíncronas definidos na [arquitetura](../arquitetura/README.md#5-backend).
3. Parta do [esquema inicial em DBML](../arquitetura/esquema-inicial.dbml) para o `data-model.md`.
4. Verifique os itens das seções 2 a 8 abaixo que tocam a funcionalidade.

## 2. Domínios e funcionalidades

| Domínio | Funcionalidades (backlog) | Regras principais ([base de especificação](spec.md)) |
|---|---|---|
| `identidade` | F-01 | RN-01, RN-15 |
| `materias`, `fontes` | F-02, F-03 | RN-02, RN-03, RN-14, RN-23 |
| `cartoes` | F-04 | RN-04, RN-05, RN-08, RN-16, RN-22 |
| `revisao` | F-05, F-07 | RN-10, RN-17, RN-19, RN-20 |
| `gamificacao` | F-09, F-10 | RN-18, RN-21 |
| `evolucao` | F-12 | RN-25 |
| `busca`, `chat` | F-06, F-16 (final acadêmico) | RN-04, RN-05, RN-24 |

## 3. Pipeline de geração de cartões (MVP)

```text
fonte processada (trechos com página e posição)
  -> seleção de trechos (não usados em gerações anteriores da mesma matéria)
  -> contexto delimitado (trechos rotulados como dado, nunca como instrução)
  -> agente gerador (saída estruturada: frente, verso, explicação, trechos citados)
  -> validação estrutural (esquema, vínculo com trechos existentes do mesmo estudante e matéria)
  -> validação de sustentação (método e métrica definidos na spec de F-04, QA-04)
  -> deduplicação contra cartões existentes e recusados
  -> "aguardando revisão" -> o estudante aceita, edita ou recusa
```

No MVP não há embeddings: a seleção de trechos é feita pela ordem e pela cobertura da fonte. O pipeline de RAG do final acadêmico está na [arquitetura](../arquitetura/README.md#55-rag-no-final-acadêmico).

## 4. Revisão e gamificação

- O agendamento vem só da biblioteca `fsrs` (RN-26, DTEC 012). O domínio converte o cartão para `fsrs.Card`, chama o `Scheduler` com a versão dos parâmetros vigente do estudante e grava o resultado, sem ajustar o vencimento calculado.
- Cada revisão é uma transação: registra o evento (com o identificador do cliente, o estado do cartão antes e depois e a versão dos parâmetros), atualiza o estado FSRS do cartão, concede XP e atualiza o dia de estudo. Ou tudo acontece, ou nada acontece.
- A lição reapresenta cartões com passo curto vencido antes de buscar o próximo cartão inédito; os testes cobrem passos curtos, lição interrompida (CB-28) e ausência de revisão antecipada (CB-30).
- O identificador do cliente tem restrição de unicidade por estudante (RN-10).
- O dia de estudo é calculado no fuso do estudante, com virada às 4h (RN-15), com testes de fronteira.
- A regra de XP é versionada (RN-18): o evento de XP guarda a versão usada.

## 5. API

Grupos conceituais (os caminhos finais são definidos nos contratos de cada spec):

```text
/auth          cadastro, login, logout, sessão
/perfil        dados e preferências (fuso, meta, tamanho da lição, novos por dia, retenção desejada)
/materias      matérias
/fontes        envio, estado, trechos, exclusão com impacto
/geracoes      pedidos de geração, cartões aguardando revisão, resumo
/cartoes       cartões (manuais e aceitos), suspensão, evidência e origem
/licoes        lição atual, trilha
/revisoes      registro idempotente de revisões
/evolucao      indicadores
/chat          conversas e mensagens (final acadêmico)
```

- O verso e a explicação não são enviados antes do momento permitido.
- O impacto da exclusão de uma fonte tem um contrato próprio, consultado antes da confirmação.

## 6. Erros

Formato uniforme `{codigo, mensagem, campos?, idRequisicao}`, com a semântica HTTP de [`../skills/padroes-implementacao.md`](../skills/padroes-implementacao.md#erros-e-respostas-da-api). Respostas de erro não expõem detalhes internos nem do provedor de IA.

## 7. Testes por funcionalidade

Os cinco tipos exigidos pela regra 17 do [`AGENTS.md`](../../.agents/AGENTS.md), com atenção especial a:

- **Segurança:** acesso cruzado entre estudantes em todos os recursos, inclusive trechos, evidências, imagens e busca.
- **Adversariais:** fontes com instruções embutidas, arquivos malformados ou disfarçados, reenvios e concorrência de revisões.
- **IA:** adaptador falso na suíte principal; o modelo real só no grupo de avaliação (DTEC 011).

## 8. Itens técnicos em aberto

Os itens técnicos em aberto estão em [`../produto/pendencias.md`](../produto/pendencias.md): QA-11 (VPS) e QA-31 (framework dos agentes do final acadêmico). Os parâmetros de divisão em trechos e de busca são experimentais e ajustados pela avaliação.
