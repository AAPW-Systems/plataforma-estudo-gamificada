# Conversão dos prompts de retomada da spec 001 para Markdown

**Data:** 2026-10-13
**Autor:**
**Agente e modelo:** Codex / GPT-6
**Etapa SDD:** implementar
**Funcionalidade:** 001-conta-acesso

## Contexto fornecido

Dois prompts de retomada em texto simples e o padrão dos registros em docs/prompts/README.md.

## Prompts

### Prompt 1

```text
transforme os arquivos 2026-10-13-001-conta-acesso-retomada, as duas versões em arquivos .md seguindo o padrão dos outros que ja estão documentados, deixando o espaço de autor disponivel para que eu coloque meu nome
```

## Saída aceita

- Os dois arquivos de retomada foram convertidos de .txt para .md, com metadados, seções do registro e campo Autor vazio.
- O texto de cada prompt foi preservado dentro de bloco de código.
- As referências no índice e nos registros anteriores foram ajustadas para .md.

## Alterações humanas

Pendente de revisão.

## Verificação

Conteúdo literal comparado com os arquivos .txt anteriores; links e formatação Markdown conferidos; git diff --check.

## Pendências

- Preencher o nome no campo Autor, se desejado.
- T027 a T045 e CI remoto permanecem pendentes conforme o segundo prompt de retomada.