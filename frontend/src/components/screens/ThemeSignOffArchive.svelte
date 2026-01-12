<script lang="ts">
  import clsx from "clsx";

  import { onMount } from "svelte";
  import { slide } from "svelte/transition";

  import {
    getApiAssignThemesUrl,
    getApiConsultationUrl,
    getApiQuestionsUrl,
    getThemeSignOffDetailUrl,
    Routes,
  } from "../../global/routes.ts";
  import { createFetchStore } from "../../global/stores.ts";
  import {
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

  const questionsStore = createFetchStore<QuestionsResponse>();
  const consultationStore = createFetchStore<ConsultationResponse>();
  const assignThemesStore = createFetchStore();

  onMount(async () => {
    $consultationStore.fetch(getApiConsultationUrl(consultationId));
    $questionsStore.fetch(getApiQuestionsUrl(consultationId));
    dataRequested = true;
  });

  let displayQuestions = $derived(
    $questionsStore.data?.results?.filter((question) =>
      `Q${question.number}: ${question.question_text}`
        .toLocaleLowerCase()
        .includes(searchValue.toLocaleLowerCase()),
    ),
  );

  let questionsForSignOff = $derived(
    $questionsStore.data?.results?.filter(
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
  {#if $consultationStore.data?.stage === "theme_mapping" || $consultationStore.data?.stage === "analysis"}
    <section in:slide>
      <ConsultationStagePanel
        consultation={$consultationStore.data || {
          id: "",
          stage: "theme_sign_off",
        }}
        questionsCount={questionsForSignOff?.length || 0}
        onConfirmClick={() => {
          /* Button removed - assign themes now triggered by admin only */
        }}
      />
    </section>
  {/if}

  {#if isAllQuestionsSignedOff && $consultationStore.data?.stage === "theme_sign_off"}
    <section in:slide>
      <Panel variant="approve-dark" bg={true}>
        <div class="px-2 py-4 text-center sm:px-8 md:px-16">
          <h2 class="mb-4 text-secondary">All Questions Signed Off</h2>
          <p class="mb-4 text-sm text-neutral-500">
            You have successfully reviewed and signed off themes for all {questionsForSignOff?.length ||
              0} consultation questions.
          </p>
          <p class="mb-2 text-sm text-neutral-500">
            <strong>Next:</strong> An admin will trigger the AI mapping phase. You'll
            be notified when mapping is complete and the Analysis Dashboard is ready.
          </p>
          <p class="mt-4 text-sm text-neutral-500">
            Contact <a
              href={`mailto:${Routes.SupportEmail}`}
              class="text-secondary hover:underline">{Routes.SupportEmail}</a
            > to proceed.
          </p>
        </div>
      </Panel>
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
          {$questionsStore.data?.results?.length || 0} questions
        </p>
      </TitleRow>
    </div>

    <Panel bg={true} border={true}>
      {#if !dataRequested || $questionsStore.isLoading}
        <div transition:slide class="my-8">
          <LoadingIndicator size="5rem" />
          <p class="text-center text-neutral-500">Loading questions...</p>
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
