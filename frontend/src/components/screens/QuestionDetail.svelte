<script lang="ts">
    import clsx from "clsx";

    import { onMount } from "svelte";
    import { fly, fade, slide } from "svelte/transition";

    import MaterialIcon from "../MaterialIcon.svelte";
    import Button from "../inputs/Button/Button.svelte";
    import Panel from "../dashboard/Panel.svelte";
    import Star from "../svg/material/Star.svelte";
    import SearchCard from "../dashboard/SearchCard.svelte";
    import QuestionCard from "../dashboard/QuestionCard.svelte";
    import TabView from "../TabView.svelte";
    import Title from "../Title.svelte";
    import QuestionSummary from "../dashboard/QuestionSummary.svelte";
    import ResponseAnalysis from "../dashboard/ResponseAnalysis.svelte";

    import { getConsultationDetailUrl } from "../../global/routes.ts";
    import { createFetchStore } from "../../global/stores.ts";
    import { SearchModeValues } from "../../global/types.ts";
    import Alert from "../Alert.svelte";

    export let consultationId: string = "";
    export let questionId: string = "";

    const PAGE_SIZE = 50;
    const MAX_THEME_FILTERS = Infinity;

    let currPage: number = 1;
    let hasMorePages: boolean = true;
    let answers = [];

    const TabNames = {
        QuestionSummary: "tab-question-summary",
        ResponseAnalysis: "tab-response-analysis",
    }

    let activeTab = TabNames.QuestionSummary;

    let searchValue: string = "";
    let searchMode: SearchModeValues = SearchModeValues.KEYWORD;
    let themeFilters: string[] = [];
    let demoFilters: {[key: string]: string[]} = {};
    let evidenceRich: boolean = false;
    let sortAscending: boolean = false;

    $: {
        resetAnswers();
        loadData({
            searchValue: searchValue,
            searchMode: searchMode,
            themeFilters: themeFilters,
            evidenceRich: evidenceRich,
            demoFilters: demoFilters,
        });
    };

    const {
        loading: isConsultationLoading,
        error: consultationError,
        load: loadConsultation,
        data: consultationData,
    } = createFetchStore();

    const {
        loading: isAnswersLoading,
        error: answersError,
        load: loadAnswers,
        data: answersData,
    } = createFetchStore();

    const {
        loading: isThemeAggrLoading,
        error: themeAggrError,
        load: loadThemeAggr,
        data: themeAggrData,
    } = createFetchStore();

    const {
        loading: isThemeInfoLoading,
        error: themeInfoError,
        load: loadThemeInfo,
        data: themeInfoData,
    } = createFetchStore();

    const {
        loading: isDemoOptionsLoading,
        error: demoOptionsError,
        load: loadDemoOptions,
        data: demoOptionsData,
    } = createFetchStore();

    const {
        loading: isDemoAggrLoading,
        error: demoAggrError,
        load: loadDemoAggr,
        data: demoAggrData,
    } = createFetchStore();

    const {
        loading: isMultiChoiceAggrLoading,
        error: multiChoiceAggrError,
        load: loadMultiChoiceAggr,
        data: multiChoiceAggrData,
    } = createFetchStore();

    onMount(() => {
        // Load consultation data once on mount
        loadConsultation(`/api/consultations/${consultationId}/`);
    })

    async function loadData(filters) {
        const queryString = buildQuery(filters);

        // Skip the rest of the requests if they are already requested for this filter set
        if (currPage === 1) {
            loadThemeAggr(`/api/consultations/${consultationId}/questions/${questionId}/theme-aggregations/${queryString}`);
            loadThemeInfo(`/api/consultations/${consultationId}/questions/${questionId}/theme-information/${queryString}`);
            loadDemoOptions(`/api/consultations/${consultationId}/demographic-options/${queryString}`);
            loadDemoAggr(`/api/consultations/${consultationId}/questions/${questionId}/demographic-aggregations/${queryString}`);
            loadMultiChoiceAggr(`/api/consultations/${consultationId}/questions/${questionId}/multi-choice-response-count/${queryString}`);
        }

        // Append next page of answers to existing answers
        try {
            await loadAnswers(`/api/consultations/${consultationId}/questions/${questionId}/responses/${queryString}`);

            if ($answersData.all_respondents) {
                const newAnswers = $answersData.all_respondents;
                answers = [...answers, ...newAnswers];
            }
            hasMorePages = $answersData.has_more_pages || false;
        } catch {}

        currPage += 1;
    }

    function buildQuery(filters) {
        const params = new URLSearchParams({
            ...(filters.searchValue && {
                searchValue: filters.searchValue
            }),
            ...(themeFilters.length > 0 && {
                themeFilters: filters.themeFilters.join(",")
            }),
            ...(searchMode && {
                searchMode: filters.searchMode
            }),
            ...(filters.evidenceRich && {
                evidenceRich: filters.evidenceRich
            }),
            page: currPage,
            page_size: PAGE_SIZE.toString(),
        })

        // Filter out demo filter keys with no value
        const validDemoFilterKeys = Object.keys(filters.demoFilters).filter(key => Boolean(filters.demoFilters[key]));
        // Add each demo filter as a duplicate demoFilter param
        for (const key of validDemoFilterKeys) {
            const filterArr = filters.demoFilters[key];
            if (filterArr && filterArr.length > 0) {
                // TODO: Replace below with the commented out code after the back end is implemented.
                // Only processing the first filter for now to avoid breaking back end responses.
                filterArr.forEach((filterArrItem: string) => {
                    params.append("demoFilters", `${key}:${filterArrItem}`);
                })
            }
        }

        const queryString = params.toString();
        return queryString ? `?${queryString}` : "";
    }

    function resetAnswers() {
        answers = [];
        currPage = 1;
        hasMorePages = true;
    }

    function formatMultiChoiceData(multiChoiceData: Array<{
        response_count: number,
        answer?: string,
    }>) {
        if (!multiChoiceData) {
            return {};
        }

        // empty string to avoid displaying title on card
        const formattedMultiChoice = {"": {}};
        multiChoiceData.forEach(data => {
            if (!data.answer) {
                return;
            }
            formattedMultiChoice[""][data.answer] = data.response_count;
        })
        return formattedMultiChoice;
    }

    const setDemoFilters = (newFilterKey: string, newFilterValue: string) => {
        if (!newFilterKey || !newFilterValue) {
            // Clear filters if nothing is passed
            demoFilters = {};
            return;
        }

        const existingFilters = demoFilters[newFilterKey] || [];

        let resultFilters;
        if (existingFilters.includes(newFilterValue)) {
            // Remove filter if already added
            resultFilters = existingFilters.filter(filter => newFilterValue !== filter);
        } else {
            // Avoid duplicates when adding filters
            resultFilters = [...new Set([...existingFilters, newFilterValue])];
        }

        demoFilters = {
            ...demoFilters,
            [newFilterKey]: resultFilters,
        }
    }

    const updateThemeFilters = (newFilter: string) => {
        if (!newFilter) {
            // Clear filters if newFilter is falsy
            themeFilters = [];
            return;
        }
        if (themeFilters.includes(newFilter)) {
            themeFilters = [...themeFilters.filter(filter => filter !== newFilter)];
        } else {
            if (themeFilters.length === MAX_THEME_FILTERS) {
                themeFilters = [...themeFilters.slice(1), newFilter];
            } else {
                themeFilters = [...themeFilters, newFilter];
            }
        }
    }

    const demoFiltersApplied = (demoFilters): boolean => {
        for (const key of Object.keys(demoFilters)) {
            const filterArr = demoFilters[key];

            // filterArr can be undefined or empty array
            if (filterArr && filterArr.filter(Boolean).length > 0) {
                return true;
            }
        }
        return false;
    }

    const themeFiltersApplied = (themeFilters: string[]): boolean => {
        return themeFilters.length > 0;
    }

    const setEvidenceRich = (value: boolean) => evidenceRich = value;
