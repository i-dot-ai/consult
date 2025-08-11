<script lang="ts">
    import clsx from "clsx";

    import { onMount } from "svelte";
    import { slide } from "svelte/transition";

    import MaterialIcon from "../MaterialIcon.svelte";
    import Button from "../inputs/Button.svelte";
    import Panel from "../dashboard/Panel.svelte";
    import Star from "../svg/material/Star.svelte";
    import SearchCard from "./SearchCard.svelte";
    import QuestionCard from "./QuestionCard.svelte";
    import TabView from "../TabView.svelte";
    import Title from "../Title.svelte";
    import QuestionSummary from "./QuestionSummary.svelte";
    import ResponseAnalysis from "./ResponseAnalysis.svelte";

    import { getConsultationDetailUrl } from "../../global/routes.ts";
    import { createFetchStore } from "../../global/stores.ts";

    export let consultationId: string = "";
    export let questionId: string = "";

    const PAGE_SIZE = 50;

    let currPage: number = 1;
    let hasMorePages: boolean = true;
    let answers = [];

    const TabNames = {
        QuestionSummary: "tab-question-summary",
        ResponseAnalysis: "tab-response-analysis",
    }

    let activeTab = TabNames.QuestionSummary;

    let searchValue: string = "";
    let searchMode: "keyword" | "semantic" = "keyword";
    let themeFilters: string[] = [];
    let demoFilters: {[key: string]: string[]} = {};
    let evidenceRich: boolean = false;

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
            await loadAnswers(`/api/consultations/${consultationId}/questions/${questionId}/filtered-responses/${queryString}`);

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
                // params.append("demoFilters", `${key}:${filterArr.join(",")}`);
                params.append("demoFilters", `${key}:${filterArr[0]}`);
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
        <MaterialIcon class="shrink-0">
            <Star />
        </MaterialIcon>
        <span class="text-sm">Back to all questions</span>
    </Button>

    <small>
        Choose a different question to analyse
    </small>
</section>

<section class="my-4">
    {#if $isConsultationLoading}
        <p transition:slide>Loading consultation</p>
    {:else if $consultationError}
        <p transition:slide>Consultation Error: {$consultationError}</p>
    {:else}
        <QuestionCard
            clickable={true}
            consultationId={$consultationData.id}
            question={$consultationData.questions?.find(question => question.id === questionId)}
        />
    {/if}
</section>

<TabView
    value={activeTab}
    onValueChange={({ curr, next }) => activeTab = next}
    tabs={[
        {
            id: TabNames.QuestionSummary,
            title: 'Question summary',
            component: QuestionSummary,
            props: {
                themes: Object.keys($themeAggrData?.theme_aggregations || []).map(themeId => {
                    return ({
                        count: $themeAggrData?.theme_aggregations[themeId],
                        ...($themeInfoData?.themes?.find(themeInfo => themeInfo.id === themeId)),
                    })
                }),
                totalAnswers: $answersData?.respondents_total,
            }
        },
        {
            id: TabNames.ResponseAnalysis,
            title: 'Response analysis',
            component: ResponseAnalysis,
            props: {
                answers: answers,
                isAnswersLoading: $isAnswersLoading,
                answersError: $answersError,
                filteredTotal: $answersData?.filtered_total,
                hasMorePages: hasMorePages,
                handleLoadClick: () => loadData({
                    searchValue: searchValue,
                    searchMode: searchMode,
                    themeFilters: themeFilters,
                    evidenceRich: evidenceRich,
                    demoFilters: demoFilters,
                }),
            }
        },
    ]}
/>
<div class="my-4">
    <Button variant="outline" handleClick={() => {
        console.log(TabNames.ResponseAnalysis)
        activeTab = TabNames.ResponseAnalysis
    }}>
        Change Tab
    </Button>
</div>

<div class="my-4">
    <Button variant="outline" handleClick={() => evidenceRich = !evidenceRich}>
        Toggle Evidence Rich
    </Button>
</div>