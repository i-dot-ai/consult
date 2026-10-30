<script lang="ts">
  import { tick, untrack } from "svelte";
  import { SvelteMap, SvelteSet } from "svelte/reactivity";

  import Alert from "../../Alert/Alert.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import StepTitle from "../StepTitle/StepTitle.svelte";
  import ErrorIcon from "../../svg/material/Error.svelte";
  import Tune from "../../svg/material/Tune.svelte";
  import QuestionSetupRow from "./QuestionSetupRow.svelte";
  import type { QuestionKind } from "./kinds";
  import { shortNameProblem } from "./shortName";

  import {
    buildDemographicMergeQuery,
    buildQuestionsV2Query,
    buildQuestionV2UpdateQuery,
    fetchDemographicAnswers,
  } from "../../../global/queries/questions/queries";
  import type {
    DashboardRole,
    DemographicAnswer,
    DemographicMergeBody,
    QuestionV2,
    QuestionV2UpdateBody,
  } from "../../../global/queries/questions/types";
  import {
    getDataUploadFinaliseUrl,
    getDataUploadReviewQuestionsUrl,
  } from "../../../global/routes";

  interface Props {
    consultationId: string;
  }

  let { consultationId }: Props = $props();

  const questionsQuery = buildQuestionsV2Query(untrack(() => consultationId));
  const merge = buildDemographicMergeQuery(untrack(() => consultationId));
  const updateQuestion = buildQuestionV2UpdateQuery(
    untrack(() => consultationId),
    async () => {
      await questionsQuery.fetch();
    },
  );

  let allQuestions: QuestionV2[] = $derived(questionsQuery.query.data ?? []);
  let questions = $derived(
    allQuestions.filter(
      (question) =>
        question.type === "closed" || question.type === "demographic",
    ),
  );
  let linkedByClosedId = $derived.by(() => {
    const map = new SvelteMap<string, QuestionV2[]>();
    for (const question of allQuestions) {
      if (question.type !== "open" || !question.closed_question) {
        continue;
      }
      const linked = map.get(question.closed_question) ?? [];
      linked.push(question);
      map.set(question.closed_question, linked);
    }
    return map;
  });

  function kindOf(question: QuestionV2): QuestionKind {
    if (question.type === "demographic") {
      return "demographic";
    }
    return linkedByClosedId.has(question.id) ? "hybrid" : "closed";
  }

  let takenNames = $derived.by(() => {
    const names = new SvelteMap<string, number>();
    for (const question of questions) {
      if (question.short_name) {
        names.set(question.short_name.toLowerCase(), question.number);
      }
    }
    return names;
  });

  let intro = $derived.by(() => {
    if (questionsQuery.query.isPending || questionsQuery.query.isError) {
      return "";
    }
    if (questions.length === 0) {
      return "Every question is open, so there are no charts or filters to set up.";
    }
    const counts = { closed: 0, hybrid: 0, demographic: 0 };
    for (const question of questions) {
      counts[kindOf(question)] += 1;
    }
    const parts = (["closed", "hybrid", "demographic"] as QuestionKind[])
      .filter((kind) => counts[kind] > 0)
      .map((kind) => `${counts[kind]} ${kind}`);
    const list =
      parts.length > 1
        ? `${parts.slice(0, -1).join(", ")} and ${parts[parts.length - 1]}`
        : parts[0];
    const subject =
      questions.length === 1
        ? `Your ${list} question becomes a chart or a filter`
        : `Your ${list} questions each become a chart or a filter`;
    const unnamed = questions.some((question) => !question.short_name);
    const prompt = unnamed
      ? "Open each one to give it a short name."
      : "Open any that need changing.";
    return `${subject} on your dashboard. They are set up from the data in the file. ${prompt}`;
  });

  const expandedIds = new SvelteSet<string>();
  const answersById = new SvelteMap<string, DemographicAnswer[]>();
  const answersFailed = new SvelteSet<string>();
  const answersLoading = new SvelteSet<string>();
  // Names each answer was merged from this visit, by question then answer.
  const groupedFrom = new SvelteMap<string, SvelteMap<string, string[]>>();
  let saving = $state(false);
  let saveError = $state("");
  let finishAttempted = $state(false);
  let finishProblems = $state<{ question: QuestionV2; message: string }[]>([]);
  let finishSummaryEl = $state<HTMLElement | null>(null);

  function toggleExpanded(questionId: string) {
    if (expandedIds.has(questionId)) {
      expandedIds.delete(questionId);
    } else {
      expandedIds.add(questionId);
    }
  }

  async function loadAnswers(questionId: string) {
    answersLoading.add(questionId);
    answersFailed.delete(questionId);
    try {
      const answers = await fetchDemographicAnswers(consultationId, questionId);
      answersById.set(questionId, answers);
    } catch {
      answersFailed.add(questionId);
    } finally {
      answersLoading.delete(questionId);
    }
  }

  $effect(() => {
    const questionIds = questions.map((question) => question.id);
    untrack(() => {
      for (const questionId of questionIds) {
        const known =
          answersById.has(questionId) ||
          answersFailed.has(questionId) ||
          answersLoading.has(questionId);
        if (!known) {
          loadAnswers(questionId);
        }
      }
    });
  });

  function recordGrouping(questionId: string, body: DemographicMergeBody) {
    const mergedIds = new Set(body.responses);
    const previous =
      groupedFrom.get(questionId) ?? new SvelteMap<string, string[]>();
    const sources: string[] = [];
    for (const answer of answersById.get(questionId) ?? []) {
      const isMerged = answer.responses.some((responseId) =>
        mergedIds.has(responseId),
      );
      const keepsName = answer.text === body.new_value;
      if (isMerged || keepsName) {
        sources.push(...(previous.get(answer.text) ?? [answer.text]));
      }
    }
    const next = new SvelteMap(previous);
    for (const answer of answersById.get(questionId) ?? []) {
      if (answer.responses.some((responseId) => mergedIds.has(responseId))) {
        next.delete(answer.text);
      }
    }
    next.set(body.new_value, [...new Set(sources)]);
    groupedFrom.set(questionId, next);
  }

  function questionNumber(questionId: string) {
    return questions.find((entry) => entry.id === questionId)?.number;
  }

  async function handleMerge(questionId: string, body: DemographicMergeBody) {
    saving = true;
    saveError = "";
    try {
      await merge.fetch(questionId, body);
      recordGrouping(questionId, body);
      await loadAnswers(questionId);
      return true;
    } catch (error) {
      console.error(error);
      saveError = `The answers for question ${questionNumber(questionId)} were not merged. Try again.`;
      return false;
    } finally {
      saving = false;
    }
  }

  async function saveQuestion(
    questionId: string,
    body: QuestionV2UpdateBody,
    failure: string,
  ) {
    saving = true;
    saveError = "";
    try {
      await updateQuestion.fetch(questionId, body);
      return true;
    } catch (error) {
      console.error(error);
      saveError = `${failure} for question ${questionNumber(questionId)} was not saved. Try again.`;
      return false;
    } finally {
      saving = false;
    }
  }

  function handleSaveShortName(questionId: string, shortName: string) {
    return saveQuestion(questionId, { short_name: shortName }, "The name");
  }

  function handleSaveDashboardRole(questionId: string, role: DashboardRole) {
    return saveQuestion(questionId, { dashboard_role: role }, "The setting");
  }

  async function handleFinish() {
    finishAttempted = true;
    finishProblems = questions
      .filter((question) => kindOf(question) === "closed")
      .map((question) => ({
        question,
        message: shortNameProblem(
          question.short_name,
          question.number,
          takenNames,
          true,
        ),
      }))
      .filter((problem) => problem.message !== "");
    if (finishProblems.length > 0) {
      for (const problem of finishProblems) {
        expandedIds.add(problem.question.id);
      }
      await tick();
      finishSummaryEl?.focus();
      return;
    }
    window.location.href = getDataUploadFinaliseUrl(consultationId);
  }
