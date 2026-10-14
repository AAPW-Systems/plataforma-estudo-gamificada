import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { consultaPerfil } from "../../api/perfil";
import { FormularioPerfil } from "../../funcionalidades/identidade/FormularioPerfil";

export const Route = createFileRoute("/_autenticado/perfil")({ component: Perfil });

/** Perfil e preferências de ritmo (design, 9.11). Depois de salvar, a consulta é invalidada. */
function Perfil() {
  const { queryClient } = Route.useRouteContext();
  const { data: perfil } = useQuery({ ...consultaPerfil, staleTime: Infinity });
  return (
    <main className="pagina pagina-estreita">
      <h1>Perfil</h1>
      {perfil ? (
        <FormularioPerfil
          perfil={perfil}
          aoSalvar={() => {
            void queryClient.invalidateQueries({ queryKey: consultaPerfil.queryKey });
          }}
        />
      ) : (
        <p>Carregando o perfil…</p>
      )}
    </main>
  );
}
