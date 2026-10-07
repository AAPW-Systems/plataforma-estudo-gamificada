# Design — Plataforma de Estudos Gamificada

## 1. Objetivo

Definir a experiência visual e de interação da plataforma, mantendo uma interface limpa, consistente, responsiva, acessível, focada no estudo e simples de compreender.

A gamificação deve reforçar o progresso sem competir visualmente com o conteúdo.

Regras de negócio, limites e comportamentos funcionais pertencem ao `SPEC.md`. Este documento define **como esses comportamentos são apresentados ao usuário**.

Arquitetura pertence ao `PLAN.md`, ordem de implementação ao `TASKS.md` e instruções para agentes ao `SKILL.md`.

---

## 2. Tecnologia de interface

| Item | Definição |
| --- | --- |
| Framework | React JS |
| Sintaxe | JSX |
| Build | Vite |
| Componentes | Material UI |
| Ícones | Material UI Icons |
| Idioma | Português brasileiro |
| Temas | Claro e escuro |
| Nome do produto | `[DEFINIR]` |

Material UI é a base do sistema visual. Evitar bibliotecas de componentes ou soluções de estilo concorrentes sem necessidade técnica.

Convenções de implementação seguem o `SKILL.md`. Paleta e tipografia são definidas em `UI-02` e `UI-03`.

---

## 3. Princípios de experiência

- **Conteúdo primeiro:** priorizar materiais, assuntos, questões e explicações. Evitar decoração, animações, cores e informações que desviem da ação atual.
- **Clareza:** deixar evidente onde o usuário está, o estado da ação, seu resultado e o próximo passo.
- **Consistência:** ações equivalentes devem possuir aparência e comportamento equivalentes.
- **Gamificação discreta:** pontos, progresso e conquistas devem incentivar continuidade sem competir com o estudo. Evitar efeitos excessivos e sons automáticos.
- **Feedback confiável:** estados de processamento, respostas, pontos, conquistas e demais ações devem refletir dados confirmados, sem indicar sucesso antecipadamente.

---

## 4. Estrutura de navegação

### Desktop

Utilizar navegação lateral compacta para:

- Início;
- Materiais;
- Trilhas;
- Evolução;
- Perfil.

Priorizar **ícone + texto**, com destaque claro para a área atual sem depender exclusivamente de cor. Evitar itens com aparência de botões independentes.

### Mobile

Adaptar a navegação às telas pequenas, mantendo acesso às mesmas áreas e sem exigir rolagem horizontal da página.

### Funcionalidades contextuais

- Flashcards → fluxo de estudo;
- Evidências → contexto da questão ou flashcard;
- Conquistas → Perfil.

Não criar telas principais independentes para essas funcionalidades no MVP.

---

## 5. Tema e identidade visual

A aplicação deve possuir temas **claro e escuro**, alternáveis pelo usuário.

Enquanto a identidade visual estiver em avaliação, paleta (`UI-02`) e tipografia (`UI-03`) devem funcionar como presets independentes e intercambiáveis.

A configuração visual deve ser centralizada no tema do Material UI. Componentes devem consumir o tema sem depender diretamente de uma paleta ou fonte específica.

O tema deve disponibilizar tokens equivalentes a:

- `primary`;
- `secondary` ou `accent`;
- `background`;
- `surface`;
- `text`;
- `border`;
- `success`;
- `warning`;
- `error`;
- `info`;
- `disabled`;
- `focus`.

Os tokens devem possuir variações adequadas para claro e escuro e respeitar os requisitos de contraste e acessibilidade deste documento.

Disponibilizar controle acessível na navegação para alternar entre os temas. O tema escuro deve utilizar tokens próprios, não simples inversão automática de cores.

---

## 6. Padrões visuais

