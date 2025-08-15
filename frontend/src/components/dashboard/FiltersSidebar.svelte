<script lang="ts">
    import { slide, fade } from "svelte/transition";

    import TitleRow from "./TitleRow.svelte";
    import Panel from "./Panel.svelte";
    import Button from "../inputs/Button.svelte";
    import Star from "../svg/material/Star.svelte";

    let {
        showEvidenceRich = true,
        demoOptions = {},
        demoData = {},
        demoFilters = {},
        setDemoFilters = () => {},
    } = $props();
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
                                        <span class="text-right">{demoData[category] && demoData[category][rowKey] || 0}%</span>
                                        <span class="text-right">{demoData[category] && demoData[category][rowKey] || 0}</span>
                                    </div>
                                    <iai-silver-progress-bar
                                        value={20}
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