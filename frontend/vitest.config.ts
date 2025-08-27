/// <reference types="vitest" />
import { getViteConfig } from "astro/config";


export default getViteConfig({
    test: {
        environment: "jsdom",
        coverage: {
            provider: 'v8'
        },
    },
    resolve: process.env.VITEST
        ? { conditions: ["browser"] }
        : undefined
});