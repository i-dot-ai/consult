/// <reference types="vitest" />
import { getViteConfig } from "astro/config";
import { coverageConfigDefaults } from "vitest/config";

export default getViteConfig({
  test: {
    environment: "jsdom",
    coverage: {
      provider: "v8",
      exclude: [
        "**/astro.config.mjs",
        "**/svelte.config.js",
        "**/tailwind.config.mjs",
        "**/pages/**",
        "**/layouts/**",
        ...coverageConfigDefaults.exclude,
      ],
    },
    globals: true,
  },
  resolve: process.env.VITEST ? { conditions: ["browser"] } : undefined,
});
