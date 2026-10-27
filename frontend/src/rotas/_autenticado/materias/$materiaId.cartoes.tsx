import { createFileRoute } from "@tanstack/react-router";

import { AbaCartoes } from "../../../funcionalidades/cartoes/AbaCartoes";

export const Route = createFileRoute("/_autenticado/materias/$materiaId/cartoes")({
  component: AbaDosCartoes,
});

function AbaDosCartoes() {
  const { materiaId } = Route.useParams();
  return <AbaCartoes materiaId={materiaId} />;
}
