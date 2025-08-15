<script lang="ts">
    import { slide, fade } from "svelte/transition";

    import TitleRow from "./TitleRow.svelte";
    import Panel from "./Panel.svelte";
    import Button from "../inputs/Button.svelte";
    import Star from "../svg/material/Star.svelte";

    import { getPercentage } from "../../global/utils.ts";

    let {
        showEvidenceRich = true,
        demoOptions = {},
        demoData = {},
        demoFilters = {},
        setDemoFilters = () => {},
    } = $props();

    // Derive to avoid calculating on re-render
    let totalCounts = $derived.by(() => {
		let counts = {};
		for (const category of Object.keys(demoData)) {
            counts[category] = Object.values(demoData[category]).reduce( (a, b) => a + b, 0 );
		}
		return counts;
	})
</script>

<aside>
    <Panel>
        <TitleRow level={2} title="Filters" subtitle="">
            <Star slot="icon" />
        </TitleRow>

        {#each Object.keys(demoOptions) as category (category)}
            <div transition:fade>
                <Panel level={2} border={true} bg={true}>
                    <Button variant="ghost" size="sm">
                        {category}
                    </Button>

                    {#each demoOptions[category] as rowKey}
                        {@const rowValue = demoData[category] && demoData[category][rowKey] || 0}
                        {@const percentage = getPercentage(rowValue, totalCounts[category])}

                        <div class="my-1">
                            <Button
                                variant="ghost"
                                size="xs"
                                fullWidth={true}
                                handleClick={() => setDemoFilters(category, rowKey)}
                                highlighted={demoFilters[category]?.includes(rowKey)}
                                highlightVariant="light"
                            >
                                <div class="demo-filter w-full">
                                    <div class="grid grid-cols-3 gap-1 mb-1">
                                        <span class="text-left">{rowKey}</span>
                                        <span class="text-right">{percentage}%</span>
                                        <span class="text-right">{rowValue}</span>
                                    </div>
                                    <iai-silver-progress-bar
                                        value={percentage}
                                    ></iai-silver-progress-bar>
                                </div>
                            </Button>
                        </div>
                    {/each}
                </Panel>
            </div>
        {/each}
        
    </Panel>
</aside>