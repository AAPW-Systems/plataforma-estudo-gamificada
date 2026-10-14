// Gerado de backend/openapi.json. Não editar.
export const limites = {
  CadastroEntrada: {
    email: { maxLength: 254 },
    fuso: { maxLength: 64 },
    nome: { maxLength: 100, minLength: 1 },
    senha: { maxLength: 128, minLength: 8 },
  },
  EntradaEntrada: {
    email: { maxLength: 254 },
    senha: { maxLength: 128, minLength: 1 },
  },
  ExclusaoContaEntrada: { senhaAtual: { maxLength: 128, minLength: 1 } },
  PerfilAlteracao: {
    fuso: { maxLength: 64 },
    limiteNovosDia: { maximum: 100, minimum: 0 },
    metaDiaria: { maximum: 200, minimum: 1 },
    nome: { maxLength: 100, minLength: 1 },
    retencaoDesejada: { maximum: 0.97, minimum: 0.7, multipleOf: 0.01 },
    tamanhoLicao: { maximum: 50, minimum: 5 },
  },
  TrocaSenhaEntrada: {
    novaSenha: { maxLength: 128, minLength: 8 },
    senhaAtual: { maxLength: 128, minLength: 1 },
  },
} as const;
