<script lang="ts">
    import { toTitleCase } from "../global/utils.ts";

    const MAX_CARDS_ALLOWED = 10;

    let {
        totalAnswers = 0,
        filteredTotal = 0,
        demoData = {},
        demoFilters = [],
        themes = [],
        themeFilters = [],
        demoFiltersApplied = () => false,
        themeFiltersApplied = () => false,
    } = $props();
</script>

<div class="flex flex-wrap gap-2 max-w-full mt-4 overflow-auto">
    {#each Object.keys(demoData) as category}
        {#if Object.values(demoData[category]).length <= MAX_CARDS_ALLOWED}
            <iai-progress-card
                class="max-w-full grow"
                title={toTitleCase(category)}
                data={demoData[category]}
            ></iai-progress-card>
        {/if}
    {/each}
</div>