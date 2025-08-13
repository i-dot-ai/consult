<script lang="ts">
    import { toTitleCase } from "../../global/utils.ts";

    import Star from "../svg/material/Star.svelte";
    import Panel from "./Panel.svelte";
    import TitleRow from "./TitleRow.svelte";
    import ThemesTable from "./ThemesTable.svelte";

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

    let sortAscending: boolean = true;
</script>

<section class="my-4">
    <Panel>
        <TitleRow
            level={2}
            title="Demographics"
            subtitle="Demographic breakdown for this question"
        >
            <Star slot="icon" />
        </TitleRow>

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
    </Panel>
</section>

<section class="my-4">
    <Panel>
        <TitleRow
            level={2}
            title="Theme analysis"
            subtitle={`Total themes ${themes?.length || 0}`}
        >
            <Star slot="icon" />
        </TitleRow>

        <ThemesTable
            themes={themes}
            totalAnswers={totalAnswers}
        />
    </Panel>
</section>