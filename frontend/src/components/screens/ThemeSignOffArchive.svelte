<script lang="ts">
  import clsx from "clsx";

  import { onMount, type Component } from "svelte";
  import { slide } from "svelte/transition";
  import type { Writable } from "svelte/store";

  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Help from "../svg/material/Help.svelte";
  import TitleRow from "../dashboard/TitleRow.svelte";
  import Panel from "../dashboard/Panel/Panel.svelte";
  import QuestionCard from "../dashboard/QuestionCard/QuestionCard.svelte";

  import {
    getApiQuestionsUrl,
    getThemeSignOffDetailUrl,
  } from "../../global/routes.ts";
  import { createFetchStore } from "../../global/stores.ts";

  import Tag from "../Tag/Tag.svelte";
  import Button from "../inputs/Button/Button.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import Checklist from "../svg/material/Checklist.svelte";
  import CheckCircle from "../svg/material/CheckCircle.svelte";
  import Finance from "../svg/material/Finance.svelte";

  interface Props {
    consultationId: string;
  }

  let {
    consultationId = "",
  }: Props = $props();

  let searchValue: string = $state("");

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

  onMount(async () => {
    loadQuestions(getApiQuestionsUrl(consultationId));
  });

  let displayQuestions = $derived($questionsData?.results?.filter((question) =>
    `Q${question.number}: ${question.question_text}`
      .toLocaleLowerCase()
      .includes(searchValue.toLocaleLowerCase()),
  ))

  let allQuestionsSignedOff = $derived($questionsData?.results?.filter(
    question => question.has_free_text
  ).every(
    question => question.theme_status === "confirmed"
  ));
</script>

{#snippet themeStage(
  text: string,
  icon: Component,
  status: "done" | "current" | "todo",
)}
  <div class="flex flex-col items-center min-w-16">
    <div class={clsx([
      "my-2",
      "p-2",
      "rounded-full",
      status === "done" && "bg-emerald-700",
      status === "todo" && "bg-neutral-200",
      status === "current" && "bg-emerald-700 ring-4 ring-emerald-100",
    ])}>
      <MaterialIcon
        color={status === "todo"
          ? "fill-neutral-500"
          : "fill-white"
        }
        size="1.2rem"
      >
        {@render icon()}
      </MaterialIcon>
    </div>
    <h3 class={clsx([
      status === "current" && "text-emerald-700",
    ])}>
      {text}
    </h3>
  </div>
{/snippet}

{#if allQuestionsSignedOff}
  <section in:slide>
    <Panel variant="approve-dark" bg={true}>
      <div class="px-2 sm:px-8 md:px-16">
        <ol class="px-1 flex items-center justify-around gap-4 text-xs text-center text-neutral-700 mb-8 w-full overflow-x-auto">
          <li>
            {@render themeStage("Consultation Overview", CheckCircle, "done")}
          </li>
          <li>
            {@render themeStage("Theme Sign Off", CheckCircle, "current")}
          </li>
          <li>
            {@render themeStage("AI Theme Mapping", CheckCircle, "todo")}
          </li>
          <li>
            {@render themeStage("Analysis Dashboard", Finance, "todo")}
          </li>
        </ol>

        <div class="px-0 md:px-16">
          <h2 class="text-emerald-700 text-center">
            All Questions Signed Off
          </h2>

          <p class="text-sm text-center text-neutral-500 my-4">
            You have successfully reviewed and signed off themes for all 8 consultation questions.
          </p>

          <p class="text-sm text-center text-neutral-500 my-4">
            <strong class="">Next:</strong> Confirm and proceed to the AI mapping phase where responses will be mapped to your selected themes.
          </p>

          <Button
            variant="approve"
            size="sm"
            fullWidth={true}
            handleClick={() => {}}
          >
            <div class="flex justify-center items-center gap-3 sm:gap-1 w-full">
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
        </div>
      </div>
    </Panel>
  </section>
{/if}

<section class="my-8">
  <div class="my-2">
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
        </div>
      </div>
    {/if}
  </Panel>
</section>
