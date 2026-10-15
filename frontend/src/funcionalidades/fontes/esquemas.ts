import { z } from "zod";

import { limites } from "../../api/limites.gerado";

const { titulo: limiteTitulo } = limites.RenomeacaoFonteEntrada;

/** O limite vem do contrato; o servidor continua sendo a autoridade (normaliza e recusa). */
export const esquemaTituloFonte = z.object({
  titulo: z
    .string()
    .trim()
    .min(limiteTitulo.minLength, "Informe o título da fonte.")
    .max(limiteTitulo.maxLength, `Use no máximo ${String(limiteTitulo.maxLength)} caracteres.`),
});
