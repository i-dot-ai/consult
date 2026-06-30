import { defineConfig } from "astro/config";
import svelte from "@astrojs/svelte";

import tailwindcss from "@tailwindcss/vite";
import node from "@astrojs/node";

import sentry from "@sentry/astro";

// https://astro.build/config
export default defineConfig({
  output: "server",
  security: {
    checkOrigin: false,
  },
  integrations: [
    svelte(),
    sentry({
      project: "consult-frontend",
      org: "incubator-for-ai",
      authToken: process.env.SENTRY_AUTH_TOKEN,
    }),
  ],

  vite: {
    optimizeDeps: {
      // svelte/elements is a types-only export, exclude from dependency scanning
      exclude: ["svelte/elements"],
    },
    server: {
      hmr: {
        host: "0.0.0.0",
        clientPort: 3000,
      },
    },
    plugins: [tailwindcss() as never],
  },

  image: {
    service: {
      entrypoint: "astro/assets/services/sharp",
    },
  },

  server: {
    host: "0.0.0.0",
    port: 3000,
  },

  adapter: node({
    mode: "standalone",
  }),
});
