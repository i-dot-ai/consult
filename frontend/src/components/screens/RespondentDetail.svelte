<script lang="ts">
  import clsx from "clsx";

  import { onMount } from "svelte";
  import { slide } from "svelte/transition";

  import {
    getApiAnswersUrl,
    getApiConsultationRespondentUrl,
    getApiConsultationRespondentsUrl,
    getApiQuestionsUrl,
    getQuestionDetailUrl,
    getQuestionsByRespondentUrl,
    getRespondentDetailUrl,
  } from "../../global/routes.ts";
  import { createQueryStore } from "../../global/stores.ts";
  import type {
    AnswersResponse,
    QuestionsResponse,
    Respondent,
    RespondentsResponse,
  } from "../../global/types.ts";

  import Alert from "../Alert.svelte";
  import LoadingMessage from "../LoadingMessage/LoadingMessage.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import Panel from "../dashboard/Panel/Panel.svelte";
  import ChevronRight from "../svg/material/ChevronRight.svelte";
  import Button from "../inputs/Button/Button.svelte";
  import RespondentSidebar from "../dashboard/RespondentSidebar/RespondentSidebar.svelte";
  import RespondentTopbar from "../dashboard/RespondentTopbar/RespondentTopbar.svelte";
  import RespondentAnswer from "../dashboard/RespondentAnswer/RespondentAnswer.svelte";

  const FLY_ANIMATION_DELAY = 100;

  interface Props {
    consultationId: string;
    questionId: string;
    respondentId: string;
    themefinderId: number;
  }

  let {
    consultationId = "",
    questionId = "",
    respondentId = "",
    themefinderId = 1,
  }: Props = $props();

  const respondentsQuery = createQueryStore<RespondentsResponse>(
    getLoadRespondentsUrl(),
  );
  const consultationQuestionsQuery = $derived(
    createQueryStore<QuestionsResponse>(getApiQuestionsUrl(consultationId)),
  );
  const questionsQuery = $derived(
    createQueryStore<QuestionsResponse>(
      getQuestionsByRespondentUrl(consultationId, respondentId),
    ),
  );
  const answersQuery = $derived(
    createQueryStore<AnswersResponse>(
      `${getApiAnswersUrl(consultationId)}?respondent_id=${respondentId}`,
    ),
  );
  const respondentUpdateQuery = $derived(
    createQueryStore<Respondent>(
      getApiConsultationRespondentUrl(consultationId, respondentId),
      { method: "PATCH" },
    ),
  );

  let dataRequested: boolean = $state(false);

  onMount(() => {
    $consultationQuestionsQuery.fetch();
    $respondentsQuery.fetch();
    $questionsQuery.fetch();
    $answersQuery.fetch();
    dataRequested = true;
  });

  function getLoadRespondentsUrl() {
    return (
      getApiConsultationRespondentsUrl(consultationId) +
      `?themefinder_id__gte=${themefinderId - 1}&themefinder_id__lte=${themefinderId + 1}`
    );
  }

  let currRespondent = $derived(
    $respondentsQuery.data?.results?.find(
      (respondent: Respondent) => respondent.id === respondentId,
    ),
  );

  let prevRespondent = $derived(
    $respondentsQuery.data?.results?.find(
      (respondent: Respondent) =>
        respondent?.themefinder_id ===
        (currRespondent?.themefinder_id || 0) - 1,
    ) ?? null,
  );
  let nextRespondent = $derived(
    $respondentsQuery.data?.results?.find(
      (respondent: Respondent) =>
        respondent?.themefinder_id ===
        (currRespondent?.themefinder_id || 0) + 1,
    ) ?? null,
  );

  let answersToDisplay = $derived(
    ($answersQuery.data?.all_respondents || []).map((answer) => {
      const question = $questionsQuery.data?.results?.find(
        (question) => question.id === answer.question_id,
      );

      return {
        ...answer,
        question: {
          title: question?.question_text || "",
          number: question?.number || 0,
        },
      };
    }),
  );
</script>

<section>
  <RespondentTopbar
    title={`Respondent ${themefinderId || "not found"}`}
    backText="Back to Analysis"
    onClickBack={() =>
      (location.href = getQuestionDetailUrl(consultationId, questionId))}
  >
    <Button
      size="xs"
      disabled={!prevRespondent}
      handleClick={() =>
        (location.href =
          getRespondentDetailUrl(consultationId, prevRespondent?.id || "") +
          `?themefinder_id=${themefinderId - 1}&question_id=${questionId}`)}
    >
      <div class="rotate-180">
        <MaterialIcon color="fill-neutral-700">
          <ChevronRight />
        </MaterialIcon>
      </div>

      <span class="my-[0.1rem] mr-2">Previous Respondent</span>
    </Button>

    <Button
      size="xs"
      disabled={!nextRespondent}
      handleClick={() =>
        (location.href =
          getRespondentDetailUrl(consultationId, nextRespondent?.id || "") +
          `?themefinder_id=${themefinderId + 1}&question_id=${questionId}`)}
    >
      <span class="my-[0.1rem] ml-2">Next Respondent</span>

      <MaterialIcon color="fill-neutral-700">
        <ChevronRight />
      </MaterialIcon>
    </Button>
  </RespondentTopbar>

  <div class={clsx(["grid", "grid-cols-12", "gap-4"])}>
    <div class="col-span-12 h-max md:sticky md:top-4 md:col-span-3" in:slide>
      <svelte:boundary>
        <RespondentSidebar
          demoData={currRespondent?.demographics || []}
          stakeholderName={currRespondent?.name}
          questionsAnswered={$questionsQuery.data?.results.length ?? 0}
          totalQuestions={$consultationQuestionsQuery.data?.results?.length ??
            0}
          updateStakeholderName={async (newStakeholderName) => {
            // update current respondent stakeholder name
            await $respondentUpdateQuery.fetch({
              body: { name: newStakeholderName },
            });

            // refresh respondents
            $respondentsQuery.fetch();
          }}
        />

        {#snippet failed(error)}
          <div>
            {console.error(error)}

            <Panel>
              <Alert>Unexpected responses error</Alert>
            </Panel>
          </div>
        {/snippet}
      </svelte:boundary>
    </div>

    <div class="col-span-12 md:col-span-9">
      <svelte:boundary>
        <Panel>
          <article>
            <h2 class="text-sm">Responses to Consultation Questions</h2>
            <p class="text-sm text-neutral-500">
              All responses submitted by this respondent, ordered by question
              number
            </p>

            {#if !dataRequested || $answersQuery.isLoading}
              <LoadingMessage message="Loading Answers..." />
            {/if}

            <ul>
              {#each answersToDisplay.sort((a, b) => {
                if (a.question.number < b.question.number) {
                  return -1;
                } else if (a.question.number > b.question.number) {
                  return 1;
                }
                return 0;
              }) as answer, i (answer.id)}
                <RespondentAnswer
                  {consultationId}
                  questionId={answer.question_id}
                  questionTitle={answer.question.title}
                  questionNumber={answer.question.number}
                  answerText={answer.free_text_answer_text}
                  multiChoice={answer.multiple_choice_answer}
                  themes={answer.themes?.map((theme) => theme.name) || []}
                  evidenceRich={answer.evidenceRich}
                  delay={FLY_ANIMATION_DELAY * i}
                />
              {/each}
            </ul>
          </article>
        </Panel>

        {#snippet failed(error)}
          <div>
            {console.error(error)}

            <Panel>
              <Alert>Unexpected responses error</Alert>
            </Panel>
          </div>
        {/snippet}
      </svelte:boundary>
    </div>
  </div>
</section>