| Elemento | Padrão |
| --- | --- |
| Espaçamento | 4, 8, 12, 16, 24, 32 e 48 px |
| Texto principal | ~16 px |
| Entrelinha | ~1,5 |
| Títulos | ~24–32 px |
| Campos e botões | raio ~8 px |
| Cartões | raio ~12 px |
| Controles interativos | altura mínima de 44 px |
| Conteúdo de leitura | ~65–75 caracteres por linha |
| Contêiner principal | máximo ~1200 px |
| Sombras | somente para comunicar elevação ou sobreposição |

Valores aproximados podem ser ajustados na definição do tema, preservando a consistência visual.

---

## 7. Componentes

| Componente | Regra |
| --- | --- |
| Campos | Rótulo persistente, obrigatoriedade quando aplicável, texto auxiliar quando necessário e erro associado. Placeholder não substitui rótulo. |
| Botões | Variantes primária, secundária, discreta e destrutiva. Usar verbos claros e evitar ações principais concorrentes. |
| Seleções | Aparência consistente e área clicável incluindo o rótulo quando aplicável. |
| Cartões | Utilizar somente para agrupamento real de informações. |
| Dialog | Utilizar para confirmações e decisões que exigem ação, com título, contexto, ações claras e controle acessível de foco/fechamento. |
| Snackbar | Utilizar para feedback breve que não exija decisão. Não substituir estados persistentes ou mensagens contextuais. |
| Progresso | Indicador visual acompanhado de valor ou descrição textual. Cálculo conforme `RN-12`. |

Ações destrutivas que exigem confirmação devem utilizar `Dialog`.

Mensagens relacionadas diretamente a campos, questões ou conteúdos devem permanecer próximas ao elemento correspondente.

Notificações operacionais devem ser discretas. Conquistas e conclusão de trilhas podem receber apresentação mais celebrativa, sem depender exclusivamente de cor ou ícone.

Evitar múltiplos Snackbars simultâneos.

---

## 8. Estados de interface

Componentes e páginas devem prever, quando aplicável:

`padrão | hover | foco | selecionado | desabilitado | carregando | vazio | sucesso | erro | acesso negado`

- **Vazio:** explicar a ausência de dados e oferecer a principal ação disponível.
- **Nenhum resultado:** diferenciar ausência de dados de ausência causada por busca ou filtro.
- **Erro:** explicar a situação e permitir nova tentativa quando apropriado.
- **Acesso negado:** não revelar informações do recurso protegido.

Ações indisponíveis devem explicar o motivo quando ele não for evidente.

Durante ações assíncronas, impedir duplicação acidental, indicar processamento, preservar informações úteis e permitir nova tentativa quando a falha for recuperável.

Não exibir conteúdo ou porcentagem de progresso fictícios.

---

# 9. Telas

As regras globais das seções anteriores aplicam-se a todas as telas. Esta seção registra apenas composição, hierarquia e comportamentos visuais específicos.

## 9.1 Autenticação

Login e Cadastro são estados da mesma experiência.

**Desktop:** composição em dois painéis, com área visual/institucional e formulário. A alternância pode reorganizar ou transicionar os painéis sem prejudicar acessibilidade ou preferência por movimento reduzido.

**Mobile:** composição em coluna única.

**Cadastro:** nome, e-mail e senha, com confirmação quando exigida pelo contrato. Ação principal `Criar conta` e alternativa `Já possui uma conta? Entrar`.

**Login:** e-mail e senha. Apresentar ação principal e alternativa `Ainda não possui uma conta? Criar conta`.

Validações e erros permanecem associados ao formulário, sem revelar informações sensíveis sobre contas existentes.

---

## 9.2 Início

A tela deve responder **“O que devo fazer agora?”**.

- novo estudante → priorizar `Enviar primeiro material`;
- com atividade → `Continuar estudo`, progresso, pontos e atividade recente.

Não apresentar métricas fictícias sem atividade.

---

## 9.3 Materiais

Apresentar materiais com título, tipo, estado de processamento e ações disponíveis.

