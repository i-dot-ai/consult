<script lang="ts">
    import clsx from "clsx";

    export let level: 1 | 2 | 3 | 4 | 5 | 6 = 1;
    export let text: string = "";
    export let weight: "bold" | "light" = "bold";

    const tagMap = {
        1: "h1",
        2: "h2",
        3: "h3",
        4: "h4",
        5: "h5",
        6: "h6",
    } as const;

    const tag = tagMap[level];
</script>

<svelte:element this={tag} class={clsx([
    weight === "bold" ? "font-bold" : "font-light",
    level === 1 && "text-xl",
    level === 2 && "text-lg",
    level === 3 && "text-md",
    "text-neutral-700",
])} >
    {@html text}
</svelte:element>