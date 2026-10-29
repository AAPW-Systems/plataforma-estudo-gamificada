export interface paths {
  "/api/v1/acervo/uso": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Consultar Uso Acervo */
    get: operations["consultarUsoAcervo"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/auth/cadastro": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Cadastrar */
    post: operations["cadastrar"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/auth/csrf": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Obter Token Csrf
     * @description Emite o token anti-CSRF, ligado à sessão atual ou, sem sessão, à pré-sessão.
     */
    get: operations["obterTokenCsrf"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/auth/entrada": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Entrar */
    post: operations["entrar"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/auth/saida": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Sair */
    post: operations["sair"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/cartoes/limites": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Consultar Limites
     * @description Limites de texto vigentes no ambiente (RF-001, D-004).
     */
    get: operations["consultarLimitesCartao"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/cartoes/{cartaoId}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Consultar Cartao
     * @description Dados de um cartão ativo ou suspenso.
     */
    get: operations["consultarCartao"];
    put?: never;
    post?: never;
    /**
     * Excluir Cartao
     * @description Exclui o cartão definitivamente; revisões e XP permanecem (US3-3; RF-008).
     */
    delete: operations["excluirCartao"];
    options?: never;
    head?: never;
    /**
     * Editar Cartao
     * @description Edita frente, verso ou explicação, sem mudar o agendamento (US2; RF-005, RF-006).
     */
    patch: operations["editarCartao"];
    trace?: never;
  };
  "/api/v1/cartoes/{cartaoId}/reativacao": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Reativar Cartao
     * @description Devolve o cartão às lições com o vencimento anterior (US3-2; RF-007). Idempotente.
     */
    post: operations["reativarCartao"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/cartoes/{cartaoId}/suspensao": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Suspender Cartao
     * @description Tira o cartão das lições, preservando o agendamento (US3-1; RF-007). Idempotente.
     */
    post: operations["suspenderCartao"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/fontes/{fonteId}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Consultar Fonte */
    get: operations["consultarFonte"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /** Renomear Fonte */
    patch: operations["renomearFonte"];
    trace?: never;
  };
  "/api/v1/fontes/{fonteId}/exclusao": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Excluir Fonte */
    post: operations["excluirFonte"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/fontes/{fonteId}/impacto-exclusao": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Consultar Impacto Exclusao Fonte */
    get: operations["consultarImpactoExclusaoFonte"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/fontes/{fonteId}/reprocessamento": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Reprocessar Fonte */
    post: operations["reprocessarFonte"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/materias": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Listar Materias */
    get: operations["listarMaterias"];
    put?: never;
    /** Criar Materia */
    post: operations["criarMateria"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/materias/{materiaId}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Consultar Materia */
    get: operations["consultarMateria"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /** Renomear Materia */
    patch: operations["renomearMateria"];
    trace?: never;
  };
  "/api/v1/materias/{materiaId}/cartoes": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Listar Cartoes
     * @description Lista os cartões ativos e suspensos da matéria, do mais recente para o mais antigo.
     */
    get: operations["listarCartoes"];
    put?: never;
    /**
     * Criar Cartao
     * @description Cria um cartão manual na matéria; com `fonteId`, a cita como referência (sem selo).
     */
    post: operations["criarCartao"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/materias/{materiaId}/exclusao": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Excluir Materia */
    post: operations["excluirMateria"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/materias/{materiaId}/fontes": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Listar Fontes */
    get: operations["listarFontes"];
    put?: never;
    /** Enviar Fonte */
    post: operations["enviarFonte"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/materias/{materiaId}/impacto-exclusao": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Consultar Impacto Exclusao Materia */
    get: operations["consultarImpactoExclusaoMateria"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/perfil": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Obter Perfil */
    get: operations["obterPerfil"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /** Alterar Perfil */
    patch: operations["alterarPerfil"];
    trace?: never;
  };
  "/api/v1/perfil/exclusao": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Excluir Conta */
    post: operations["excluirConta"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/perfil/senha": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Trocar Senha */
    post: operations["trocarSenha"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/health": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Verificar Processo */
    get: operations["verificarProcesso"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/health/ready": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Prontidao */
    get: operations["verificarProntidao"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
}
export type webhooks = Record<string, never>;
export interface components {
  schemas: {
    /** CadastroEntradaDTO */
    CadastroEntrada: {
      /**
       * Email
       * Format: email
       */
      email: string;
      /** Fuso */
      fuso?: string | null;
      /** Nome */
      nome: string;
      /** Senha */
      senha: string;
    };
    /** CartaoDTO */
    Cartao: {
      /**
       * Atualizadoem
       * Format: date-time
       */
      atualizadoEm: string;
      /**
       * Criadoem
       * Format: date-time
       */
      criadoEm: string;
      /** Explicacao */
      explicacao: string | null;
      /**
       * Frente
       * @description Texto puro; quebras de linha como `\n` (RQ-001)
       */
      frente: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Materiaid
       * Format: uuid
       */
      materiaId: string;
      origem: components["schemas"]["OrigemCartao"];
      /** @description Só em cartões criados pelo estudante que citam uma fonte */
      referencia: components["schemas"]["ReferenciaFonte"] | null;
      situacao: components["schemas"]["SituacaoCartao"];
      /**
       * Verificado
       * @description Verdadeiro só com origem `gerado_verificado`; nunca em cartão do estudante
       */
      verificado: boolean;
      /** Verso */
      verso: string;
    };
    /**
     * CodigoErro
     * @description Códigos estáveis do contrato. As specs acrescentam; nunca renomeiam nem removem.
     * @enum {string}
     */
    CodigoErro:
      | "requisicao_malformada"
      | "dados_invalidos"
      | "email_em_uso"
      | "credenciais_invalidas"
      | "senha_atual_incorreta"
      | "nao_autenticado"
      | "csrf_invalido"
      | "origem_nao_permitida"
      | "recurso_nao_encontrado"
      | "muitas_tentativas"
      | "erro_interno"
      | "materia_nome_em_uso"
      | "cota_materias_excedida"
      | "cota_fontes_excedida"
      | "cota_armazenamento_excedida"
      | "fonte_duplicada"
      | "arquivo_muito_grande"
      | "formato_nao_aceito"
      | "tipo_divergente"
      | "arquivo_vazio"
      | "arquivo_corrompido"
      | "pdf_protegido"
      | "pdf_paginas_excedidas"
      | "codificacao_invalida"
      | "confirmacao_invalida"
      | "impacto_alterado"
      | "reprocessamento_indisponivel"
      | "cursor_invalido";
    /**
     * CodigoFalhaFonte
     * @description Nome do contrato (`CodigoFalhaFonte`); no código, `CodigoFalha` basta.
     * @enum {string}
     */
    CodigoFalhaFonte: "falha_tecnica" | "sem_texto" | "conteudo_invalido";
    /**
     * ContagensExclusaoFonteDTO
     * @description O que a exclusão da fonte afeta; o diálogo mostra e a confirmação devolve (DTEC 031).
     */
    ContagensExclusaoFonte: {
      /**
       * Cartoesaguardandorevisao
       * @description Sempre apagados
       */
      cartoesAguardandoRevisao: number;
      /**
       * Cartoesgeradosaceitos
       * @description Cartões gerados da fonte e já aceitos; seguem a escolha `modoCartoes`
       */
      cartoesGeradosAceitos: number;
      /**
       * Cartoesreferencia
       * @description Criados pelo estudante citando a fonte; sempre mantidos com "Fonte apagada" (D-009)
       */
      cartoesReferencia: number;
    };
    /**
     * ContagensExclusaoMateriaDTO
     * @description O que a exclusão da matéria apaga; o diálogo mostra e a confirmação devolve (DTEC 031).
     */
    ContagensExclusaoMateria: {
      /** Cartoesaguardandorevisao */
      cartoesAguardandoRevisao: number;
      /**
       * Cartoesativos
       * @description Cartões ativos e suspensos da matéria, que serão apagados
       */
      cartoesAtivos: number;
      /** Fontes */
      fontes: number;
    };
    /** CriacaoCartaoEntradaDTO */
    CriacaoCartaoEntrada: {
      /**
       * Explicacao
       * @description Opcional; até `explicacaoMax` caracteres; vazia equivale a ausente
       */
      explicacao?: string | null;
      /**
       * Fonteid
       * @description Fonte da mesma matéria, em qualquer estado, citada como referência (RF-002)
       */
      fonteId?: string | null;
      /**
       * Frente
       * @description 1 a `frenteMax` caracteres depois da normalização; o teto absoluto é 4.000
       */
      frente: string;
      /**
       * Verso
       * @description 1 a `versoMax` caracteres depois da normalização; o teto absoluto é 8.000
       */
      verso: string;
    };
    /**
     * EdicaoCartaoEntradaDTO
     * @description Campos ausentes não mudam; `explicacao` nula ou vazia remove a explicação (US2).
     */
    EdicaoCartaoEntrada: {
      /**
       * Explicacao
       * @description `null` ou vazia remove a explicação
       */
      explicacao?: string | null;
      /** Frente */
      frente?: string;
      /** Verso */
      verso?: string;
    };
    /** EntradaEntradaDTO */
    EntradaEntrada: {
      /** Email */
      email: string;
      /** Senha */
      senha: string;
    };
    /**
     * EnvioFonteEntradaDTO
     * @description Corpo *multipart* do envio: um arquivo e, opcionalmente, o título.
     *
     *     Fica aqui, e não em `dtos.py`, porque `UploadFile` é um tipo do FastAPI (a camada de DTOs
     *     não importa o framework, DTEC 018): o formulário é um detalhe de transporte do controlador.
     */
    EnvioFonteEntrada: {
      /**
       * Arquivo
       * Format: binary
       * @description Um único arquivo .pdf, .txt, .md ou .markdown
       */
      arquivo: string;
      /** Titulo */
      titulo?: string | null;
    };
    /**
     * Erro
     * @description Corpo único de erro do contrato (`Erro`).
     */
    Erro: {
      /** Campos */
      campos?: components["schemas"]["ErroCampo"][] | null;
      codigo: components["schemas"]["CodigoErro"];
      /**
       * Idrequisicao
       * Format: uuid
       */
      idRequisicao: string;
      /** Mensagem */
      mensagem: string;
    };
    /** ErroCampo */
    ErroCampo: {
      /** Campo */
      campo: string;
      /** Mensagem */
      mensagem: string;
    };
    /**
     * EstadoFonte
     * @enum {string}
     */
    EstadoFonte: "pendente" | "processando" | "concluido" | "falhou";
    /** ExclusaoContaEntradaDTO */
    ExclusaoContaEntrada: {
      /** Senhaatual */
      senhaAtual: string;
    };
    /** ExclusaoFonteEntradaDTO */
    ExclusaoFonteEntrada: {
      impactoConfirmado: components["schemas"]["ContagensExclusaoFonte"];
      /** @description "Manter os cartões" ou "Excluir os cartões junto" (RN-14) */
      modoCartoes: components["schemas"]["ModoCartoes"];
    };
    /**
     * ExclusaoMateriaEntradaDTO
     * @description O nome é comparado pelo domínio (NFC, extremidades, caixa), não pelo esquema.
     */
    ExclusaoMateriaEntrada: {
      impactoConfirmado: components["schemas"]["ContagensExclusaoMateria"];
      /**
       * Nomeconfirmacao
       * @description Comparado com o nome depois de NFC e sem espaços nas extremidades, diferenciando maiúsculas e minúsculas
       */
      nomeConfirmacao: string;
    };
    /** FonteDTO */
    Fonte: {
      codigoFalha: components["schemas"]["CodigoFalhaFonte"] | null;
      /**
       * Enviadaem
       * Format: date-time
       */
      enviadaEm: string;
      estado: components["schemas"]["EstadoFonte"];
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Materiaid
       * Format: uuid
       */
      materiaId: string;
      /** Mensagemfalha */
      mensagemFalha: string | null;
      /** Nomearquivo */
      nomeArquivo: string;
      /** Podetentarnovamente */
      podeTentarNovamente: boolean;
      /** Processadaem */
      processadaEm: string | null;
      /** Tamanhobytes */
      tamanhoBytes: number;
      /**
       * Tipomidia
       * @enum {string}
       */
      tipoMidia: "application/pdf" | "text/plain" | "text/markdown";
      /** Titulo */
      titulo: string;
      /** Totalpaginas */
      totalPaginas: number | null;
      /** Totaltrechos */
      totalTrechos: number | null;
    };
    /** HTTPValidationError */
    HTTPValidationError: {
      /** Detail */
      detail?: components["schemas"]["ValidationError"][];
    };
    /** ImpactoExclusaoFonteDTO */
    ImpactoExclusaoFonte: {
      contagens: components["schemas"]["ContagensExclusaoFonte"];
      estado: components["schemas"]["EstadoFonte"];
      /** Titulo */
      titulo: string;
    };
    /** ImpactoExclusaoMateriaDTO */
    ImpactoExclusaoMateria: {
      contagens: components["schemas"]["ContagensExclusaoMateria"];
      /**
       * Nome
       * @description Nome que o estudante deve digitar para confirmar
       */
      nome: string;
    };
    /** LimitesCartaoDTO */
    LimitesCartao: {
      /** Buscamax */
      buscaMax: number;
      /** Explicacaomax */
      explicacaoMax: number;
      /** Frentemax */
      frenteMax: number;
      /** Versomax */
      versoMax: number;
    };
    /** ListaCartoesDTO */
    ListaCartoes: {
      /** Itens */
      itens: components["schemas"]["Cartao"][];
      /**
       * Proximocursor
       * @description Nulo na última página (DTEC 034)
       */
      proximoCursor: string | null;
      /**
       * Total
       * @description Cartões que atendem aos filtros, em todas as páginas
       */
      total: number;
    };
    /** ListaFontesDTO */
    ListaFontes: {
      /** Itens */
      itens: components["schemas"]["Fonte"][];
    };
    /** ListaMateriasDTO */
    ListaMaterias: {
      /** Itens */
      itens: components["schemas"]["Materia"][];
    };
    /** MateriaDTO */
    Materia: {
      /**
       * Atualizadoem
       * Format: date-time
       */
      atualizadoEm: string;
      /** Cartoesaguardandorevisao */
      cartoesAguardandoRevisao: number;
      /** Cartoesativos */
      cartoesAtivos: number;
      /**
       * Criadoem
       * Format: date-time
       */
      criadoEm: string;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Nome */
      nome: string;
      /** Totalfontes */
      totalFontes: number;
    };
    /** MateriaEntradaDTO */
    MateriaEntrada: {
      /** Nome */
      nome: string;
    };
    /**
     * ModoCartoes
     * @description Escolha do estudante sobre os cartões gerados e aceitos de uma fonte (RN-14).
     * @enum {string}
     */
    ModoCartoes: "manter" | "excluir";
    /**
     * OrigemCartao
     * @enum {string}
     */
    OrigemCartao: "gerado_verificado" | "editado" | "criado";
    /** PerfilDTO */
    Perfil: {
      /**
       * Criadoem
       * Format: date-time
       */
      criadoEm: string;
      /**
       * Email
       * Format: email
       */
      email: string;
      /** Fuso */
      fuso: string;
      /** Limitenovosdia */
      limiteNovosDia: number;
      /** Metadiaria */
      metaDiaria: number;
      /** Nome */
      nome: string;
      /**
       * Papel
       * @enum {string}
       */
      papel: "estudante" | "admin";
      /** Retencaodesejada */
      retencaoDesejada: number;
      /** Tamanholicao */
      tamanhoLicao: number;
    };
    /**
     * PerfilAlteracaoDTO
     * @description Alteração parcial: só os campos enviados mudam (`model_fields_set`); ao menos um.
     *
     *     O domínio impõe os limites (tudo ou nada, todos os erros de uma vez); aqui só se garante
     *     o tipo: inteiros de verdade (sem `"5"`, `5.5` nem `true`) e número JSON finito para a retenção
     *     (sem `"0.9"`).
     */
    PerfilAlteracao: {
      /** Fuso */
      fuso?: string | null;
      /** Limitenovosdia */
      limiteNovosDia?: number | null;
      /** Metadiaria */
      metaDiaria?: number | null;
      /** Nome */
      nome?: string | null;
      /** Retencaodesejada */
      retencaoDesejada?: number | null;
      /** Tamanholicao */
      tamanhoLicao?: number | null;
    };
    /**
     * ReferenciaFonteDTO
     * @description Descrição da origem copiada na criação; não muda com a renomeação nem com a exclusão.
     */
    ReferenciaFonte: {
      /**
       * Enviadaem
       * Format: date-time
       */
      enviadaEm: string;
      /**
       * Fonteapagada
       * @description Exibe "Fonte apagada" junto da descrição (RF-009)
       */
      fonteApagada: boolean;
      /**
       * Fonteid
       * @description Nulo depois que a fonte foi excluída
       */
      fonteId: string | null;
      /** Nomearquivo */
      nomeArquivo: string;
      /** Titulo */
      titulo: string;
    };
    /** RenomeacaoFonteEntradaDTO */
    RenomeacaoFonteEntrada: {
      /** Titulo */
      titulo: string;
    };
    /** Saude */
    Saude: {
      /**
       * Estado
       * @enum {string}
       */
      estado: "ok" | "indisponivel";
      /** Verificacoes */
      verificacoes?: {
        [key: string]: "ok" | "falhou";
      } | null;
    };
    /**
     * SituacaoCartao
     * @enum {string}
     */
    SituacaoCartao: "ativo" | "suspenso";
    /** TrocaSenhaEntradaDTO */
    TrocaSenhaEntrada: {
      /** Novasenha */
      novaSenha: string;
      /** Senhaatual */
      senhaAtual: string;
    };
    /** UsoAcervoDTO */
    UsoAcervo: {
      /** Cotaarmazenamentobytes */
      cotaArmazenamentoBytes: number;
      /** Cotafontespormateria */
      cotaFontesPorMateria: number;
      /** Cotamaterias */
      cotaMaterias: number;
      /** Extensoesaceitas */
      extensoesAceitas: string[];
      /** Paginasmaximaspdf */
      paginasMaximasPdf: number;
      /** Tamanhomaximobytes */
      tamanhoMaximoBytes: number;
      /** Totalmaterias */
      totalMaterias: number;
      /** Usoarmazenamentobytes */
      usoArmazenamentoBytes: number;
    };
    /** ValidationError */
    ValidationError: {
      /** Context */
      ctx?: Record<string, never>;
      /** Input */
      input?: unknown;
      /** Location */
      loc: (string | number)[];
      /** Message */
      msg: string;
      /** Error Type */
      type: string;
    };
  };
  responses: never;
  parameters: never;
  requestBodies: never;
  headers: never;
  pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
  consultarUsoAcervo: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["UsoAcervo"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  cadastrar: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CadastroEntrada"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Perfil"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Too Many Requests */
      429: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  obterTokenCsrf: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
    };
  };
  entrar: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["EntradaEntrada"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Perfil"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Too Many Requests */
      429: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  sair: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  consultarLimitesCartao: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["LimitesCartao"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  consultarCartao: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` do cartão */
        cartaoId: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Cartao"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  excluirCartao: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` do cartão */
        cartaoId: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  editarCartao: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` do cartão */
        cartaoId: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["EdicaoCartaoEntrada"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Cartao"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  reativarCartao: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` do cartão */
        cartaoId: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Cartao"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  suspenderCartao: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` do cartão */
        cartaoId: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Cartao"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  consultarFonte: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` da fonte */
        fonteId: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Fonte"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  renomearFonte: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` da fonte */
        fonteId: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["RenomeacaoFonteEntrada"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Fonte"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  excluirFonte: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` da fonte */
        fonteId: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ExclusaoFonteEntrada"];
      };
    };
    responses: {
      /** @description Successful Response */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  consultarImpactoExclusaoFonte: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` da fonte */
        fonteId: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ImpactoExclusaoFonte"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  reprocessarFonte: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` da fonte */
        fonteId: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      202: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Fonte"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  listarMaterias: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ListaMaterias"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  criarMateria: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["MateriaEntrada"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Materia"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  consultarMateria: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` da matéria */
        materiaId: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Materia"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  renomearMateria: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` da matéria */
        materiaId: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["MateriaEntrada"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Materia"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  listarCartoes: {
    parameters: {
      query?: {
        /** @description `proximoCursor` da página anterior, com os mesmos filtros */
        cursor?: string | null;
        limite?: number;
      };
      header?: never;
      path: {
        /** @description `public_id` da matéria */
        materiaId: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ListaCartoes"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  criarCartao: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` da matéria */
        materiaId: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CriacaoCartaoEntrada"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Cartao"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  excluirMateria: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` da matéria */
        materiaId: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ExclusaoMateriaEntrada"];
      };
    };
    responses: {
      /** @description Successful Response */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  listarFontes: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` da matéria */
        materiaId: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ListaFontes"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  enviarFonte: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` da matéria */
        materiaId: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "multipart/form-data": components["schemas"]["EnvioFonteEntrada"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Fonte"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Content Too Large */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  consultarImpactoExclusaoMateria: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        /** @description `public_id` da matéria */
        materiaId: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ImpactoExclusaoMateria"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Not Found */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  obterPerfil: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Perfil"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  alterarPerfil: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["PerfilAlteracao"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Perfil"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  excluirConta: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ExclusaoContaEntrada"];
      };
    };
    responses: {
      /** @description Successful Response */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Too Many Requests */
      429: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  trocarSenha: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["TrocaSenhaEntrada"];
      };
    };
    responses: {
      /** @description Successful Response */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unauthorized */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Forbidden */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
      /** @description Too Many Requests */
      429: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Erro"];
        };
      };
    };
  };
  verificarProcesso: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Saude"];
        };
      };
    };
  };
  verificarProntidao: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Saude"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Saude"];
        };
      };
    };
  };
}
