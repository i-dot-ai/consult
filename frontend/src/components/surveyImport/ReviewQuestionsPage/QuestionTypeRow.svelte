<script lang="ts">
  import clsx from "clsx";

  import Button from "../../inputs/Button/Button.svelte";
  import Select from "../../inputs/Select/Select.svelte";
  import Textarea from "../../inputs/Textarea/Textarea.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import EditSquare from "../../svg/material/EditSquare.svelte";
  import Link from "../../svg/material/Link.svelte";
  import Tag from "../../Tag/Tag.svelte";

  import type {
    QuestionV2,
    QuestionV2UpdateBody,
  } from "../../../global/queries/questions/types";

  // Hybrid is not a type on the API: it is a closed question with open
  // questions linked to it through closed_question (ADR-0006).
  type TypeChoice = "open" | "closed" | "hybrid" | "demographic" | "";

  interface Props {
    question: QuestionV2;
    linkedQuestions: QuestionV2[];
    openQuestions: QuestionV2[];
    proposed: QuestionV2 | undefined;
    changeTags: string[];
    linking: boolean;
    editing: boolean;
    saving: boolean;
    answers: string[] | undefined;
    answersFailed: boolean;
    onStartLinking: () => void;
    onCancelLinking: () => void;
    onStartEditing: () => void;
    onCancelEditing: () => void;
    onShowAnswers: () => void;
    onRejectProposal: () => void;
    onSave: (
      questionId: string,
      body: QuestionV2UpdateBody,
    ) => Promise<boolean>;
  }

  let {
    question,
    linkedQuestions,
    openQuestions,
    proposed,
    changeTags,
    linking,
    editing,
    saving,
    answers,
    answersFailed,
    onStartLinking,
    onCancelLinking,
    onStartEditing,
    onCancelEditing,
    onShowAnswers,
    onRejectProposal,
    onSave,
  }: Props = $props();

  const TYPE_OPTIONS: { value: TypeChoice; label: string }[] = [
    { value: "", label: "Choose a type" },
    { value: "open", label: "Open" },
    { value: "closed", label: "Closed" },
    { value: "hybrid", label: "Hybrid" },
    { value: "demographic", label: "Demographic" },
  ];

  let choice = $derived.by<TypeChoice>(() => {
    if (question.type === "closed" && linkedQuestions.length > 0) {
      return "hybrid";
    }
    return question.type ?? "";
  });

  let linkTargets = $derived(
    openQuestions.map((open) => ({
      value: open.id,
      label: `Q${open.number} ${open.text}`,
    })),
  );
  let linkChoice = $state("");
  let pending = $state<TypeChoice | null>(null);
  let shown = $derived(linking ? "hybrid" : (pending ?? choice));

  async function handleTypeChange(value: TypeChoice | undefined) {
    pending = value ?? "";
    if (value === "hybrid") {
      let isClosed = question.type === "closed";
      if (!isClosed) {
        isClosed = await onSave(question.id, {
          type: "closed",
          closed_question: null,
        });
      }
      if (isClosed) {
        onStartLinking();
      }
      pending = null;
      return;
    }
    if (value === "closed" && choice === "hybrid") {
      // The type is unchanged, so the server will not drop the links itself.
      for (const linked of linkedQuestions) {
        const saved = await onSave(linked.id, { closed_question: null });
        if (!saved) {
          break;
        }
      }
    } else {
      await onSave(question.id, { type: value || null, closed_question: null });
    }
    pending = null;
  }

  async function handleLink() {
    if (!linkChoice) {
      return;
    }
    const saved = await onSave(linkChoice, {
      type: "open",
      closed_question: question.id,
    });
    if (saved) {
      cancelLinking();
    }
  }

  function cancelLinking() {
    linkChoice = "";
    onCancelLinking();
  }

  async function acceptProposal() {
    if (!proposed) {
      return;
    }
    await onSave(proposed.id, { type: "open", closed_question: question.id });
  }

  let showAnswers = $state(false);
  let draft = $state("");
  let draftError = $state("");

  function toggleAnswers() {
    showAnswers = !showAnswers;
    if (showAnswers) {
      onShowAnswers();
    }
  }

  function startEditing() {
    draft = question.text;
    draftError = "";
    onStartEditing();
  }

  async function saveWording() {
    const text = draft.trim();
    if (!text) {
      draftError = "Enter the question wording. It cannot be empty.";
      return;
    }
    if (text === question.text) {
      onCancelEditing();
      return;
    }
    const saved = await onSave(question.id, { text });
    if (saved) {
      onCancelEditing();
    }
  }
</script>

<div
  class={clsx([
    "flex flex-wrap items-start gap-4 border-t border-neutral-200 px-7 py-4",
    changeTags.length > 0 && "bg-neutral-50",
  ])}
