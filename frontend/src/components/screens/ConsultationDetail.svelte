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
  import Alert from "../Alert.svelte";

  import type {
    ApiError,
    DemoOptionsResponse,
    QuestionsResponse,
  } from "../../global/types.ts";
  import {
    getApiDemoOptionsUrl,
    getApiQuestionsUrl,
    getQuestionDetailUrl,
    Routes,
  } from "../../global/routes.ts";
  import { createQueryStore, favStore } from "../../global/stores.ts";

  interface Props {
    consultationId: string;
  }

  let { consultationId }: Props = $props();

  let searchValue: string = $state("");
  let dataRequested: boolean = $state(false);

  const questionsQuery = $derived(createQueryStore<QuestionsResponse>(
    getApiQuestionsUrl(consultationId),
  ));
  const demoOptionsQuery = $derived(createQueryStore<DemoOptionsResponse>(
    getApiDemoOptionsUrl(consultationId),
  ));

  onMount(() => {
    $questionsQuery.fetch();
    $demoOptionsQuery.fetch();
    dataRequested = true;
  });

  let favQuestions = $derived(
    $questionsQuery.data?.results?.filter((question) =>
      $favStore.includes(question.id),
    ),
  );

  let displayQuestions = $derived(
    $questionsQuery.data?.results?.filter((question) =>
      `Q${question.number}: ${question.question_text}`
        .toLocaleLowerCase()
        .includes(searchValue.toLocaleLowerCase()),
    ),
  );
</script>

<section class="my-8">
  <Metrics
    {consultationId}
    questions={$questionsQuery.data?.results || []}
    loading={!dataRequested || $questionsQuery.isLoading}
    demoOptionsLoading={!dataRequested || $demoOptionsQuery.isLoading}
    demoOptions={$demoOptionsQuery.data || []}
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
  {:else if !dataRequested || $questionsQuery.isLoading}
    <LoadingMessage message="Loading Questions..." />
  {:else if $questionsQuery.error}
    <p transition:slide>{$questionsQuery.error}</p>
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
        {$questionsQuery.data?.results?.length || 0} questions
      </p>
    </TitleRow>
  </div>

  <Panel bg={true} border={true}>
    {#if !dataRequested || $questionsQuery.isLoading}
      <LoadingMessage message="Loading Questions..." />
    {:else if $questionsQuery.error}
      <Alert>
        <p transition:slide>
          {($questionsQuery.error as ApiError).detail}
        </p>
      </Alert>
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
        />

        <div class="mb-4">
          {#if !displayQuestions?.length && !$questionsQuery.isLoading}
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
        </div>
      </div>
    {/if}
  </Panel>
</section>
