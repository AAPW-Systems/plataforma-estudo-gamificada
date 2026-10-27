import { z } from "zod";

import type { LimitesCartao } from "../../api/cartoes";
import { contarCaracteres } from "../../componentes/ui/CampoTextoLongo";
import { formatarNumero } from "./textos";

/**
 * Os limites vêm do servidor (`GET /cartoes/limites`) e a contagem é a mesma dele: code points
 * depois de tirar as pontas em branco (DTEC 036). O servidor continua sendo a autoridade.
 */
export function esquemaCartao(limites: LimitesCartao) {
  const obrigatorio = (maximo: number) =>
    z.string().refine(
      (valor) => {
        const total = contarCaracteres(valor.trim());
        return total >= 1 && total <= maximo;
      },
      `Use de 1 a ${formatarNumero(maximo)} caracteres.`,
    );
  return z.object({
    frente: obrigatorio(limites.frenteMax),
    verso: obrigatorio(limites.versoMax),
    explicacao: z
      .string()
      .refine(
        (valor) => contarCaracteres(valor.trim()) <= limites.explicacaoMax,
        `Use até ${formatarNumero(limites.explicacaoMax)} caracteres.`,
      ),
    fonteId: z.string(),
  });
}

export type DadosCartao = z.infer<ReturnType<typeof esquemaCartao>>;

export const CARTAO_VAZIO: DadosCartao = { frente: "", verso: "", explicacao: "", fonteId: "" };
