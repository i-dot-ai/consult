<script lang="ts">
  import clsx from "clsx";

  import { onMount, untrack } from "svelte";
  import { SvelteURLSearchParams } from "svelte/reactivity";
  import { slide, fly, fade } from "svelte/transition";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import QuestionCard from "../../dashboard/QuestionCard/QuestionCard.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import Alert from "../../Alert.svelte";
  import KeyboardArrowDown from "../../svg/material/KeyboardArrowDown.svelte";
  import Lan from "../../svg/material/Lan.svelte";
  import FilterAlt from "../../svg/material/FilterAlt.svelte";
  import Flag2 from "../../svg/material/Flag2.svelte";
  import Finance from "../../svg/material/Finance.svelte";

  import {
    getApiConsultationUrl,
    getApiDemographicsUrl,
    getApiQuestionResponsesUrl,
    getApiQuestionThemesUrl,
    getApiQuestionUrl,
    getConsultationDetailUrl,
    updateResponseReadStatus,
  } from "../../../global/routes.ts";

  import { createFetchStore } from "../../../global/stores.ts";
  import {
    SearchModeValues,
    type ResponsesBody,
    type ConsultationResponse,
    type DemoOptionsResponse,
    type FormattedTheme,
    type Question,
    type ThemeInfoResponse,
    type ResponseBody,
  } from "../../../global/types.ts";
  import {
    themeFilters,
    demoFilters,
    multiAnswerFilters,
  } from "../../../global/state.svelte.ts";
  import FiltersSidebar from "../../dashboard/FiltersSidebar/FiltersSidebar.svelte";
  import MultiChoice from "../../dashboard/MultiChoice/MultiChoice.svelte";
  import ThemesTable from "../../dashboard/ThemesTable/ThemesTable.svelte";
  import TitleRow from "../../dashboard/TitleRow.svelte";
  import CsvDownload from "../../CsvDownload/CsvDownload.svelte";
  import NotFoundMessage from "../../NotFoundMessage/NotFoundMessage.svelte";
  import ResponseCard from "../../dashboard/ResponseCard/ResponseCard.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import Switch from "../../inputs/Switch/Switch.svelte";
  import Diamond from "../../svg/material/Diamond.svelte";
  import Visibility from "../../svg/material/Visibility.svelte";
  import { getPercentage } from "../../../global/utils.ts";

  const PINNED_BOTTOM_THEMES = ["no reason given", "other"];

  const sortThemes = (
    a: { name: string; count: number },
    b: { name: string; count: number },
  ) => {
    const aIsPinned = PINNED_BOTTOM_THEMES.includes(a.name.toLowerCase());
    const bIsPinned = PINNED_BOTTOM_THEMES.includes(b.name.toLowerCase());
    if (aIsPinned !== bIsPinned) return aIsPinned ? 1 : -1;
    return b.count - a.count;
  };

  interface QueryFilters {
    searchValue: string;
    themeFilters: string[];
    searchMode: SearchModeValues;
    evidenceRich: boolean;
    unread: boolean;
    flagged: boolean;
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
  let responses: ResponseBody[] = $state([]);
  let responseTotalCount: number | null = $state(null);
  let lastAggregationQs: string | null = $state(null);

  let searchValue: string = $state("");
  let searchMode: SearchModeValues = $state(SearchModeValues.KEYWORD);
  let evidenceRich: boolean = $state(false);
  let unread: boolean = $state(false);
  let flagged: boolean = $state(false);
  let dataRequested: boolean = $state(false);
  let isResponsesLoading: boolean = $state(true);

  const consultationStore = createFetchStore<ConsultationResponse>();
  const questionStore = createFetchStore<Question>();
  const responsesStore = createFetchStore<ResponsesBody>();
  const themesStore = createFetchStore<ThemeInfoResponse>();
  const demographicsStore = createFetchStore<DemoOptionsResponse>();

  onMount(() => {
    $consultationStore.fetch(getApiConsultationUrl(consultationId));
    $questionStore.fetch(getApiQuestionUrl(consultationId, questionId));
    dataRequested = true;
  });

  async function loadData() {
    isResponsesLoading = true;
    const baseFilters = {
      searchValue: searchValue,
      searchMode: searchMode,
      themeFilters: themeFilters.filters,
      evidenceRich: false,
      unread: false,
      demoFilters: demoFilters.filters,
      flagged: false,
      multiAnswerFilters: multiAnswerFilters.filters,
    };
    const responseFilters = {
      ...baseFilters,
      evidenceRich: evidenceRich,
      unread: unread,
      flagged: flagged,
    };
    const aggregationQs = buildQueryString(baseFilters);
    const responseQs = buildQueryString(responseFilters, {
      includePagination: true,
    });

    if (aggregationQs !== lastAggregationQs) {
      lastAggregationQs = aggregationQs;
      $questionStore.fetch(
        `${getApiQuestionUrl(consultationId, questionId)}${aggregationQs}`,
      );
      $themesStore.fetch(
        `${getApiQuestionThemesUrl(consultationId, questionId)}${aggregationQs}`,
      );
      $demographicsStore.fetch(
        `${getApiDemographicsUrl(consultationId)}${aggregationQs}${aggregationQs ? "&" : "?"}question_id=${questionId}`,
      );
    }

    // Append next page of answers to existing answers
    await $responsesStore.fetch(
      `${getApiQuestionResponsesUrl(consultationId, questionId)}${responseQs}`,
    );

    if ($responsesStore.data?.all_respondents) {
      const newResponses = $responsesStore.data?.all_respondents;
      responses = [...responses, ...newResponses];
    }
    if ($responsesStore.data?.total_count !== undefined) {
      responseTotalCount = $responsesStore.data.total_count;
    }
    isResponsesLoading = false;
    hasMorePages = $responsesStore.data?.has_more_pages || false;

    currPage += 1;
  }

  function buildQueryString(
    filters: QueryFilters,
    { includePagination = false }: { includePagination?: boolean } = {},
  ) {
    const params = new SvelteURLSearchParams({
      ...(filters.searchValue && {
        searchValue: filters.searchValue,
        searchMode: filters.searchMode,
      }),
      ...(filters.themeFilters.length > 0 && {
        themeFilters: filters.themeFilters.join(","),
      }),
      ...(filters.evidenceRich && {
        evidenceRich: JSON.stringify(filters.evidenceRich),
      }),
      ...(filters.unread && {
        unseenResponsesOnly: JSON.stringify(filters.unread),
      }),
      ...(filters.flagged && {
        is_flagged: JSON.stringify(filters.flagged),
      }),
      ...(filters.multiAnswerFilters.length > 0 && {
        multiple_choice_answer: filters.multiAnswerFilters.join(","),
      }),
      ...(filters.demoFilters.length > 0 && {
        demographics: filters.demoFilters.join(","),
      }),
      ...(includePagination && {
        page: currPage.toString(),
        page_size: PAGE_SIZE.toString(),
      }),
    });

    const qs = params.toString();
    return qs ? `?${qs}` : "";
  }

  function resetAnswers() {
    responses = [];
    currPage = 1;
    hasMorePages = true;
    isResponsesLoading = true;
    responseTotalCount = null;
  }

  const resetFilters = () => {
    themeFilters.reset();
    demoFilters.reset();
    multiAnswerFilters.reset();
    evidenceRich = false;
    unread = false;
    searchValue = "";
    flagged = false;
  };

  const anyFilterApplied = () => {
    return Boolean(
      themeFilters.applied() ||
        demoFilters.applied() ||
        multiAnswerFilters.applied() ||
        searchValue,
    );
  };

  $effect(() => {
    void searchValue;
    void searchMode;
    void themeFilters.filters;
    void evidenceRich;
    void unread;
    void demoFilters.filters;
    void multiAnswerFilters.filters;
    void flagged;

    resetAnswers();

    // do not track deep dependencies
    untrack(() => loadData());
  });

  async function markResponsesAsRead() {
    if (responses.length === 0) return;
    await Promise.all(
      responses.map((response) =>
        fetch(updateResponseReadStatus(consultationId, response.id), {
          method: "POST",
        }),
      ),
    );
  }

  let demographics = $derived($demographicsStore.data || []);
  let hasFreeText = $derived($questionStore.data?.has_free_text ?? true);
  let themes: FormattedTheme[] = $derived(
    ($themesStore.data?.themes || [])
      .map((theme) => ({
        ...theme,
        highlighted: themeFilters.filters.includes(theme.id),
        handleClick: () => themeFilters.update(theme.id),
      }))
      .sort(sortThemes) as FormattedTheme[],
  );

  const BASE_FLY_DELAY = 100;
  function getDelay(index: number): number {
    return BASE_FLY_DELAY * (index % PAGE_SIZE);
  }
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
    testId="back-to-all-questions-button"
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
</section>

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
  {:else if $questionStore.data}
    <QuestionCard
      skeleton={!dataRequested || $consultationStore.isLoading}
      countsLoading={$questionStore.isLoading}
      clickable={false}
      consultationId={$consultationStore.data?.id || ""}
      question={$questionStore.data}
      hideIcon={true}
      horizontal={true}
    />
  {/if}
</section>

<div class="grid grid-cols-4 gap-4">
  <div class="col-span-4 md:col-span-1">
    <FiltersSidebar
      {demographics}
      loading={!dataRequested || $demographicsStore.isLoading}
    />
  </div>

  <div class="col-span-4 md:col-span-3">
    {#if $questionStore.data?.multiple_choice_answer?.filter( (item) => Boolean(item.text), ).length}
      <MultiChoice
        data={$questionStore.data.multiple_choice_answer.filter((item) =>
          Boolean(item.text),
        )}
        multiChoiceResponseCount={$questionStore.data
          ?.multi_choice_response_count || 0}
        countsLoading={$questionStore.isLoading &&
          ($questionStore.data?.multiple_choice_answer?.length ?? 0) > 0}
      />
    {/if}

    {#if hasFreeText}
      <section class="my-4">
        <Panel>
          <TitleRow
            level={2}
            title="Theme analysis"
            subtitle="Analysis of key themes mentioned in responses to this question."
          >
            <Lan slot="icon" />

            <div slot="aside">
              <CsvDownload
                fileName={`theme_mentions_for_${$consultationStore.data?.code || ""}.csv`}
                data={themes.map((theme) => ({
                  "Theme Name": theme.name,
                  "Theme Description": theme.description,
                  Mentions: theme.count,
                  Percentage: getPercentage(
                    theme.count,
                    $questionStore.data?.free_text_response_count || 0,
                  ),
                }))}
              />
            </div>
          </TitleRow>

          {#if themes.length === 0 && !$themesStore.isLoading}
            <NotFoundMessage
              title="No themes found"
              body="Try adjusting your search terms or filters."
            />
          {:else}
            <Panel>
              <ThemesTable
                {themes}
                freeTextResponseCount={$questionStore.data
                  ?.free_text_response_count || 0}
                skeleton={!dataRequested || $themesStore.isLoading}
                countsLoading={$themesStore.isLoading && themes.length > 0}
              />
            </Panel>
          {/if}
        </Panel>
      </section>

      <section class="my-4">
        <Panel>
          <TitleRow
            level={2}
            title="Free Text Responses"
            subtitle={$questionStore.isLoading
              ? ""
              : `${$questionStore.data?.free_text_response_count || 0} responses`}
          >
            <Finance slot="icon" />

            <div slot="aside" class="flex flex-wrap items-center gap-2">
              {#if anyFilterApplied()}
                <div
                  class="flex items-center gap-2 rounded-md bg-neutral-100 px-3 py-1"
                >
                  <MaterialIcon size="1rem" color="fill-neutral-500">
                    <FilterAlt />
                  </MaterialIcon>
                  <span class="text-sm text-neutral-600">Filtered</span>
                  <Button
                    size="xs"
                    handleClick={() => {
                      resetFilters();
                    }}
                  >
                    Clear
                  </Button>
                </div>
              {/if}
            </div>
          </TitleRow>

          <div class="mt-6">
            <TextInput
              variant="search"
              id="search-input"
              label="Search"
              placeholder="Search responses..."
              hideLabel={true}
              value={searchValue}
              setValue={(value: string) => (searchValue = value.trim())}
            />
          </div>

          <div class="my-6 flex flex-wrap items-center gap-8">
            <Switch
              id="evidence-rich-toggle"
              value={evidenceRich}
              handleChange={(value) => (evidenceRich = value)}
            >
              {#snippet label()}
                <div class="flex items-center gap-2">
                  <MaterialIcon size="1.1rem" color="fill-yellow-600">
                    <Diamond />
                  </MaterialIcon>
                  <span class="text-sm">Evidence rich</span>
                </div>
              {/snippet}
            </Switch>

            <Switch
              id="unseen-responses-toggle"
              value={unread}
              handleChange={(value) => (unread = value)}
            >
              {#snippet label()}
                <div class="flex items-center gap-2">
                  <MaterialIcon size="1.1rem" color="fill-teal-600">
                    <Visibility />
                  </MaterialIcon>
                  <span class="text-sm">Unread</span>
                </div>
              {/snippet}
            </Switch>

            <Switch
              id="flagged-only-toggle"
              value={flagged}
              handleChange={(value) => (flagged = value)}
            >
              {#snippet label()}
                <div class="flex items-center gap-2">
                  <MaterialIcon size="1.1rem" color="fill-primary">
                    <Flag2 />
                  </MaterialIcon>
                  <span class="text-sm">Flagged</span>
                </div>
              {/snippet}
            </Switch>
          </div>

          {#if isResponsesLoading && responses.length === 0}
            <div transition:fade>
              {#each "_".repeat(5) as _, i (i)}
                <ResponseCard skeleton={true} />
              {/each}
            </div>
          {:else if $responsesStore.error}
            <div transition:slide class="my-2">
              <Alert>
                <span class="text-sm">
                  Responses Error: {$responsesStore.error}
                </span>
              </Alert>
            </div>
          {:else}
            <div>
              <ul>
                {#each responses as response, i (response.id)}
                  <li>
                    <div in:fly={{ x: 300, delay: getDelay(i) }}>
                      <ResponseCard
                        {consultationId}
                        {questionId}
                        answerId={response.id}
                        respondentId={response.respondent_id}
                        respondentDisplayId={response.identifier.toString()}
                        demoData={Object.values(response.demographic_data)}
                        multiAnswers={response.multiple_choice_answer}
                        evidenceRich={response.evidenceRich}
                        text={response.free_text_answer_text}
                        themes={response.themes || []}
                        themeOptions={$themesStore.data?.themes || []}
                        highlightText={searchValue}
                        isFlagged={response.is_flagged}
                        isEdited={response.is_edited}
                        resetData={() => {
                          resetAnswers();
                          loadData();
                        }}
                        onInteract={() => {
                          fetch(
                            updateResponseReadStatus(
                              consultationId,
                              response.id,
                            ),
                            { method: "POST" },
                          );
                        }}
                      />
                    </div>
                  </li>
                {/each}
              </ul>

              {#if responses.length === 0}
                <div transition:fade>
                  <NotFoundMessage
                    title="No responses found"
                    body="Try adjusting your search terms or filters."
                  />
                </div>
              {/if}

              {#if isResponsesLoading}
                <div transition:fade>
                  {#each "_".repeat(5) as _, i (i)}
                    <ResponseCard skeleton={true} />
                  {/each}
                </div>
              {/if}

              <div class="m-auto w-max">
                {#if hasMorePages}
                  <div
                    class={clsx([
                      "transition-all",
                      "duration-300",
                      "overflow-hidden",
                      isResponsesLoading ? "w-[14ch]" : "w-[10ch]",
                    ])}
                  >
                    <Button
                      fullWidth={true}
                      handleClick={() => {
                        markResponsesAsRead();
                        loadData();
                      }}
                      size="sm"
                    >
                      <span class="w-full whitespace-nowrap text-center">
                        {isResponsesLoading ? "Loading responses" : "Load more"}
                      </span>
                    </Button>
                  </div>
                {/if}
              </div>

              {#if responses.length > 0}
                <p class="mt-2 text-center text-sm text-neutral-500">
                  {#if !hasMorePages}
                    Showing all {responses.length} responses.
                  {:else if responseTotalCount !== null}
                    Showing {responses.length} of {responseTotalCount} responses.
                  {:else}
                    Showing {responses.length} responses.
                  {/if}
                </p>
              {/if}
            </div>
          {/if}
        </Panel>
      </section>
    {/if}
  </div>
</div>
