<script lang="ts">
  import { onMount } from "svelte";
  import { slide } from "svelte/transition";

  import NotFoundMessage from "../NotFoundMessage/NotFoundMessage.svelte";
  import LoadingMessage from "../LoadingMessage/LoadingMessage.svelte";
  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Help from "../svg/material/Help.svelte";
  import Star from "../svg/material/Star.svelte";
  import TitleRow from "../dashboard/TitleRow.svelte";
  import Panel from "../dashboard/Panel/Panel.svelte";
  import QuestionCard from "../dashboard/QuestionCard/QuestionCard.svelte";
  import Metrics from "../dashboard/Metrics/Metrics.svelte";

  import type {
    DemoOptionsResponse,
    QuestionsResponse,
  } from "../../global/types.ts";
  import {
    getApiQuestionsUrl,
    getQuestionDetailUrl,
  } from "../../global/routes.ts";
  import { createFetchStore, favStore } from "../../global/stores.ts";
  import { buildPaginatedQuery } from "../../global/queryClient.ts";
  import LoadingIndicator from "../LoadingIndicator/LoadingIndicator.svelte";

  interface Props {
    consultationId: string;
  }

  let { consultationId }: Props = $props();

  let searchValue: string = $state("");
  let dataRequested: boolean = $state(false);

  const questionsStore = createFetchStore<QuestionsResponse>();
  let currQuestionPage = $state(1);

  const questionsQuery = $derived(buildPaginatedQuery(getApiQuestionsUrl(consultationId) + `?page=${currQuestionPage}`, {
    getKey: () => [getApiQuestionsUrl(consultationId)],
    getPageParam: () => currQuestionPage,
    setPageParam: (newPageParam) => currQuestionPage = newPageParam,
  }));

  const demoOptionsStore = createFetchStore<DemoOptionsResponse>();

  onMount(async () => {
    $demoOptionsStore.fetch(
      `/api/consultations/${consultationId}/demographic-options/`,
    );
    dataRequested = true;

    await questionsQuery.fetchNextPage();

    while (questionsQuery.hasNextPage) {
      await questionsQuery.fetchNextPage();
    }
  });

  let allQuestions = $derived(questionsQuery.data?.pages
    .map(page => page.items)
    .flat()
  );

  let favQuestions = $derived(
    allQuestions?.filter((question) =>
      $favStore.includes(question.id),
    )
  );

  let displayQuestions = $derived(
    allQuestions?.filter((question) => (
      `Q${question.number}: ${question.question_text}`
        .toLocaleLowerCase()
        .includes(searchValue.toLocaleLowerCase())
    ))
  );
</script>

<section class="my-8">
  <Metrics
    {consultationId}
    questions={$questionsStore.data?.results || []}
    loading={!dataRequested || $questionsStore.isLoading}
    demoOptionsLoading={!dataRequested || $demoOptionsStore.isLoading}
    demoOptions={$demoOptionsStore.data || []}
  />
</section>

<section transition:slide class="my-8">
  <div class="my-2">
    <TitleRow title="Favourited questions">
      <Star slot="icon" />
    </TitleRow>
  </div>

  {#if dataRequested && (favQuestions?.length === 0 || $favStore.length === 0)}
    <p transition:slide class="mb-12">You have not favourited any question.</p>
  {:else if !dataRequested || $questionsStore.isLoading}
    <LoadingMessage message="Loading Questions..." />
  {:else if $questionsStore.error}
    <p transition:slide>{$questionsStore.error}</p>
  {:else}
    <div transition:slide>
      <div class="mb-8">
        {#each favQuestions as question (question.id)}
          <QuestionCard
            {consultationId}
            {question}
            highlightText={searchValue}
            clickable={true}
            url={getQuestionDetailUrl(consultationId, question.id || "")}
          />
        {/each}
      </div>
    </div>
  {/if}
</section>

<section class="my-8">
  <div class="my-2">
    <TitleRow
      title="All consultation questions"
      subtitle="Browse or search through all questions in this consultation."
    >
      <Help slot="icon" />

      <p slot="aside">
        {$questionsStore.data?.results?.length || 0} questions
      </p>
    </TitleRow>
  </div>

  <Panel bg={true} border={true}>
    {#if !dataRequested || $questionsStore.isLoading}
      <LoadingMessage message="Loading Questions..." />
    {:else if $questionsStore.error}
      <p transition:slide>{$questionsStore.error}</p>
    {:else}
      <div transition:slide>
        <TextInput
          variant="search"
          id="search-input"
          label="Search"
          placeholder="Search..."
          hideLabel={true}
          value={searchValue}
          setValue={(value) => (searchValue = value.trim())}
          disabled={questionsQuery.hasNextPage}
        />

        <div class="mb-4">
          {#if !displayQuestions?.length && !$questionsStore.isLoading}
            <NotFoundMessage
              variant="archive"
              body="No questions found matching your search."
            />
          {:else}
            {#each displayQuestions as question (question.id)}
              <QuestionCard
                {consultationId}
                {question}
                highlightText={searchValue}
                clickable={true}
                url={getQuestionDetailUrl(consultationId, question.id || "")}
              />
            {/each}
          {/if}

          {#if questionsQuery.hasNextPage}
            <LoadingIndicator />
          {/if}
        </div>
      </div>
    {/if}
  </Panel>
</section>
