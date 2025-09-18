<script lang="ts">
    import clsx from "clsx";

    import type { TitleLevels } from "../global/types";

    export let level: TitleLevels = 1;
    export let text: string = "";
    export let weight: "light"  | "normal" | "bold" = "normal";
    export let maxChars: number = 0;

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

<svelte:element
    this={tag}
    style={clsx([maxChars && `max-width: ${maxChars}ch;`])}
    class={clsx([
        "text-neutral-700",
        weight === "bold" && "font-bold",
        weight === "light" && "font-light",
        level === 1 && "text-3xl mb-5 font-semibold",
        level === 2 && "text-lg",
        level === 3 && "text-md",
        level === 4 && "text-sm",
        maxChars && clsx([
            "max-w-[50ch]",
            "text-ellipsis",
            "whitespace-nowrap",
            "overflow-x-hidden",
        ])
    ])}
>
    {@html text}
</svelte:element>