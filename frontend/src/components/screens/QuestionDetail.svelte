<script lang="ts">
  import clsx from "clsx";

  import { onMount, untrack } from "svelte";
  import { SvelteURLSearchParams } from "svelte/reactivity";

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
    getApiConsultationUrl,
    getApiDemographicsUrl,
    getApiQuestionResponsesUrl,
    getApiQuestionThemesUrl,
    getApiQuestionUrl,
    getConsultationDetailUrl,
  } from "../../global/routes.ts";

  import { createFetchStore } from "../../global/stores.ts";
  import {
    SearchModeValues,
    TabNames,
    type AnswersResponse,
    type ConsultationResponse,
    type DemoData,
    type DemoOption,
    type DemoOptionsResponse,
    type DemoOptionsResponseItem,
    type FormattedTheme,
    type Question,
    type ResponseAnswer,
    type ThemeInfoResponse,
  } from "../../global/types.ts";
  import {
    themeFilters,
    demoFilters,
    multiAnswerFilters,
  } from "../../global/state.svelte.ts";
  import Panel from "../dashboard/Panel/Panel.svelte";

  interface QueryFilters {
    searchValue: string;
    themeFilters: string[];
    searchMode: SearchModeValues;
    evidenceRich: boolean;
    unseenResponsesOnly: boolean;
    flaggedOnly: boolean;
    demoFilters: string[];
    multiAnswerFilters: string[];
  }

  interface Props {
    consultationId: string;
    questionId: string;
  }

  let { consultationId = "", questionId = "" }: Props = $props();

  const PAGE_SIZE: number = 5;

  let currPage: number = $state(1);
  let hasMorePages: boolean = $state(true);
  let answers: ResponseAnswer[] = $state([]);

  let activeTab: TabNames = $state(TabNames.QuestionSummary);

  let searchValue: string = $state("");
  let searchMode: SearchModeValues = $state(SearchModeValues.KEYWORD);
  let evidenceRich: boolean = $state(false);
  let unseenResponsesOnly: boolean = $state(false);
  let sortAscending: boolean = $state(false);
  let flaggedOnly: boolean = $state(false);
  let dataRequested: boolean = $state(false);
  let isAnswersLoading: boolean = $state(true);

  const consultationStore = createFetchStore<ConsultationResponse>();
  const questionStore = createFetchStore<Question>();
  const answersStore = createFetchStore<AnswersResponse>();
  const themesStore = createFetchStore<ThemeInfoResponse>();
  const demographicsStore = createFetchStore<DemoOptionsResponse>();

  onMount(() => {
    $consultationStore.fetch(getApiConsultationUrl(consultationId));
    $questionStore.fetch(getApiQuestionUrl(consultationId, questionId));
    dataRequested = true;
  });

  async function loadData() {
    isAnswersLoading = true;
    const filters = {
      searchValue: searchValue,
      searchMode: searchMode,
      themeFilters: themeFilters.filters,
      evidenceRich: evidenceRich,
      unseenResponsesOnly: unseenResponsesOnly,
      demoFilters: demoFilters.filters,
      flaggedOnly: flaggedOnly,
      multiAnswerFilters: multiAnswerFilters.filters,
    };
    const filterQs = buildQueryString(filters);
    const responseQs = buildQueryString(filters, { includeSearch: true });

    // Only fetch aggregations on the first page (filters haven't changed for subsequent pages)
    if (currPage === 1) {
      $questionStore.fetch(
        `${getApiQuestionUrl(consultationId, questionId)}${filterQs}`,
      );
      $themesStore.fetch(
        `${getApiQuestionThemesUrl(consultationId, questionId)}${filterQs}`,
      );
      $demographicsStore.fetch(
        `${getApiDemographicsUrl(consultationId)}${filterQs}${filterQs ? "&" : "?"}question_id=${questionId}`,
      );
    }

    // Append next page of answers to existing answers
    await $answersStore.fetch(
      `${getApiQuestionResponsesUrl(consultationId, questionId)}${responseQs}`,
    );

    if ($answersStore.data?.all_respondents) {
      const newAnswers = $answersStore.data?.all_respondents;
      answers = [...answers, ...newAnswers];
    }
    isAnswersLoading = false;
    hasMorePages = $answersStore.data?.has_more_pages || false;

    currPage += 1;
  }

  function buildQueryString(
    filters: QueryFilters,
    { includeSearch = false }: { includeSearch?: boolean } = {},
  ) {
    const searchParams = {
      searchValue: filters.searchValue,
      searchMode: filters.searchMode,
      page: currPage.toString(),
      page_size: PAGE_SIZE.toString(),
    };

    const params = new SvelteURLSearchParams({
      ...(filters.themeFilters.length > 0 && {
        themeFilters: filters.themeFilters.join(","),
      }),
      ...(filters.evidenceRich && {
        evidenceRich: JSON.stringify(filters.evidenceRich),
      }),
      ...(filters.unseenResponsesOnly && {
        unseenResponsesOnly: JSON.stringify(filters.unseenResponsesOnly),
      }),
      ...(filters.flaggedOnly && {
        is_flagged: JSON.stringify(filters.flaggedOnly),
      }),
      ...(filters.multiAnswerFilters.length > 0 && {
        multiple_choice_answer: filters.multiAnswerFilters.join(","),
      }),
      ...(filters.demoFilters.length > 0 && {
        demographics: filters.demoFilters.join(","),
      }),
      ...(includeSearch && searchParams),
    });

    const qs = params.toString();
    return qs ? `?${qs}` : "";
  }

  function resetAnswers() {
    answers = [];
    currPage = 1;
    hasMorePages = true;
    isAnswersLoading = true;
  }

  const resetFilters = () => {
    themeFilters.reset();
    demoFilters.reset();
    multiAnswerFilters.reset();
    evidenceRich = false;
    unseenResponsesOnly = false;
    searchValue = "";
    flaggedOnly = false;
  };

  const anyFilterApplied = () => {
    return Boolean(
      themeFilters.applied() ||
        demoFilters.applied() ||
        multiAnswerFilters.applied() ||
        evidenceRich ||
        unseenResponsesOnly ||
        searchValue ||
        flaggedOnly,
    );
  };

  const setEvidenceRich = (value: boolean) => (evidenceRich = value);
  const setUnseenResponses = (value: boolean) => (unseenResponsesOnly = value);

  $effect(() => {
    void searchValue;
    void searchMode;
    void themeFilters.filters;
    void evidenceRich;
    void unseenResponsesOnly;
    void demoFilters.filters;
    void multiAnswerFilters.filters;
    void flaggedOnly;

    resetAnswers();

    // do not track deep dependencies
    untrack(() => loadData());
  });

  let formattedDemoOptions = $derived.by(() => {
    if (!$demographicsStore.data) {
      return;
    }

    const formattedData: DemoOption = {};
    const categories = [
      ...new Set($demographicsStore.data.map((data) => data.name)),
    ];

    for (const category of categories) {
      const categoryData: DemoOptionsResponseItem[] =
        $demographicsStore.data.filter((opt) => opt.name === category);

      formattedData[category] = categoryData
        .map((opt) => opt.value)
        .filter((value) => value !== null && value !== undefined);
    }
    return formattedData;
  });

  let demoData = $derived.by(() => {
    if (!$demographicsStore.data) {
      return {};
    }

    const result: DemoData = {};
    for (const item of $demographicsStore.data) {
      if (!result[item.name]) {
        result[item.name] = {};
      }
      result[item.name][item.value] = item.count;
    }
    return result;
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
    <div class="flex items-center justify-between gap-2">
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
    {#if $consultationStore.error || $questionStore.error}
      <div class="my-2">
        <Alert>
          <span class="text-sm">
            Question Details Error: {$consultationStore.error ||
              $questionStore.error}
          </span>
        </Alert>
      </div>
    {:else}
      <QuestionCard
        skeleton={!dataRequested ||
          $questionStore.isLoading ||
          $consultationStore.isLoading}
        clickable={false}
        consultationId={$consultationStore.data?.id || ""}
        question={$questionStore.data || {}}
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
        showThemes={Boolean(
          !dataRequested ||
            $questionStore.isLoading ||
            $questionStore.data?.has_free_text,
        )}
        themes={($themesStore.data?.themes || []).map((theme) => ({
          ...theme,
          highlighted: themeFilters.filters.includes(theme.id),
          handleClick: () => themeFilters.update(theme.id),
        })) as FormattedTheme[]}
        themesLoading={!dataRequested || $themesStore.isLoading}
        filtersLoading={!dataRequested || $demographicsStore.isLoading}
        totalAnswers={$questionStore.data?.total_responses || 0}
        {demoData}
        demoOptions={formattedDemoOptions || {}}
        demoOptionsData={$demographicsStore.data || undefined}
        multiChoice={$questionStore.data?.multiple_choice_answer?.filter(
          (item) => Boolean(item.text),
        ) || []}
        consultationCode={$consultationStore.data?.code}
        {sortAscending}
        setActiveTab={(newTab) => (activeTab = newTab)}
        anyFilterApplied={anyFilterApplied()}
      />
    {:else if activeTab === TabNames.ResponseAnalysis}
      <ResponseAnalysis
        consultationId={$consultationStore.data?.id}
        questionId={$questionStore.data?.id}
        pageSize={PAGE_SIZE}
        {answers}
        {isAnswersLoading}
        answersError={$answersStore.error}
        filteredTotal={$answersStore.data?.filtered_total}
        {hasMorePages}
        handleLoadClick={() => loadData()}
        resetData={() => {
          resetAnswers();
          loadData();
        }}
        {searchValue}
        setSearchValue={(value: string) => (searchValue = value)}
        {demoData}
        demoOptions={formattedDemoOptions || {}}
        demoOptionsData={$demographicsStore.data || undefined}
        themes={$themesStore.data?.themes}
        {evidenceRich}
        {setEvidenceRich}
        unseenResponses={unseenResponsesOnly}
        {setUnseenResponses}
        isFiltersLoading={!dataRequested || $demographicsStore.isLoading}
        {flaggedOnly}
        setFlaggedOnly={(newValue: boolean) => (flaggedOnly = newValue)}
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
