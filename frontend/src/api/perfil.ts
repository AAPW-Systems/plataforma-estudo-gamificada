import { queryOptions } from "@tanstack/react-query";

import { lerErro } from "./erros";

// A T037 substitui a leitura pelo cliente tipado quando a T036 exportar /perfil.
export const consultaPerfil = queryOptions({
  queryKey: ["perfil"],
  queryFn: async (): Promise<unknown> => {
    const resposta = await fetch(`${window.location.origin}/api/v1/perfil`, {
      credentials: "same-origin",
    });
    if (!resposta.ok) throw await lerErro(resposta);
    return resposta.json() as Promise<unknown>;
  },
  retry: false,
  staleTime: 0,
});
