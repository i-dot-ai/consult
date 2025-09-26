import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import { defineConfig, globalIgnores } from "eslint/config";
import eslintPluginPrettierRecommended from "eslint-plugin-prettier/recommended";

export default defineConfig([
  {
    files: ["**/*.{js,mjs,cjs,ts,mts,cts}"],
    plugins: { js },
    extends: ["js/recommended", eslintPluginPrettierRecommended],
    languageOptions: { globals: globals.browser },
  },
  globalIgnores(["public/lit/"]),
  tseslint.configs.recommended,
]);
