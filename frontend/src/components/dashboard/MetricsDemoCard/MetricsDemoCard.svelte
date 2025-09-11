<script lang="ts">
    import clsx from "clsx";

    import { slide } from "svelte/transition";

    import Progress from "../../Progress/Progress.svelte";
    import Title from "../../Title.svelte";
    import Panel from "../Panel/Panel.svelte";
    import Button from "../../inputs/Button/Button.svelte";
    import MaterialIcon from "../../MaterialIcon.svelte";
    import ArrowForward from "../../svg/material/ArrowForward.svelte";


    interface MetricsDemoItem {
        title: string;
        count: number;
        percentage: number;
    }

    interface Props {
        title: string;
        items?: MetricsDemoItem[];
    }

    let {
        title = "",
        items = [],
    }: Props = $props();

    let displayAll: boolean = $state(false);

    const NUM_ABOVE_FOLD = 3;
</script>

{#snippet cardItem({title, count, percentage}: MetricsDemoItem, index: number)}
    {#if displayAll || index < NUM_ABOVE_FOLD}
        <div
            transition:slide
            class={clsx([
                "flex",
                "items-center",
                "gap-2",
                "my-2",
                "justify-between",
            ])}
        >
            <p class="text-xs grow max-w-[60%]">{title}</p>

            <div class="flex items-center gap-2 justify-end">
                <span class="text-sm">{count.toLocaleString()}</span>
                <span class="text-xs text-primary">{percentage}%</span>
                <div class="w-[2rem]">
                    <Progress value={percentage} />
                </div>
            </div>
        </div>
    {/if}
{/snippet}

<div transition:slide class="metrics-demo-card col-span-12 sm:col-span-6 lg:col-span-4">
    <Panel bg={true} border={true}>
        <Title level={4} text={title} />

        {#each items as item, index}
            {@render cardItem(item, index)}
        {/each}

        {#if items.length > NUM_ABOVE_FOLD}
            <hr class="my-2 border-neutral-300" />

            <Button
                size="xs"
                variant="ghost"
                handleClick={() => displayAll = !displayAll}
            >
                <div class="flex justify-center items-center gap-1">
                    <span>View All {items.length}</span>

                    <MaterialIcon color="fill-neutral-500">
                        <ArrowForward />
                    </MaterialIcon>
                </div>
            </Button>
        {/if}
    </Panel>
</div>