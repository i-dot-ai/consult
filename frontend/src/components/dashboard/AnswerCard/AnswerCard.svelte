<script lang="ts">
    import clsx from "clsx";

    import Button from "../../inputs/Button/Button.svelte";
    import Panel from "../Panel/Panel.svelte";
    import Tag from "../../Tag/Tag.svelte";
    import MaterialIcon from "../../MaterialIcon.svelte";
    import Diamond from "../../svg/material/Diamond.svelte";
    import { applyHighlight } from "../../../global/utils";
    import { themeFilters } from "../../../global/state.svelte";

    interface Theme {
        id: string;
        name: string;
    }

    interface Props {
        id?: string;
        text?: string;
        demoData?: string[];
        evidenceRich?: boolean;
        multiAnswers?: string[];
        themes?: Theme[];
        skeleton?: boolean;
        highlightText?: string;
    }

    let {
        id = "",
        text = "",
        demoData = [],
        evidenceRich = false,
        multiAnswers = [],
        themes = [],
        skeleton = false,
        highlightText = "",
    }: Props = $props();
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
            {#if (demoData && demoData.length > 0 || evidenceRich) || skeleton}
                <div class={clsx([
                    "flex",
                    "flex-wrap",
                    "items-center",
                    "gap-1",
                ])}>
                    {#if skeleton}
                        {#each "_".repeat(3) as _}
                            <div class="blink">
                                <Tag>
                                    <span class="text-xs bg-neutral-100 text-neutral-100 select-none">skeleton</span>
                                </Tag>
                            </div>
                        {/each}
                    {:else}
                        {#each demoData as demoDataItem}
                            <Tag>
                                <span class="text-xs">{demoDataItem.replaceAll("'", "")}</span>
                            </Tag>
                        {/each}
                    {/if}

                    {#if evidenceRich && !skeleton}
                        <Tag variant="warning">
                            <MaterialIcon size="1rem" color="fill-yellow-700">
                                <Diamond />
                            </MaterialIcon>

                            <span class="text-xs">Evidence-rich</span>
                        </Tag>
                    {/if}
                </div>
            {/if}

            <small class={clsx([
                skeleton && "bg-neutral-100 text-neutral-100 select-none blink"
            ])}>
                {#if skeleton}
                    SKELETON
                {:else}
                    ID: {id || "Not Available"}
                {/if}
            </small>
        </header>

        {#if skeleton}
            <p class={clsx([
                "bg-neutral-100",
                "text-neutral-100",
                "select-none",
                "blink",
            ])}>
                {"SKELETON ".repeat(20)}
            </p>
        {:else if text}
            <p>
                {@html applyHighlight(text, highlightText)}
            </p>
        {/if}

        {#if multiAnswers && multiAnswers.length > 0 && !skeleton}
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

        {#if themes && themes.length > 0 && !skeleton}
            <footer class={clsx([
                "flex",
                "items-center",
                "gap-1",
                "flex-wrap",
            ])}>
                <small class="text-neutral-500">
                    Themes:
                </small>
                {#each themes as theme}
                    <Button
                        handleClick={() => themeFilters.update(theme.id)}
                        highlighted={themeFilters.filters.includes(theme.id)}
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