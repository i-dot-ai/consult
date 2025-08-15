<script lang="ts">
    import clsx from "clsx";
    import { slide, fade } from "svelte/transition";

    import { getPercentage } from "../../global/utils.ts";
    import Panel from "./Panel.svelte";
    import Button from "../inputs/Button.svelte";
    import MaterialIcon from "../MaterialIcon.svelte";
    import KeyboardArrowDown from "../svg/material/KeyboardArrowDown.svelte";

    let {
        category = "",
        demoOptions = {},
        demoData = {},
        demoFilters = {},
        setDemoFilters = () => {},
        totalCounts = {},
    } = $props();

    let expanded = $state(true);
</script>

<section transition:fade>
    <Panel level={2} border={true} bg={true}>
        <Button
            variant="ghost"
            size="sm"
            fullWidth={true}
            handleClick={() => expanded = !expanded}
        >
            <div class="flex justify-between w-full">
                <h3>{category}</h3>

                <div class={clsx([
                    "transition-transform",
                    !expanded && "-rotate-90",
                ])}>
                    <MaterialIcon size="1.3rem">
                        <KeyboardArrowDown />
                    </MaterialIcon>
                </div>
            </div>
        </Button>

        {#each demoOptions[category] as rowKey}
            {@const rowValue = demoData[category] && demoData[category][rowKey] || 0}
            {@const percentage = getPercentage(rowValue, totalCounts[category])}

            {#if expanded}
                <div transition:slide class="my-1">
                    <Button
                        variant="ghost"
                        size="xs"
                        fullWidth={true}
                        handleClick={() => setDemoFilters(category, rowKey)}
                        highlighted={demoFilters[category]?.includes(rowKey)}
                        highlightVariant="light"
                    >
                        <div class="demo-filter w-full relative pb-3">
                            <div class="grid grid-cols-3 gap-1 mb-1">
                                <span class="text-left">{rowKey}</span>
                                <span class="text-right">{percentage}%</span>
                                <span class="text-right">{rowValue}</span>
                            </div>
                            <iai-silver-progress-bar
                                class="absolute bottom-1 left-0 w-full"
                                value={percentage}
                            ></iai-silver-progress-bar>
                        </div>
                    </Button>
                </div>
            {/if}
        {/each}
    </Panel>
</section>