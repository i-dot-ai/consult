import { defineConfig } from "astro/config";
import svelte from "@astrojs/svelte";

import tailwind from "@astrojs/tailwind";
import node from "@astrojs/node";

// https://astro.build/config
export default defineConfig({
  output: "server",
  integrations: [svelte(), tailwind({ applyBaseStyles: false })],

  vite: {
    optimizeDeps: {
      // svelte/elements is a types-only export, exclude from dependency scanning
      exclude: ["svelte/elements"],
    },
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
