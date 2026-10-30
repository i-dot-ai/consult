<script lang="ts">
  import clsx from "clsx";
  import { SvelteSet } from "svelte/reactivity";

  import Button from "../../inputs/Button/Button.svelte";
  import Checkbox from "../../inputs/Checkbox/Checkbox.svelte";
  import RadioCards from "../../inputs/RadioCards/RadioCards.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Progress from "../../Progress/Progress.svelte";
  import KeyboardArrowDown from "../../svg/material/KeyboardArrowDown.svelte";
  import Tag from "../../Tag/Tag.svelte";
  import { orderAnswers } from "./scales";
  import { shortNameProblem } from "./shortName";
  import type { QuestionKind } from "./kinds";

  import type {
    DashboardRole,
    DemographicAnswer,
    DemographicMergeBody,
    QuestionV2,
  } from "../../../global/queries/questions/types";

  interface Props {
    question: QuestionV2;
    kind: QuestionKind;
    linkedQuestions: QuestionV2[];
    answers: DemographicAnswer[] | undefined;
    answersFailed: boolean;
    grouped: Map<string, string[]> | undefined;
    takenNames: Map<string, number>;
    nameRequired: boolean;
    expanded: boolean;
    saving: boolean;
    onToggle: () => void;
    onRetry: () => void;
    onMerge: (
      questionId: string,
      body: DemographicMergeBody,
    ) => Promise<boolean>;
    onSaveShortName: (
      questionId: string,
      shortName: string,
    ) => Promise<boolean>;
    onSaveDashboardRole: (
      questionId: string,
      role: DashboardRole,
    ) => Promise<boolean>;
  }

  let {
    question,
    kind,
    linkedQuestions,
    answers,
    answersFailed,
    grouped,
    takenNames,
    nameRequired,
    expanded,
    saving,
    onToggle,
    onRetry,
    onMerge,
    onSaveShortName,
    onSaveDashboardRole,
  }: Props = $props();

  const PREVIEW_ROWS = 3;
  const ROLE_OPTIONS: { value: DashboardRole; text: string; hint: string }[] = [
    {
      value: "filter",
      text: "Filter across all questions",
      hint: "Alongside your demographic questions",
    },
    {
      value: "standalone",
      text: "Show on its own",
      hint: "Counted and charted, not used as a filter",
    },
  ];

  let editedName = $state<string | null>(null);
  let draftName = $derived(editedName ?? question.short_name);
  let nameError = $derived(
    shortNameProblem(draftName, question.number, takenNames, nameRequired),
  );

  async function saveShortName() {
    const name = draftName.trim();
    if (nameError) {
      return;
    }
    if (name === question.short_name) {
      editedName = null;
      return;
    }
    const saved = await onSaveShortName(question.id, name);
    if (saved) {
      editedName = null;
    }
  }

  async function useQuestionAsName() {
    editedName = question.text.replace(/\?$/, "");
    await saveShortName();
  }

  let kindLabel = $derived.by(() => {
    if (kind === "demographic") {
      return "Demographic";
    }
    if (kind === "hybrid") {
      return "Hybrid";
    }
    return question.dashboard_role === "filter" ? "Filter" : "On its own";
  });
  let linkedNumbers = $derived(
    linkedQuestions.map((linked) => `Q${linked.number}`).join(" and "),
  );

  const selected = new SvelteSet<string>();
  let merging = $state(false);
  let mergeName = $state("");
  let renaming = $state<string | null>(null);
  let renameValue = $state("");

  let ordered = $derived(orderAnswers(answers ?? []));
  let total = $derived(
    ordered.answers.reduce((sum, answer) => sum + answer.count, 0),
  );
  let largest = $derived(
    ordered.answers.reduce((max, answer) => Math.max(max, answer.count), 0),
  );
  let spellings = $derived(
    ordered.answers.reduce(
      (sum, answer) => sum + (grouped?.get(answer.text)?.length ?? 1),
      0,
    ),
  );
  let selectedAnswers = $derived(
    ordered.answers.filter((answer) => selected.has(answer.text)),
  );
  let answersLabel = $derived.by(() => {
    if (answersFailed) {
      return "Answers unavailable";
    }
    if (answers === undefined) {
      return "Loading answers";
    }
    return `${answers.length} ${answers.length === 1 ? "answer" : "answers"}`;
  });

  function percent(count: number) {
    return total === 0 ? 0 : Math.round((count / total) * 100);
  }

  function share(count: number) {
    return largest === 0 ? 0 : Math.round((count / largest) * 100);
  }

  function toggleSelected(text: string, checked: boolean) {
    if (checked) {
      selected.add(text);
    } else {
      selected.delete(text);
    }
  }

  function clearSelection() {
    selected.clear();
    merging = false;
  }

  function startMerge() {
    if (selectedAnswers.length < 2) {
      return;
    }
    mergeName = selectedAnswers[0].text;
    renaming = null;
    merging = true;
  }

  async function confirmMerge() {
    const name = mergeName.trim();
    if (!name) {
      return;
    }
    const responses = selectedAnswers.flatMap((answer) => answer.responses);
    const saved = await onMerge(question.id, { new_value: name, responses });
    if (saved) {
      clearSelection();
    }
  }

  function startRename(answer: DemographicAnswer) {
    renaming = answer.text;
    renameValue = answer.text;
    merging = false;
  }

  async function saveRename(answer: DemographicAnswer) {
    const name = renameValue.trim();
    if (!name) {
      return;
    }
    if (name === answer.text) {
      renaming = null;
      return;
    }
    const saved = await onMerge(question.id, {
      new_value: name,
      responses: answer.responses,
    });
    if (saved) {
      renaming = null;
    }
  }

  function groupedNote(answer: DemographicAnswer) {
    const sources = grouped?.get(answer.text);
    if (!sources || sources.length === 0) {
      return "";
    }
    if (sources.length === 1 && sources[0] !== answer.text) {
      return `was ${sources[0]}`;
    }
    if (sources.length > 1) {
      return `grouped from ${sources.join(", ")}`;
    }
    return "";
  }
