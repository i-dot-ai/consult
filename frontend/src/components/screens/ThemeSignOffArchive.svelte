<script lang="ts">
  import clsx from "clsx";

  import { onMount } from "svelte";
  import { slide } from "svelte/transition";

  import {
    getApiConsultationUrl,
    getApiQuestionsUrl,
    getThemeSignOffDetailUrl,
    Routes,
  } from "../../global/routes.ts";
  import { createQueryStore } from "../../global/stores.ts";
  import {
    ConsultationStageNames,
    type ApiError,
    type ConsultationResponse,
    type Question,
    type QuestionsResponse,
  } from "../../global/types.ts";

  import Tag from "../Tag/Tag.svelte";
  import Modal from "../Modal/Modal.svelte";
  import Alert from "../Alert.svelte";
  import LoadingIndicator from "../LoadingIndicator/LoadingIndicator.svelte";
  import OnboardingTour from "../OnboardingTour/OnboardingTour.svelte";
  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import TitleRow from "../dashboard/TitleRow.svelte";
  import Panel from "../dashboard/Panel/Panel.svelte";
  import QuestionCard from "../dashboard/QuestionCard/QuestionCard.svelte";
  import ConsultationStagePanel from "../theme-sign-off/ConsultationStagePanel/ConsultationStagePanel.svelte";

  import MaterialIcon from "../MaterialIcon.svelte";
  import Checklist from "../svg/material/Checklist.svelte";
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
  let dataRequested: boolean = $state(false);

  const questionsQuery = $derived(createQueryStore<QuestionsResponse>(
    getApiQuestionsUrl(consultationId),
  ));
  const consultationQuery = $derived(createQueryStore<ConsultationResponse>(
    getApiConsultationUrl(consultationId),
  ));
  const consultationUpdateQuery = $derived(createQueryStore(
    getApiConsultationUrl(consultationId),
    { method: "PATCH" },
  ));

  onMount(async () => {
    $consultationQuery.fetch();
    $questionsQuery.fetch();
    dataRequested = true;
  });

  let displayQuestions = $derived(
    $questionsQuery.data?.results?.filter((question) =>
      `Q${question.number}: ${question.question_text}`
        .toLocaleLowerCase()
        .includes(searchValue.toLocaleLowerCase()),
    ),
  );

  let questionsForSignOff = $derived(
    $questionsQuery.data?.results?.filter(
      (question: Question) => question.has_free_text,
    ),
  );

  let isAllQuestionsSignedOff: boolean = $derived(
    Boolean(
      questionsForSignOff?.every(
        (question: Question) => question.theme_status === "confirmed",
      ),
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

<svelte:boundary>
  {#if isAllQuestionsSignedOff || $consultationQuery.data?.stage === ConsultationStageNames.THEME_MAPPING || $consultationQuery.data?.stage === ConsultationStageNames.ANALYSIS}
    <section in:slide>
      <ConsultationStagePanel
        consultation={$consultationQuery.data || {
          id: "",
          stage: ConsultationStageNames.THEME_SIGN_OFF,
        }}
        questionsCount={questionsForSignOff?.length || 0}
        onConfirmClick={() => (isConfirmModalOpen = true)}
      />

      <Modal
        variant="secondary"
        title="Confirm AI Mapping"
        confirmText="Yes, Start AI Mapping"
        icon={Warning}
        open={isConfirmModalOpen}
        setOpen={(newOpen: boolean) => (isConfirmModalOpen = newOpen)}
        handleConfirm={async () => {
          await $consultationUpdateQuery.fetch({
            body: {
              stage: ConsultationStageNames.THEME_MAPPING,
            }
          });

          if (!$consultationUpdateQuery.error) {
            isConfirmModalOpen = false;
            location.href = location.href;
          }
        }}
      >
        <p class="mb-4 text-sm text-neutral-500">
          You have successfully reviewed and signed off themes for all {questionsForSignOff?.length ||
            0} consultation questions. Are you ready to proceed with AI mapping?
        </p>

        <p class="mb-2 text-sm text-neutral-500">This action will:</p>
        <ol class="mb-2 list-disc pl-4 text-sm text-neutral-500">
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

        <p class="mb-2 text-sm text-neutral-500">
          If you have concerns or need assistance, please contact support:
        </p>
        <a
          href={`mailto:${Routes.SupportEmail}`}
          class="support-link mb-4 block text-sm text-secondary hover:text-primary"
        >
          <div class="flex items-center gap-1">
            <MaterialIcon color="fill-secondary">
              <Headphones />
            </MaterialIcon>
            {Routes.SupportEmail}
          </div>
        </a>

        {#if $consultationUpdateQuery.error}
          <div class="mb-4 mt-2">
            <Alert>
              <span class="text-sm">
                {($consultationUpdateQuery.error as ApiError).detail}
              </span>
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
          {$questionsQuery.data?.results?.length || 0} questions
        </p>
      </TitleRow>
    </div>

    <Panel bg={true} border={true}>
      {#if !dataRequested || $questionsQuery.isLoading}
        <div transition:slide class="my-8">
          <LoadingIndicator size="5rem" />
          <p class="text-center text-neutral-500">Loading questions...</p>
        </div>
      {:else if $questionsQuery.error}
        <p transition:slide>{($questionsQuery.error as ApiError).detail}</p>
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
                  clickable={question.has_free_text}
                  disabled={!question.has_free_text}
                  url={getThemeSignOffDetailUrl(
                    consultationId,
                    question.id || "",
                  )}
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
