import { defineConfig } from "astro/config";
import svelte from "@astrojs/svelte";

import tailwindcss from "@tailwindcss/vite";
import node from "@astrojs/node";

import sentry from "@sentry/astro";

// https://astro.build/config
export default defineConfig({
  output: "server",
  security: {
    // Disable origin check from astro v6+ due to issues with django admin passthrough
    // Django itself contains CSRF which should make this moot when combined with our infra setup
    checkOrigin: false,
    csp: {
      // Omit script-src/style-src here: Astro injects them with per-build hashes,
      // and listing them drops the hashes.
      directives: [
        "default-src 'self'",
        "img-src 'self' data:",
        "font-src 'self' data:",
        "connect-src 'self' *.ingest.de.sentry.io",
      ],
    },
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

  // Shiki emits inline styles the CSP rejects.
  markdown: {
    syntaxHighlight: false,
  },

  server: {
    host: "0.0.0.0",
    port: 3000,
  },

  adapter: node({
    mode: "standalone",
  }),
});
