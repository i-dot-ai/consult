import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  theme: {
    extend: {
      colors: {
        primary: "var(--color-primary)",
        secondary: "var(--color-secondary)",
        iaiteal: {
          50: "oklch(0.96 0.02 175)",
          100: "oklch(0.91 0.05 175)",
          200: "oklch(0.84 0.08 175)",
          300: "oklch(0.75 0.12 175)",
          400: "oklch(0.64 0.16 175)",
          500: "oklch(0.49 0.14 175)",
          600: "oklch(0.42 0.12 175)",
          700: "oklch(0.35 0.10 175)",
          800: "oklch(0.26 0.08 175)",
          900: "oklch(0.18 0.06 175)",
        },
      },
      screens: {
        "3xl": "1920px",
      },
    },
  },
  plugins: [],
} satisfies Config;
