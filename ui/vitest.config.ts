/// <reference types="vitest" />
import { getViteConfig } from "astro/config";


export default getViteConfig({
    test: {
        environment: "jsdom"
    },
    resolve: process.env.VITEST
        ? { conditions: ["browser"] }
        : undefined
});