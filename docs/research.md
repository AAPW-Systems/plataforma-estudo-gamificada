# Pesquisa e decisões técnicas do projeto

**Funcionalidade:** projeto (decisões transversais, válidas para todas as specs)  
**Data:** 29/09/2026

Este arquivo registra as decisões técnicas que valem para o projeto inteiro, no formato do [modelo de `research.md`](sdd_guidelines/modelos/research.md). Decisões específicas de uma funcionalidade ficam no `research.md` da pasta da spec correspondente (`docs/specs/NNN-nome-curto/`). As questões técnicas ainda abertas (QA-18, QA-22 e outras) estão em [`produto/pendencias.md`](produto/pendencias.md) e, quando decididas, entram aqui como novas decisões `DTEC`.

| Decisão | Título | Status |
|---|---|---|
| [DTEC 001](#decisão-dtec-001-ferramenta-de-testes-do-backend) | Ferramenta de testes do backend | Decidida por Artur Lins em 29/09/2026; aprovação da equipe pendente ([VAL-05](produto/pendencias.md#val-05-aprovação-das-regras-de-git-e-testes)) |

## Decisão DTEC 001 Ferramenta de testes do backend

**Questão:** qual ferramenta executa os testes automatizados do backend em Python, exigidos para toda spec implementada (regra 17 do [`AGENTS.md`](../.agents/AGENTS.md)), cobrindo testes unitários, de integração, funcionais, de segurança e adversariais?  
**Critérios:** suporte aos cinco tipos de teste na mesma suíte; independência do framework do backend, ainda pendente (QA-18); clareza das falhas; reuso de preparação de ambiente (banco, usuários, provedor de IA simulado); execução em contêiner e em integração contínua; maturidade e documentação; curva de aprendizado da equipe.  
**Alternativas consideradas:**

1. **pytest:** asserts simples com mensagens detalhadas de falha, fixtures com escopo e injeção por nome, parametrização de casos, marcadores para classificar e filtrar testes e um ecossistema amplo de plugins (cobertura, execução paralela, testes assíncronos, integração com os dois frameworks avaliados em QA-18). Executa também testes escritos com `unittest`. Consequência: é uma dependência externa, e o uso excessivo de fixtures implícitas pode dificultar a leitura se não houver convenção.
2. **unittest (biblioteca padrão):** não exige dependência, mas requer classes e métodos de assert específicos, a preparação de ambiente é por herança (`setUp`/`tearDown`), não há parametrização nativa equivalente e o ecossistema de extensões é restrito. Consequência: mais código repetitivo por teste e menos recursos para organizar os cinco tipos de teste.
3. **Test runner do framework (ex.: `manage.py test` do Django):** integrado ao framework, mas baseado em `unittest` e amarrado a uma escolha ainda pendente (QA-18). Consequência: a decisão de testes ficaria bloqueada por QA-18 e mudaria se o framework mudasse.

**Decisão:** usar **pytest** como ferramenta única de execução dos testes do backend e de qualquer outro código Python do projeto (versão estável mais recente na data desta decisão: 9.1.1, a ser fixada no arquivo de dependências do backend).  
**Justificativa:** é a única alternativa que atende a todos os critérios sem depender de QA-18. As fixtures resolvem a preparação reutilizável de banco, usuários e IA simulada; a parametrização concentra os casos adversariais e de fronteira em tabelas legíveis; os marcadores permitem separar e executar por tipo os cinco grupos exigidos pela regra 17; e existe integração mantida para FastAPI e para Django, qualquer que seja o resultado de QA-18.  
**Consequências:**

- Os testes são classificados por marcadores registrados (`unit`, `integration`, `functional`, `security`, `adversarial`), com marcadores desconhecidos tratados como erro, para que nenhum teste fique sem tipo.
- A suíte roda dentro do contêiner do backend, com os serviços reais do ambiente (ex.: PostgreSQL) nos testes de integração, conforme a regra 11 do `AGENTS.md`. O comando único de execução é documentado no `quickstart.md` da spec.
- Os complementos dependem de QA-18 e são decididos no primeiro `plan.md`: cliente HTTP de teste e plugin de integração com o framework, plugin de testes assíncronos, medição de cobertura e, como candidato para os testes adversariais, geração de entradas por propriedades.
- O pytest não cobre o frontend em React. A ferramenta de testes do frontend é uma decisão separada, a registrar quando o frontend for planejado.
- Nenhum merge na `main` acontece sem a suíte completa passando na `develop` (regra 17). A automação dessa verificação (integração contínua e proteção da `main`) é trabalho futuro.

**Condição para revisão:** incompatibilidade comprovada entre o pytest e o framework escolhido em QA-18, ou tempo de execução da suíte que inviabilize rodá-la completa antes de cada merge mesmo com execução paralela.

## Fontes consultadas

- Documentação oficial do pytest (fixtures, parametrização, marcadores e plugins).
- Documentação oficial do `unittest` da biblioteca padrão do Python.
- Índice de pacotes do Python (PyPI), consultado em 29/09/2026 para a versão estável mais recente do pytest.
- [`produto/pendencias.md`](produto/pendencias.md), QA-18, para a comparação entre os frameworks do backend.
