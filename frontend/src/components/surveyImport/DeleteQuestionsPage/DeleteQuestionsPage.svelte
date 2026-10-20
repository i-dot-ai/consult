<script lang="ts">
  import Alert from "../../Alert/Alert.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import Checkbox from "../../inputs/Checkbox/Checkbox.svelte";
  import Modal from "../../Modal/Modal.svelte";
  import StepTitle from "../StepTitle/StepTitle.svelte";
  import Delete from "../../svg/material/Delete.svelte";
  import Warning from "../../svg/material/Warning.svelte";

  import { SvelteMap, SvelteSet } from "svelte/reactivity";

  import {
    buildListQuestionsQuery,
    deleteQuestion,
  } from "../../../global/queries/questions";
  import {
    getDataUploadUrl,
    getApiQuestionResponsesUrl,
  } from "../../../global/routes";
  import type { Question } from "../../../global/types";

  interface Props {
    consultationId: string;
  }

  let { consultationId }: Props = $props();

  const questionsQuery = buildListQuestionsQuery(consultationId);

  let questions: Question[] = $derived(
    questionsQuery.query.data?.results ?? [],
  );

  let selectedIds = new SvelteSet<string>();
  let expandedIds = new SvelteSet<string>();
  let confirmOpen = $state(false);
  let deleting = $state(false);
  let deleteError = $state("");
  let successMessage = $state("");

  let selectedQuestions = $derived(
    questions.filter((q) => selectedIds.has(q.id)),
  );

  let questionIndexMap = $derived(
    new Map(questions.map((q, i) => [q.id, i + 1])),
  );

  const freeTextSamples = new SvelteMap<string, string[]>();
  const freeTextFailed = new SvelteSet<string>();

  async function fetchFreeTextSample(questionId: string) {
    if (freeTextSamples.has(questionId)) return;
    freeTextFailed.delete(questionId);
    const url = `${getApiQuestionResponsesUrl(consultationId, questionId)}?page_size=3`;
    try {
      const res = await fetch(url);
      if (!res.ok) {
        freeTextFailed.add(questionId);
        return;
      }
      const data = await res.json();
      freeTextSamples.set(
        questionId,
        (data.all_respondents ?? []).map(
          (r: { free_text_answer_text: string }) => r.free_text_answer_text,
        ),
      );
    } catch {
      freeTextFailed.add(questionId);
    }
  }

  function toggleSelected(id: string, checked: boolean) {
    if (checked) {
      selectedIds.add(id);
    } else {
      selectedIds.delete(id);
    }
  }

  function clearSelection() {
    selectedIds.clear();
  }

  function toggleExpanded(question: Question) {
    if (expandedIds.has(question.id)) {
      expandedIds.delete(question.id);
    } else {
      expandedIds.add(question.id);
      if (question.has_free_text && !question.has_multiple_choice) {
        fetchFreeTextSample(question.id);
      }
    }
  }

  async function handleConfirmDelete() {
    deleting = true;
    deleteError = "";

    const results = await Promise.allSettled(
      selectedQuestions.map((q) => deleteQuestion(consultationId, q.id)),
    );

    const failed = results.filter((r) => r.status === "rejected");
    const succeeded = results.length - failed.length;

    if (succeeded > 0) {
      successMessage = `${succeeded} ${succeeded === 1 ? "question has" : "questions have"} been deleted.`;
      await questionsQuery.fetch();
    }
    if (failed.length > 0) {
      deleteError = `${failed.length} ${failed.length === 1 ? "question" : "questions"} could not be deleted.`;
    }

    clearSelection();
    confirmOpen = false;
    deleting = false;
  }
</script>

<StepTitle stepNo={4} maxStepNo={6} title="Delete questions" Icon={Delete} />

<p class="mt-3.5 mb-[26px] text-[15px] leading-relaxed text-neutral-500">
  Consult reads every column in the file as a question. Delete any that are not
  questions, such as response IDs or dates. If every one is a question,
  continue.
</p>

