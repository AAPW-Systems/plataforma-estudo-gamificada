# Guia de validação local

**Funcionalidade:** 002-materias-fontes (matérias, envio e processamento de fontes)

Este guia descreve como outra pessoa verifica o incremento sem depender de explicações orais. Ele parte do ambiente da [spec 001](../001-conta-acesso/quickstart.md): mesmos pré-requisitos, mesma configuração e mesmos comandos de execução e de testes. Os passos abaixo passam a funcionar depois das tarefas da US1 da 002 (`tasks.md`, etapa 6). Todo serviço roda em contêiner (regra 11).

## Pré-requisitos

- O ambiente da 001 funcionando (`docker compose up --build`, serviços saudáveis em `docker compose ps`).
- Uma conta fictícia criada pela interface (ex.: `ana.teste@exemplo.com`, regra 10).
- Variáveis novas no `.env`: nenhuma é obrigatória, porque todas têm padrão no `.env.example` ([plano](plan.md#variáveis-de-ambiente-acréscimos-ao-envexample)). Se o `.env` foi criado antes da 002, compare-o com o exemplo:

  ```bash
  diff <(cut -d= -f1 .env.example | sort) <(cut -d= -f1 .env | sort)
  ```

## Arquivos de exemplo

Os arquivos fictícios são **gerados**, nunca baixados nem copiados de material real. O comando abaixo cria em `dados/exemplos/` (ignorado pelo git) os mesmos conjuntos usados nos testes de CS-001 e CS-002:

```bash
docker compose run --rm api uv run python -m tests.fabricas_arquivos dados/exemplos
```

| Arquivo | Uso esperado |
|---|---|
| `validos/biologia-citologia.pdf` | PDF de cerca de 1 MB, com texto em várias páginas (cenário 2) |
| `validos/pdf-2mb.pdf` | PDF de quase 2 MB, para medir o CS-003 |
| `validos/anotacoes.md`, `validos/resumo.txt` | Markdown e TXT em UTF-8 |
| `validos/um-paragrafo.txt` | Pouco texto (cenário 8) |
| `invalidos/grande-3mb.pdf` | Acima do limite (cenário 4) |
| `invalidos/disfarcado.pdf` | Texto com extensão `.pdf` (cenário 4) |
| `invalidos/corrompido.pdf` | PDF truncado (cenário 4) |
| `invalidos/protegido.pdf` | PDF com senha |
| `invalidos/latin1.txt`, `invalidos/vazio.txt` | Codificação inválida e arquivo vazio |
| `processamento/digitalizado.pdf` | PDF sem camada de texto (cenário 5) |

## Testes

Os comandos da 001 valem sem mudança. Para rodar só os testes da 002:

```bash
docker compose run --rm api uv run pytest tests -k "materias or fontes or acervo"
docker compose run --rm web npm test -- materias fontes
```

## Verificação da história P1

### US1 Criar matéria e enviar uma fonte

1. Entre com a conta fictícia e abra **Matérias**. **Esperado:** estado vazio com a ação "Criar primeira matéria".
2. Crie a matéria `Biologia`. **Esperado:** ela aparece na lista com 0 fontes, 0 cartões ativos e 0 aguardando revisão, e a página da matéria oferece "Enviar a primeira fonte" (cenário 1).
3. Tente criar `biologia`. **Esperado:** recusa junto do campo, informando que o nome já existe, com o valor digitado preservado (US3, cenário 2).
4. Na matéria, confira a área de envio. **Esperado:** formatos aceitos (PDF com texto, TXT, Markdown) e o limite de 2 MB visíveis, com botão de seleção e arrastar e soltar.
5. Envie `validos/biologia-citologia.pdf` com o título `Citologia`. **Esperado:** a fonte aparece no acervo como **Pendente**, passa a **Processando** e chega a **Concluído** sozinha, sem recarregar a página. Cada estado é mostrado com texto e ícone (cenário 2).
6. Abra a fonte. **Esperado:** título, nome do arquivo, tipo PDF, tamanho, data do envio, número de páginas e quantidade de trechos (cenário 3).
7. Envie de novo o mesmo arquivo. **Esperado:** recusa com "Esta fonte já está nesta matéria: «Citologia»" (cenário 7).
8. Envie cada arquivo de `invalidos/`. **Esperado:** cada um é recusado com uma explicação específica (tamanho, conteúdo diferente da extensão, arquivo corrompido, PDF protegido, codificação, vazio), e nada aparece no acervo (cenário 4).
9. Envie `processamento/digitalizado.pdf`. **Esperado:** a fonte chega a **Falhou** com a explicação de que PDFs digitalizados não são aceitos, **sem** o botão "Tentar novamente" (cenário 5).
10. Envie `validos/um-paragrafo.txt`. **Esperado:** chega a **Concluído**, com 1 trecho (cenário 8).
11. Simule uma falha técnica: pare o worker, envie `validos/resumo.txt`, tire a permissão de leitura do objeto dele e volte o worker.

    ```bash
    docker compose stop worker
    # envie validos/resumo.txt pela interface (fica Pendente)
    docker compose exec api sh -c 'chmod 000 "$(ls -td /dados/arquivos/usuarios/*/fontes/* | head -1)"'
    docker compose start worker
    ```

    **Esperado:** depois das novas tentativas automáticas (menos de 1 minuto), a fonte chega a **Falhou** com a mensagem de problema técnico e o botão "Tentar novamente". Devolva a permissão e use o botão:

    ```bash
    docker compose exec api sh -c 'chmod 600 "$(ls -td /dados/arquivos/usuarios/*/fontes/* | head -1)"'
    ```

    **Esperado:** a fonte volta a **Pendente** e chega a **Concluído**, com a mesma quantidade de trechos de um envio normal, sem duplicação (cenário 6, RF-008).

12. Meça o CS-003: envie `validos/pdf-2mb.pdf` e acompanhe o tempo até **Concluído**.

    ```bash
    docker compose logs worker | grep processamento_concluido | tail -1
    ```

    **Esperado:** campo de duração abaixo de 60 s.

**Evidência observável:**

- Os testes `functional` da US1 passam, inclusive os de CS-001, CS-002 e CS-003.
- O log mostra `fonte_recebida`, `processamento_iniciado`, `processamento_concluido` e `fonte_recusada`, com `public_id`, sem nome de arquivo nem conteúdo (RQ-002):

  ```bash
  docker compose logs api worker | grep -E "fonte_recebida|fonte_recusada|processamento_"
  ```

- As chaves no volume seguem `usuarios/{uuid}/fontes/{uuid}`, sem o nome enviado (RQ-001):

  ```bash
  docker compose exec api sh -c 'find /dados/arquivos -type f | head'
  ```

### US2 e US3 (verificação complementar)

- **Exclusão de fonte:** sem a spec 003, as contagens de cartões são zero. Exclua `Citologia` e confira o diálogo: título, caráter definitivo, as duas opções e o foco no diálogo. A fonte some do acervo, e o arquivo some do volume. A verificação com cartões reais é refeita quando a 003 e a 004 forem implementadas (DTEC 027).
- **Exclusão de matéria:** o botão só é habilitado depois de digitar `Biologia` exatamente. Depois da exclusão, a matéria, as fontes e os arquivos não existem mais.
- **Renomear:** renomeie a matéria e uma fonte; o novo nome aparece em todas as telas.

## Falhas conhecidas

- **Contagens de cartões em zero:** até as specs 003 e 004, os diálogos de exclusão e a lista de matérias mostram zero cartões. Os testes da US2 usam um participante falso.
- **Testes de limite de memória:** dependem de `RLIMIT_AS` e só rodam em Linux, isto é, dentro do contêiner. Rodar o pytest direto no Windows pula esses testes com justificativa registrada.
- **Envio no mesmo navegador em duas abas:** o acervo da outra aba é atualizado pelo *polling* só enquanto houver fonte em andamento. Senão, ao voltar o foco para a aba (DTEC 026).
- **Sem visualização do arquivo original:** o MVP não abre nem baixa o arquivo (D-007).
