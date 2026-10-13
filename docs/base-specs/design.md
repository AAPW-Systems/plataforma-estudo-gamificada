# Base de design: Plataforma de Estudos Gamificada

**Atualizado em:** 12/10/2026 ([registro da sessão](../prompts/2026-10-12-alinhamento-produto-arquitetura.md))
**Status:** rascunho de apoio às specs com interface. As regras de interface permanentes estão em [`../skills/padroes-interface.md`](../skills/padroes-interface.md); este documento descreve as telas e a composição visual do produto.

## 1. Objetivo

Definir a experiência visual e de interação: limpa, consistente, responsiva, acessível, focada no estudo e com uma progressão visível. A gamificação reforça a constância sem competir com o conteúdo do cartão.

As regras de negócio estão na [base de especificação](spec.md). Este documento define **como** elas são apresentadas.

## 2. Tecnologia de interface

| Item | Definição |
|---|---|
| Base | React + TypeScript + Vite ([DTEC 004](../research.md#decisão-dtec-004-frontend)) |
| Estilo | Tailwind CSS com tokens de design centralizados |
| Componentes | Próprios. Diálogos, menus e listas acessíveis podem usar primitivas sem estilo |
| Ícones | Conjunto SVG único, a definir no plano da primeira interface |
| Idioma | Português brasileiro |
| Temas | Claro (padrão) e escuro, alternáveis (QA-19) |
| Nome do produto | A definir (UI-01) |

Não misture bibliotecas de componentes com estilos concorrentes.

## 3. Princípios de experiência

- **Conteúdo primeiro:** o cartão, a fonte e a explicação são o centro. Decoração, animação e cor não desviam da ação atual.
- **Clareza:** fica evidente onde o estudante está, o estado da ação, o resultado e o próximo passo.
- **Consistência:** ações equivalentes têm aparência e comportamento equivalentes.
- **Progressão visível:** a trilha mostra de onde o estudante veio e o que vem a seguir. É a principal representação do progresso.
- **Gamificação honesta:** XP, meta e sequência refletem dados confirmados pelo servidor. Sem sons automáticos, sem efeitos excessivos, sem números fictícios.

## 4. Navegação

### Desktop

Navegação lateral compacta, com ícone e texto e destaque da área atual sem depender só de cor:

- **Trilha** (início);
- **Matérias**;
- **Evolução**;
- **Perfil**.

### Mobile

Navegação inferior com as mesmas áreas, sem rolagem horizontal.

### Funcionalidades contextuais

- Lição → a partir da Trilha;
- Fontes, cartões e revisão dos cartões gerados → dentro da Matéria;
- Chat (final acadêmico) → ao lado das fontes, dentro da Matéria;
- Tira-dúvidas (final acadêmico) → dentro da Lição, a partir de um cartão;
- Evidência → contexto do cartão.

## 5. Tema e tokens

Os valores visuais ficam em tokens centralizados na configuração do Tailwind, com variações próprias para claro e escuro (o escuro não é uma inversão automática): `primary`, `accent`, `background`, `surface`, `text`, `muted`, `border`, `success`, `warning`, `error`, `info`, `disabled`, `focus`, além de tokens da trilha (nó alcançado, nó atual, nó futuro).

Enquanto UI-02 e UI-03 estiverem abertas, paleta e tipografia funcionam como presets intercambiáveis. Componentes consomem tokens, nunca valores soltos.

## 6. Padrões visuais

| Elemento | Padrão |
|---|---|
| Espaçamento | 4, 8, 12, 16, 24, 32 e 48 px |
| Texto principal | ~16 px, entrelinha ~1,5 |
| Títulos | ~24–32 px |
| Campos e botões | raio ~8 px |
| Cartões | raio ~12 px |
| Controles interativos | altura mínima de 44 px |
| Conteúdo de leitura | ~65–75 caracteres por linha |
| Contêiner principal | máximo ~1200 px |
| Sombras | só para comunicar elevação ou sobreposição |

## 7. Componentes

| Componente | Regra |
|---|---|
| Campos | Rótulo persistente, obrigatoriedade, texto auxiliar e erro associado. *Placeholder* não substitui rótulo |
| Botões | Primário, secundário, discreto e destrutivo. Verbos claros, uma ação principal por área |
| Diálogo | Confirmações e decisões, com título, contexto, ações claras e foco controlado |
| Aviso breve | Feedback que não exige decisão. Nunca substitui estados persistentes. Um de cada vez |
| Progresso | Indicador visual sempre acompanhado de valor textual |
| Flashcard | Frente, ação "Revelar resposta" operável por teclado (sem depender de gesto ou animação de virar), verso, quatro botões de autoavaliação |
| Origem do cartão | Selo "Gerado e verificado", "Editado por você" ou "Criado por você"; "Fonte apagada" quando for o caso |

## 8. Estados de interface

Componentes e páginas preveem, quando aplicável: `padrão | hover | foco | selecionado | desabilitado | carregando | vazio | sucesso | erro | acesso negado`.

- **Vazio:** explica a ausência e oferece a principal ação.
- **Nenhum resultado:** diferencia ausência de dados de ausência por filtro.
- **Erro:** explica e permite nova tentativa quando recuperável, sem expor detalhes do provedor de IA.
- **Acesso negado:** não revela informações do recurso.
- **Processamento sem progresso mensurável:** indicador indeterminado, nunca percentual artificial.

## 9. Telas

### 9.1 Autenticação

Login e cadastro são estados da mesma experiência. Desktop em dois painéis (área institucional e formulário); mobile em coluna única. Cadastro com nome, e-mail e senha; login com e-mail e senha. Erros não revelam se uma conta existe. Recuperação de senha no final acadêmico.

### 9.2 Trilha (início)

Responde a "o que devo fazer agora?".

- **Estudante novo:** guia para "Criar primeira matéria" e "Enviar primeira fonte".
- **Com cartões:** destaque para **Começar lição**, meta do dia (revisões feitas sobre a meta efetiva), XP e sequência.
- **Caminho visual:** preferencialmente vertical, com nós conectados. Cada nó é uma lição; os nós alcançados ficam acesos como marcos, o nó atual é destacado e os futuros aparecem como próximos passos. Marcos periódicos (ex.: a cada certo número de lições ou de cartões dominados) reforçam a progressão sem criar novas regras.
- **Sem cartões disponíveis:** nenhuma lição; a tela mostra quando chegam os próximos cartões e que o dia é neutro para a sequência.
- **Final acadêmico:** filtro por matéria e domínio por matéria.

Estados de nó: alcançado, atual, futuro. Nunca dependem só de cor.

### 9.3 Matérias

Lista de matérias com nome, quantidade de cartões ativos, cartões aguardando revisão e fontes. Ações: criar, renomear, excluir (diálogo com o impacto).

### 9.4 Matéria

Página central de cada matéria, com três áreas:

- **Fontes:** acervo da matéria com título, tipo, estado de processamento e ações (enviar, pedir cartões, excluir).
- **Cartões:** cartões ativos e suspensos, com origem; criar cartão manual; editar, suspender e excluir.
- **Chat (final acadêmico):** painel ao lado das fontes. Respostas com citações que abrem o trecho e a página; "não encontrei nas suas fontes" quando faltar evidência.

No desktop, fontes e chat ficam lado a lado; no mobile, em abas.

### 9.5 Envio e processamento de fontes

- Seleção por botão, com arrastar e soltar como complemento. Formatos e limites visíveis (RN-02).
- Estados de processamento claros (RN-03), com falha explicada e nova tentativa.
- PDF sem texto é recusado com explicação (CB-23).
- Aviso, antes da primeira geração, de que trechos das fontes são enviados a um provedor de IA externo (Princípio II).

### 9.6 Revisão dos cartões gerados

- Lista dos cartões "aguardando revisão", com frente, verso, explicação e o trecho de origem.
- Ações por cartão: **Aceitar**, **Editar e aceitar**, **Recusar**. Ação em lote **Aceitar todos**, posicionada após a lista.
- Ao terminar, o **cartão de resumo** mostra os gerados, os aceitos e os recusados, e oferece **Gerar mais**.

### 9.7 Lição

Ordem visual:

**posição na lição → frente → Revelar resposta → verso → Errei / Difícil / Bom / Fácil → (ao errar) explicação e evidência → próximo cartão**

- O avanço depende de ação do estudante.
- Os quatro botões são iguais para todos os cartões, operáveis por teclado (atalhos numéricos).
- O XP e a meta exibidos vêm da resposta do servidor.
- O tira-dúvidas (final acadêmico) é uma ação secundária, que não interrompe o fluxo principal.
- Um cartão marcado Errei pode voltar na mesma lição alguns minutos depois (passo curto do FSRS, RN-26). A posição na lição conta cartões distintos, e a reapresentação é sinalizada discretamente ("revendo").
- O fechamento da lição mostra XP ganho, revisões, cartões dominados e sequência, com "Continuar" (lição extra) ou "Voltar à trilha". "Continuar" só aparece se houver cartões disponíveis; sem eles, o fechamento mostra quando o próximo cartão vence.

### 9.8 Evidência

Conteúdo contextual, recolhido por padrão e expansível sem esconder a explicação. Mostra a fonte, o trecho e a página somente quando conhecida. Se a fonte foi apagada, mostra "Fonte apagada" com a descrição da origem (título, arquivo, página, data), sem o trecho.

### 9.9 Exclusão de fonte

Diálogo com o nome da fonte, o caráter definitivo, a quantidade de cartões aceitos e aguardando revisão afetados, e a escolha entre **Manter os cartões** ou **Excluir os cartões junto**. Ação destrutiva distinta visualmente.

### 9.10 Evolução

Dias estudados (calendário), XP total, sequência atual e recorde, cartões dominados e tempo dedicado, por matéria e no total. Valores sempre também em texto. No MVP, o mínimo da RN-25.

### 9.11 Perfil

Identificação, fuso, meta diária, tamanho da lição, limite de novos cartões por dia e retenção desejada (com explicação em linguagem simples do efeito de aumentá-la ou reduzi-la). As conquistas entram aqui quando existirem (fora do MVP).

## 10. Validações na interface

Os limites são os mesmos da API, com valores centralizados. Valide após a interação ou a tentativa de envio. Quando o servidor rejeitar: preserve os valores, associe os erros aos campos e foque o primeiro erro.

## 11. Acessibilidade e responsividade

WCAG 2.2 AA, conforme [`../skills/padroes-interface.md`](../skills/padroes-interface.md): HTML semântico, foco visível, operação completa por teclado (inclusive a lição e a trilha), contraste mínimo de 4,5:1 e 3:1, anúncio discreto de XP e resultado a tecnologias assistivas, respeito ao movimento reduzido. Funciona a partir de 320 px, sem rolagem horizontal.

## 12. Pendências de design

| ID | Pendência |
|---|---|
| UI-01 | Nome do produto (QA-19) |
| UI-02 | Paleta. Opções em comparação: `#3D007A`/`#E8ECF1`, `#C8FF00`/`#06110D`, `#0038FF`/`#FFD8B8`, `#042F32`/`#D6FFCB`, `#5F2CFF`/`#DFF6FF`, `#CFFF74`/`#2F3A1D`. Avaliar contraste em claro e escuro |
| UI-03 | Tipografia. Opções: Plus Jakarta Sans, Manrope, Sora, Outfit. Avaliar português, legibilidade em textos longos, números e licença |
| UI-04 | Quais indicadores da evolução usam gráfico, sempre com o valor em texto |
| UI-05 | Composição da trilha: nós, marcos, densidade, ícones, comportamento no celular. Identidade própria, sem reproduzir outras plataformas |
