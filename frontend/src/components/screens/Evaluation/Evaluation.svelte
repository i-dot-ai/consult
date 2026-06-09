<script lang="ts">
  import { getApiConsultationEvaluationUrl } from "../../../global/routes";
  import type { SearchableSelectOption } from "../../../global/types";
  import SearchableSelect from "../../inputs/SearchableSelect.svelte";
  import type {
    ConsultationEval,
    EvalUser,
    F1Stats,
    QuestionEval,
  } from "./types";

  interface Props {
    consultationId: string;
    initialData: ConsultationEval;
    questionDetailBaseUrl: string;
  }

  let { consultationId, initialData, questionDetailBaseUrl }: Props = $props();

  const availableUsers: EvalUser[] = initialData.users;
  let data: ConsultationEval = $state(initialData);
  let selectedUserIds: string[] = $state([]);
  let isLoading = $state(false);

  async function fetchEvaluation() {
    isLoading = true;
    const baseUrl = getApiConsultationEvaluationUrl(consultationId);
    const params =
      selectedUserIds.length > 0
        ? `?user_ids=${selectedUserIds.join(",")}`
        : "";
    const response = await fetch(`${baseUrl}${params}`);
    if (response.ok) {
      data = await response.json();
    }
    isLoading = false;
  }

  const formatPercent = (numerator: number, denominator: number): string => {
    if (denominator === 0) return "0%";
    return `${Math.round((numerator / denominator) * 100)}%`;
  };

  const formatCount = (count: number, total: number): string => {
    return `${count} (${formatPercent(count, total)})`;
  };

  const formatF1 = (f1: F1Stats | null): string => {
    if (!f1) return "—";
    const prefix = f1.approximate ? "~" : "";
    const ci =
      f1.ci_lower !== null && f1.ci_upper !== null
        ? ` (${f1.ci_lower}–${f1.ci_upper})`
        : "";
    return `${prefix}${f1.mean}${ci}`;
  };

  let bannerTitle = $derived.by(() => {
    const { status, f1 } = data.summary;
    switch (status) {
      case "insufficient_data":
        return "More responses need to be read";
      case "below_benchmark":
        return `Consult's theme assignment is below human-level alignment (F1 = ${f1!.mean})`;
      case "meets_benchmark":
        return `Consult's theme assignment is at or above human-level alignment (F1 = ${f1!.mean})`;
    }
  });

  let bannerDetail = $derived.by(() => {
    const { status, responses_read } = data.summary;
    const { config } = data;
    switch (status) {
      case "insufficient_data":
        if (responses_read < config.min_sample_size) {
          return `Only ${responses_read} responses have been read so far. At least ${config.min_sample_size} are needed for reliable scores.`;
        }
        return `While ${responses_read} responses have been read, not enough had non-generic themes to compare. At least ${config.min_sample_size} are needed for reliable scores.`;
      case "below_benchmark":
        return `Our meta-analysis found that when two humans independently assign themes to the same responses, they agree at an F1 of ${config.benchmark_f1}. This consultation is below that benchmark. Review the per-question breakdown below to identify which questions need more attention.`;
      case "meets_benchmark":
        return `Our meta-analysis found that when two humans independently assign themes to the same responses, they agree at an F1 of ${config.benchmark_f1}. This consultation meets or exceeds that benchmark.`;
    }
  });

  let questionsNeedingMoreReads = $derived(
    data.questions.filter((q) => q.status === "insufficient_data").length,
  );
  let questionsBelowBenchmark = $derived(
    data.questions.filter((q) => q.status === "below_benchmark").length,
  );
  let questionsAboveBenchmark = $derived(
    data.questions.filter((q) => q.status === "meets_benchmark").length,
  );

  function getQuestionWarning(q: QuestionEval): string | null {
    switch (q.status) {
      case "insufficient_data":
        if (q.responses_read < data.config.min_sample_size) {
          return `Only ${q.responses_read} responses read — at least ${data.config.min_sample_size} needed for reliable scores.`;
        }
        return `More responses need to be read — not enough had non-generic themes to compare (at least ${data.config.min_sample_size} needed).`;
      case "below_benchmark":
        return `F1 score is below human-level benchmark (${data.config.benchmark_f1}).`;
      default:
        return null;
    }
  }
</script>

