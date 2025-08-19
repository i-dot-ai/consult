<script lang="ts">
    import TitleRow from "./TitleRow.svelte";
    import Panel from "./Panel.svelte";
    import DemoFilter from "./DemoFilter.svelte";
    import FilterAlt from "../svg/material/FilterAlt.svelte";
    import Switch from "../inputs/Switch.svelte";
    import MaterialIcon from "../MaterialIcon.svelte";
    import Diamond from "../svg/material/Diamond.svelte";

    let {
        showEvidenceRich = true,
        demoOptions = {},
        demoData = {},
        demoFilters = {},
        setDemoFilters = () => {},
        evidenceRich = false,
        setEvidenceRich = () => {},
    } = $props();

    // Derive to avoid calculating on re-render
    let totalCounts = $derived.by(() => {
		let counts = {};
		for (const category of Object.keys(demoData)) {
            counts[category] = Object.values(demoData[category]).reduce(
                (a, b) => a + b, 0
            );
		}
		return counts;
	})
</script>

<aside>
    <Panel>
        <TitleRow level={2} title="Filters" subtitle="">
            <FilterAlt slot="icon" />
        </TitleRow>

        {#if showEvidenceRich}
            <Panel level={2} border={true} bg={true}>
                <Switch
                    id="evidence-rich-toggle"
                    value={evidenceRich}
                    handleChange={(value: boolean) => setEvidenceRich(value)}
                >
                    <div slot="label" class="flex gap-1 items-center">
                        <div class="bg-yellow-100 rounded-2xl text-xs p-0.5">
                            <MaterialIcon size="1rem" color="fill-yellow-700">
                                <Diamond />
                            </MaterialIcon>
                        </div>

                        <span class="text-xs">Show evidence rich first</span>
                    </div>
                </Switch>
            </Panel>
        {/if}

        {#each Object.keys(demoOptions) as category (category)}
            <DemoFilter
                {setDemoFilters}
                {category}
                {demoOptions}
                {demoData}
                {demoFilters}
                {totalCounts}
            />
        {/each}
    </Panel>
</aside>