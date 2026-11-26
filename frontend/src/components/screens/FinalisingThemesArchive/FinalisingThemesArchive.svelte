<script lang="ts">
  import clsx from "clsx";

  import { onDestroy, onMount } from "svelte";
  import { slide } from "svelte/transition";

  import {
    getApiAssignThemesUrl,
    getApiConsultationUrl,
    getApiConsultationV2Url,
    getApiQuestionsUrl,
    getApiQuestionsV2Url,
    getFinaliseThemesDetailUrl,
    Routes,
  } from "../../../global/routes.ts";
  import { createFetchStore } from "../../../global/stores.ts";
  import { getDataSetupV2Enabled } from "../../../global/utils.ts";
  import {
    type ConsultationResponse,
    type Question,
    type QuestionsResponse,
  } from "../../../global/types.ts";
  import type { ConsultationV2 } from "../../../global/queries/consultations/types.ts";
  import type { QuestionDetailV2 } from "../../../global/queries/questions/types.ts";
  import { excludeDemographicQuestions } from "../../../global/queries/questions/queries.ts";
  import Tag from "../../Tag/Tag.svelte";
  import Modal from "../../Modal/Modal.svelte";
  import Alert from "../../Alert/Alert.svelte";
  import LoadingIndicator from "../../LoadingIndicator/LoadingIndicator.svelte";
  import OnboardingTour from "../../OnboardingTour/OnboardingTour.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import TitleRow from "../../dashboard/TitleRow.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import QuestionCard from "../../dashboard/QuestionCard/QuestionCard.svelte";
  import ConsultationStagePanel from "../../finalising-themes/ConsultationStagePanel/ConsultationStagePanel.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Checklist from "../../svg/material/Checklist.svelte";
  import Warning from "../../svg/material/Warning.svelte";
  import Headphones from "../../svg/material/Headphones.svelte";
  import Help from "../../svg/material/Help.svelte";
  import Target from "../../svg/material/Target.svelte";
  import NotFoundMessage from "../../NotFoundMessage/NotFoundMessage.svelte";
  import Price from "../../svg/material/Price.svelte";

  const FIVE_MINUTES = 5 * 60 * 1000;

  interface Props {
    consultationId: string;
    pollFrequency?: number;
    handleIntervalTick?: () => void;
  }

  let {
    consultationId = "",
    pollFrequency = FIVE_MINUTES,
    handleIntervalTick = () => {
      $consultationStore.fetch(consultationUrl);
    },
  }: Props = $props();

  let searchValue: string = $state("");
  let isConfirmModalOpen: boolean = $state(false);
  let dataRequested: boolean = $state(false);

  // V2 flag: question list and consultation payload come from the v2 API;
  // sign-off gating derives from `type`/`status` instead of v1 booleans.
  const isV2 = getDataSetupV2Enabled();
  const consultationUrl = isV2
    ? getApiConsultationV2Url(consultationId)
    : getApiConsultationUrl(consultationId);
  const questionsUrl = isV2
    ? getApiQuestionsV2Url(consultationId)
    : getApiQuestionsUrl(consultationId);
  const questionText = (question: Question | QuestionDetailV2): string =>
    "question_text" in question
      ? question.question_text
      : (question.text ?? "");
  const isFreeTextQuestion = (
    question: Question | QuestionDetailV2,
  ): boolean =>
    "question_text" in question
      ? question.has_free_text
      : question.type === "open";
  const isConfirmed = (question: Question | QuestionDetailV2): boolean =>
    "question_text" in question
      ? question.theme_status === "confirmed"
      : question.status === "confirmed";

  const questionsStore = createFetchStore<
    QuestionsResponse | QuestionDetailV2[]
  >();
  const consultationStore = createFetchStore<
    ConsultationResponse | ConsultationV2
  >();
  const consultationUpdateStore = createFetchStore();

  onMount(async () => {
    $consultationStore.fetch(consultationUrl);
    $questionsStore.fetch(questionsUrl);
    dataRequested = true;
  });

  let questions = $derived(
    excludeDemographicQuestions(
      Array.isArray($questionsStore.data)
        ? $questionsStore.data
        : $questionsStore.data?.results || [],
    ),
  );

  let displayQuestions = $derived(
    questions.filter((question) =>
      `Q${question.number}: ${questionText(question)}`
        .toLocaleLowerCase()
        .includes(searchValue.toLocaleLowerCase()),
    ),
  );

  let questionsForSignOff = $derived(
    questions.filter((question) => isFreeTextQuestion(question)),
  );

  let allQuestionsFinalised: boolean = $derived(
    Boolean(
      questionsForSignOff?.length &&
      questionsForSignOff.every((question) => isConfirmed(question)),
    ),
  );

  let finalisedQuestionCount = $derived(
    questionsForSignOff?.filter((question) => isConfirmed(question))?.length ||
      0,
  );

  let pollingInterval: ReturnType<typeof setInterval> | null = $state(null);

  const clearPollingInterval = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
  };

  $effect(() => {
    const runningJob = $consultationStore.data?.running_job;

    if (runningJob === "assign-themes" && !pollingInterval) {
      pollingInterval = setInterval(handleIntervalTick, pollFrequency);
    } else if (pollingInterval && runningJob !== "assign-themes") {
      clearPollingInterval();
    }
  });

  onDestroy(() => {
    clearPollingInterval();
  });
