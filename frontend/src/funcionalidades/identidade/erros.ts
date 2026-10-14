import type { FieldValues, Path, UseFormReturn } from "react-hook-form";

import { ErroApi } from "../../api/erros";

export const MENSAGEM_FALHA_GENERICA = "Não foi possível concluir a operação. Tente novamente.";

/**
 * Distribui um erro da API pelo formulário: erros de campo ficam junto do campo (com foco no
 * primeiro) e qualquer outro vira uma mensagem do formulário. Devolve essa mensagem, se houver.
 */
export function aplicarErroDaApi<Campos extends FieldValues>(
  erro: unknown,
  formulario: Pick<UseFormReturn<Campos>, "setError" | "setFocus">,
  campos: readonly Path<Campos>[],
): string | undefined {
  if (!(erro instanceof ErroApi)) return MENSAGEM_FALHA_GENERICA;
  const conhecidos = erro.campos.filter((item): item is { campo: Path<Campos>; mensagem: string } =>
    (campos as readonly string[]).includes(item.campo),
  );
  const primeiro = conhecidos[0];
  if (!primeiro) return erro.message;
  for (const item of conhecidos) {
    formulario.setError(item.campo, { type: "servidor", message: item.mensagem });
  }
  formulario.setFocus(primeiro.campo);
  return undefined;
}
