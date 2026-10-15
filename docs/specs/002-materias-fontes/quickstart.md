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

Os comandos da 001 valem sem mudança (ver [padrões de implementação](../../skills/padroes-implementacao.md#comandos-e-endereços-verificados-na-spec-001)). Para rodar só os testes da 002, com o banco de pé (`docker compose up -d --wait db`):

```bash
docker compose run --rm --no-deps api uv run --frozen pytest tests -k "materias or fontes or acervo"
docker compose exec web npm test -- materias fontes   # com o ambiente de pé
docker compose run --rm --no-deps web npm test -- materias fontes   # com o web parado
```

Cada marcador também roda sozinho (`-m functional`, `-m security`, `-m adversarial`). Os arquivos dos testes da 002 são gerados por `tests/fabricas_arquivos.py`; nada é versionado.

**Verificado fora do Compose.** Nas sessões de implementação, em contêiner de nuvem sem acesso às imagens, a suíte rodou no host (Python 3.13 com `uv`, `UV_PROJECT_ENVIRONMENT` fora do repositório, contra um PostgreSQL local) e o frontend no Node 22 e no Node 24 (o do CI). O CI do GitHub é a verificação nos contêineres.

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

Com a matéria `Biologia` e as fontes `Citologia` e `Resumo` já concluídas:

1. **Exclusão de fonte (US2):** sem a spec 003, as contagens de cartões são zero. Em `Resumo`, escolha **Excluir** e confira o diálogo: título, "Ação definitiva", as duas opções sem nenhuma marcada, o foco preso no diálogo e Escape devolvendo o foco ao botão. Confirme com **Manter os cartões**. **Esperado:** a fonte some do acervo, e o arquivo some do volume. A verificação com cartões reais é refeita quando a 003 e a 004 forem implementadas (DTEC 027).
2. **Renomear a matéria (US3, cenários 1 e 2):** na página da matéria, escolha **Renomear matéria**. **Esperado:** o campo abre com o nome atual e o foco. Digite `química` (se a matéria `Química` existir) e salve: a recusa aparece junto do campo, com o valor preservado. Digite `  Biologia Celular ` e salve: o título da página e a lista de matérias mostram `Biologia Celular`, sem espaços nas pontas, e o foco volta ao botão.
3. **Renomear a fonte (US3, cenário 5):** abra `Citologia` e escolha **Renomear fonte**. Salve com o título vazio: "Informe o título da fonte." junto do campo. Salve `Aula 3: organelas`. **Esperado:** o novo título aparece no painel e no acervo; arquivo, tipo, páginas e trechos não mudam.
4. **Excluir a matéria (US3, cenários 3 e 4):** escolha **Excluir matéria**. **Esperado:** o diálogo mostra o nome, o número de fontes e de cartões (zero até a 003), diz que revisões, XP e sequência permanecem, e o botão **Excluir matéria** só é habilitado depois de digitar o nome exatamente (`biologia celular` não basta: a caixa conta). Cancele ou use Escape: nada muda, e o nome digitado é descartado. Reabra, digite `Biologia Celular` e confirme. **Esperado:** a tela volta à lista de matérias, sem a matéria excluída (nem por um instante), e o volume não guarda mais os arquivos dela:

   ```bash
   docker compose exec api sh -c 'find /dados/arquivos -type f | wc -l'
   ```

   O log traz `materia_excluida` com `public_id` e contagens, sem o nome:

   ```bash
   docker compose logs api | grep materia_excluida
   ```

## Medições (T049)

Valores medidos em 15/10/2026 no ambiente de nuvem (API, worker e PostgreSQL locais, um PDF fictício de 2 MB com 380 páginas e 760 trechos, gerado por `tests/fabricas_arquivos.py`). No Compose do Docker Desktop, os números devem ser parecidos; repita se o hardware for muito diferente.

| Medida | Meta do plano | Medido |
|---|---|---|
| PDF de 2 MB do envio até **Concluído** (CS-003) | até 60 s | cerca de 9 s (10 rodadas, de 8,9 s a 9,2 s) |
| Tempo da resposta do envio, com a verificação isolada do PDF | 0,2 a 0,5 s de custo do subprocesso | mediana de 251 ms (PDF de 1 MB) e de 262 ms (PDF de 2 MB), máximo de 295 ms, em 8 envios de cada |
| Pico de memória da extração no `worker` | até 512 MiB por extração | o subprocesso de extração chegou a 114 MiB, e o processo do `worker`, a 130 MiB (somados, cerca de 245 MiB) |
| Pico de memória da `api` durante o envio | 2 × 256 MiB (teto de cada verificação) | o processo da API ficou em 155 MiB, e o subprocesso da verificação do PDF chegou a 65 MiB |

Como medir de novo: a duração está em `docker compose logs worker | grep processamento_concluido | tail -1` (campo `duracao_ms`); o tempo do envio, no campo `duracaoMs` do log `requisicao` da rota `POST /api/v1/materias/{id}/fontes`; a memória, com `docker stats worker` durante o processamento (o subprocesso de extração vive só alguns segundos, então a amostragem fina lê `/proc/<pid>/status` a cada poucos milissegundos).

## Falhas conhecidas

- **Contagens de cartões em zero:** até as specs 003 e 004, os diálogos de exclusão e a lista de matérias mostram zero cartões. Os testes da US2 usam um participante falso.
- **Testes de limite de memória:** dependem de `RLIMIT_AS` e só rodam em Linux, isto é, dentro do contêiner. Rodar o pytest direto no Windows pula esses testes com justificativa registrada.
- **Envio no mesmo navegador em duas abas:** o acervo da outra aba é atualizado pelo *polling* só enquanto houver fonte em andamento. Senão, ao voltar o foco para a aba (DTEC 026).
- **Sem visualização do arquivo original:** o MVP não abre nem baixa o arquivo (D-007).
