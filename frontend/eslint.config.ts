import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import { defineConfig, globalIgnores } from "eslint/config";
import eslintPluginPrettierRecommended from "eslint-plugin-prettier/recommended";
import svelte from "eslint-plugin-svelte";

export default defineConfig([
  globalIgnores([
    ".astro/",
    "coverage/",
    "dist/",
    "node_modules/",
    "public/lit/",
  ]),
  {
    files: ["**/*.{js,ts,mjs,svelte}"],
    extends: [
      js.configs.recommended,
      eslintPluginPrettierRecommended,
      ...tseslint.configs.recommended,
      ...svelte.configs["flat/recommended"],
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
]);
