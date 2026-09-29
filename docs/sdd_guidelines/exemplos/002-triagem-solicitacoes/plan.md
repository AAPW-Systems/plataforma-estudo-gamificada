# Plano de implementação da triagem de solicitações

## Resumo técnico

Uma API recebe a descrição, aplica a política de entrada e chama uma interface `Classifier`. O primeiro adaptador usa um modelo de linguagem com saída estruturada; um adaptador de regras fornece contingência e testes determinísticos. O serviço de domínio aplica limiar, verifica se a categoria pertence ao conjunto aprovado e substitui o resultado por escolha manual quando o classificador está indisponível.

## Contexto técnico

- **Linguagem:** Python 3.12.
- **API:** FastAPI e Pydantic.
- **Classificação:** adaptador de modelo com JSON validado por schema.
- **Persistência:** nenhuma para o texto; métricas agregadas em SQLite.
- **Testes:** pytest, contrato HTTP e jornada no navegador.
- **Configuração:** mapa de setores versionado em YAML.

## Componentes

```text
interface -> API -> InputPolicy -> TriageService -> Classifier
                                     |              |-> modelo
                                     |              |-> regras
                                     |-> mapa de setores
```

`TriageService` rejeita categorias desconhecidas, aplica o limiar e nunca executa envio. O frontend mantém a correção apenas no estado da sessão. Métricas registram estado final, categoria e duração sem o texto informado.

## Estratégia de avaliação

- Quinze casos de desenvolvimento podem orientar prompt, regras e limiar.
- Cinco casos reservados são executados uma vez na verificação da versão.
- O relatório separa acerto, erro, recusa por baixa confiança e indisponibilidade.
- Uma correção feita pelo usuário não altera automaticamente prompt ou modelo.

## Riscos

| Risco | Mitigação | Verificação |
|---|---|---|
| Saída fora do schema | validação e estado de indisponibilidade | teste com respostas inválidas |
| Categoria inventada | enumeração no domínio | teste de contrato |
| Log do texto | logger aceita somente objeto de métricas | teste de captura de logs |
| Confiança mal calibrada | conjunto de desenvolvimento e relatório de recusas | avaliação registrada |

## Estrutura prevista

```text
backend/src/domain/triage_service.py
backend/src/domain/input_policy.py
backend/src/ports/classifier.py
backend/src/adapters/llm_classifier.py
backend/src/adapters/rule_classifier.py
backend/src/api/routes/triage.py
backend/tests/
frontend/src/triage-form.js
config/sectors.yaml
evals/triage_cases.jsonl
```
