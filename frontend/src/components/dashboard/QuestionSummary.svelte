<script lang="ts">
    import { slide, fly } from "svelte/transition";

    import { TabNames, type FormattedTheme } from "../../global/types.ts";
    import { getPercentage } from "../../global/utils.ts";

    import Lan from "../svg/material/Lan.svelte";
    import Close from "../svg/material/Close.svelte";
    import Panel from "./Panel.svelte";
    import MaterialIcon from "../MaterialIcon.svelte";
    import Title from "../Title.svelte";
    import Button from "../inputs/Button/Button.svelte";
    import TitleRow from "./TitleRow.svelte";
    import ThemesTable from "./ThemesTable.svelte";
    import ProgressCards from "../ProgressCards.svelte";
    import FiltersSidebar from "./FiltersSidebar.svelte";
    import Tag from "../Tag/Tag.svelte";
    import Alert from "../Alert.svelte";
    import FilterAlt from "../svg/material/FilterAlt.svelte";
    import List from "../svg/material/List.svelte";

    import { themeFilters, demoFilters } from "../../global/state.svelte.ts";
    import NotFoundMessage from "../NotFoundMessage.svelte";

    const MAX_CARDS_ALLOWED = 10;

    interface Props {
        themesLoading?: boolean;
        totalAnswers: number;
        filteredTotal: number;
        demoData: any;
        demoOptions: any;
        themes: FormattedTheme[];
        multiChoice: Object;
        consultationSlug?: string;
        sortAscending?: boolean;
        searchValue: string;
        evidenceRich: boolean;
        setActiveTab: (newTab: TabNames) => {};
    }
    let {
        themesLoading = true,
        totalAnswers = 0,
        filteredTotal = 0,
        demoData = {},
        demoOptions = {},
        themes = [],
        multiChoice = {},
        consultationSlug = "",
        searchValue = "",
        evidenceRich = false,
        sortAscending = true,
        setActiveTab = () => {},
    }: Props = $props();
</script>

<div class="grid grid-cols-4 gap-4">
    <div class="col-span-4 md:col-span-1">
        <FiltersSidebar
            showEvidenceRich={false}
            {demoOptions}
            {demoData}
            loading={themesLoading}
        />
    </div>

    <div class="col-span-4 md:col-span-3">
        {#if multiChoice[""] && Object.keys(multiChoice[""]).length > 0}
            <section class="my-4">
                <Panel>
                    <TitleRow
                        level={2}
                        title="Multiple Choice Answers"
                    >
                        <List slot="icon" />
                    </TitleRow>

                    <ProgressCards
                        totalAnswers={totalAnswers}
                        filteredTotal={filteredTotal}
                        demoData={multiChoice}
                        themes={themes}
                        themeFilters={themeFilters.filters}
                        demoFiltersApplied={demoFilters.applied}
                        themeFiltersApplied={themeFilters.applied}
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

                {#if demoFilters.applied() || themeFilters.applied() || evidenceRich || searchValue}
                    <div transition:fly={{x:300}} class="my-4">
                        <Alert>
                            <FilterAlt slot="icon" />

                            <div class="flex justify-between items-center gap-4 flex-wrap">
                                <p class="text-sm">
                                    Results are filtered
                                </p>

                                <Button
                                    variant="primary"
                                    size="sm"
                                    handleClick={() => setActiveTab(TabNames.ResponseAnalysis)}
                                >
                                    {`View Responses${themeFilters.filters.length > 0
                                        ? ` (${themeFilters.filters.length} Themes)`
                                        : ""
                                    }`}
                                </Button>
                            </div>
                        </Alert>
                    </div>
                {/if}

                {#if themeFilters.applied()}
                    <section transition:slide class="my-4">

                        <div class="mb-2">
                            <Title level={3} text={`Selected Themes (${themeFilters.filters.length})`} />
                        </div>

                        <div class="flex gap-1 flex-wrap">
                            {#each themeFilters.filters as themeFilterId (themeFilterId)}
                                <div transition:fly={{ x: 300 }}>
                                    <Tag variant="primary">
                                        <span>
                                            {themes.find(theme => theme.id === themeFilterId)?.name || themeFilterId}
                                        </span>

                                        <Button
                                            variant="ghost"
                                            size="xs"
                                            handleClick={() => themeFilters.update(themeFilterId)}
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

                {#if themes.length === 0 && !themesLoading}
                    <NotFoundMessage
                        title="No themes found"
                        body="Try adjusting your search terms or filters."
                    />
                {:else}
                    <ThemesTable
                        themes={[...themes].sort((a,b) => sortAscending
                            ? a.count - b.count
                            : b.count - a.count
                        )}
                        totalAnswers={filteredTotal}
                        skeleton={themesLoading}
                    />
                {/if}

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