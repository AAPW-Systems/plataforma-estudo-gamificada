import { z } from "zod";

import { limites } from "../../api/limites.gerado";

const { nome: limiteNome } = limites.MateriaEntrada;

/** O limite vem do contrato; o servidor continua sendo a autoridade (normaliza e recusa duplicados). */
export const esquemaMateria = z.object({
  nome: z
    .string()
    .trim()
    .min(limiteNome.minLength, "Informe o nome da matéria.")
    .max(limiteNome.maxLength, `Use no máximo ${String(limiteNome.maxLength)} caracteres.`),
});

export type DadosMateria = z.infer<typeof esquemaMateria>;
