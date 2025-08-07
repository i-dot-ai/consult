// @ts-check
import { defineConfig } from 'astro/config';
import svelte from "@astrojs/svelte";

import tailwindcss from "@tailwindcss/vite";

// https://astro.build/config
export default defineConfig({
    output: "server",
    integrations: [svelte()],
    vite: {
        plugins: [tailwindcss()],
    },
});