# Guia de validação local da consulta de prazos

Este guia descreve os comandos previstos pelo plano. Eles passam a ser a referência de execução quando as tarefas estiverem implementadas.

## Pré requisitos

- Python 3.12
- navegador Chromium instalado pelo Playwright
- SQLite com FTS5 habilitado

## Configuração

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
alembic upgrade head
python -m app.ingest ../data/corpus
```

O arquivo `.env` deve definir `ACADEMIC_SUPPORT_URL`. Nenhuma credencial real pertence ao repositório.

## Execução

```bash
uvicorn app.main:app --reload
```

Em outro terminal:

```bash
python -m http.server 8080 --directory frontend
```

## Testes

```bash
cd backend
pytest
cd ../frontend
npx playwright test
```

## Verificação da história P1

1. Abra `http://localhost:8080`.
2. Pergunte “Qual é o período de matrícula regular do segundo semestre?”.
3. Confirme que a resposta contém a data, o título, a seção e a versão da fonte.
4. Abra a fonte usando somente o teclado.
5. Verifique no log que há `query_id`, estado, IDs de fonte, versão do corpus e duração, mas não a pergunta bruta.

## Verificação de falha

1. Pare o backend.
2. Envie uma nova pergunta pela interface.
3. Confirme que a interface informa indisponibilidade e não exibe uma resposta anterior como resultado atual.