Permitir visualmente as ações previstas para envio, detalhe, arquivamento, restauração e exclusão. Regras funcionais seguem `RN-02`, `RN-03` e `RN-14`.

**Upload:** seleção por botão; arrastar e soltar pode ser complementar. Exibir limites definidos em `RN-02` e estado individual quando houver múltiplos arquivos.

**Exclusão:** quando permitida, utilizar `Dialog` indicando material, caráter definitivo, cancelamento e ação destrutiva. Quando bloqueada, explicar o motivo e apresentar `Arquivar` como alternativa quando aplicável.

Arquivamento, restauração e exclusão devem permanecer visualmente distintos.

---

## 9.4 Processamento

Representar claramente os estados definidos em `RN-03`.

Diferenciar processamento técnico de cobertura pedagógica. Falhas devem apresentar mensagem compreensível e recuperação quando disponível, sem expor detalhes internos do provedor de IA.

---

## 9.5 Trilhas

Representar a trilha como **caminho visual de progressão**, preferencialmente vertical, utilizando nós conectados e marcos visuais.

Deve ficar claro:

**onde está → o que concluiu → próximo passo**

Cada nó representa uma etapa/tópico e deve comunicar assunto, estado, progresso quando aplicável e disponibilidade. Ao selecioná-lo, apresentar contexto e ação disponível.

Distinguir:

- disponível;
- atual/recomendado;
- concluído;
- aguardando material de apoio.

Estados devem combinar recursos visuais sem depender exclusivamente de cor.

Marcos reforçam progressão, mas não criam novas regras de gamificação.

Quando `RN-06` se aplicar, integrar ao caminho o estado `Aguardando material de apoio` e oferecer `Enviar material complementar`.

---

## 9.6 Estudo

Priorizar visualmente:

**posição → enunciado e resposta → confirmação → feedback → explicação → evidência → continuação**

Enunciado e controles de resposta devem permanecer no mesmo agrupamento visual.

Suportar conteúdo longo sem truncamento e não avançar automaticamente após a resposta.

---

## 9.7 Questões

Suportar os tipos e comportamentos definidos em `RN-07`, `RN-09` e `RN-16`.

Apresentar posição, enunciado, dificuldade, opções e `Confirmar resposta` no mesmo contexto visual.

Antes da confirmação, não revelar informações capazes de indicar o gabarito.

Após a resposta, priorizar:

**resultado → explicação → evidência → continuação**

Manter o feedback visível até ação do estudante.

---

## 9.8 Evidência

Evidências são contextuais e não possuem tela principal independente.

Após a resposta, disponibilizar `Ver evidência` como conteúdo inicialmente secundário e recolhido, expansível sem ocultar a explicação.

Quando disponível, apresentar:

- material;
- trecho;
- página, somente quando conhecida conforme `RN-05`.

O mesmo padrão aplica-se às evidências acessadas por flashcards.

---

## 9.9 Flashcards

Apresentar flashcards como recurso de revisão conforme `RN-08`.

**Antes da revelação:** pergunta ou estímulo de recordação + `Revelar resposta`.

**Depois:** resposta, explicação quando aplicável e acesso à evidência conforme `9.8`.

A interação não deve depender de gesto ou animação de virar cartão.

---

## 9.10 Evolução

Apresentar de forma simples:

- pontos;
- questões respondidas;
- questões acertadas;
- percentual de acertos;
- progresso das trilhas.

Deixar claro que **acurácia ≠ conclusão**.

Gráficos são opcionais e devem ser usados somente quando melhorarem a compreensão, mantendo representação textual dos valores essenciais.

A jornada completa permanece em `Trilhas`; Evolução apresenta apenas seu resumo.

---

## 9.11 Perfil

Reunir identificação básica do estudante, informações úteis da conta e conquistas, sem transformar a tela em outro dashboard de desempenho.

### Conquistas

Apresentar somente as conquistas definidas em `RN-13`, diferenciando obtidas e pendentes.

Cada conquista deve comunicar nome, critério, estado e data de obtenção quando aplicável.

