import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_publico/entrar")({
  component: () => (
    <main>
      <h1>Entrar</h1>
    </main>
  ),
});
