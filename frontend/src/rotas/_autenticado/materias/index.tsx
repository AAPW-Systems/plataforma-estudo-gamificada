import { useQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";

import { consultaMaterias } from "../../../api/acervo";
import { FormularioMateria } from "../../../funcionalidades/materias/FormularioMateria";
import { ListaMaterias } from "../../../funcionalidades/materias/ListaMaterias";

export const Route = createFileRoute("/_autenticado/materias/")({ component: Materias });

/** Lista de matérias e criação (design 9.3). */
function Materias() {
  const { data: materias, isPending, isError } = useQuery(consultaMaterias);
  const navegar = useNavigate();
  return (
    <main className="pagina pagina-estreita">
      <h1>Matérias</h1>
      {isPending && <p>Carregando as matérias…</p>}
      {isError && (
        <p role="alert" className="erro-formulario">
          Não foi possível carregar as matérias. Tente novamente.
        </p>
      )}
      {materias && <ListaMaterias materias={materias} />}
      {materias && (
        <section aria-labelledby="titulo-nova-materia" className="secao-perfil">
          <h2 id="titulo-nova-materia">Nova matéria</h2>
          <FormularioMateria
            primeira={materias.length === 0}
            aoCriar={(materia) => {
              void navegar({ to: "/materias/$materiaId", params: { materiaId: materia.id } });
            }}
          />
        </section>
      )}
    </main>
  );
}