A apresentação pode utilizar badges/medalhas, ícones e tratamento visual mais celebrativo, sem depender exclusivamente de cor.

---

## 10. Validações na interface

A interface deve respeitar `RN-02` e os contratos da API, sem inventar limites ou regras funcionais.

Validar preferencialmente após interação, saída do campo quando apropriado ou tentativa de envio, evitando erros prematuros.

Quando o servidor rejeitar um formulário:

- preservar valores válidos;
- associar erros aos campos correspondentes quando possível;
- focar o primeiro erro relevante quando apropriado.

A validação do frontend melhora a experiência, mas não substitui a validação do servidor.

---

## 11. Acessibilidade

A interface deve:

- utilizar HTML semântico e hierarquia lógica de títulos;
- associar rótulos aos campos e nomes acessíveis aos botões de ícone;
- possuir foco visível e funcionar por teclado;
- comunicar resultados por texto, sem depender somente de cor;
- gerenciar corretamente o foco em diálogos;
- respeitar preferência por movimento reduzido.

Contraste mínimo: **4,5:1** para texto comum e **3:1** para texto grande e elementos visuais essenciais. Validar novamente após a definição da paleta final.

---

## 12. Responsividade

A aplicação deve funcionar a partir de **320 px** até desktop, sem rolagem horizontal da página.

Navegação, formulários, conteúdo de estudo, evidências, trilhas e diálogos devem adaptar-se ao espaço disponível sem truncar conteúdo relevante.

---

## 13. Pendências de design

Somente decisões visuais ainda não aprovadas devem permanecer nesta seção. O agente não deve assumir como definitiva nenhuma alternativa pendente sem decisão explícita da equipe.

### UI-01 — Nome do produto

`[DEFINIR]`

### UI-02 — Identidade visual e paleta

Nenhuma paleta está aprovada. Durante a prototipação, manter as seis opções como presets intercambiáveis para comparação na mesma interface:

| Opção | Cor principal | Cor de apoio |
| --- | --- | --- |
| 01 | `#3D007A` | `#E8ECF1` |
| 02 | `#C8FF00` | `#06110D` |
| 03 | `#0038FF` | `#FFD8B8` |
| 04 | `#042F32` | `#D6FFCB` |
| 05 | `#5F2CFF` | `#DFF6FF` |
| 06 | `#CFFF74` | `#2F3A1D` |

Avaliar identidade, legibilidade, conforto, contraste, acessibilidade e funcionamento em claro/escuro, desktop/mobile e elementos de gamificação.

As cores são referências da identidade base e não determinam diretamente os tokens do tema.

Após a escolha, remover alternativas e seleção entre presets e definir os tokens definitivos conforme a seção 5.

### UI-03 — Tipografia

Nenhuma fonte está aprovada. Durante a prototipação, manter como presets intercambiáveis:

- Plus Jakarta Sans;
- Manrope;
- Sora;
- Outfit.

Avaliar suporte ao português brasileiro, legibilidade em textos longos, pesos, caracteres semelhantes, números/símbolos, desktop/mobile, licença web e carregamento.

Comparar as fontes utilizando conteúdo equivalente e hierarquia provisória consistente.

Após a escolha, remover alternativas e seleção entre presets e definir família, pesos e hierarquia tipográfica definitiva.

### UI-04 — Visualização da evolução

Definir durante a prototipação quais métricas se beneficiam de representação gráfica.

Gráficos devem agregar compreensão, manter os valores essenciais disponíveis em texto e preservar a distinção entre acurácia e conclusão.

### UI-05 — Representação visual das trilhas

Validar durante a prototipação a composição do caminho definido em `9.5`, incluindo:

- nós e disposição do caminho;
- estados e marcos;
- ícones e identificação dos tópicos;
- densidade de informação;
- comportamento em desktop e mobile.

A solução deve possuir identidade própria sem reproduzir diretamente outras plataformas.
