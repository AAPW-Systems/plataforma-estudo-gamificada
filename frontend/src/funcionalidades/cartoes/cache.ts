import type { InfiniteData, QueryClient } from "@tanstack/react-query";

import { chaves } from "../../api/acervo";
import { type Cartao, type ListaCartoes, chavesCartoes } from "../../api/cartoes";

function alterarPaginas(
  queryClient: QueryClient,
  materiaId: string,
  alterar: (itens: Cartao[]) => Cartao[],
) {
  queryClient.setQueryData<InfiniteData<ListaCartoes>>(chavesCartoes.lista(materiaId), (dados) =>
    dados
      ? {
          ...dados,
          pages: dados.pages.map((pagina) => ({ ...pagina, itens: alterar(pagina.itens) })),
        }
      : dados,
  );
}

/** Troca o cartão nas páginas já carregadas, sem esperar a lista voltar da rede. */
export function substituirNaLista(queryClient: QueryClient, materiaId: string, novo: Cartao) {
  alterarPaginas(queryClient, materiaId, (itens) =>
    itens.map((item) => (item.id === novo.id ? novo : item)),
  );
}

/** Tira o cartão das páginas carregadas; o total volta certo com a lista invalidada. */
export function removerDaLista(queryClient: QueryClient, materiaId: string, cartaoId: string) {
  alterarPaginas(queryClient, materiaId, (itens) => itens.filter((item) => item.id !== cartaoId));
}

/** A lista de cartões e as contagens de cartões ativos das matérias. */
export async function invalidarCartoesEMaterias(queryClient: QueryClient, materiaId: string) {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: chavesCartoes.lista(materiaId) }),
    queryClient.invalidateQueries({ queryKey: chaves.materias }),
  ]);
}
