import "./estilos/global.css";

import { RouterProvider, createRouter } from "@tanstack/react-router";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { routeTree } from "./routeTree.gen";

const roteador = createRouter({ routeTree, defaultPreload: "intent" });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof roteador;
  }
}

const elemento = document.getElementById("raiz");
if (!elemento) throw new Error("Elemento #raiz ausente no index.html.");

createRoot(elemento).render(
  <StrictMode>
    <RouterProvider router={roteador} />
  </StrictMode>,
);
