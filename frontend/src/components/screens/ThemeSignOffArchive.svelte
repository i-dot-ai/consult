<script lang="ts">
  import clsx from "clsx";

  import { onMount, type Component } from "svelte";
  import { slide } from "svelte/transition";
  import type { Writable } from "svelte/store";

  import {
    getApiConsultationUrl,
    getApiQuestionsUrl,
    getThemeSignOffDetailUrl,
    Routes,
  } from "../../global/routes.ts";
  import { createFetchStore } from "../../global/stores.ts";
  import { type Question } from "../../global/types.ts";

  import Tag from "../Tag/Tag.svelte";
  import Modal from "../Modal/Modal.svelte";
  import Alert from "../Alert.svelte";
  import OnboardingTour from "../OnboardingTour/OnboardingTour.svelte";
  import Button from "../inputs/Button/Button.svelte";
  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import TitleRow from "../dashboard/TitleRow.svelte";
  import Panel from "../dashboard/Panel/Panel.svelte";
  import QuestionCard from "../dashboard/QuestionCard/QuestionCard.svelte";

  import MaterialIcon from "../MaterialIcon.svelte";
  import Checklist from "../svg/material/Checklist.svelte";
  import CheckCircle from "../svg/material/CheckCircle.svelte";
  import Finance from "../svg/material/Finance.svelte";
  import WandStars from "../svg/material/WandStars.svelte";
  import Warning from "../svg/material/Warning.svelte";
  import Headphones from "../svg/material/Headphones.svelte";
  import Help from "../svg/material/Help.svelte";
  import Target from "../svg/material/Target.svelte";
  import NotFoundMessage from "../NotFoundMessage/NotFoundMessage.svelte";
  import Price from "../svg/material/Price.svelte";

  interface Props {
    consultationId: string;
  }

  let { consultationId = "" }: Props = $props();

  let searchValue: string = $state("");
  let isConfirmModalOpen: boolean = $state(false);

  const {
    loading: isQuestionsLoading,
    error: questionsError,
    load: loadQuestions,
    data: questionsData,
  }: {
    loading: Writable<boolean>;
    error: Writable<string>;
    load: Function;
    data: Writable<any>;
  } = createFetchStore();

  const {
    loading: isConsultationLoading,
    error: loadConsultationError,
    load: loadConsultation,
    data: consultationData,
  }: {
    loading: Writable<boolean>;
    error: Writable<string>;
    load: Function;
    data: Writable<any>;
  } = createFetchStore();

  const {
    loading: isConsultationUpdating,
    error: updateConsultationError,
    load: updateConsultation,
    data: updateConsultationData,
  }: {
    loading: Writable<boolean>;
    error: Writable<string>;
    load: Function;
    data: Writable<any>;
  } = createFetchStore();

  onMount(async () => {
    loadConsultation(getApiConsultationUrl(consultationId));
    loadQuestions(getApiQuestionsUrl(consultationId));
  });

  let displayQuestions = $derived(
    $questionsData?.results?.filter((question) =>
      `Q${question.number}: ${question.question_text}`
        .toLocaleLowerCase()
        .includes(searchValue.toLocaleLowerCase()),
    ),
  );

  let questionsForSignOff = $derived(
    $questionsData?.results?.filter(
      (question: Question) => question.has_free_text,
    ),
  );

  let isAllQuestionsSignedOff: boolean = $derived(
    questionsForSignOff?.every(
      (question: Question) => question.theme_status === "confirmed",
    ),
  );
</script>

<TitleRow
  level={1}
  context="theme-sign-off"
  title="Theme Sign Off"
  subtitle="Finalise themes to use for AI to map responses to"
>
  <Price slot="icon" />
</TitleRow>

<hr class="my-6" />

{#snippet themeStage(
  text: string,
  icon: Component,
  status: "done" | "current" | "todo",
)}
  <div class="flex flex-col items-center min-w-16">
    <div
      class={clsx([
        "my-2",
        "p-2",
        "rounded-full",
        status === "done" && "bg-secondary",
        status === "todo" && "bg-neutral-200",
        status === "current" && "bg-secondary ring-4 ring-teal-100",
      ])}
    >
      <MaterialIcon
        color={status === "todo" ? "fill-neutral-500" : "fill-white"}
        size="1.2rem"
      >
        {@render icon()}
      </MaterialIcon>
    </div>
    <h3 class={clsx([status === "current" && "text-secondary"])}>
      {text}
    </h3>
  </div>
{/snippet}