</script>

<TitleRow
  level={1}
  context="finalising-themes"
  title="Finalise Themes"
  subtitle="Finalise themes to use for AI to map responses to"
>
  <Price slot="icon" />
</TitleRow>

<hr class="my-6" />

<svelte:boundary>
  {#if $consultationStore.data?.running_job === "assign-themes"}
    <div class="blink-light">
      <Alert variant="info">
        We are currently processing theme assignment for this consultation. This
        may take a while.
      </Alert>
    </div>
  {/if}

  {#snippet failed(error)}
    <div>
      {console.error(error)}

      <Panel>
        <Alert variant="error">Unexpected Running Job Alert Error</Alert>
      </Panel>
    </div>
  {/snippet}
</svelte:boundary>

<svelte:boundary>
  {#if $consultationStore.data}
    <section in:slide>
      <ConsultationStagePanel
        consultation={$consultationStore.data}
        questionsCount={questionsForSignOff?.length || 0}
        {finalisedQuestionCount}
        {allQuestionsFinalised}
        onConfirmClick={() => (isConfirmModalOpen = true)}
      />

      <Modal
        variant="secondary"
        title="Confirm AI Assignment"
        confirmText={$consultationUpdateStore.isLoading
          ? "Submitting consultation themes"
          : "Yes, Start AI Assignment"}
        confirmDisabled={$consultationUpdateStore.isLoading}
        Icon={Warning}
        open={isConfirmModalOpen}
        setOpen={(newOpen: boolean) => (isConfirmModalOpen = newOpen)}
        handleConfirm={async () => {
          if ($consultationUpdateStore.isLoading) return;
          await $consultationUpdateStore.fetch(
            getApiAssignThemesUrl(consultationId as string),
            "POST",
          );

          if (!$consultationUpdateStore.error) {
            isConfirmModalOpen = false;
            location.href = location.href;
          }
        }}
      >
        <p class="mb-4 text-sm text-text">
          You have successfully reviewed and signed off themes for all {questionsForSignOff?.length ||
            0} consultation questions. Are you ready to proceed with AI mapping?
        </p>

        <p class="mb-2 text-sm text-text">This action will:</p>
        <ol class="mb-2 list-disc pl-4 text-sm text-text">
          <li class="mb-2">
            Process all consultation responses across {questionsForSignOff?.length ||
              0} questions
          </li>
          <li class="mb-2">
            Assign responses to your selected themes using AI analysis
          </li>
          <li class="mb-2">Incur computational costs for the AI processing</li>
          <li class="mb-2">
            Take several hours to complete. More responses = longer time to
            process
          </li>
        </ol>

        <Alert variant="error">
          <span class="text-sm">
            <strong>Warning:</strong> Once started, this process cannot be stopped
            or easily reversed. Ensure all theme selections are final.
          </span>
        </Alert>

        <hr class="my-4" />

        <p class="mb-2 text-sm text-text">
          If you have concerns or need assistance, please contact support:
        </p>
        <a
          href={`mailto:${Routes.SupportEmail}`}
          class="support-link mb-4 block text-sm text-success hover:text-primary"
        >
          <div class="flex items-center gap-1">
            <MaterialIcon color="fill-success">
              <Headphones />
            </MaterialIcon>
            {Routes.SupportEmail}
          </div>
        </a>

        {#if $consultationUpdateStore.error}
          <div class="mb-4 mt-2">
            <Alert variant="error">
              <span class="text-sm">{$consultationUpdateStore.error}</span>
            </Alert>
          </div>
        {/if}
      </Modal>
    </section>
  {/if}

  {#snippet failed(error)}
    <div>
      {console.error(error)}

      <Panel>
        <Alert variant="error">Unexpected Sign-Off Modal Error</Alert>
      </Panel>
    </div>
  {/snippet}
</svelte:boundary>

<svelte:boundary>
  <section class="my-8">
    <div class="my-2" id="onboarding-step-1">
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

    <Panel border={true}>
      {#if !dataRequested || $questionsStore.isLoading}
        <div transition:slide class="my-8">
          <LoadingIndicator size="5rem" />
          <p class="text-center text-text">Loading questions...</p>
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
              {#each displayQuestions as question (question.id)}
                <QuestionCard
                  {consultationId}
                  {question}
                  highlightText={searchValue}
                  clickable={isFreeTextQuestion(question)}
                  disabled={!isFreeTextQuestion(question)}
                  url={getFinaliseThemesDetailUrl(
                    consultationId,
                    question.id || "",
                  )}
                  subtext={!isFreeTextQuestion(question)
                    ? "No free text responses for this question = no themes to sign off. Multiple choice data will be shown in analysis dashboard."
                    : undefined}
                >
                  {#snippet tag()}
                    {#if !isFreeTextQuestion(question)}
                      <Tag variant="primary-light">
                        <MaterialIcon color="fill-primary">
                          <Checklist />
                        </MaterialIcon>

                        Multiple choice
                      </Tag>
                    {:else if isConfirmed(question)}
                      <Tag variant="primary-light">Signed off</Tag>
                    {:else}
                      <div></div>
                    {/if}
                  {/snippet}
                </QuestionCard>
              {/each}
            {/if}
          </div>
        </div>
      {/if}
    </Panel>
  </section>

  {#snippet failed(error)}
    <div>
      {console.error(error)}

      <Panel>
        <Alert variant="error">Unexpected Question List Error</Alert>
      </Panel>
    </div>
  {/snippet}
</svelte:boundary>

{#snippet onboardingBody()}
  <p>Here's how to finalise themes:</p>
  <ol class="mt-4">
    {@render onboardingBodyItem(
      1,
      "Choose a Question",
      "Select any consultation question to start working with themes AI has found",
      true,
    )}
    {@render onboardingBodyItem(
      2,
      "Select & Edit Themes",
      "Review AI themes, select relevant ones, and edit or merge as needed",
      false,
    )}
    {@render onboardingBodyItem(
      3,
      "Sign Off & Proceed",
      "Finalise your theme selection to enable AI response mapping",
      false,
    )}
  </ol>
{/snippet}

{#snippet onboardingBodyItem(
  number: number,
  title: string,
  body: string,
  active: boolean,
)}
  <li class="mb-4 flex items-start gap-2">
    <div
      class={clsx([
        "flex",
        "items-center",
        "justify-center",
        "w-[1ch]",
        "h-[1ch]",
        "p-3",
        "rounded-full",
        "font-bold",
        active ? "text-primary" : "text-text",
        active ? "bg-primary-light-95" : "bg-text-light-95",
      ])}
    >
      {number}
    </div>
    <div>
      <h4 class="font-medium">{title}</h4>
      <p>{body}</p>
    </div>
  </li>
{/snippet}

<svelte:boundary>
  <OnboardingTour
    key="finalising-themes-archive"
    steps={[
      {
        id: "onboarding-step-1",
        title: "Welcome to Finalise Themes",
        subtitle: "3-step process to finalise themes",
        body: onboardingBody,
        icon: Target,
        nextButtonText: "Get Started",
      },
    ]}
    resizeObserverTarget={document.querySelector("main")}
  />
  {#snippet failed(error)}
    <div>
      {console.error(error)}

      <Panel>
        <Alert variant="error">Unexpected onboarding tour error</Alert>
      </Panel>
    </div>
  {/snippet}
</svelte:boundary>

<style>
  .support-link:hover :global(svg) {
    fill: var(--color-primary);
  }
</style>
