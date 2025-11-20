<script lang="ts">
  import { onMount } from "svelte";
  import { slide } from "svelte/transition";
  import type { Writable } from "svelte/store";

  import NotFoundMessage from "../NotFoundMessage/NotFoundMessage.svelte";
  import LoadingIndicator from "../LoadingIndicator/LoadingIndicator.svelte";
  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Help from "../svg/material/Help.svelte";
  import Star from "../svg/material/Star.svelte";
  import TitleRow from "../dashboard/TitleRow.svelte";
  import Panel from "../dashboard/Panel/Panel.svelte";
  import QuestionCard from "../dashboard/QuestionCard/QuestionCard.svelte";
  import Metrics from "../dashboard/Metrics/Metrics.svelte";

  import type {
    Consultation,
    DemoOptionsResponse,
  } from "../../global/types.ts";
  import {
    getApiQuestionsUrl,
    getQuestionDetailUrl,
  } from "../../global/routes.ts";
  import { createFetchStore, favStore } from "../../global/stores.ts";

  interface Props {
    consultationId: string;
  }

  let {
    consultationId
  }: Props = $props();

  let searchValue: string = $state("");
  let dataRequested: boolean = $state(false);

  const questionsStore = createFetchStore();
  const demoOptionsStore = createFetchStore();

  onMount(() => {
    $questionsStore.fetch(getApiQuestionsUrl(consultationId));
    $demoOptionsStore.fetch(`/api/consultations/${consultationId}/demographic-options/`);
    dataRequested = true;
  })

  let favQuestions = $derived(
    $questionsStore.data?.results?.filter((question) =>
      $favStore.includes(question.id),
    )
  )

  let displayQuestions = $derived($questionsStore.data?.results?.filter((question) =>
    `Q${question.number}: ${question.question_text}`
      .toLocaleLowerCase()
      .includes(searchValue.toLocaleLowerCase()),
  ));
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

  {#if dataRequested && (favQuestions?.length === 0 || $favStore.length === 0) }
    <p transition:slide class="mb-12">You have not favourited any question.</p>
  {:else}
    {#if !dataRequested || $questionsStore.isLoading}
      <div transition:slide class="my-8">
        <LoadingIndicator size="5rem" />
        <p class="text-center text-neutral-500">
          Loading questions...
        </p>
      </div>
    {:else if $questionsStore.error}
      <p transition:slide>{$questionsStore.error}</p>
    {:else}
      <div transition:slide>
        <div class="mb-8">
          {#each favQuestions as question}
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
      <div transition:slide class="my-8">
        <LoadingIndicator size="5rem" />
        <p class="text-center text-neutral-500">
          Loading questions...
        </p>
      </div>
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
        />

        <div class="mb-4">
          {#if !displayQuestions?.length && !$questionsStore.isLoading}
            <NotFoundMessage
              variant="archive"
              body="No questions found matching your search."
            />
          {:else}
            {#each displayQuestions as question}
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