<div class={isLoading ? "opacity-60 transition-opacity" : ""}>
  {#if availableUsers.length > 0}
    <div class="mb-6 flex items-start justify-end">
      <div class="w-64">
        <SearchableSelect
          label="Filter by user"
          placeholder="Select users..."
          options={availableUsers.map((user) => ({
            value: user.id,
            label: user.email,
            disabled: false,
          }))}
          selectedValues={selectedUserIds}
          handleChange={(option: SearchableSelectOption<string>) => {
            if (selectedUserIds.includes(option.value)) {
              selectedUserIds = selectedUserIds.filter(
                (id) => id !== option.value,
              );
            } else {
              selectedUserIds = [...selectedUserIds, option.value];
            }
            fetchEvaluation();
          }}
        />
        {#if selectedUserIds.length > 0}
          <div class="mt-2 flex flex-wrap gap-1">
            {#each selectedUserIds as userId (userId)}
              {@const user = availableUsers.find((u) => u.id === userId)}
              {#if user}
                <span
                  class="inline-flex items-center gap-1 rounded-full border border-neutral-200 bg-neutral-50 px-2 py-0.5 text-xs text-neutral-700"
                >
                  {user.email}
                  <button
                    class="text-neutral-400 hover:text-neutral-600"
                    onclick={() => {
                      selectedUserIds = selectedUserIds.filter(
                        (id) => id !== userId,
                      );
                      fetchEvaluation();
                    }}
                  >
                    &times;
                  </button>
                </span>
              {/if}
            {/each}
            <button
              class="text-xs text-neutral-400 underline hover:text-neutral-600"
              onclick={() => {
                selectedUserIds = [];
                fetchEvaluation();
              }}
            >
              Clear all
            </button>
          </div>
          <p class="mt-2 text-xs text-neutral-500">
            Showing only responses read by {selectedUserIds.length === 1
              ? "this user"
              : "these users"}. F1 compares original AI assignments against
            current themes, which may include edits by other users.
          </p>
        {/if}
      </div>
    </div>
  {/if}

  <div
    class="my-6 rounded-lg border-l-4 p-5 {data.summary.status ===
    'insufficient_data'
      ? 'border-amber-500 bg-amber-50'
      : data.summary.status === 'below_benchmark'
        ? 'border-red-600 bg-red-50'
        : 'border-green-600 bg-green-50'}"
  >
    <p
      class="text-lg font-bold {data.summary.status === 'insufficient_data'
        ? 'text-amber-900'
        : data.summary.status === 'below_benchmark'
          ? 'text-red-900'
          : 'text-green-900'}"
    >
      {bannerTitle}
    </p>
    <ul
      class="mt-3 list-disc space-y-1 pl-5 text-sm {data.summary.status ===
      'insufficient_data'
        ? 'text-amber-800'
        : data.summary.status === 'below_benchmark'
          ? 'text-red-800'
          : 'text-green-800'}"
    >
      <li>
        Theme assignment is the step where Consult classifies each response
        against the finalised themes. Accurate assignments are essential for
        understanding theme prevalence, comparing themes across groups, and
        finding relevant responses to read when exploring a particular theme.
      </li>
      <li>
        Performance is measured by how often human reviewers agreed with
        Consult's theme assignments. When a reviewer reads a response, they can
        edit the assigned themes if they disagree. The fewer edits, the higher
        the alignment score.
      </li>
      <li>{bannerDetail}</li>
    </ul>
  </div>

  <h2 class="mb-4 mt-8 text-xl font-semibold">Summary</h2>

  <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
    <div class="rounded-lg border p-4">
      <div class="text-2xl font-bold">{data.summary.responses_read}</div>
      <div class="text-sm text-neutral-500">
        of {data.summary.responses} responses read ({formatPercent(
          data.summary.responses_read,
          data.summary.responses,
        )})
      </div>
    </div>
    <div class="rounded-lg border p-4">
      <div class="text-2xl font-bold">{data.summary.responses_edited}</div>
      <div class="text-sm text-neutral-500">
        of {data.summary.responses_read} read were edited ({formatPercent(
          data.summary.responses_edited,
          data.summary.responses_read,
        )})
      </div>
    </div>
    <div class="rounded-lg border p-4">
      <div class="text-2xl font-bold">{formatF1(data.summary.f1)}</div>
      <div class="text-sm text-neutral-500">F1 score</div>
    </div>
    <div class="rounded-lg border p-4">
      <div class="text-2xl font-bold">
        {formatF1(data.summary.f1_all_themes)}
      </div>
      <div class="text-sm text-neutral-500">F1 score (all themes)</div>
    </div>
  </div>

  <h2 class="mt-10 text-xl font-semibold">Per Question</h2>

  <div class="mt-3 flex flex-wrap items-center gap-4 text-sm">
    {#if questionsAboveBenchmark > 0}
      <span class="rounded-full bg-green-100 px-3 py-1 text-green-800">
        {questionsAboveBenchmark} questions performing well
      </span>
    {/if}
    {#if questionsBelowBenchmark > 0}
      <span class="rounded-full bg-red-100 px-3 py-1 text-red-800">
        {questionsBelowBenchmark} questions need attention (F1 &lt; {data.config
          .benchmark_f1})
      </span>
    {/if}
    {#if questionsNeedingMoreReads > 0}
      <span class="rounded-full bg-neutral-100 px-3 py-1 text-neutral-600">
        {questionsNeedingMoreReads} questions need more responses read
      </span>
    {/if}
    <a
      href="#methodology"
      class="ml-auto text-base text-primary hover:underline"
    >
      How are these scores calculated? &darr;
    </a>
  </div>

  <div class="mt-4 overflow-x-auto">
    <table class="w-full text-left">
      <thead class="border-b font-medium">
        <tr>
          <th class="py-2 pl-2 pr-4">Q</th>
          <th class="py-2 pr-4">Question</th>
          <th class="py-2 pr-4">Responses</th>
          <th class="py-2 pr-4">Read</th>
          <th class="py-2 pr-4">Edited</th>
          <th class="py-2 pr-4">F1</th>
          <th class="py-2 pr-4">F1 (all themes)</th>
        </tr>
      </thead>
      <tbody>
        {#each data.questions as question (question.id)}
          {@const warning = getQuestionWarning(question)}
          <tr
            class="border-b {question.status === 'below_benchmark'
              ? 'border-l-4 border-l-red-500'
              : ''}"
          >
            <td class="py-2 pl-2 pr-4">{question.number}</td>
            <td class="max-w-md py-2 pr-4">
              <a
                href="{questionDetailBaseUrl}/{question.id}"
                class="text-primary hover:underline"
              >
                {question.text}
              </a>
              {#if warning}
                <p class="mt-1 text-sm italic text-neutral-500">{warning}</p>
              {/if}
            </td>
            <td class="py-2 pr-4">{question.responses}</td>
            <td class="py-2 pr-4"
              >{formatCount(question.responses_read, question.responses)}</td
            >
            <td class="py-2 pr-4"
              >{formatCount(
                question.responses_edited,
                question.responses_read,
              )}</td
            >
            <td class="py-2 pr-4">{formatF1(question.f1)}</td>
            <td class="py-2 pr-4">{formatF1(question.f1_all_themes)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</div>
