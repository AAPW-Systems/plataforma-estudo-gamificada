import { defineConfig, mergeConfig } from "vitest/config";

import viteConfig from "./vite.config";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      environmentOptions: { jsdom: { url: "https://teste" } },
      setupFiles: ["./src/testes/configuracao.ts"],
      include: ["src/**/*.test.{ts,tsx}"],
      restoreMocks: true,
      coverage: {
        provider: "v8",
        include: ["src/**/*.{ts,tsx}"],
        exclude: [
          "src/**/*.test.{ts,tsx}",
          "src/**/*.gerado.*",
          "src/routeTree.gen.ts",
          "src/testes/**",
        ],
      },
    },
  }),
);
