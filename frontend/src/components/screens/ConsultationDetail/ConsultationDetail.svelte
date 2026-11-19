<script lang="ts">
  import { onMount } from "svelte";
  import { slide } from "svelte/transition";

  import NotFoundMessage from "../../NotFoundMessage/NotFoundMessage.svelte";
  import LoadingMessage from "../../LoadingMessage/LoadingMessage.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import Help from "../../svg/material/Help.svelte";
  import Star from "../../svg/material/Star.svelte";
  import TitleRow from "../../dashboard/TitleRow.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import QuestionCard from "../../dashboard/QuestionCard/QuestionCard.svelte";
  import Metrics from "../../dashboard/Metrics/Metrics.svelte";

  import type {
    DemoOptionsResponse,
    QuestionsResponse,
    RespondentsResponse,
    Question,
  } from "../../../global/types.ts";
  import type { QuestionDetailV2 } from "../../../global/queries/questions/types.ts";
  import { excludeDemographicQuestions } from "../../../global/queries/questions/queries.ts";
  import {
    getApiConsultationRespondentsUrl,
    getApiDemographicOptionsV2Url,
    getApiQuestionsUrl,
    getApiQuestionsV2Url,
    getQuestionDetailUrl,
  } from "../../../global/routes.ts";
  import { createFetchStore, favStore } from "../../../global/stores.ts";
  import { getDataSetupV2Enabled } from "../../../global/utils.ts";

  interface Props {
    consultationId: string;
  }

  let { consultationId }: Props = $props();

  let searchValue: string = $state("");
  let dataRequested: boolean = $state(false);

  // V2 flag: question list and demographic options come from the v2 API; the
  // respondents count endpoint is schema-agnostic and stays on v1.
  const isV2 = getDataSetupV2Enabled();
  const questionsUrl = isV2
    ? getApiQuestionsV2Url(consultationId)
    : getApiQuestionsUrl(consultationId);
  const demoOptionsUrl = isV2
    ? getApiDemographicOptionsV2Url(consultationId)
    : `/api/consultations/${consultationId}/demographics/`;
  const questionText = (question: Question | QuestionDetailV2): string =>
    "question_text" in question
      ? question.question_text
      : (question.text ?? "");

  const questionsStore = createFetchStore<
    QuestionsResponse | QuestionDetailV2[]
  >();
  const demoOptionsStore = createFetchStore<DemoOptionsResponse>();
  const respondentsStore = createFetchStore<RespondentsResponse>();

  onMount(() => {
    $questionsStore.fetch(questionsUrl);
    $demoOptionsStore.fetch(demoOptionsUrl);
    $respondentsStore.fetch(getApiConsultationRespondentsUrl(consultationId));
    dataRequested = true;
  });

  let questions = $derived(
    excludeDemographicQuestions(
      Array.isArray($questionsStore.data)
        ? $questionsStore.data
        : $questionsStore.data?.results || [],
    ),
  );

  let favQuestions = $derived(
    questions.filter((question) => $favStore.includes(question.id)),
  );

  let displayQuestions = $derived(
    questions.filter((question) =>
      `Q${question.number}: ${questionText(question)}`
        .toLocaleLowerCase()
        .includes(searchValue.toLocaleLowerCase()),
    ),
  );
</script>

<section class="my-8">
  <Metrics
    {consultationId}
    {questions}
    loading={!dataRequested || $questionsStore.isLoading}
    demoOptionsLoading={!dataRequested || $demoOptionsStore.isLoading}
    demoOptions={$demoOptionsStore.data || []}
    respondentCount={$respondentsStore.data?.count ?? 0}
  />
</section>

<section
  data-testid="favourite-questions-section"
  transition:slide
  class="my-8"
>
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
        {questions.length} questions
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
        </div>
      </div>
    {/if}
  </Panel>
</section>
