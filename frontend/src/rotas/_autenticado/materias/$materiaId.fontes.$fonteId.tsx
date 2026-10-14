import { createFileRoute, useNavigate } from "@tanstack/react-router";

import { PainelFonte } from "../../../funcionalidades/fontes/PainelFonte";

export const Route = createFileRoute("/_autenticado/materias/$materiaId/fontes/$fonteId")({
  component: PainelDaFonte,
});

function PainelDaFonte() {
  const { materiaId, fonteId } = Route.useParams();
  const navegar = useNavigate();
  return (
    <PainelFonte
      fonteId={fonteId}
      aoFechar={() => {
        void navegar({ to: "/materias/$materiaId", params: { materiaId } });
      }}
    />
  );
}
