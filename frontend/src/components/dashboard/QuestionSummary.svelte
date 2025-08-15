<script lang="ts">
    import type { FormattedTheme } from "../../globa/types.ts";
    import { toTitleCase, getPercentage } from "../../global/utils.ts";

    import Star from "../svg/material/Star.svelte";
    import Panel from "./Panel.svelte";
    import Button from "../inputs/Button.svelte";
    import TitleRow from "./TitleRow.svelte";
    import ThemesTable from "./ThemesTable.svelte";
    import ProgressCards from "../ProgressCards.svelte";
    import FiltersSidebar from "./FiltersSidebar.svelte";

    const MAX_CARDS_ALLOWED = 10;

    interface Props {
        totalAnswers: number;
        filteredTotal: number;
        demoData: any;
        demoFilters: {};
        themes: FormattedTheme[];
        themeFilters: string[];
        multiChoice: Object;
        consultationSlug?: string;
        sortAscending?: boolean;
        setDemoFilters?: () => {};
        demoFiltersApplied?: () => boolean;
        themeFiltersApplied?: () => boolean;
    }
    let {
        totalAnswers = 0,
        filteredTotal = 0,
        demoData = {},
        demoOptions = {},
        demoFilters = {},
        themes = [],
        themeFilters = [],
        multiChoice = {},
        consultationSlug = "",
        sortAscending = true,
        setDemoFilters,
        demoFiltersApplied = () => false,
        themeFiltersApplied = () => false,
    }: Props = $props();
</script>

<div class="grid grid-cols-4 gap-4">
    <div class="col-span-4 md:col-span-1">
        <FiltersSidebar {demoOptions} {demoData} {demoFilters} {setDemoFilters} />
    </div>

    <div class="col-span-4 md:col-span-3">
        <!-- <section class="my-4">
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
        </section> -->

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
                    subtitle="Analysis of key themes mentioned in responses to this question."
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

                <p>{filteredTotal}</p>
                <ThemesTable
                    themes={[...themes].sort((a,b) => sortAscending
                        ? a.count - b.count
                        : b.count - a.count
                    )}
                    totalAnswers={filteredTotal}
                />

                <div class="flex justify-between items-center flex-wrap gap-y-4">
                    <small>
                        {`Showing ${themes?.length || 0} themes • Click rows to select themes for response analysis`}
                    </small>

                    <div class="flex items-center gap-1">
                        <small>Order:</small>
                        <Button size="xs" highlighted={!sortAscending} handleClick={() => sortAscending = false}>
                            High to Low
                        </Button>
                        <Button size="xs" highlighted={sortAscending} handleClick={() => sortAscending = true}>
                            Low to High
                        </Button>
                    </div>
                </div>
            </Panel>
        </section>
    </div>
</div>