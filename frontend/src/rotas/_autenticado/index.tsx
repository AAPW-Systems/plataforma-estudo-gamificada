import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_autenticado/")({
  component: () => (
    <main>
      <h1>Seus estudos</h1>
    </main>
  ),
});
