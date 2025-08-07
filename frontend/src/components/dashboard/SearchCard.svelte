<script lang="ts">
    import clsx from "clsx";

    import Title from "../Title.svelte";
    import MaterialIcon from "../MaterialIcon.svelte";
    import Star from "../svg/material/Star.svelte";

    export let title: string = "";
    export let description: string = "";
    export let tags: Array<string> = [];
    export let highlightText: string = "";

    const applyTextHighlight = (text) => {
        if (!highlightText) {
            return text;
        }
        const regex = new RegExp(highlightText, "gi");
        return text.replace(regex, match => `<span class="bg-yellow-300">${match}</span>`);
    }
</script>

<article>
    <div class={clsx([
        "flex",
        "gap-2",
    ])}>
        <div class={clsx([
            "mt-1",
        ])}>
            <MaterialIcon size={"1.3rem"}>
                <Star />
            </MaterialIcon>
        </div>

        <div class={clsx([
            "grow",
            "flex",
            "flex-col",
            "gap-2",
        ])}>
            <div class={clsx([
                "flex",
                "justify-between",
            ])}>
                <Title
                    weight={"light"}
                    level={3}
                    text={applyTextHighlight(title)}
                />

                <slot name="aside" />
            </div>

            {#if description}
                <p>
                    {@html applyTextHighlight(description)}
                </p>    
            {/if}
            
            <footer class={clsx([
                "flex",
                "gap-3",
                "flex-wrap",
            ])}>
                <slot name="footer" />
                
                {#each tags as tag}
                    <span class={clsx([
                        "flex",
                        "justify-center",
                        "items-center",
                        "py-1",
                        "px-2",
                        "bg-gray-100",
                        "text-sm",
                        "rounded-md",
                    ])}>
                        {tag}
                    </span>
                {/each}
            </footer>
        </div>
    </div>
</article>