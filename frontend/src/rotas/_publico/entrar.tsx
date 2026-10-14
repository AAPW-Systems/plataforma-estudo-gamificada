import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";

import { consultaPerfil } from "../../api/perfil";
import { FormularioEntrada } from "../../funcionalidades/identidade/FormularioEntrada";
import { LayoutAutenticacao } from "../../funcionalidades/identidade/LayoutAutenticacao";

export const Route = createFileRoute("/_publico/entrar")({ component: Entrar });

function Entrar() {
  const { queryClient } = Route.useRouteContext();
  const navegar = useNavigate();
  return (
    <LayoutAutenticacao titulo="Entrar">
      <FormularioEntrada
        aoConcluir={(perfil) => {
          queryClient.setQueryData(consultaPerfil.queryKey, perfil);
          void navegar({ to: "/" });
        }}
      />
      <p>
        Ainda não tem conta? <Link to="/cadastro">Criar conta</Link>
      </p>
    </LayoutAutenticacao>
  );
}
