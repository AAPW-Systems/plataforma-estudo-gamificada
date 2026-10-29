import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useMemo } from "react";

import type { FiltrosCartoes } from "../../../api/cartoes";
import { AbaCartoes } from "../../../funcionalidades/cartoes/AbaCartoes";
import {
  type MudancaFiltros,
  combinarFiltros,
  validarFiltros,
} from "../../../funcionalidades/cartoes/filtros";

/** Busca e filtros ficam na URL, validados: sobrevivem ao recarregar e ao Voltar (US4). */
export const Route = createFileRoute("/_autenticado/materias/$materiaId/cartoes")({
  validateSearch: (parametros: Record<string, unknown>): FiltrosCartoes =>
    validarFiltros(parametros),
  component: AbaDosCartoes,
});

function AbaDosCartoes() {
  const { materiaId } = Route.useParams();
  // De novo aqui: os parâmetros que a validação descarta (ex.: `origem=xpto`) continuam no
  // objeto da busca que o roteador entrega, herdados da URL bruta.
  const bruto = Route.useSearch();
  const filtros = useMemo(() => validarFiltros(bruto as Record<string, unknown>), [bruto]);
  const navegar = Route.useNavigate();
  const aoMudarFiltros = useCallback(
    (mudanca: MudancaFiltros) => {
      // Sobre a busca mais recente da URL, não a desta renderização: duas mudanças seguidas,
      // antes de a navegação terminar, não desfazem uma à outra. Trocar a busca não empilha uma
      // entrada por tecla no histórico.
      void navegar({
        search: (anterior) =>
          combinarFiltros(validarFiltros(anterior as Record<string, unknown>), mudanca),
        replace: true,
      });
    },
    [navegar],
  );
  return <AbaCartoes materiaId={materiaId} filtros={filtros} aoMudarFiltros={aoMudarFiltros} />;
}