>
  <span class="w-16 shrink-0 pt-1.5 text-md text-neutral-500">
    Q{question.number}
  </span>
  <div class="min-w-48 flex-1 pt-1.5">
    {#if editing}
      <div>
        {#if draftError}
          <p
            id={`wording-${question.id}-error`}
            class="mb-1 text-sm font-bold text-red-600"
            role="alert"
          >
            {draftError}
          </p>
        {/if}
        <Textarea
          id={`wording-${question.id}`}
          label="Question wording"
          hideLabel
          rows={2}
          value={draft}
          setValue={(value) => (draft = value)}
        />
        <div class="mt-2 flex gap-2">
          <Button
            size="sm"
            variant="primary"
            disabled={saving}
            handleClick={saveWording}
          >
            Save wording
          </Button>
          <Button size="sm" disabled={saving} handleClick={onCancelEditing}>
            Cancel
          </Button>
        </div>
      </div>
    {:else}
      <p class="text-md text-neutral-900">{question.text}</p>
    {/if}
    {#if changeTags.length > 0}
      <div class="mt-2 flex flex-wrap gap-2">
        {#each changeTags as tag (tag)}
          <Tag border={true}>
            <span class="flex items-center gap-1">
              <MaterialIcon color="fill-neutral-500" size="0.8rem">
                <EditSquare />
              </MaterialIcon>
              {tag}
            </span>
          </Tag>
        {/each}
      </div>
    {/if}

    <div class="mt-2">
      <Button
        variant="text"
        size="sm"
        noPadding={true}
        ariaExpanded={showAnswers}
        handleClick={toggleAnswers}
      >
        {showAnswers ? "Hide answers" : "Show answers"}
      </Button>
    </div>
    {#if showAnswers}
      <div class="mt-3 rounded-lg bg-neutral-100 p-3 text-sm">
        {#if answersFailed}
          <p class="text-neutral-500">No answers for this question.</p>
        {:else if answers === undefined}
          <p class="text-neutral-500">Loading answers...</p>
        {:else if answers.length === 0}
          <p class="text-neutral-500">No answers for this question.</p>
        {:else}
          <p class="mb-1.5 text-xs text-neutral-500">
            A sample. {answers.length} of {question.response_count} answers to this
            question
          </p>
          {#each answers as text, index (index)}
            <p class="leading-relaxed text-neutral-900 not-last:mb-2">{text}</p>
          {/each}
        {/if}
      </div>
    {/if}

    {#if question.type === "closed"}
      {#if proposed && !linking && linkedQuestions.length === 0}
        <div
          class="mt-2 rounded-lg bg-neutral-100 p-3 text-sm leading-relaxed text-neutral-500"
          role="group"
          aria-label={`Suggested link for question ${question.number}`}
        >
          This looks like a hybrid pair. Q{proposed.number} asks people to explain
          this answer, so its answers could be read by how people answered here.
          <div class="mt-2 flex gap-2">
            <Button
              size="sm"
              variant="primary"
              disabled={saving}
              handleClick={acceptProposal}
            >
              Yes, they are a pair
            </Button>
            <Button size="sm" disabled={saving} handleClick={onRejectProposal}>
              No, separate questions
            </Button>
          </div>
        </div>
      {:else if linking}
        <div class="mt-2">
          {#if linkTargets.length === 0}
            <p class="text-sm text-neutral-500">
              Set an open question first, then link it to this one.
            </p>
          {:else}
            <div
              class="flex flex-wrap items-center gap-2"
              role="group"
              aria-label={`Link question ${question.number} to an open question`}
            >
              <div class="link-picker max-w-md flex-1">
                <Select
                  id={`link-${question.id}`}
                  label="Question to link to"
                  items={[
                    { value: "", label: "Choose an open question" },
                    ...linkTargets,
                  ]}
                  value={linkChoice}
                  disabled={saving}
                  onchange={(value) => (linkChoice = value ?? "")}
                />
              </div>
              <Button
                size="sm"
                variant="primary"
                disabled={saving || !linkChoice}
                handleClick={handleLink}
              >
                Link
              </Button>
              <Button size="sm" disabled={saving} handleClick={cancelLinking}>
                Cancel
              </Button>
            </div>
          {/if}
        </div>
      {:else if linkedQuestions.length > 0}
        <div class="mt-2 flex flex-wrap gap-2">
          {#each linkedQuestions as linked (linked.id)}
            <Tag border={true} wrap={true}>
              <span class="flex flex-wrap items-center gap-1">
                <MaterialIcon color="fill-neutral-500" size="0.8rem">
                  <Link />
                </MaterialIcon>
                Explains Q{linked.number}. Its answers can be filtered by this
                one.
                <span class="ml-2">
                  <Button
                    variant="text"
                    size="sm"
                    noPadding={true}
                    disabled={saving}
                    ariaLabel={`Remove link to Q${linked.number}`}
                    handleClick={() =>
                      onSave(linked.id, { closed_question: null })}
                  >
                    remove
                  </Button>
                </span>
              </span>
            </Tag>
          {/each}
        </div>
      {:else}
        <div class="mt-2">
          <Button
            variant="text"
            size="sm"
            noPadding={true}
            disabled={saving}
            handleClick={onStartLinking}
          >
            This question explains another
          </Button>
        </div>
      {/if}
    {/if}
  </div>
  <div class="type-cell min-w-48 flex-1 sm:w-48 sm:flex-none">
    <Select
      id={`type-${question.id}`}
      label="This question is"
      items={TYPE_OPTIONS}
      value={shown}
      disabled={saving}
      onchange={handleTypeChange}
    />
  </div>
  <div class="w-16 shrink-0 pt-1.5">
    {#if !editing}
      <Button
        size="sm"
        disabled={saving}
        ariaLabel={`Edit wording of question ${question.number}`}
        handleClick={startEditing}
      >
        Edit
      </Button>
    {/if}
  </div>
</div>

<style>
  @reference "../../../styles/global.css";

  .type-cell :global(label) {
    @apply text-sm text-neutral-500 md:text-sm;
  }

  .link-picker :global(label) {
    @apply sr-only;
  }
</style>
