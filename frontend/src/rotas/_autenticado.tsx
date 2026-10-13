import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";

import { ErroApi } from "../api/erros";
import { consultaPerfil } from "../api/perfil";

export const Route = createFileRoute("/_autenticado")({
  beforeLoad: async ({ context }) => {
    try {
      await context.queryClient.query(consultaPerfil);
    } catch (erro) {
      if (erro instanceof ErroApi && erro.status === 401) return redirect({ to: "/entrar" });
      throw erro;
    }
    return undefined;
  },
  component: Outlet,
  errorComponent: ({ reset }) => (
    <main role="alert">
      <p>Não foi possível carregar seus estudos.</p>
      <button onClick={reset}>Tentar novamente</button>
    </main>
  ),
});
