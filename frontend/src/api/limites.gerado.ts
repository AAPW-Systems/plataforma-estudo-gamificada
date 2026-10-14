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
} as const;