</script>

<StepTitle
  stepNo={6}
  maxStepNo={6}
  title="Set up your charts and filters"
  Icon={Tune}
/>

{#if intro}
  <p class="mt-3.5 mb-6 text-md leading-relaxed text-neutral-500">{intro}</p>
{/if}

{#if finishProblems.length > 0}
  <div class="mb-6" role="alert" tabindex="-1" bind:this={finishSummaryEl}>
    <Alert variant="error" Icon={ErrorIcon}>
      <p class="font-bold">There is a problem</p>
      <ul class="mt-1 list-disc pl-5">
        {#each finishProblems as problem (problem.question.id)}
          <li>
            <a class="underline" href={`#short-name-${problem.question.id}`}>
              Question {problem.question.number}: {problem.message}
            </a>
          </li>
        {/each}
      </ul>
    </Alert>
  </div>
{/if}

{#if saveError}
  <div class="mb-6" role="alert">
    <Alert variant="error" onTimeout={() => (saveError = "")}>{saveError}</Alert
    >
  </div>
{/if}

{#if questionsQuery.query.isPending}
  <p class="mt-6 text-md text-neutral-500">Loading questions...</p>
{:else if questionsQuery.query.isError}
  <p class="mt-6 text-md text-neutral-500">Failed to load questions.</p>
{:else if questions.length > 0}
  <div class="rounded-xl border border-neutral-300 bg-white px-7">
    {#each questions as question (question.id)}
      <QuestionSetupRow
        {question}
        kind={kindOf(question)}
        linkedQuestions={linkedByClosedId.get(question.id) ?? []}
        answers={answersById.get(question.id)}
        answersFailed={answersFailed.has(question.id)}
        grouped={groupedFrom.get(question.id)}
        {takenNames}
        nameRequired={finishAttempted && kindOf(question) === "closed"}
        expanded={expandedIds.has(question.id)}
        {saving}
        onToggle={() => toggleExpanded(question.id)}
        onRetry={() => loadAnswers(question.id)}
        onMerge={handleMerge}
        onSaveShortName={handleSaveShortName}
        onSaveDashboardRole={handleSaveDashboardRole}
      />
    {/each}
  </div>
{/if}

<div class="mt-7 flex flex-wrap justify-between gap-2">
  <Button size="sm" href={getDataUploadReviewQuestionsUrl(consultationId)}>
    Back
  </Button>
  <Button size="sm" variant="primary" handleClick={handleFinish}>
    Finish set-up
  </Button>
</div>
