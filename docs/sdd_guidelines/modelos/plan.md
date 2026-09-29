# Plano de implementação

**Funcionalidade:** [nome]  
**Spec:** [link relativo para spec.md]  
**Data:** [data]  
**Responsáveis:** [nomes]

## Resumo técnico

[Explique a abordagem em um parágrafo. Relacione-a ao requisito principal e aos riscos conhecidos.]

## Contexto técnico

- **Linguagem e versão:**
- **Dependências principais:**
- **Persistência:**
- **Testes:**
- **Plataforma de execução:**
- **Limites de desempenho ou custo:**
- **Escala prevista:**

## Verificação da constituição

| Princípio | Como o plano atende | Evidência prevista |
|---|---|---|
| [princípio] | [decisão] | [teste, log, revisão ou documento] |

Registre qualquer exceção em `complexidade e exceções` antes de iniciar a implementação.

## Arquitetura e fluxo

```text
[entrada] -> [componente] -> [componente] -> [saída]
```

Descreva responsabilidades, limites e dependências entre os componentes.

## Estrutura do repositório

```text
src/
tests/
docs/
```

**Decisão de estrutura:** [explique a opção escolhida e cite diretórios reais]

## Contratos

- [endpoint, evento, arquivo ou interface]
- [regras de erro e versionamento]

## Dados

- [entidades persistidas]
- [origem, validação, retenção e descarte]

## Estratégia de testes

- **Unitários:** [regras isoladas]
- **Integração:** [limites entre componentes]
- **Contrato:** [interfaces]
- **Jornada:** [fluxo prioritário]
- **Casos de falha:** [ausência, indisponibilidade e entrada inválida]

## Observabilidade e operação

- [logs sem dados sensíveis]
- [métrica ou verificação de saúde]
- [tratamento de timeout e retomada]

## Riscos técnicos

| Risco | Consequência | Mitigação | Como verificar |
|---|---|---|---|
| [risco] | [efeito] | [ação] | [teste ou evidência] |

## Complexidade e exceções

| Exceção | Por que é necessária | Alternativa mais simples rejeitada porque |
|---|---|---|
| [se houver] |  |  |

## Saídas do planejamento

- `research.md` para decisões que exigiram investigação;
- `data-model.md` para entidades e validações;
- `contracts/` para interfaces externas;
- `quickstart.md` para validar a implementação localmente;
- `tasks.md` criado somente depois da revisão deste plano.
