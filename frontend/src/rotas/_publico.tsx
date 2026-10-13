import { Outlet, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_publico")({ component: Outlet });
