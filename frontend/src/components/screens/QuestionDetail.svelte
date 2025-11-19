<script lang="ts">
  import clsx from "clsx";

  import { onMount, untrack } from "svelte";
  import type { Writable } from "svelte/store";

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

  import {
    getApiAnswersUrl,
    getApiConsultationUrl,
    getApiQuestionsUrl,
    getConsultationDetailUrl,
  } from "../../global/routes.ts";

  import { createFetchStore } from "../../global/stores.ts";
  import {
    SearchModeValues,
    TabNames,
    type AnswersResponse,
    type ConsultationResponse,
    type DemoAggrResponse,
    type DemoOption,
    type DemoOptionsResponse,
    type DemoOptionsResponseItem,
    type FormattedTheme,
    type MultiChoiceResponse,
    type Question,
    type ResponseAnswer,
    type ThemeAggrResponse,
    type ThemeInfoResponse,
  } from "../../global/types.ts";
  import {
    themeFilters,
    demoFilters,
    multiAnswerFilters,
  } from "../../global/state.svelte.ts";
  import Panel from "../dashboard/Panel/Panel.svelte";

  interface QueryFilters {
    questionId: string;
    searchValue: string;
    themeFilters: string[];
    searchMode: SearchModeValues;
    evidenceRich: boolean;
    flaggedOnly: boolean;
    demoFilters: string[];
    multiAnswerFilters: string[];
  }

  interface Props {
    consultationId: string;
    questionId: string;
  }

  let { consultationId = "", questionId = "" }: Props = $props();

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

  const consultationStore = createFetchStore();
  const questionsStore = createFetchStore();
  const questionStore = createFetchStore();
  const answersStore = createFetchStore();
  const themeAggrStore = createFetchStore();
  const themeInfoStore = createFetchStore();
  const demoOptionsStore = createFetchStore();
  const demoAggrStore = createFetchStore();

  onMount(() => {
    // Load consultation and questions data once on mount
    $consultationStore.fetch(getApiConsultationUrl(consultationId));
    $questionsStore.fetch(getApiQuestionsUrl(consultationId));
  });

  async function loadData() {
    const queryString = buildQuery({
      questionId: questionId,
      searchValue: searchValue,
      searchMode: searchMode,
      themeFilters: themeFilters.filters,
      evidenceRich: evidenceRich,
      demoFilters: demoFilters.filters,
      flaggedOnly: flaggedOnly,
      multiAnswerFilters: multiAnswerFilters.filters,
    });

    // Skip the rest of the requests if they are already requested for this filter set
    if (currPage === 1) {
      $themeAggrStore.fetch(
        `/api/consultations/${consultationId}/responses/theme-aggregations/${queryString}&question_id=${questionId}`,
      );
      $themeInfoStore.fetch(
        `/api/consultations/${consultationId}/questions/${questionId}/theme-information/${queryString}`,
      );
      $demoOptionsStore.fetch(
        `/api/consultations/${consultationId}/demographic-options/${queryString}`,
      );
      $demoAggrStore.fetch(
        `/api/consultations/${consultationId}/responses/demographic-aggregations/${queryString}&question_id=${questionId}`,
      );
      $questionStore.fetch(
        `/api/consultations/${consultationId}/questions/${questionId}/${queryString}`,
      );
    }

    // Append next page of answers to existing answers
    try {
      await $answersStore.fetch(`${getApiAnswersUrl(consultationId)}${queryString}`);

      if ($answersStore.data.all_respondents) {
        const newAnswers = $answersStore.data.all_respondents;
        answers = [...answers, ...newAnswers];
      }
      hasMorePages = $answersStore.data.has_more_pages || false;
    } catch {}

    currPage += 1;
  }

  function buildQuery(filters: QueryFilters) {
    const params = new URLSearchParams({
      ...(filters.questionId && {
        question_id: filters.questionId,
      }),
      ...(filters.searchValue && {
        searchValue: filters.searchValue,
      }),
      ...(filters.themeFilters.length > 0 && {
        themeFilters: filters.themeFilters.join(","),
      }),
      ...(searchMode && {
        searchMode: filters.searchMode,
      }),
      ...(filters.evidenceRich && {
        evidenceRich: JSON.stringify(filters.evidenceRich),
      }),
      ...(filters.flaggedOnly && {
        is_flagged: JSON.stringify(filters.flaggedOnly),
      }),
      ...(filters.multiAnswerFilters.length > 0 && {
        multiple_choice_answer: filters.multiAnswerFilters.join(","),
      }),
      page: currPage.toString(),
      page_size: PAGE_SIZE.toString(),
    });

    // Add demographic filters (now just an array of IDs)
    if (filters.demoFilters.length > 0) {
      params.set("demographics", filters.demoFilters.join(","));
    }

    const queryString = params.toString();
    return queryString ? `?${queryString}` : "";
  }

  function resetAnswers() {
    answers = [];
    currPage = 1;
    hasMorePages = true;
  }

  const resetFilters = () => {
    themeFilters.reset();
    demoFilters.reset();
    multiAnswerFilters.reset();
    evidenceRich = false;
    searchValue = "";
    flaggedOnly = false;
  };

  const anyFilterApplied = () => {
    return Boolean(
      themeFilters.applied() ||
        demoFilters.applied() ||
        multiAnswerFilters.applied() ||
        evidenceRich ||
        searchValue ||
        flaggedOnly,
    );
  };

  const setEvidenceRich = (value: boolean) => (evidenceRich = value);

  $effect(() => {
    // @ts-ignore: ignore dependencies
    (searchValue,
      searchMode,
      themeFilters.filters,
      evidenceRich,
      demoFilters.filters,
      multiAnswerFilters.filters,
      flaggedOnly);

    resetAnswers();

    // do not track deep dependencies
    untrack(() => loadData());
  });

  let question = $derived(
    $questionsStore.data?.results?.find((question) => question.id === questionId),
  );

  let formattedDemoOptions = $derived.by(() => {
    if (!$demoOptionsStore.data) {
      return;
    }

    const formattedData: DemoOption = {};
    const categories = [...new Set($demoOptionsStore.data.map((data) => data.name))];

    for (const category of categories) {
      const categoryData: DemoOptionsResponseItem[] = $demoOptionsStore.data.filter(
        (opt) => opt.name === category,
      );

      formattedData[category] = categoryData
        .map((opt) => opt.value)
        .filter((value) => value !== null && value !== undefined);
    }
    return formattedData;
  });
