import { RouterProvider, createMemoryHistory } from "@tanstack/react-router";
import { render } from "@testing-library/react";

import { criarRoteador } from "../roteador";

export function renderizarComRoteador(caminho = "/") {
  const roteador = criarRoteador(createMemoryHistory({ initialEntries: [caminho] }));
  return { ...render(<RouterProvider router={roteador} />), roteador };
}
