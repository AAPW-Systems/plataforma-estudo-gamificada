export interface paths {
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
      | "erro_interno";
    /** EntradaEntradaDTO */
    EntradaEntrada: {
      /** Email */
      email: string;
      /** Senha */
      senha: string;
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
    /** ExclusaoContaEntradaDTO */
    ExclusaoContaEntrada: {
      /** Senhaatual */
      senhaAtual: string;
    };
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
    /** TrocaSenhaEntradaDTO */
    TrocaSenhaEntrada: {
      /** Novasenha */
      novaSenha: string;
      /** Senhaatual */
      senhaAtual: string;
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
