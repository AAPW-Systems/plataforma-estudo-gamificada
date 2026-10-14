import { useQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";

import { consultaPerfil } from "../../api/perfil";
import { DialogoExclusao } from "../../funcionalidades/identidade/DialogoExclusao";
import { FormularioPerfil } from "../../funcionalidades/identidade/FormularioPerfil";
import { FormularioSenha } from "../../funcionalidades/identidade/FormularioSenha";

export const Route = createFileRoute("/_autenticado/perfil")({ component: Perfil });

/** Perfil e preferências de ritmo (design, 9.11). Depois de salvar, a consulta é invalidada. */
function Perfil() {
  const { queryClient } = Route.useRouteContext();
  const { data: perfil } = useQuery({ ...consultaPerfil, staleTime: Infinity });
  const navegar = useNavigate();
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
      <section aria-labelledby="titulo-seguranca" className="secao-perfil">
        <h2 id="titulo-seguranca">Segurança</h2>
        <FormularioSenha aoTrocar={() => undefined} />
      </section>
      <section aria-labelledby="titulo-exclusao" className="secao-perfil">
        <h2 id="titulo-exclusao">Excluir conta</h2>
        <p>Apaga todos os seus dados, de forma definitiva. Você precisa confirmar com a senha.</p>
        <DialogoExclusao
          aoExcluir={() => {
            // Nada da conta fica no navegador: o cache é limpo e a pessoa volta ao cadastro.
            queryClient.clear();
            void navegar({ to: "/cadastro" });
          }}
        />
      </section>
    </main>
  );
}
