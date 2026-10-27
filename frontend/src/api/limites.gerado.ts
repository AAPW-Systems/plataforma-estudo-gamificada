// Gerado de backend/openapi.json. Não editar.
export const limites = {
  CadastroEntrada: {
    email: { maxLength: 254 },
    fuso: { maxLength: 64 },
    nome: { maxLength: 100, minLength: 1 },
    senha: { maxLength: 128, minLength: 8 },
  },
  ContagensExclusaoFonte: {
    cartoesAguardandoRevisao: { minimum: 0 },
    cartoesGeradosAceitos: { minimum: 0 },
    cartoesReferencia: { minimum: 0 },
  },
  ContagensExclusaoMateria: {
    cartoesAguardandoRevisao: { minimum: 0 },
    cartoesAtivos: { minimum: 0 },
    fontes: { minimum: 0 },
  },
  CriacaoCartaoEntrada: {
    frente: { maxLength: 4000 },
    verso: { maxLength: 8000 },
  },
  EdicaoCartaoEntrada: {
    frente: { maxLength: 4000 },
    verso: { maxLength: 8000 },
  },
  EntradaEntrada: {
    email: { maxLength: 254 },
    senha: { maxLength: 128, minLength: 1 },
  },
  EnvioFonteEntrada: { titulo: { maxLength: 120, minLength: 1 } },
  ExclusaoContaEntrada: { senhaAtual: { maxLength: 128, minLength: 1 } },
  ExclusaoMateriaEntrada: { nomeConfirmacao: { maxLength: 60, minLength: 1 } },
  Fonte: { tamanhoBytes: { minimum: 1 } },
  LimitesCartao: {
    buscaMax: { maximum: 100, minimum: 100 },
    explicacaoMax: { maximum: 4000, minimum: 1 },
    frenteMax: { maximum: 4000, minimum: 1 },
    versoMax: { maximum: 8000, minimum: 1 },
  },
  ListaCartoes: { total: { minimum: 0 } },
  Materia: {
    cartoesAguardandoRevisao: { minimum: 0 },
    cartoesAtivos: { minimum: 0 },
    totalFontes: { minimum: 0 },
  },
  MateriaEntrada: { nome: { maxLength: 60, minLength: 1 } },
  PerfilAlteracao: {
    fuso: { maxLength: 64 },
    limiteNovosDia: { maximum: 100, minimum: 0 },
    metaDiaria: { maximum: 200, minimum: 1 },
    nome: { maxLength: 100, minLength: 1 },
    retencaoDesejada: { maximum: 0.97, minimum: 0.7, multipleOf: 0.01 },
    tamanhoLicao: { maximum: 50, minimum: 5 },
  },
  RenomeacaoFonteEntrada: { titulo: { maxLength: 120, minLength: 1 } },
  TrocaSenhaEntrada: {
    novaSenha: { maxLength: 128, minLength: 8 },
    senhaAtual: { maxLength: 128, minLength: 1 },
  },
  UsoAcervo: {
    totalMaterias: { minimum: 0 },
    usoArmazenamentoBytes: { minimum: 0 },
  },
} as const;
