<script lang="ts">
  import clsx from "clsx";

  import { onMount } from "svelte";
  import { slide } from "svelte/transition";

  import {
    getApiAnswersUrl,
    getApiConsultationRespondentUrl,
    getApiConsultationRespondentsUrl,
    getApiQuestionsUrl,
    getApiQuestionsV2Url,
    getApiResponsesV2Url,
    getQuestionDetailUrl,
    getQuestionsByRespondentUrl,
    getRespondentDetailUrl,
  } from "../../../global/routes.ts";
  import { createFetchStore } from "../../../global/stores.ts";
  import { getDataSetupV2Enabled } from "../../../global/utils.ts";
  import type { QuestionDetailV2 } from "../../../global/queries/questions/types.ts";
  import { excludeDemographicQuestions } from "../../../global/queries/questions/queries.ts";
  import type {
    ResponsesBody,
    ResponsesBodyV2,
    QuestionsResponse,
    Respondent,
    RespondentsResponse,
    ResponseBody,
    ResponseBodyV2,
    Question,
  } from "../../../global/types.ts";
  import Alert from "../../Alert/Alert.svelte";
  import LoadingMessage from "../../LoadingMessage/LoadingMessage.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import ChevronRight from "../../svg/material/ChevronRight.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import RespondentSidebar from "../../dashboard/RespondentSidebar/RespondentSidebar.svelte";
  import RespondentTopbar from "../../dashboard/RespondentTopbar/RespondentTopbar.svelte";
  import RespondentAnswer from "../../dashboard/RespondentResponse/RespondentResponse.svelte";

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

  const respondentsStore = createFetchStore<RespondentsResponse>();
  const respondentStore = createFetchStore<Respondent>();
  const consultationQuestionsStore = createFetchStore<
    QuestionsResponse | QuestionDetailV2[]
  >();
  const questionsStore = createFetchStore<
    QuestionsResponse | QuestionDetailV2[]
  >();
  const responsesStore = createFetchStore<ResponsesBody | ResponsesBodyV2>();

  let dataRequested: boolean = $state(false);

  // V2 flag: questions and responses come from the v2 API; the respondents
  // list (prev/next respondent navigation) stays on the v1 endpoint as its
  // payload is schema-agnostic. Sidebar demographics are derived from the
  // respondent's responses to demographic-type questions.
  const isV2 = getDataSetupV2Enabled();
  const consultationQuestionsUrl = isV2
    ? getApiQuestionsV2Url(consultationId)
    : getApiQuestionsUrl(consultationId);
  const respondentQuestionsUrl = isV2
    ? `${getApiQuestionsV2Url(consultationId)}?respondent_id=${respondentId}`
    : getQuestionsByRespondentUrl(consultationId, respondentId);
  const responsesUrl = isV2
    ? `${getApiResponsesV2Url(consultationId)}?respondent_id=${respondentId}`
    : `${getApiAnswersUrl(consultationId)}?respondent_id=${respondentId}`;

  onMount(() => {
    $consultationQuestionsStore.fetch(consultationQuestionsUrl);
    $respondentsStore.fetch(getLoadRespondentsUrl());
    $questionsStore.fetch(respondentQuestionsUrl);
    $responsesStore.fetch(responsesUrl);
    dataRequested = true;
  });

  function getLoadRespondentsUrl() {
    return (
      getApiConsultationRespondentsUrl(consultationId) +
      `?themefinder_id__gte=${themefinderId - 1}&themefinder_id__lte=${themefinderId + 1}`
    );
  }

  const listResults = (
    data: QuestionsResponse | QuestionDetailV2[] | null,
  ): Array<Question | QuestionDetailV2> =>
    Array.isArray(data) ? data : (data?.results ?? []);

  const questionText = (question: Question | QuestionDetailV2): string =>
    "question_text" in question
      ? question.question_text
      : (question.text ?? "");

  const responseText = (response: ResponseBody | ResponseBodyV2): string =>
    ("text" in response ? response.text : response.free_text_answer_text) ?? "";

  let consultationQuestions = $derived(
    excludeDemographicQuestions(listResults($consultationQuestionsStore.data)),
  );
  let respondentQuestions = $derived(
    excludeDemographicQuestions(listResults($questionsStore.data)),
  );

  let questionsById = $derived(
    new Map(respondentQuestions.map((question) => [question.id, question])),
  );

  let currRespondent = $derived(
    $respondentsStore.data?.results?.find(
      (respondent: Respondent) => respondent.id === respondentId,
    ),
  );

  let prevRespondent = $derived(
    $respondentsStore.data?.results?.find(
      (respondent: Respondent) =>
        respondent?.themefinder_id ===
        (currRespondent?.themefinder_id || 0) - 1,
    ) ?? null,
  );
  let nextRespondent = $derived(
    $respondentsStore.data?.results?.find(
      (respondent: Respondent) =>
        respondent?.themefinder_id ===
        (currRespondent?.themefinder_id || 0) + 1,
    ) ?? null,
  );

  let responsesToDisplay = $derived(
    (Array.isArray($responsesStore.data)
      ? []
      : $responsesStore.data?.all_respondents || []) as Array<
      ResponseBody | ResponseBodyV2
    >,
  );

  let sidebarDemoData = $derived(
    isV2
      ? responsesToDisplay
          .filter((response) => {
            const question = questionsById.get(response.question_id);
            return (
              question && "type" in question && question.type === "demographic"
            );
          })
          .filter((response) => responseText(response))
          .map((response) => {
            const question = questionsById.get(response.question_id);
            return {
              name: question ? questionText(question) : "",
              value: responseText(response),
            };
          })
      : (currRespondent?.demographics ?? []),
  );

  let responsesWithQuestions = $derived(
    responsesToDisplay
      .filter((response) => {
        const question = questionsById.get(response.question_id);
        return (
          !question || !("type" in question) || question.type !== "demographic"
        );
      })
      .map((response) => {
        const question = questionsById.get(response.question_id);
        return {
          ...response,
          question: {
            title: question ? questionText(question) : "",
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
          demoData={sidebarDemoData}
          stakeholderName={currRespondent?.name}
          questionsAnswered={respondentQuestions.length}
          totalQuestions={consultationQuestions.length}
          updateStakeholderName={async (newStakeholderName) => {
            // update current respondent stakeholder name
            await $respondentStore.fetch(
              getApiConsultationRespondentUrl(consultationId, respondentId),
              "PATCH",
              {
                name: newStakeholderName,
              },
            );

            // refresh respondents
            $respondentsStore.fetch(getLoadRespondentsUrl());
          }}
        />

        {#snippet failed(error)}
          <div>
            {console.error(error)}

            <Panel>
              <Alert variant="error">Unexpected responses error</Alert>
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

            {#if !dataRequested || $responsesStore.isLoading}
              <LoadingMessage message="Loading Responses..." />
            {/if}

            <ul>
              {#each responsesWithQuestions.sort((a, b) => {
                if (a.question.number < b.question.number) {
                  return -1;
                } else if (a.question.number > b.question.number) {
                  return 1;
                }
                return 0;
              }) as response, i (response.id)}
                <RespondentAnswer
                  {consultationId}
                  questionId={response.question_id}
                  questionTitle={response.question.title}
                  questionNumber={response.question.number}
                  responseText={responseText(response)}
                  multiChoice={response.multiple_choice_answer}
                  themes={response.themes?.map((theme) => theme.name) || []}
                  evidenceRich={response.evidenceRich ?? false}
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
              <Alert variant="error">Unexpected responses error</Alert>
            </Panel>
          </div>
        {/snippet}
      </svelte:boundary>
    </div>
  </div>
</section>
