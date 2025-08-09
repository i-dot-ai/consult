<script lang="ts">
    import clsx from "clsx";

    import Button from "../inputs/Button.svelte";

    export let id: string = "";
    export let text: string = "";
    export let demoData: string[] = [];
    export let evidenceRich: boolean = false;
    export let multiAnswers: string[] = [];
    export let themes: string[] = [];
    export let handleThemeTagClick = () => {};
</script>

<article class={clsx([
    "flex",
    "flex-col",
    "gap-2",
    "w-full",
    "my-4",
    "p-4",
    "leading-[1.5rem]",
    "bg-neutral-100",
    "rounded-xl",
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
                    <iai-silver-tag
                        icon={"diamond"}
                        text={demoDataItem}
                        variant={"default"}
                    ></iai-silver-tag>
                {/each}

                {#if evidenceRich}
                    <iai-silver-tag
                        icon={"diamond"}
                        text={"Evidence rich"}
                        variant={"rich"}
                    ></iai-silver-tag>
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
                <iai-silver-tag
                    text={multiAnswer}
                ></iai-silver-tag>
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
                    size="xs"
                >
                    {theme.name}
                </Button>
            {/each}
        </footer>
    {/if}
</article>