import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import { defineConfig, globalIgnores } from "eslint/config";
import eslintPluginPrettierRecommended from "eslint-plugin-prettier/recommended";
import svelte from "eslint-plugin-svelte";
import astro from "eslint-plugin-astro";

export default defineConfig([
  globalIgnores([
    ".astro/",
    "coverage/",
    "dist/",
    "node_modules/",
    "public/lit/",
  ]),
  {
    files: ["**/*.{js,ts,svelte,astro}"],
    extends: [
      js.configs.recommended,
      eslintPluginPrettierRecommended,
      ...tseslint.configs.recommended,
      ...svelte.configs["flat/recommended"],
      ...astro.configs.recommended,
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: {
        parser: tseslint.parser,
      },
    },
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          args: "after-used",
          argsIgnorePattern: "^_",
        },
      ],
    },
  },
  {
    files: ["**/*.{js,mjs}"],
    ignores: ["svelte.config.js"], // Svelte does not support svelte.config.ts
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector: "Program",
          message:
            "JavaScript files are not allowed. Please use TypeScript (.ts) instead.",
        },
      ],
    },
  },
]);
