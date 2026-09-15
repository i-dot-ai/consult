import { createRawSnippet } from "svelte";

const childContentClass = "text-red-600 font-bold";

export const childrenDefault = createRawSnippet(() => ({
    render: () => `
        <p color="${childContentClass}">
            Child content
        </p>
    `,
}));

export const childrenLong = createRawSnippet(() => ({
    render: () => `
        <p color="${childContentClass}">
            ${"Long child content".repeat(20)}
        </p>
    `,
}));