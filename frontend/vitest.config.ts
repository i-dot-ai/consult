import { getViteConfig } from "astro/config";
import { coverageConfigDefaults } from "vitest/config";

export default getViteConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["vitest-setup.ts"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,svelte}"],
      exclude: coverageConfigDefaults.exclude,
    },
    globals: true,
  },
  resolve: process.env.VITEST ? { conditions: ["browser"] } : undefined,
});
