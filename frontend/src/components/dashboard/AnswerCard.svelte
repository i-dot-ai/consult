<script lang="ts">
    import clsx from "clsx";

    import Button from "../inputs/Button.svelte";
    import Panel from "./Panel.svelte";
    import Tag from "../Tag.svelte";
    import MaterialIcon from "../MaterialIcon.svelte";
    import Diamond from "../svg/material/Diamond.svelte";

    export let id: string = "";
    export let text: string = "";
    export let demoData: string[] = [];
    export let evidenceRich: boolean = false;
    export let multiAnswers: string[] = [];
    export let themes: string[] = [];
    export let themeFilters: string[] = [];
    export let handleThemeTagClick = () => {};
</script>

<Panel>
    <article class={clsx([
        "flex",
        "flex-col",
        "gap-2",
        "w-full",
        "rounded-xl",
        "leading-[1.5rem]",
    ])}>
        <header class={clsx([
            "flex",
            "justify-between",
            "items-center",
            "gap-1",
            "flex-wrap",
            "text-sm",
        ])}>
            {#if demoData.length > 0 || evidenceRich}
                <div class={clsx([
                    "flex",
                    "flex-wrap",
                    "items-center",
                    "gap-1",
                ])}>
                    {#each demoData as demoDataItem}
                        <Tag>
                            <span class="text-xs">{demoDataItem}</span>
                        </Tag>
                    {/each}

                    {#if evidenceRich}
                        <Tag variant="warning">
                            <MaterialIcon size="1rem" color="fill-yellow-700">
                                <Diamond />
                            </MaterialIcon>

                            <span class="text-xs">Evidence-rich</span>
                        </Tag>
                    {/if}
                </div>
            {/if}

            <small>
                ID: {id || "Not Available"}
            </small>
        </header>

        {#if text}
            <p>
                {text}
            </p>
        {/if}

        {#if multiAnswers.length > 0}
            <ul class={clsx([
                "flex",
                "gap-1",
            ])}>
                {#each multiAnswers as multiAnswer}
                    <Tag>
                        <span class="text-xs">{multiAnswer}</span>
                    </Tag>
                {/each}
            </ul>
        {/if}

        {#if themes.length > 0}
            <footer class={clsx([
                "flex",
                "items-center",
                "gap-1",
                "flex-wrap",
            ])}>
                <small>
                    Themes:
                </small>
                {#each themes as theme}
                    <Button
                        handleClick={() => handleThemeTagClick(theme.id)}
                        highlighted={themeFilters.includes(theme.id)}
                        highlightVariant="light"
                        size="xs"
                    >
                        {theme.name}
                    </Button>
                {/each}
            </footer>
        {/if}
    </article>
</Panel>