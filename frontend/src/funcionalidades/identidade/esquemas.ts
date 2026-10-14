import { z } from "zod";

import { limites } from "../../api/limites.gerado";

/**
 * Esquemas dos formulários de identidade. Os limites vêm do contrato (`limites.gerado.ts`),
 * nunca de números soltos. O servidor continua sendo a autoridade: ele também recusa senhas
 * comuns e normaliza nome e e-mail.
 */
const { CadastroEntrada: cadastro, EntradaEntrada: entrada } = limites;

const nome = z
  .string()
  .trim()
  .min(cadastro.nome.minLength, "Informe o nome.")
  .max(cadastro.nome.maxLength, `Use no máximo ${String(cadastro.nome.maxLength)} caracteres.`);

const email = (maximo: number) =>
  z
    .string()
    .trim()
    .min(1, "Informe o e-mail.")
    .max(maximo, "Informe um e-mail válido.")
    .pipe(z.email("Informe um e-mail válido."));

export const esquemaCadastro = z.object({
  nome,
  email: email(cadastro.email.maxLength),
  senha: z
    .string()
    .min(1, "Informe a senha.")
    .min(cadastro.senha.minLength, `Use pelo menos ${String(cadastro.senha.minLength)} caracteres.`)
    .max(cadastro.senha.maxLength, `Use no máximo ${String(cadastro.senha.maxLength)} caracteres.`),
});

export const esquemaEntrada = z.object({
  email: email(entrada.email.maxLength),
  senha: z
    .string()
    .min(entrada.senha.minLength, "Informe a senha.")
    .max(entrada.senha.maxLength, "E-mail ou senha incorretos."),
});

export type DadosCadastro = z.infer<typeof esquemaCadastro>;
export type DadosEntrada = z.infer<typeof esquemaEntrada>;
