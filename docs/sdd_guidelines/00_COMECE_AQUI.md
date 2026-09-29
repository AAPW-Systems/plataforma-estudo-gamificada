# Kit de autoestudo de SDD

Este material ensina a transformar uma intenção em artefatos que um grupo e um agente de programação conseguem revisar e executar. Você não precisa instalar o Spec Kit para usar os modelos. Os arquivos são Markdown comum e podem ser preenchidos manualmente.

## O que você deve produzir

Para uma funcionalidade do projeto, crie uma pasta em `specs/` com esta estrutura:

```text
specs/001-nome-curto/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
├── traceability.md
├── checklists/
│   └── requirements.md
└── contracts/
    └── openapi.yaml
```

Nem toda funcionalidade precisa de todos os arquivos. `spec.md`, `plan.md` e `tasks.md` são o núcleo. Use `research.md` quando houver decisões técnicas a investigar, `data-model.md` quando existirem dados persistidos e `contracts/` quando a funcionalidade expuser ou consumir uma interface.

## Ordem de estudo

1. Leia a apostila em `apostila/`.
2. Examine `exemplos/001-consulta-prazos/` na ordem `spec.md`, `plan.md` e `tasks.md`.
3. Observe os artefatos de apoio e a matriz `traceability.md`.
4. Abra `exemplos/002-triagem-solicitacoes/` para acompanhar uma revisão.
5. Copie `modelos/` para a pasta da funcionalidade do seu grupo.
6. Siga `atividades/roteiro_autonomo.md`.
7. Antes da entrega, use `atividades/checklist_entrega.md`.

## Regra de trabalho

Não avance automaticamente de um artefato para o próximo. Revise a especificação antes de planejar e revise o plano antes de criar tarefas. Se uma decisão de produto estiver indefinida, registre a dúvida e confirme com o PO. Se a dúvida for técnica, registre as alternativas em `research.md`.

## Uso com um agente de programação

O agente pode ajudar a escrever, comparar e implementar os artefatos. O grupo continua responsável por:

- confirmar requisitos e prioridades;
- rejeitar suposições não autorizadas;
- verificar contratos, código e testes;
- registrar mudanças que alterem o comportamento esperado;
- explicar as decisões tomadas.

Prompts prontos estão em `atividades/prompts_para_agente.md`.

## Relação com o Spec Kit

O fluxo atual do Spec Kit organiza o trabalho em Specify, Plan, Tasks, Implement e Converge, com etapas opcionais de Clarify, Checklist e Analyze. Este kit usa nomes de arquivos compatíveis com esse fluxo, mas simplifica o conteúdo para o projeto da disciplina.

Documentação oficial:

- https://github.com/github/spec-kit
- https://github.com/github/spec-kit/blob/main/docs/quickstart.md
- https://github.com/github/spec-kit/blob/main/docs/concepts/sdd.md

Consulte a documentação oficial antes de instalar ou atualizar a ferramenta, pois comandos e integrações podem mudar.
