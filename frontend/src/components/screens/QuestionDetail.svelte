<script lang="ts">
    import clsx from "clsx";

    import { onMount, untrack } from "svelte";
    import type { Writable } from "svelte/store"

    import MaterialIcon from "../MaterialIcon.svelte";
    import Button from "../inputs/Button/Button.svelte";
    import QuestionCard from "../dashboard/QuestionCard/QuestionCard.svelte";
    import TabView from "../TabView/TabView.svelte";
    import QuestionSummary from "../dashboard/QuestionSummary/QuestionSummary.svelte";
    import ResponseAnalysis from "../dashboard/ResponseAnalysis/ResponseAnalysis.svelte";
    import Alert from "../Alert.svelte";
    import KeyboardArrowDown from "../svg/material/KeyboardArrowDown.svelte";
    import Lan from "../svg/material/Lan.svelte";
    import Finance from "../svg/material/Finance.svelte";

    import { getConsultationDetailUrl } from "../../global/routes.ts";
    import { createFetchStore } from "../../global/stores.ts";
    import {
        SearchModeValues,
        TabNames,
        type AnswersResponse,
        type ConsultationResponse,
        type DemoAggrResponse,
        type DemoOptionsResponse,
        type FormattedTheme,
        type MultiChoiceResponse,
        type ResponseAnswer,
        type ThemeAggrResponse,
        type ThemeInfoResponse
    } from "../../global/types.ts";
    import { themeFilters, demoFilters, multiAnswerFilters } from "../../global/state.svelte.ts";


    interface QueryFilters {
        searchValue: string;
        themeFilters: string[];
        searchMode: SearchModeValues;
        evidenceRich: boolean;
        flaggedOnly: boolean;
        demoFilters: {[category:string]: string[]}
    }

    interface Props {
        consultationId: string;
        questionId: string;
    }

    let {
        consultationId = "",
        questionId = "",
    }: Props = $props();

    const PAGE_SIZE: number = 50;
    const MAX_THEME_FILTERS: number = Infinity;

    let currPage: number = $state(1);
    let hasMorePages: boolean = $state(true);
    let answers: ResponseAnswer[] = $state([]);

    let activeTab: TabNames = $state(TabNames.QuestionSummary);

    let searchValue: string = $state("");
    let searchMode: SearchModeValues = $state(SearchModeValues.KEYWORD);
    let evidenceRich: boolean = $state(false);
    let sortAscending: boolean = $state(false);
    let flaggedOnly: boolean = $state(false);

    const {
        loading: isConsultationLoading,
        error: consultationError,
        load: loadConsultation,
        data: consultationData,
    }: {
        loading: Writable<boolean>,
        error: Writable<string>,
        load: Function,
        data: Writable<ConsultationResponse>,
    } = createFetchStore();

    const {
        loading: isAnswersLoading,
        error: answersError,
        load: loadAnswers,
        data: answersData,
    }: {
        loading: Writable<boolean>,
        error: Writable<string>,
        load: Function,
        data: Writable<AnswersResponse>,
    } = createFetchStore();

    const {
        loading: isThemeAggrLoading,
        error: themeAggrError,
        load: loadThemeAggr,
        data: themeAggrData,
    }: {
        loading: Writable<boolean>,
        error: Writable<string>,
        load: Function,
        data: Writable<ThemeAggrResponse>,
    } = createFetchStore();

    const {
        loading: isThemeInfoLoading,
        error: themeInfoError,
        load: loadThemeInfo,
        data: themeInfoData,
    }: {
        loading: Writable<boolean>,
        error: Writable<string>,
        load: Function,
        data: Writable<ThemeInfoResponse>,
    } = createFetchStore();

    const {
        loading: isDemoOptionsLoading,
        error: demoOptionsError,
        load: loadDemoOptions,
        data: demoOptionsData,
    }: {
        loading: Writable<boolean>,
        error: Writable<string>,
        load: Function,
        data: Writable<DemoOptionsResponse>,
    } = createFetchStore();

    const {
        loading: isDemoAggrLoading,
        error: demoAggrError,
        load: loadDemoAggr,
        data: demoAggrData,
    }: {
        loading: Writable<boolean>,
        error: Writable<string>,
        load: Function,
        data: Writable<DemoAggrResponse>,
    } = createFetchStore();

    const {
        loading: isMultiChoiceAggrLoading,
        error: multiChoiceAggrError,
        load: loadMultiChoiceAggr,
        data: multiChoiceAggrData,
    }: {
        loading: Writable<boolean>,
        error: Writable<string>,
        load: Function,
        data: Writable<MultiChoiceResponse>,
    } = createFetchStore();

    onMount(() => {
        // Load consultation data once on mount
        loadConsultation(`/api/consultations/${consultationId}/`);
    })

    async function loadData() {
        const queryString = buildQuery({
            searchValue: searchValue,
            searchMode: searchMode,
            themeFilters: themeFilters.filters,
            evidenceRich: evidenceRich,
            demoFilters: demoFilters.filters,
            flaggedOnly: flaggedOnly,
        });

        // Skip the rest of the requests if they are already requested for this filter set
        if (currPage === 1) {
            loadThemeAggr(`/api/consultations/${consultationId}/questions/${questionId}/responses/theme-aggregations/${queryString}`);
            loadThemeInfo(`/api/consultations/${consultationId}/questions/${questionId}/theme-information/${queryString}`);
            loadDemoOptions(`/api/consultations/${consultationId}/demographic-options/${queryString}`);
            loadDemoAggr(`/api/consultations/${consultationId}/questions/${questionId}/responses/demographic-aggregations/${queryString}`);
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

    function buildQuery(filters: QueryFilters) {
        const params = new URLSearchParams({
            ...(filters.searchValue && {
                searchValue: filters.searchValue
            }),
            ...(filters.themeFilters.length > 0 && {
                themeFilters: filters.themeFilters.join(",")
            }),
            ...(searchMode && {
                searchMode: filters.searchMode
            }),
            ...(filters.evidenceRich && {
                evidenceRich: JSON.stringify(filters.evidenceRich)
            }),
            ...(filters.flaggedOnly && {
                is_flagged: JSON.stringify(filters.flaggedOnly)
            }),
            page: currPage.toString(),
            page_size: PAGE_SIZE.toString(),
        })

        // Filter out demo filter keys with no value
        const validDemoFilterKeys = Object.keys(filters.demoFilters).filter(key => Boolean(filters.demoFilters[key]));
        // Add each demo filter as a duplicate demoFilter param
        for (const key of validDemoFilterKeys) {
            const filterArr: string[] = filters.demoFilters[key];

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

    const setEvidenceRich = (value: boolean) => evidenceRich = value;

    $effect(() => {
        // @ts-ignore: ignore dependencies
        searchValue, searchMode, themeFilters.filters, evidenceRich, demoFilters.filters, multiAnswerFilters.filters, flaggedOnly;

        resetAnswers();

        // do not track deep dependencies
        untrack(() => loadData());
    })

    let question = $derived($consultationData?.questions?.find(
        question => question.id === questionId
    ));
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
        <div class="flex items-center gap-2 justify-between">
            <div class="rotate-90">
                <MaterialIcon color="fill-neutral-600">
                    <KeyboardArrowDown />
                </MaterialIcon>
            </div>

            <span class="text-sm">Back to all questions</span>
        </div>
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
            consultationId={$consultationData?.id}
            question={question}
            hideIcon={true}
            horizontal={true}
        />
    {/if}
</section>

<TabView
    value={activeTab}
    handleChange={(next: string) => activeTab = next as TabNames}
    tabs={[
        { id: TabNames.QuestionSummary, title: "Question Summary", icon: Lan },
        { id: TabNames.ResponseAnalysis, title: "Response Analysis", icon: Finance},
    ]}
>
    {#if activeTab === TabNames.QuestionSummary}
        <QuestionSummary
            themes={Object.keys($themeAggrData?.theme_aggregations || []).map(themeId => {
                return ({
                    id: themeId,
                    count: $themeAggrData?.theme_aggregations[themeId],
                    highlighted: themeFilters.filters.includes(themeId),
                    handleClick: () => themeFilters.update(themeId),
                    ...($themeInfoData?.themes?.find(themeInfo => themeInfo?.id === themeId)),
                })
            }) as FormattedTheme[]}
            themesLoading={$isThemeAggrLoading}
            totalAnswers={question?.total_responses || 0}
            filteredTotal={$answersData?.filtered_total}
            demoData={$demoAggrData?.demographic_aggregations}
            demoOptions={$demoOptionsData?.demographic_options}
            multiChoice={$multiChoiceAggrData?.filter(item => Boolean(item.answer))}
            consultationSlug={$consultationData?.slug}
            evidenceRich={evidenceRich}
            searchValue={searchValue}
            sortAscending={sortAscending}
            setActiveTab={(newTab) => activeTab = newTab}
        />
    {:else if activeTab === TabNames.ResponseAnalysis}
        <ResponseAnalysis
            consultationId={$consultationData?.id}
            questionId={question?.id}
            pageSize={PAGE_SIZE}
            answers={answers}
            isAnswersLoading={$isAnswersLoading}
            answersError={$answersError}
            filteredTotal={$answersData?.filtered_total}
            hasMorePages={hasMorePages}
            handleLoadClick={() => loadData()}
            resetData={() => {
                resetAnswers();
                loadData();
            }}
            searchValue={searchValue}
            setSearchValue={(value) => searchValue = value}
            searchMode={searchMode}
            setSearchMode={(newSearchMode: SearchModeValues) => searchMode = newSearchMode}
            demoData={$demoAggrData?.demographic_aggregations}
            demoOptions={$demoOptionsData?.demographic_options}
            themes={$themeInfoData?.themes}
            evidenceRich={evidenceRich}
            setEvidenceRich={setEvidenceRich}
            isThemesLoading={$isThemeAggrLoading}
            flaggedOnly={flaggedOnly}
            setFlaggedOnly={(newValue) => flaggedOnly = newValue}
        />
    {/if}
</TabView>