{#if successMessage}
  <div class="mb-6">
    <Alert variant="success" onTimeout={() => (successMessage = "")}>
      {successMessage}
    </Alert>
  </div>
{/if}

{#if deleteError}
  <div class="mb-6">
    <Alert variant="error" onTimeout={() => (deleteError = "")}>
      {deleteError}
    </Alert>
  </div>
{/if}

<div class="rounded-xl border border-neutral-300 bg-white">
  <div class="px-7 py-4 text-[15px] text-neutral-500">
    {#if questionsQuery.query.isPending}
      Loading questions...
    {:else if questionsQuery.query.isError}
      Failed to load questions.
    {:else}
      {questions.length}
      {questions.length === 1 ? "question" : "questions"}
    {/if}
  </div>

  {#if selectedIds.size > 0}
    <div
      class="mx-7 mb-4 flex items-center gap-4 rounded-lg border border-neutral-300 bg-neutral-50 px-4 py-3"
    >
      <span class="text-[15px] font-medium text-neutral-900">
        {selectedIds.size} selected
      </span>
      <Button
        size="sm"
        variant="danger"
        handleClick={() => (confirmOpen = true)}
      >
        Delete selected questions
      </Button>
      <Button size="sm" variant="ghost" handleClick={clearSelection}>
        Clear selection
      </Button>
    </div>
  {/if}

  {#if !questionsQuery.query.isPending && !questionsQuery.query.isError}
    <div class="border-t border-neutral-200">
      <div
        class="grid grid-cols-[3rem_4rem_1fr] px-7 py-2 text-sm text-neutral-500"
      >
        <span></span>
        <span>No.</span>
        <span>Question</span>
      </div>

      {#each questions as question, i (question.id)}
        <div class="border-t border-neutral-200">
          <div class="grid grid-cols-[3rem_4rem_1fr] items-start px-7 py-4">
            <div class="pt-0.5">
              <Checkbox
                id={`question-${question.id}`}
                checked={selectedIds.has(question.id)}
                label={question.question_text}
                hideLabel
                onchange={(checked) => toggleSelected(question.id, checked)}
              />
            </div>
            <span class="text-[15px] text-neutral-500">Q{i + 1}</span>
            <div>
              <p class="text-[15px] text-neutral-900">
                {question.question_text}
              </p>
              <Button
                size="sm"
                variant="ghost"
                handleClick={() => toggleExpanded(question)}
              >
                {expandedIds.has(question.id) ? "Hide answers" : "Show answers"}
              </Button>

              {#if expandedIds.has(question.id)}
                <div class="mt-3 text-sm text-neutral-500">
                  {#if question.has_free_text && !question.has_multiple_choice}
                    {#if freeTextFailed.has(question.id)}
                      No answers for this question.
                    {:else if !freeTextSamples.has(question.id)}
                      Loading answers...
                    {:else if freeTextSamples.get(question.id)!.length === 0}
                      No answers for this question.
                    {:else}
                      <p class="mb-2">
                        A sample. {freeTextSamples.get(question.id)!.length} of {question.free_text_response_count}
                        answers to this question
                      </p>
                      {#each freeTextSamples.get(question.id)! as text, i (i)}
                        <p>{text}</p>
                      {/each}
                    {/if}
                  {:else if question.total_response_count === 0}
                    No answers for this question.
                  {:else}
                    {@const sample =
                      question.multiple_choice_answer?.slice(0, 3) ?? []}
                    <p class="mb-2">
                      A sample. {Math.min(3, question.total_response_count)} of {question.total_response_count}
                      answers to this question
                    </p>
                    {#each sample as answer (answer.id)}
                      <p>{answer.text}</p>
                    {/each}
                  {/if}
                </div>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<div class="mt-7 flex flex-wrap justify-between gap-2">
  <Button size="sm" href={getDataUploadUrl(consultationId)}>
    Back to overview
  </Button>
  <Button size="sm" variant="primary" href="step-5">
    <!-- TODO: Replace with getDataUploadReviewQuestionsUrl(consultationId) once step 5 is built -->
    Continue to review questions
  </Button>
</div>

<Modal
  variant="warning"
  open={confirmOpen}
  setOpen={(open) => {
    if (!open) confirmOpen = false;
  }}
  title="Delete questions"
  Icon={Warning}
  confirmText="Delete questions"
  confirmDisabled={deleting}
  handleConfirm={handleConfirmDelete}
>
  <p class="mb-4 text-[15px] leading-relaxed text-neutral-500">
    Deleting removes the questions and their answers from Consult. This cannot
    be undone.
  </p>
  <div
    class="mb-4 max-h-48 overflow-y-auto rounded-lg border border-neutral-200 bg-neutral-50 px-4 py-3"
  >
    {#each selectedQuestions as q (q.id)}
      <p class="py-1.5 text-[15px] text-neutral-900">
        <span class="text-neutral-500">Q{questionIndexMap.get(q.id)}</span>
        {q.question_text}
      </p>
    {/each}
  </div>
</Modal>
