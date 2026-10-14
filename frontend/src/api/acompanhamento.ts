/**
 * Acompanhamento de processamentos assíncronos por polling condicional (DTEC 026).
 *
 * A consulta da lista se repete a cada `INTERVALO_ACOMPANHAMENTO_MS` somente enquanto algum
 * item está num estado não final; quando todos chegam a um estado final, ela para sozinha. O
 * TanStack Query também consulta ao voltar o foco à aba (`refetchOnWindowFocus`, padrão).
 */
export const INTERVALO_ACOMPANHAMENTO_MS = 2000;

export const ESTADOS_NAO_FINAIS = ["pendente", "processando"] as const;

/** Valor de `refetchInterval` para uma lista de itens com `estado`. */
export function intervaloDeAcompanhamento(
  itens: readonly { estado: string }[] | undefined,
): number | false {
  const emAndamento = itens?.some((item) =>
    (ESTADOS_NAO_FINAIS as readonly string[]).includes(item.estado),
  );
  return emAndamento ? INTERVALO_ACOMPANHAMENTO_MS : false;
}
