<script lang="ts">
    export let level: 1 | 2 | 3 | 4 | 5 | 6 = 1;
    export let text: string = "";

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

<svelte:element this={tag} class="font-bold text-2xl">
    {text}
</svelte:element>