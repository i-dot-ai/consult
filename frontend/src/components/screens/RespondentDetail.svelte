<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import {
    getApiAnswersUrl,
    getApiConsultationRespondentUrl,
    getApiConsultationRespondentsUrl,
    getApiConsultationUrl,
    getQuestionDetailUrl,
    getQuestionsByRespondentUrl,
    getRespondentDetailUrl,
  } from "../../global/routes.ts";
  import { createFetchStore } from "../../global/stores.ts";

  import Panel from "../dashboard/Panel/Panel.svelte";
  import Alert from "../Alert.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import ChevronRight from "../svg/material/ChevronRight.svelte";
  import Button from "../inputs/Button/Button.svelte";
  import RespondentSidebar from "../dashboard/RespondentSidebar/RespondentSidebar.svelte";
  import RespondentTopbar from "../dashboard/RespondentTopbar/RespondentTopbar.svelte";
  import RespondentAnswer from "../dashboard/RespondentAnswer/RespondentAnswer.svelte";

  const FLY_ANIMATION_DELAY = 100;

  interface Respondent {
    id: string;
    consultation: string;
    themefinder_id: number;
    demographics: any[];
    name?: any;
  }

  interface Props {
    consultationId: string;
    questionId: string;
    respondentId: string;
    themefinderId: number;
  }

  let { consultationId = "", questionId = "", respondentId = "", themefinderId = 1 }: Props = $props();

  const {
    load: loadRespondents,
    loading: isRepondentsLoading,
    data: respondentsData,
    error: respondentsError,
  } = createFetchStore();

  const {
    load: loadRespondent,
    loading: isRepondentLoading,
    data: respondentData,
    error: respondentError,
  } = createFetchStore();

  const {
    load: loadConsultation,
    loading: isConsultationLoading,
    data: consultationData,
    error: consultationError,
  } = createFetchStore();

  const {
    load: loadQuestions,
    loading: isQuestionsLoading,
    data: questionsData,
    error: questionsError,
  } = createFetchStore();

  const {
    load: loadAnswers,
    loading: isAnswersLoading,
    data: answersData,
    error: answersError,
  } = createFetchStore();

  $effect(() => {
    loadConsultation(getApiConsultationUrl(consultationId));
    loadRespondents(getLoadRespondentsUrl());
    loadQuestions(getQuestionsByRespondentUrl(consultationId, respondentId));
    loadAnswers(
      `${getApiAnswersUrl(consultationId)}?respondent_id=${respondentId}`,
    );
  });

  function getLoadRespondentsUrl() {
    return (
      getApiConsultationRespondentsUrl(consultationId)
      + `?themefinder_id__gte=${themefinderId - 1}&themefinder_id__lte=${themefinderId + 1}`
    )
  }

  let currRespondent = $derived(
    $respondentsData?.results?.find(
      (respondent: Respondent) => respondent.id === respondentId,
    ),
  );

  let prevRespondent = $derived(
    $respondentsData?.results?.find(
      (respondent: Respondent) =>
        respondent?.themefinder_id === currRespondent?.themefinder_id - 1,
    ) ?? null,
  );
  let nextRespondent = $derived(
    $respondentsData?.results?.find(
      (respondent: Respondent) =>
        respondent?.themefinder_id === currRespondent?.themefinder_id + 1,
    ) ?? null,
  );
</script>

<section>
  <RespondentTopbar
    title={`Respondent ${themefinderId || "not found"}`}
    backText={"Back to Analysis"}
    onClickBack={() => location.href = getQuestionDetailUrl(consultationId, questionId)}
  >
    <Button
      size="xs"
      disabled={!Boolean(prevRespondent)}
      handleClick={(e) =>
        (location.href = getRespondentDetailUrl(
          consultationId,
          prevRespondent.id,
        ) + `?themefinder_id=${themefinderId - 1}&question_id=${questionId}`)}
    >
      <div class="rotate-180">
        <MaterialIcon color="fill-neutral-700">
          <ChevronRight />
        </MaterialIcon>
      </div>

      <span class="mr-2 my-[0.1rem]">Previous Respondent</span>
    </Button>

    <Button
      size="xs"
      disabled={!Boolean(nextRespondent)}
      handleClick={(e) =>
        (location.href = getRespondentDetailUrl(
          consultationId,
          nextRespondent.id,
        ) + `?themefinder_id=${themefinderId + 1}&question_id=${questionId}`)}
    >
      <span class="ml-2 my-[0.1rem]">Next Respondent</span>

      <MaterialIcon color="fill-neutral-700">
        <ChevronRight />
      </MaterialIcon>
    </Button>
  </RespondentTopbar>

  <div class={clsx(["grid", "grid-cols-12", "gap-4"])}>
    <div class="col-span-12 md:col-span-3 h-max md:sticky md:top-4" in:slide>
      <svelte:boundary>
        <RespondentSidebar
          demoData={currRespondent?.demographics}
          stakeholderName={currRespondent?.name}
          questionsAnswered={$questionsData?.results.length ?? 0}
          totalQuestions={$consultationData?.questions?.length ?? 0}
          updateStakeholderName={async (newStakeholderName) => {
            // update current respondent stakeholder name
            await loadRespondent(
              getApiConsultationRespondentUrl(consultationId, respondentId),
              "PATCH",
              {
                name: newStakeholderName,
              },
            );

            // refresh respondents
            loadRespondents(getLoadRespondentsUrl());
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

            <ul>
              {#each $answersData?.all_respondents ?? [] as answer, i}
                {@const answerQuestion = $questionsData?.results?.find(
                  (question) => question.id === answer.question_id,
                )}

                <RespondentAnswer
                  {consultationId}
                  questionId={answer.question_id}
                  questionTitle={answerQuestion?.question_text}
                  questionNumber={answerQuestion?.number}
                  answerText={answer.free_text_answer_text}
                  multiChoice={answer.multiple_choice_answer}
                  themes={answer.themes?.map((theme) => theme.name)}
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