<svelte:boundary>
  {#if isAllQuestionsSignedOff}
    <section in:slide>
      <Panel variant="approve-dark" bg={true}>
        <div class="px-2 sm:px-8 md:px-16">
          <ol
            class="px-1 flex items-center justify-around gap-4 text-xs text-center text-neutral-700 mb-8 w-full overflow-x-auto"
          >
            <li>
              {@render themeStage("Consultation Overview", CheckCircle, "done")}
            </li>
            <li>
              {@render themeStage(
                "Theme Sign Off",
                CheckCircle,
                $consultationData?.stage === "theme_sign_off"
                  ? "current"
                  : "done",
              )}
            </li>
            <li>
              {@render themeStage(
                "AI Theme Mapping",
                WandStars,
                $consultationData?.stage === "theme_mapping"
                  ? "current"
                  : $consultationData?.stage === "analysis"
                    ? "done"
                    : "todo",
              )}
            </li>
            <li>
              {@render themeStage(
                "Analysis Dashboard",
                Finance,
                $consultationData?.stage === "analysis" ? "current" : "todo",
              )}
            </li>
          </ol>

          <div class="px-0 md:px-16">
            <h2 class="text-secondary text-center">All Questions Signed Off</h2>

            <p class="text-sm text-center text-neutral-500 my-4">
              You have successfully reviewed and signed off themes for all {questionsForSignOff?.length ||
                0} consultation questions.
            </p>

            <p class="text-sm text-center text-neutral-500 my-4">
              <strong class="">Next:</strong> Confirm and proceed to the AI mapping
              phase where responses will be mapped to your selected themes.
            </p>

            {#if $consultationData?.stage !== "theme_mapping" && $consultationData?.stage !== "analysis"}
              <Button
                variant="approve"
                size="sm"
                fullWidth={true}
                handleClick={() => (isConfirmModalOpen = true)}
              >
                <div
                  class="flex justify-center items-center gap-3 sm:gap-1 w-full"
                >
                  <div class="shrink-0">
                    <MaterialIcon>
                      <CheckCircle />
                    </MaterialIcon>
                  </div>
                  <span class="text-left">
                    Confirm and Proceed to Mapping
                  </span>
                </div>
              </Button>
            {/if}
          </div>
        </div>
      </Panel>

      <Modal
        variant="secondary"
        title="Confirm AI Mapping"
        confirmText="Yes, Start AI Mapping"
        icon={Warning}
        open={isConfirmModalOpen}
        setOpen={(newOpen: boolean) => (isConfirmModalOpen = newOpen)}
        handleConfirm={async () => {
          await updateConsultation(
            getApiConsultationUrl(consultationId),
            "PATCH",
            {
              stage: "theme_mapping",
            },
          );

          if (!$updateConsultationError) {
            isConfirmModalOpen = false;
            location.href = location.href;
          }
        }}
      >
        <p class="text-sm text-neutral-500 mb-4">
          You have successfully reviewed and signed off themes for all {questionsForSignOff?.length ||
            0} consultation questions. Are you ready to proceed with AI mapping?
        </p>

        <p class="text-sm text-neutral-500 mb-2">This action will:</p>
        <ol class="text-sm text-neutral-500 mb-2 list-disc pl-4">
          <li class="mb-2">
            Process all consultation responses across {questionsForSignOff?.length ||
              0} questions
          </li>
          <li class="mb-2">
            Map responses to your selected themes using AI analysis
          </li>
          <li class="mb-2">Incur computational costs for the AI processing</li>
          <li class="mb-2">
            Take several hours to complete. More responses = longer time to
            process
          </li>
        </ol>

        <Alert>
          <span class="text-sm">
            <strong>Warning:</strong> Once started, this process cannot be stopped
            or easily reversed. Ensure all theme selections are final.
          </span>
        </Alert>

        <hr class="my-4" />

        <p class="text-sm text-neutral-500 mb-2">
          If you have concerns or need assistance, please contact support:
        </p>
        <a
          href={`mailto:${Routes.SupportEmail}`}
          class="support-link block mb-4 text-sm text-secondary hover:text-primary"
        >
          <div class="flex items-center gap-1">
            <MaterialIcon color="fill-secondary">
              <Headphones />
            </MaterialIcon>
            {Routes.SupportEmail}
          </div>
        </a>

        {#if $updateConsultationError}
          <div class="mt-2 mb-4">
            <Alert>
              <span class="text-sm">{$updateConsultationError}</span>
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
        <Alert>Unexpected Sign-Off Modal Error</Alert>
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
          {$questionsData?.results?.length || 0} questions
        </p>
      </TitleRow>
    </div>

    <Panel bg={true} border={true}>
      {#if $isQuestionsLoading}
        <p transition:slide>Loading questions...</p>
      {:else if $questionsError}
        <p transition:slide>{$questionsError}</p>
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
            {#if !displayQuestions?.length && !$isQuestionsLoading}
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
                  clickable={question.has_free_text}
                  disabled={!question.has_free_text}
                  url={getThemeSignOffDetailUrl(consultationId, question.id)}
                  subtext={!question.has_free_text
                    ? "No free text responses for this question = no themes to sign off. Multiple choice data will be shown in analysis dashboard."
                    : undefined}
                >
                  {#snippet tag()}
                    {#if !question.has_free_text}
                      <Tag variant="primary-light">
                        <MaterialIcon color="fill-primary">
                          <Checklist />
                        </MaterialIcon>

                        Multiple choice
                      </Tag>
                    {:else if question.theme_status === "confirmed"}
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
        <Alert>Unexpected Question List Error</Alert>
      </Panel>
    </div>
  {/snippet}
</svelte:boundary>

{#snippet onboardingBody()}
  <p>Here's how the theme sign-off process works:</p>
  <ol class="mt-4">
    {@render onboardingBodyItem(
      1,
      "Choose a Question",
      "Select any consultation question to start working with its AI-generated themes",
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
  <li class="flex items-start gap-2 mb-4">
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
        active ? "text-primary" : "text-neutral-500",
        active ? "bg-pink-100" : "bg-neutral-100",
      ])}
    >
      {number}
    </div>
    <div>
      <h4 class="font-[500]">{title}</h4>
      <p>{body}</p>
    </div>
  </li>
{/snippet}

<svelte:boundary>
  <OnboardingTour
    key="theme-sign-off-archive"
    steps={[
      {
        id: "onboarding-step-1",
        title: "Welcome to Theme Sign Off",
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
        <Alert>Unexpected onboarding tour error</Alert>
      </Panel>
    </div>
  {/snippet}
</svelte:boundary>

<style>
  .support-link:hover :global(svg) {
    fill: var(--color-primary);
  }
</style>