</script>

<section class={clsx([
    "flex",
    "justify-between",
    "flex-wrap",
    "gap-2",
    "items-center",
])}>
    <Button handleClick={() => {
        window.location.href = getConsultationDetailUrl(consultationId);
    }}>
        <MaterialIcon color="fill-neutral-600" class="shrink-0">
            <Star />
        </MaterialIcon>
        <span class="text-sm">Back to all questions</span>
    </Button>

    <small>
        Choose a different question to analyse
    </small>
</section>

<section class="my-4">
    {#if $consultationError}
        <div class="my-2">
            <Alert>
                <span class="text-sm">
                    Consultation Error: {$consultationError}
                </span>
            </Alert>
        </div>
    {:else}
        <QuestionCard
            skeleton={$isConsultationLoading}
            clickable={false}
            consultationId={!$isConsultationLoading && $consultationData.id}
            question={!$isConsultationLoading &&
                $consultationData.questions?.find(question => question.id === questionId)
            }
            hideIcon={true}
            horizontal={true}
        />
    {/if}
</section>

<TabView
    value={activeTab}
    onValueChange={({ curr, next }) => activeTab = next}
    tabs={[
        { id: TabNames.QuestionSummary, title: "Question Summary" },
        { id: TabNames.ResponseAnalysis, title: "Response Analysis"},
    ]}
>
    {#if activeTab === TabNames.QuestionSummary}
        <QuestionSummary
            themes={Object.keys($themeAggrData?.theme_aggregations || []).map(themeId => {
                return ({
                    id: themeId,
                    count: $themeAggrData?.theme_aggregations[themeId],
                    highlighted: themeFilters.includes(themeId),
                    handleClick: () => updateThemeFilters(themeId),
                    ...($themeInfoData?.themes?.find(themeInfo => themeInfo.id === themeId)),
                })
            })}
            themesLoading={$isThemeAggrLoading}
            totalAnswers={$answersData?.respondents_total}
            filteredTotal={$answersData?.filtered_total}
            demoData={$demoAggrData?.demographic_aggregations}
            demoOptions={$demoOptionsData?.demographic_options}
            demoFilters={demoFilters}
            themeFilters={themeFilters}
            setDemoFilters={setDemoFilters}
            updateThemeFilters={updateThemeFilters}
            demoFiltersApplied={demoFiltersApplied}
            themeFiltersApplied={themeFiltersApplied}
            evidenceRich={evidenceRich}
            setEvidenceRich={setEvidenceRich}
            multiChoice={formatMultiChoiceData($multiChoiceAggrData)}
            consultationSlug={$consultationData?.slug}
            sortAscending={sortAscending}
        />
    {:else if activeTab === TabNames.ResponseAnalysis}
        <ResponseAnalysis
            answers={answers}
            isAnswersLoading={$isAnswersLoading}
            answersError={$answersError}
            filteredTotal={$answersData?.filtered_total}
            hasMorePages={hasMorePages}
            handleLoadClick={() => loadData({
                searchValue: searchValue,
                searchMode: searchMode,
                themeFilters: themeFilters,
                evidenceRich: evidenceRich,
                demoFilters: demoFilters,
            })}
            searchValue={searchValue}
            setSearchValue={(value) => searchValue = value}
            searchMode={searchMode}
            setSearchMode={(newSearchMode: SearchModeValues) => searchMode = newSearchMode}
            demoData={$demoAggrData?.demographic_aggregations}
            demoOptions={$demoOptionsData?.demographic_options}
            demoFilters={demoFilters}
            themes={$themeInfoData?.themes}
            themeFilters={themeFilters}
            setDemoFilters={setDemoFilters}
            updateThemeFilters={updateThemeFilters}
            evidenceRich={evidenceRich}
            setEvidenceRich={setEvidenceRich}
            themeFiltersApplied={themeFiltersApplied}
            demoFiltersApplied={demoFiltersApplied}
            isThemesLoading={$isThemeAggrLoading}
        />
    {/if}
</TabView>