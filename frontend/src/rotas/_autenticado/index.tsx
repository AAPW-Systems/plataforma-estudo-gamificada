import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { consultaPerfil } from "../../api/perfil";

export const Route = createFileRoute("/_autenticado/")({ component: Trilha });

/** A trilha chega com a spec 005; até lá, o estado vazio explica o que falta. */
function Trilha() {
  const { data: perfil } = useQuery({ ...consultaPerfil, staleTime: Infinity });
  return (
    <main className="pagina">
      <h1>Seus estudos</h1>
      {perfil && <p>Olá, {perfil.nome}.</p>}
      <p>
        Você ainda não tem cartões para revisar. Quando criar matérias e cartões, a sua trilha de
        lições aparece aqui.
      </p>
    </main>
  );
}
