<script lang="ts">
    import type { FormattedTheme } from "../../globa/types.ts";
    import { toTitleCase, getPercentage } from "../../global/utils.ts";

    import Star from "../svg/material/Star.svelte";
    import Panel from "./Panel.svelte";
    import TitleRow from "./TitleRow.svelte";
    import ThemesTable from "./ThemesTable.svelte";
    import ProgressCards from "../ProgressCards.svelte";

    const MAX_CARDS_ALLOWED = 10;

    interface Props {
        totalAnswers: number;
        filteredTotal: number;
        demoData: any;
        demoFilters: any;
        themes: FormattedTheme[];
        themeFilters: string[];
        multiChoice: Object;
        consultationSlug?: string;
        demoFiltersApplied?: () => boolean;
        themeFiltersApplied?: () => boolean;
    }
    let {
        totalAnswers = 0,
        filteredTotal = 0,
        demoData = {},
        demoFilters = [],
        themes = [],
        themeFilters = [],
        multiChoice = {},
        consultationSlug = "",
        demoFiltersApplied = () => false,
        themeFiltersApplied = () => false,
    }: Props = $props();

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

        <ProgressCards
            totalAnswers={totalAnswers}
            filteredTotal={filteredTotal}
            demoData={demoData}
            demoFilters={demoFilters}
            themes={themes}
            themeFilters={themeFilters}
            demoFiltersApplied={demoFiltersApplied}
            themeFiltersApplied={themeFiltersApplied}
        />
    </Panel>
</section>

{#if multiChoice[""] && Object.keys(multiChoice[""]).length > 0}
    <section class="my-4">
        <Panel>
            <TitleRow
                level={2}
                title="Multiple Choice Answers"
            >
                <Star slot="icon" />
            </TitleRow>

            <ProgressCards
                totalAnswers={totalAnswers}
                filteredTotal={filteredTotal}
                demoData={multiChoice}
                demoFilters={demoFilters}
                themes={themes}
                themeFilters={themeFilters}
                demoFiltersApplied={demoFiltersApplied}
                themeFiltersApplied={themeFiltersApplied}
            />
        </Panel>
    </section>
{/if}

<section class="my-4">
    <Panel>
        <TitleRow
            level={2}
            title="Theme analysis"
            subtitle={`Total themes ${themes?.length || 0}`}
        >
            <Star slot="icon" />

            <iai-csv-download
                slot="aside"
                class="text-xs"
                fileName={`theme_mentions_for_${consultationSlug}.csv`}
                variant="silver"
                data={
                    themes.map(theme => ({
                        "Theme Name": theme.name,
                        "Theme Description": theme.description,
                        "Mentions": theme.count,
                        "Percentage": getPercentage(theme.count, totalAnswers),
                    }))
                }
            ></iai-csv-download>
        </TitleRow>

        <ThemesTable
            themes={themes}
            totalAnswers={totalAnswers}
        />
    </Panel>
</section>