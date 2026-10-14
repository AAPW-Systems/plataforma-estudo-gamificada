import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";

import { consultaPerfil } from "../../api/perfil";
import { FormularioCadastro } from "../../funcionalidades/identidade/FormularioCadastro";
import { LayoutAutenticacao } from "../../funcionalidades/identidade/LayoutAutenticacao";

export const Route = createFileRoute("/_publico/cadastro")({ component: Cadastro });

function Cadastro() {
  const { queryClient } = Route.useRouteContext();
  const navegar = useNavigate();
  return (
    <LayoutAutenticacao titulo="Criar conta">
      <FormularioCadastro
        aoConcluir={(perfil) => {
          queryClient.setQueryData(consultaPerfil.queryKey, perfil);
          void navegar({ to: "/" });
        }}
      />
      <p>
        <Link to="/entrar">Já tenho conta</Link>
      </p>
    </LayoutAutenticacao>
  );
}