</script>

<section
  class={clsx([
    "flex",
    "justify-between",
    "flex-wrap",
    "gap-2",
    "items-center",
  ])}
>
  <Button
    handleClick={() => {
      window.location.href = getConsultationDetailUrl(consultationId);
    }}
  >
    <div class="flex items-center gap-2 justify-between">
      <div class="rotate-90">
        <MaterialIcon color="fill-neutral-600">
          <KeyboardArrowDown />
        </MaterialIcon>
      </div>

      <span class="text-sm">Back to all questions</span>
    </div>
  </Button>

  <!-- Text disabled temporarily, div kept to maintain layout -->
  <div>
    <!-- <small>
            Choose a different question to analyse
        </small> -->
  </div>
</section>

<svelte:boundary>
  <section class="my-4">
    {#if $consultationStore.error || $questionsStore.error}
      <div class="my-2">
        <Alert>
          <span class="text-sm">
            Question Details Error: {$consultationStore.error || $questionsStore.error}
          </span>
        </Alert>
      </div>
    {:else}
      <QuestionCard
        skeleton={$questionsStore.isLoading || $consultationStore.isLoading}
        clickable={false}
        consultationId={$consultationStore.data?.id}
        {question}
        hideIcon={true}
        horizontal={true}
      />
    {/if}
  </section>

  {#snippet failed(error)}
    <div>
      {console.error(error)}

      <Panel>
        <Alert>Unexpected question error</Alert>
      </Panel>
    </div>
  {/snippet}
</svelte:boundary>

<svelte:boundary>
  <TabView
    value={activeTab}
    handleChange={(next: string) => (activeTab = next as TabNames)}
    tabs={[
      { id: TabNames.QuestionSummary, title: "Question Summary", icon: Lan },

      //  No second tab without free text
      ...($questionStore.data?.has_free_text
        ? [
            {
              id: TabNames.ResponseAnalysis,
              title: "Response Analysis",
              icon: Finance,
            },
          ]
        : []),
    ]}
  >
    {#if activeTab === TabNames.QuestionSummary}
      <QuestionSummary
        showThemes={Boolean($questionStore.isLoading || $questionStore.data?.has_free_text)}
        themes={Object.keys($themeAggrStore.data?.theme_aggregations || []).map(
          (themeId) => {
            return {
              id: themeId,
              count: $themeAggrStore.data?.theme_aggregations[themeId],
              highlighted: themeFilters.filters.includes(themeId),
              handleClick: () => themeFilters.update(themeId),
              ...$themeInfoStore.data?.themes?.find(
                (themeInfo) => themeInfo?.id === themeId,
              ),
            };
          },
        ) as FormattedTheme[]}
        themesLoading={$themeAggrStore.isLoading}
        totalAnswers={question?.total_responses || 0}
        filteredTotal={$answersStore.data?.filtered_total}
        demoData={$demoAggrStore.data?.demographic_aggregations}
        demoOptions={formattedDemoOptions || {}}
        demoOptionsData={$demoOptionsStore.data}
        multiChoice={$questionStore.data?.multiple_choice_answer?.filter((item) =>
          Boolean(item.text),
        ) || []}
        consultationCode={$consultationStore.data?.code}
        {evidenceRich}
        {searchValue}
        {sortAscending}
        setActiveTab={(newTab) => (activeTab = newTab)}
        anyFilterApplied={anyFilterApplied()}
      />
    {:else if activeTab === TabNames.ResponseAnalysis}
      <ResponseAnalysis
        consultationId={$consultationStore.data?.id}
        questionId={question?.id}
        pageSize={PAGE_SIZE}
        {answers}
        isAnswersLoading={$answersStore.isLoading}
        answersError={$answersStore.error}
        filteredTotal={$answersStore.data?.filtered_total}
        {hasMorePages}
        handleLoadClick={() => loadData()}
        resetData={() => {
          resetAnswers();
          loadData();
        }}
        {searchValue}
        setSearchValue={(value) => (searchValue = value)}
        {searchMode}
        setSearchMode={(newSearchMode: SearchModeValues) =>
          (searchMode = newSearchMode)}
        demoData={$demoAggrStore.data?.demographic_aggregations}
        demoOptions={formattedDemoOptions || {}}
        demoOptionsData={$demoOptionsStore.data}
        themes={$themeInfoStore.data?.themes}
        {evidenceRich}
        {setEvidenceRich}
        isThemesLoading={$themeAggrStore.isLoading}
        {flaggedOnly}
        setFlaggedOnly={(newValue) => (flaggedOnly = newValue)}
        anyFilterApplied={anyFilterApplied()}
        {resetFilters}
      />
    {/if}
  </TabView>

  {#snippet failed(error)}
    <div>
      {console.error(error)}

      <Panel>
        <Alert>Unexpected tab error</Alert>
      </Panel>
    </div>
  {/snippet}
</svelte:boundary>
