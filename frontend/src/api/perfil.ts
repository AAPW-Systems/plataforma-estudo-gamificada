import { queryOptions } from "@tanstack/react-query";

import { cliente } from "./cliente";

/**
 * Perfil do estudante autenticado. Também decide se há sessão válida: sem ela, o middleware
 * do cliente lança `ErroApi` com `status` 401 e o roteador redireciona para a entrada.
 */
export const consultaPerfil = queryOptions({
  queryKey: ["perfil"],
  queryFn: async () => {
    const { data } = await cliente.GET("/api/v1/perfil");
    if (!data) throw new Error("A API respondeu sem o perfil.");
    return data;
  },
  retry: false,
  staleTime: 0,
});
