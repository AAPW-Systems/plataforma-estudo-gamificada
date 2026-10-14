import { QueryClient } from "@tanstack/react-query";
import { createRouter, type RouterHistory } from "@tanstack/react-router";

import { definirTratadorNaoAutenticado } from "./api/cliente";
import { routeTree } from "./routeTree.gen";

export function criarRoteador(history?: RouterHistory) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const roteador = createRouter({
    routeTree,
    context: { queryClient },
    defaultPreload: "intent",
    ...(history ? { history } : {}),
  });
  // Sessão encerrada no servidor (expirou, saída em outra aba): nada do estudante fica no cache.
  definirTratadorNaoAutenticado(() => {
    queryClient.clear();
    void roteador.navigate({ to: "/entrar" });
  });
  return roteador;
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof criarRoteador>;
  }
}
