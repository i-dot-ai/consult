<script lang="ts">
    import TitleRow from "./TitleRow.svelte";
    import Panel from "./Panel.svelte";
    import DemoFilter from "./DemoFilter.svelte";
    import Star from "../svg/material/Star.svelte";

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