// @ts-check
import { defineConfig } from 'astro/config';
import svelte from "@astrojs/svelte";

import tailwind from "@astrojs/tailwind";
import node from "@astrojs/node";

// https://astro.build/config
export default defineConfig({
  output: "server",
  integrations: [svelte(), tailwind({ applyBaseStyles: false })],

  server: {
    host: "0.0.0.0",
    port: 3000,
  },

  adapter: node({
    mode: "standalone",
  }),
});
