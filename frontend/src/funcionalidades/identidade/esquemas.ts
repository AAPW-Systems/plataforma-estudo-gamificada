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

const alteravel = limites.PerfilAlteracao;

const inteiroNoLimite = (limite: { minimum: number; maximum: number }) => {
  const mensagem = `Use um valor de ${String(limite.minimum)} a ${String(limite.maximum)}.`;
  return z
    .number({ error: "Informe um número." })
    .int(mensagem)
    .min(limite.minimum, mensagem)
    .max(limite.maximum, mensagem);
};

const formatarDecimal = (valor: number) => valor.toFixed(2).replace(".", ",");

export const MENSAGEM_RETENCAO = `Use um valor de ${formatarDecimal(alteravel.retencaoDesejada.minimum)} a ${formatarDecimal(alteravel.retencaoDesejada.maximum)}, com no máximo duas casas decimais.`;

/** Lê "0,85" ou "0.85" como 0.85; `undefined` se não for um número com até duas casas. */
export function lerRetencao(texto: string): number | undefined {
  const normalizado = texto.trim().replace(",", ".");
  if (!/^\d+(\.\d{1,2})?$/.test(normalizado)) return undefined;
  const valor = Number(normalizado);
  const { minimum, maximum } = alteravel.retencaoDesejada;
  return valor >= minimum && valor <= maximum ? valor : undefined;
}

export const esquemaPerfil = z.object({
  nome: z
    .string()
    .trim()
    .min(alteravel.nome.minLength, "Informe o nome.")
    .max(alteravel.nome.maxLength, `Use no máximo ${String(alteravel.nome.maxLength)} caracteres.`),
  fuso: z
    .string()
    .trim()
    .min(1, "Informe o fuso.")
    .max(alteravel.fuso.maxLength, "Fuso desconhecido."),
  metaDiaria: inteiroNoLimite(alteravel.metaDiaria),
  tamanhoLicao: inteiroNoLimite(alteravel.tamanhoLicao),
  limiteNovosDia: inteiroNoLimite(alteravel.limiteNovosDia),
  retencaoDesejada: z
    .string()
    .refine((texto) => lerRetencao(texto) !== undefined, { error: MENSAGEM_RETENCAO }),
});

export type DadosPerfil = z.infer<typeof esquemaPerfil>;
