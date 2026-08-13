import { getViteConfig } from "astro/config";
import { coverageConfigDefaults, mergeConfig } from "vitest/config";

const astroViteConfig = getViteConfig({
  resolve: process.env.VITEST ? { conditions: ["browser"] } : undefined,
});

export default async (env: Parameters<typeof astroViteConfig>[0]) => {
  const base = await astroViteConfig(env);
  return mergeConfig(base, {
    test: {
      environment: "jsdom",
      setupFiles: ["vitest-setup.ts"],
      coverage: {
        provider: "v8",
        include: ["src/**/*.{ts,svelte}"],
        exclude: [...coverageConfigDefaults.exclude, "**/*Story.svelte.ts"],
      },
      globals: true,
    },
  });
};
