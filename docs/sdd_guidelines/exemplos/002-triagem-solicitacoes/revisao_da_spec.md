# Revisão da especificação inicial

## Problemas encontrados

| Trecho | Problema | Pergunta necessária |
|---|---|---|
| “qualquer solicitação” | escopo ilimitado | Quais categorias entram no primeiro recorte? |
| “rápida e correta” | sem medida ou conjunto de avaliação | Qual tempo e quem define a categoria correta? |
| “encaminhar automaticamente” | ação externa sem confirmação | O sistema pode enviar ou apenas sugerir o destino? |
| “intuitiva e bonita” | adjetivos não verificáveis | Qual tarefa e observação demonstram usabilidade? |
| “guardar o histórico” | finalidade e retenção indefinidas | Quais campos, por quanto tempo e com qual base? |
| “seguro” | requisito amplo | Quais ameaças e controles são relevantes neste recorte? |
| “funcionar bem” | conclusão subjetiva | Quais cenários precisam passar? |

## Decisões confirmadas com o PO

- O primeiro recorte cobre matrícula, documentos acadêmicos, financeiro e outros.
- O sistema sugere uma categoria e um setor; não envia a solicitação.
- O usuário confirma ou corrige a sugestão.
- O texto da solicitação não será persistido nesta versão.
- O PO fornecerá 20 casos rotulados para avaliação, dos quais cinco ficarão reservados para a verificação final.

## Mudanças necessárias

1. Definir uma jornada prioritária completa.
2. Tratar baixa confiança, entrada inválida e indisponibilidade.
3. Medir tempo, concordância com o gabarito e conclusão da tarefa.
4. Separar comportamento do produto de escolhas de tecnologia.
