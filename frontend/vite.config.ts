import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Em desenvolvimento, o Vite encaminha /api para a API: mesma origem, cookies do mesmo site
// e nenhum CORS (plano da 001, "Contêineres"). No Compose, a API responde em http://api:8000.
const destinoApi = process.env.VITE_DESTINO_API ?? "http://api:8000";

export default defineConfig({
  plugins: [
    tanstackRouter({
      target: "react",
      routesDirectory: "./src/rotas",
      generatedRouteTree: "./src/routeTree.gen.ts",
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: destinoApi,
        // xfwd envia X-Forwarded-For; a API só o aceita de proxies confiáveis (DTEC 020).
        xfwd: true,
      },
    },
  },
  build: {
    sourcemap: true,
    target: "es2023",
  },
});