</script>

<div class="border-t border-neutral-200 first:border-t-0">
  <button
    type="button"
    class="group flex w-full flex-wrap items-start justify-between gap-4 py-4 text-left"
    aria-expanded={expanded}
    aria-controls={`answers-${question.id}`}
    onclick={onToggle}
  >
    <span class="min-w-48 flex-1">
      <span
        class="block text-md font-medium text-neutral-900 group-hover:underline group-hover:underline-offset-2"
      >
        Question {question.number}
        {#if question.short_name}
          · {question.short_name}
        {:else}
          · <span class="font-normal text-neutral-500">needs a short name</span>
        {/if}
      </span>
      <span class="mt-0.5 block text-sm leading-relaxed text-neutral-500">
        {question.text}
      </span>
    </span>
    <span class="ml-auto flex shrink-0 items-center gap-2">
      {#if !question.short_name}
        <Tag variant="warning">Needs a name</Tag>
      {/if}
      <Tag>{answersLabel}</Tag>
      <Tag>{kindLabel}</Tag>
      <span class={clsx(["transition-transform", expanded && "rotate-180"])}>
        <MaterialIcon color="fill-neutral-500" size="1rem">
          <KeyboardArrowDown />
        </MaterialIcon>
      </span>
    </span>
  </button>

  {#if expanded}
    <div id={`answers-${question.id}`} class="pb-5">
      <div class="flex flex-wrap items-end gap-2" onfocusout={saveShortName}>
        <div class="name-field max-w-xs flex-1">
          <TextInput
            id={`short-name-${question.id}`}
            label="Short name, used on the dashboard"
            placeholder="A few words"
            value={draftName}
            setValue={(value) => (editedName = value)}
            disabled={saving}
            ariaInvalid={nameError !== ""}
            ariaDescribedby={nameError
              ? `short-name-${question.id}-error`
              : undefined}
          />
        </div>
        <div>
          <Button size="sm" disabled={saving} handleClick={useQuestionAsName}>
            Use the question
          </Button>
        </div>
      </div>
      {#if nameError}
        <p
          id={`short-name-${question.id}-error`}
          class="mt-1 text-sm font-bold text-red-600"
          role="alert"
        >
          {nameError}
        </p>
      {/if}
      <p class="mt-1.5 text-sm leading-relaxed text-neutral-500">
        This labels the filter on your dashboard, so it is worth a few words of
        your own. None has been guessed, because a bad label is harder to spot
        than a missing one.
      </p>

      {#if kind === "demographic"}
        <p class="mt-3.5 text-sm leading-relaxed text-neutral-500">
          This is a demographic question, so you can use it to filter every
          question on your dashboard. To change that, set it to closed on the
          previous step.
        </p>
      {:else if kind === "hybrid"}
        <p class="mt-3.5 text-sm leading-relaxed text-neutral-500">
          This is a hybrid question. It filters {linkedNumbers} rather than the whole
          dashboard. To change that, edit the pairing on the previous step.
        </p>
      {:else}
        <div class="role-field mt-4">
          <RadioCards
            name={`role-${question.id}`}
            legend="How this question works"
            items={ROLE_OPTIONS}
            value={question.dashboard_role}
            onchange={(role) => onSaveDashboardRole(question.id, role)}
          />
        </div>
      {/if}

      <p class="mt-4 text-xs text-neutral-500">Answers found in your file</p>
      {#if answersFailed}
        <p
          class="mt-1 flex flex-wrap items-center gap-2 text-sm text-neutral-500"
        >
          <span>The answers could not be loaded.</span><Button
            variant="text"
            size="sm"
            noPadding={true}
            handleClick={onRetry}>Try again</Button
          >
        </p>
      {:else if answers === undefined}
        <p class="mt-1 text-sm text-neutral-500">Loading answers...</p>
      {:else if answers.length === 0}
        <p class="mt-1 text-sm text-neutral-500">
          No answers to this question.
        </p>
      {:else}
        <p class="mt-1 text-sm text-neutral-500">
          {#if ordered.isScale}
            These answers form a scale, so they're shown in scale order rather
            than by count. Your dashboard will use the same order.
          {:else}
            Ordered by how often each answer was given.
          {/if}
        </p>
        <p class="mt-2 mb-2.5 text-sm leading-relaxed text-neutral-500">
          {answers.length}
          {answers.length === 1 ? "answer" : "answers"}{spellings >
          answers.length
            ? `, grouped from ${spellings} spellings.`
            : "."} If two of these are really the same answer, tick them and merge.
        </p>

        <div class="mb-2.5 flex flex-wrap items-center justify-between gap-2">
          <Button
            size="sm"
            variant={selectedAnswers.length > 1 ? "primary" : "default"}
            disabled={saving || selectedAnswers.length < 2}
            handleClick={startMerge}
          >
            Merge selected{selectedAnswers.length > 0
              ? ` (${selectedAnswers.length})`
              : ""}
          </Button>
          {#if selectedAnswers.length > 0}
            <Button
              variant="text"
              size="sm"
              noPadding={true}
              handleClick={clearSelection}>Clear selection</Button
            >
          {:else}
            <span class="text-xs text-neutral-500">
              Tick two or more answers to merge them
            </span>
          {/if}
        </div>

        {#if merging}
          <div
            class="mb-3.5 rounded-lg bg-neutral-100 px-3.5 py-3"
            role="group"
            aria-label={`Merge answers to question ${question.number}`}
          >
            <div class="flex flex-wrap items-end gap-2">
              <div class="merge-name max-w-xs flex-1">
                <TextInput
                  id={`merge-${question.id}`}
                  label={`Combine ${selectedAnswers.length} answers into one, called`}
                  value={mergeName}
                  setValue={(value) => (mergeName = value)}
                />
              </div>
              <div>
                <Button
                  size="sm"
                  variant="primary"
                  disabled={saving || mergeName.trim() === ""}
                  handleClick={confirmMerge}
                >
                  Merge
                </Button>
              </div>
              <div>
                <Button
                  size="sm"
                  disabled={saving}
                  handleClick={() => (merging = false)}
                >
                  Cancel
                </Button>
              </div>
            </div>
            <p class="mt-2 text-xs leading-relaxed text-neutral-500">
              Their counts are added together. You can use one of the existing
              names or write a new one.
            </p>
          </div>
        {/if}

        <div class="rounded-lg bg-neutral-100 px-3 py-1">
          <table class="w-full">
            <caption class="sr-only"
              >Answers to question {question.number}</caption
            >
            <tbody>
              {#each ordered.answers as answer, index (answer.text)}
                {@const note = groupedNote(answer)}
                <tr
                  class={clsx([
                    "border-t border-neutral-200 first:border-t-0",
                    note && "bg-neutral-200",
                  ])}
                >
                  <td class="w-8 py-2 pl-2 align-middle">
                    <Checkbox
                      id={`select-${question.id}-${index}`}
                      size="sm"
                      label={`Select ${answer.text} for merging`}
                      hideLabel
                      checked={selected.has(answer.text)}
                      disabled={saving}
                      onchange={(checked) =>
                        toggleSelected(answer.text, checked)}
                    />
                  </td>
                  <td class="py-2 pr-2 align-middle text-md text-neutral-900">
                    {#if renaming === answer.text}
                      <div class="flex flex-wrap items-center gap-2">
                        <div class="rename-name max-w-xs flex-1">
                          <TextInput
                            id={`rename-${question.id}-${index}`}
                            label={`New name for ${answer.text}`}
                            hideLabel
                            value={renameValue}
                            setValue={(value) => (renameValue = value)}
                          />
                        </div>
                        <Button
                          size="sm"
                          variant="primary"
                          disabled={saving || renameValue.trim() === ""}
                          handleClick={() => saveRename(answer)}
                        >
                          Save
                        </Button>
                        <Button
                          size="sm"
                          disabled={saving}
                          handleClick={() => (renaming = null)}
                        >
                          Cancel
                        </Button>
                      </div>
                      <span class="mt-0.5 block text-xs text-neutral-500">
                        Renaming to a name already in the list merges the two,
                        and their counts are added together.
                      </span>
                    {:else}
                      {answer.text}
                      {#if note}
                        <span class="mt-0.5 block text-xs text-neutral-500">
                          {note}
                        </span>
                      {/if}
                    {/if}
                  </td>
                  <td class="hidden w-28 py-2 pr-2 align-middle sm:table-cell">
                    <Progress
                      value={share(answer.count)}
                      thickness={1.5}
                      variant="neutral"
                    />
                  </td>
                  <td
                    class="w-24 py-2 pr-2 text-right align-middle text-sm whitespace-nowrap text-neutral-500"
                  >
                    {answer.count} ({percent(answer.count)}%)
                  </td>
                  <td
                    class="w-20 py-2 pr-2 text-right align-middle whitespace-nowrap"
                  >
                    {#if answer.responses.length > 1 && renaming !== answer.text}
                      <Button
                        size="sm"
                        disabled={saving}
                        ariaLabel={`Rename ${answer.text}`}
                        handleClick={() => startRename(answer)}
                      >
                        Rename
                      </Button>
                    {/if}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        <p class="mt-4 text-xs text-neutral-500">
          How it will look on your dashboard
        </p>
        <div class="mt-1 rounded-lg bg-neutral-100 px-4 py-3">
          <p class="mb-1.5 text-sm font-medium text-neutral-900">
            {question.short_name || "Not named yet"}
          </p>
          {#each ordered.answers.slice(0, PREVIEW_ROWS) as answer (answer.text)}
            <div class="flex justify-between gap-3 text-xs text-neutral-500">
              <span>{answer.text}</span>
              <span>{answer.count}</span>
            </div>
            <div class="mt-1 mb-2" style:width={`${share(answer.count)}%`}>
              <Progress value={100} thickness={2} variant="neutral" />
            </div>
          {/each}
          {#if ordered.answers.length > PREVIEW_ROWS}
            <p class="text-xs text-neutral-500">
              and {ordered.answers.length - PREVIEW_ROWS} more
            </p>
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  @reference "../../../styles/global.css";

  .name-field :global(input),
  .merge-name :global(input) {
    @apply rounded-md px-2.5 py-2;
  }

  .rename-name :global(input) {
    @apply h-8 rounded-md px-2 text-sm;
  }

  .name-field :global(label) {
    @apply mb-1 block text-xs text-neutral-500;
  }

  .merge-name :global(label) {
    @apply mb-1 block text-sm text-neutral-900;
  }

  .role-field :global(legend h2) {
    @apply text-xs font-normal text-neutral-500;
  }

  .role-field :global(label) {
    @apply rounded-md px-3 py-2.5;
  }

  .role-field :global(fieldset > div) {
    @apply mt-1.5 flex flex-wrap gap-2;
  }
</style>
