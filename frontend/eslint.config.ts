import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import { defineConfig, globalIgnores } from "eslint/config";
import eslintPluginPrettierRecommended from "eslint-plugin-prettier/recommended";

export default defineConfig([
  globalIgnores([
    ".astro/",
    "coverage/",
    "dist/",
    "node_modules/",
    "public/lit/",
  ]),
  {
    files: ["**/*.{js,ts,mjs}"],
    extends: [
      js.configs.recommended,
      eslintPluginPrettierRecommended,
      ...tseslint.configs.recommended,
    ],
    languageOptions: { globals: globals.browser },
  },
]);
