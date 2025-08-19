<script lang="ts">
    import { slide, fly, fade } from "svelte/transition";

    import type { FormattedTheme } from "../../globa/types.ts";
    import { toTitleCase, getPercentage } from "../../global/utils.ts";

    import Star from "../svg/material/Star.svelte";
    import Lan from "../svg/material/Lan.svelte";
    import Close from "../svg/material/Close.svelte";
    import Panel from "./Panel.svelte";
    import MaterialIcon from "../MaterialIcon.svelte";
    import Title from "../Title.svelte";
    import Button from "../inputs/Button.svelte";
    import TitleRow from "./TitleRow.svelte";
    import ThemesTable from "./ThemesTable.svelte";
    import ProgressCards from "../ProgressCards.svelte";
    import FiltersSidebar from "./FiltersSidebar.svelte";
    import Tag from "../Tag.svelte";
    import Alert from "../Alert.svelte";
    import FilterAlt from "../svg/material/FilterAlt.svelte";

    const MAX_CARDS_ALLOWED = 10;

    interface Props {
        loading?: boolean;
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
        updateThemeFilters?: () => {};
        demoFiltersApplied?: (filters) => boolean;
        themeFiltersApplied?: (filters: string[]) => boolean;
        evidenceRich: boolean;
        setEvidenceRich: (value: boolean) => {};
    }
    let {
        loading = true,
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
        setDemoFilters = () => {},
        updateThemeFilters = () => {},
        demoFiltersApplied = () => false,
        themeFiltersApplied = () => false,
    }: Props = $props();
</script>

<div class="grid grid-cols-4 gap-4">
    <div class="col-span-4 md:col-span-1">
        <FiltersSidebar
            showEvidenceRich={false}
            {demoOptions}
            {demoData}
            {demoFilters}
            {setDemoFilters}
        />
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
                    <Lan slot="icon" />

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

                {#if demoFiltersApplied(demoFilters) || themeFiltersApplied(themeFilters)}
                    <div transition:fly={{x:300}} class="my-4">
                        <Alert>
                            <FilterAlt slot="icon" />

                            <p slot="text" class="text-sm">
                                Results are filtered
                            </p>
                        </Alert>
                    </div>
                {/if}

                {#if themeFiltersApplied(themeFilters)}
                    <section transition:slide class="my-4">

                        <div class="mb-2">
                            <Title level={3} text={`Selected Themes (${themeFilters.length})`} />
                        </div>

                        <div class="flex gap-1 flex-wrap">
                            {#each themeFilters as themeFilterId (themeFilterId)}
                                <div transition:fly={{ x: 300 }}>
                                    <Tag variant="primary">
                                        <span>
                                            {themes.find(theme => theme.id === themeFilterId)?.name || themeFilterId}
                                        </span>

                                        <Button
                                            variant="ghost"
                                            size="xs"
                                            handleClick={() => updateThemeFilters(themeFilterId)}
                                        >
                                            <MaterialIcon color="fill-white" hoverColor="fill-primary">
                                                <Close />
                                            </MaterialIcon>
                                        </Button>
                                    </Tag>
                                </div>
                            {/each}
                        </div>
                    </section>
                {/if}

                <ThemesTable
                    themes={[...themes].sort((a,b) => sortAscending
                        ? a.count - b.count
                        : b.count - a.count
                    )}
                    totalAnswers={filteredTotal}
                    skeleton={loading}
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