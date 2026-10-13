import "./estilos/global.css";

import { RouterProvider } from "@tanstack/react-router";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { criarRoteador } from "./roteador";

const roteador = criarRoteador();

const elemento = document.getElementById("raiz");
if (!elemento) throw new Error("Elemento #raiz ausente no index.html.");

createRoot(elemento).render(
  <StrictMode>
    <RouterProvider router={roteador} />
  </StrictMode>,
);
