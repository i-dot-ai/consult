<script lang="ts">
    import clsx from "clsx";
    import { slide } from "svelte/transition";

    import { getPercentage } from "../../global/utils.ts";
    import Panel from "../dashboard/Panel.svelte";
    import Button from "../inputs/Button/Button.svelte";
    import MaterialIcon from "../MaterialIcon.svelte";
    import KeyboardArrowDown from "../svg/material/KeyboardArrowDown.svelte";

    import { demoFilters } from "../../global/state.svelte.ts";

    interface Props {
        category: string;
        demoOptions: Object;
        demoData: Object;
        totalCounts: Object;
        skeleton: boolean;
    }

    let {
        category = "",
        demoOptions = {},
        demoData = {},
        totalCounts = {},
        skeleton = false,
    }: Props = $props();

    let expanded = $state(true);
</script>

<section>
    <Panel level={2} border={true} bg={skeleton ? false : true}>
        {#if skeleton}
            <h3 class="bg-neutral-100 text-neutral-100 select-none w-max blink">skeleton</h3>
        {:else}
            <Button
                variant="ghost"
                size="sm"
                fullWidth={true}
                handleClick={() => expanded = !expanded}
            >
                <div class="flex justify-between w-full">
                    <h3 class="truncate" title={category}>{category}</h3>

                    <div class={clsx([
                        "transition-transform",
                        !expanded && "-rotate-90",
                    ])}>
                        <MaterialIcon color="fill-neutral-400" size="1.3rem">
                            <KeyboardArrowDown />
                        </MaterialIcon>
                    </div>
                </div>
            </Button>
        {/if}

        {#if skeleton}
            <div class="my-1">
                <div class="demo-filter w-full relative pb-3">
                    <div class="grid grid-cols-3 gap-1 mb-1">
                        <span class="text-left bg-neutral-100 text-neutral-100 select-none blink">skeleton</span>
                        <span class="text-right bg-neutral-100 text-neutral-100 select-none blink">000%</span>
                        <span class="text-right bg-neutral-100 text-neutral-100 select-none blink">00000</span>
                    </div>
                    <div class="w-full bg-neutral-100 text-neutral-100 select-none blink">
                        {"_".repeat(10)}
                    </div>
                </div>
            </div>
        {:else}
            {#each demoOptions[category] as rowKey}
                {@const rowValue = demoData[category] && demoData[category][rowKey] || 0}
                {@const percentage = getPercentage(rowValue, totalCounts[category])}

                {#if expanded}
                    <div transition:slide class="my-1">
                        <Button
                            variant="ghost"
                            size="xs"
                            fullWidth={true}
                            handleClick={() => demoFilters.update(category, rowKey)}
                            highlighted={demoFilters.filters[category]?.includes(rowKey)}
                            highlightVariant="light"
                        >
                            <div class="demo-filter w-full relative pb-3">
                                <div class="grid grid-cols-3 gap-1 mb-1">
                                    <span class="text-left truncate" title={rowKey}>
                                        {rowKey.replaceAll("'", "")}
                                    </span>
                                    <span class="text-right">{percentage}%</span>
                                    <span class="text-right">{rowValue}</span>
                                </div>
                                <iai-silver-progress-bar
                                    class="absolute bottom-1 left-0 w-full"
                                    value={percentage}
                                ></iai-silver-progress-bar>
                            </div>

                            <!-- TODO: Alt Design, TBC
                                <div class="demo-filter w-full relative pb-2">
                                    <p class="text-left">{rowKey}</p>
                                    <div class="flex justify-between">
                                        <span class="text-right">{percentage}%</span>
                                        <iai-silver-progress-bar
                                            class="absolute bottom-1 left-0 w-1/2 left-[25%] bottom-3"
                                            value={percentage}
                                        ></iai-silver-progress-bar>
                                        <span class="text-right">{rowValue}</span>
                                    </div>
                                </div>
                            -->
                        </Button>
                    </div>
                {/if}
            {/each}
        {/if}
    </Panel>
</section>