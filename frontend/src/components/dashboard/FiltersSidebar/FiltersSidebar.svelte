<script lang="ts">
    import { fade } from "svelte/transition";

    import TitleRow from "../TitleRow.svelte";
    import Panel from "../Panel.svelte";
    import DemoFilter from "../../DemoFilter/DemoFilter.svelte";
    import FilterAlt from "../../svg/material/FilterAlt.svelte";
    import Switch from "../../inputs/Switch/Switch.svelte";
    import MaterialIcon from "../../MaterialIcon.svelte";
    import Diamond from "../../svg/material/Diamond.svelte";

    let {
        showEvidenceRich = true,
        demoOptions = {},
        demoData = {},
        evidenceRich = false,
        setEvidenceRich = () => {},
        loading = true,
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
                    label="Evidence Rich"
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

        {#if loading}
            <div in:fade>
                {#each "_".repeat(3) as _}
                    <DemoFilter skeleton={true} />
                {/each}
            </div>
        {:else}
            <div in:fade>
                {#each Object.keys(demoOptions) as category (category)}
                    <DemoFilter
                        {category}
                        {demoOptions}
                        {demoData}
                        {totalCounts}
                        skeleton={loading}
                    />
                {/each}
            </div>
        {/if}
    </Panel>
</aside>