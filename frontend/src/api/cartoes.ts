import { infiniteQueryOptions, queryOptions } from "@tanstack/react-query";

import { chaves as chavesAcervo } from "./acervo";
import { cliente } from "./cliente";
import type { components } from "./esquema.gerado";

export type Cartao = components["schemas"]["Cartao"];
export type LimitesCartao = components["schemas"]["LimitesCartao"];
export type ListaCartoes = components["schemas"]["ListaCartoes"];
export type CriacaoCartao = components["schemas"]["CriacaoCartaoEntrada"];
export type EdicaoCartao = components["schemas"]["EdicaoCartaoEntrada"];
export type SituacaoCartao = components["schemas"]["SituacaoCartao"];
export type OrigemCartao = components["schemas"]["OrigemCartao"];

/** Busca e filtros da lista (US4); ausentes valem como "todos". */
export interface FiltrosCartoes {
  busca?: string;
  situacao?: SituacaoCartao;
  origem?: OrigemCartao;
}

/** A lista de cartões fica sob a chave da matéria: invalidar a matéria a inclui. */
export const chavesCartoes = {
  limites: ["cartoes", "limites"] as const,
  lista: (materiaId: string) => [...chavesAcervo.materia(materiaId), "cartoes"] as const,
};

function exigir<T>(dados: T | undefined): T {
  if (dados === undefined) throw new Error("A API respondeu sem corpo.");
  return dados;
}

/** Limites vigentes no ambiente (D-004): a tela nunca fixa números. */
export const consultaLimitesCartao = queryOptions({
  queryKey: chavesCartoes.limites,
  queryFn: async () => exigir((await cliente.GET("/api/v1/cartoes/limites")).data),
});

/**
 * Páginas da lista, por cursor (DTEC 034); "Carregar mais" pede a próxima. Cada combinação de
 * filtros tem a sua entrada no cache, sob a chave da lista: invalidar a lista invalida todas.
 */
export const consultaCartoes = (materiaId: string, filtros: FiltrosCartoes = {}) =>
  infiniteQueryOptions({
    queryKey: [...chavesCartoes.lista(materiaId), filtros] as const,
    queryFn: async ({ pageParam }) =>
      exigir(
        (
          await cliente.GET("/api/v1/materias/{materiaId}/cartoes", {
            params: {
              path: { materiaId },
              query: { ...filtros, ...(pageParam ? { cursor: pageParam } : {}) },
            },
          })
        ).data,
      ),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (pagina) => pagina.proximoCursor ?? undefined,
  });

export async function criarCartao(materiaId: string, corpo: CriacaoCartao): Promise<Cartao> {
  const { data } = await cliente.POST("/api/v1/materias/{materiaId}/cartoes", {
    params: { path: { materiaId } },
    body: corpo,
  });
  return exigir(data);
}

/** Envia só os campos alterados; o agendamento não muda (RF-005). */
export async function editarCartao(cartaoId: string, corpo: EdicaoCartao): Promise<Cartao> {
  const { data } = await cliente.PATCH("/api/v1/cartoes/{cartaoId}", {
    params: { path: { cartaoId } },
    body: corpo,
  });
  return exigir(data);
}

/** Idempotente: num cartão já suspenso, devolve o mesmo cartão (RF-007). */
export async function suspenderCartao(cartaoId: string): Promise<Cartao> {
  const { data } = await cliente.POST("/api/v1/cartoes/{cartaoId}/suspensao", {
    params: { path: { cartaoId } },
  });
  return exigir(data);
}

/** Idempotente: o cartão volta com o vencimento de antes da suspensão (RF-007). */
export async function reativarCartao(cartaoId: string): Promise<Cartao> {
  const { data } = await cliente.POST("/api/v1/cartoes/{cartaoId}/reativacao", {
    params: { path: { cartaoId } },
  });
  return exigir(data);
}

/** Exclusão definitiva (RF-008); a confirmação é feita antes, no diálogo. */
export async function excluirCartao(cartaoId: string): Promise<void> {
  await cliente.DELETE("/api/v1/cartoes/{cartaoId}", { params: { path: { cartaoId } } });
}
