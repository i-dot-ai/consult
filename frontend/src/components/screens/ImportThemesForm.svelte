<script lang="ts">
  import clsx from "clsx";
  import { slide } from "svelte/transition";

  import { getApiImportFinalisedThemesUrl } from "../../global/routes";
  import Button from "../inputs/Button/Button.svelte";
  import Text from "../Text/Text.svelte";

  interface QuestionPreview {
    question_number: number;
    question_text: string;
    status: string;
    source_themes?: string[];
  }

  interface ImportPreviewResponse {
    dry_run: boolean;
    source_consultation: { id: string; title: string };
    target_consultation: { id: string; title: string };
    total_themes_imported?: number;
    questions: QuestionPreview[];
    warnings: {
      unmatched_source_questions: string[];
    };
    performed_by?: string;
  }

  export let targetConsultationId: string;
  export let targetConsultationTitle: string;

  let sourceConsultationId = "";
  let loading = false;
  let errors: Record<string, string> = {};
  let preview: ImportPreviewResponse | null = null;
  let result: ImportPreviewResponse | null = null;

  const statusLabels: Record<string, string> = {
    will_import: "Will import",
    duplicate_in_target: "Warning — Multiple matching questions",
    duplicate_in_source: "Warning — Duplicate question",
    no_match_in_source: "Warning — No matching question",
    no_themes_in_source: "Warning — Matching question has no themes",
    has_existing_themes: "Warning — Selected themes already exist",
  };

  const parseResponse = async (response: Response) => {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return await response.json();
    }
    return null;
  };

  const handlePreview = async () => {
    errors = {};
    preview = null;
    result = null;
    loading = true;

    try {
      const response = await fetch(
        getApiImportFinalisedThemesUrl(targetConsultationId) + "?dry_run=true",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_consultation_id: sourceConsultationId,
          }),
        },
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        errors["general"] =
          data?.error || `Error ${response.status}: ${response.statusText}`;
        return;
      }

      preview = data;
    } catch (err: unknown) {
      errors["general"] =
        err instanceof Error ? err.message : "An unknown error occurred";
    } finally {
      loading = false;
    }
  };

  const handleConfirm = async () => {
    errors = {};
    loading = true;

    try {
      const response = await fetch(
        getApiImportFinalisedThemesUrl(targetConsultationId),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_consultation_id: sourceConsultationId,
          }),
        },
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        errors["general"] =
          data?.error || `Error ${response.status}: ${response.statusText}`;
        return;
      }

      result = data;
      preview = null;
    } catch (err: unknown) {
      errors["general"] =
        err instanceof Error ? err.message : "An unknown error occurred";
    } finally {
      loading = false;
    }
  };

  $: themesToImport = preview
    ? preview.questions.filter((q) => q.status === "will_import")
    : [];
</script>

<form
  class={clsx(["flex", "flex-col", "gap-4"])}
  on:submit|preventDefault={handlePreview}
>
  <Text>
    Import finalised themes into <strong>{targetConsultationTitle}</strong> from
    another consultation.
  </Text>

  <label class="flex flex-col gap-1">
    <span class="text-sm font-medium">Source consultation ID</span>
    <input
      type="text"
      bind:value={sourceConsultationId}
      placeholder="e.g. 4d1414d5-9300-447b-b788-50d0bef7e807"
      class="rounded-sm border border-gray-300 px-3 py-2 text-sm"
      required
    />
  </label>

  {#if "general" in errors}
    <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
      {errors.general}
    </small>
  {/if}

  {#if !preview && !result}
    <Button
      type="submit"
      variant="primary"
      disabled={loading || !sourceConsultationId}
    >
      {loading ? "Loading..." : "Preview import"}
    </Button>
  {/if}
</form>

{#if preview}
  <div class="mt-6 flex flex-col gap-4">
    <Text>
      Importing from <strong>{preview.source_consultation.title}</strong>
    </Text>

    {#if themesToImport.length > 0}
      <div class="rounded-sm border border-green-200 bg-green-50 p-3">
        <p class="text-sm font-medium text-green-800">
          {themesToImport.reduce(
            (sum, q) => sum + (q.source_themes?.length || 0),
            0,
          )} finalised theme(s) will be imported across {themesToImport.length} question(s).
        </p>
      </div>
    {:else}
      <div class="rounded-sm border border-amber-200 bg-amber-50 p-3">
        <p class="text-sm font-medium text-amber-800">
          No finalised themes will be imported.
        </p>
      </div>
    {/if}

    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead class="font-bold">
          <tr>
            <th class="py-2 pr-2">Q#</th>
            <th class="py-2 pr-2">Question</th>
            <th class="py-2 pr-2">Status</th>
            <th class="py-2 pr-2">Themes</th>
          </tr>
        </thead>
        <tbody>
          {#each preview.questions as question (question.question_number)}
            <tr class="border-t hover:bg-gray-50">
              <td class="py-2 pr-2">{question.question_number}</td>
              <td class="max-w-xs wrap-break-word py-2 pr-2"
                >{question.question_text}</td
              >
              <td class="py-2 pr-2">
                <span
                  class={clsx([
                    "rounded-sm px-2 py-0.5 text-xs",
                    question.status === "will_import" &&
                      "bg-green-100 text-green-800",
                    question.status !== "will_import" &&
                      "bg-red-100 text-red-800",
                  ])}
                >
                  {statusLabels[question.status] || question.status}
                </span>
              </td>
              <td class="py-2 pr-2">
                {#if question.source_themes}
                  <ul class="m-0 list-none p-0">
                    {#each question.source_themes as theme, i (i)}
                      <li>{theme}</li>
                    {/each}
                  </ul>
                {:else}
                  —
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    {#if preview.warnings.unmatched_source_questions.length > 0}
      <div class="rounded-sm border border-amber-200 bg-amber-50 p-3">
        <p class="text-sm font-medium text-amber-800">
          {preview.warnings.unmatched_source_questions.length} source question(s)
          have no match in target:
        </p>
        <ul class="mt-1 list-inside list-disc text-sm text-amber-700">
          {#each preview.warnings.unmatched_source_questions as q, i (i)}
            <li>{q}</li>
          {/each}
        </ul>
      </div>
    {/if}

    {#if themesToImport.length > 0}
      <div class="flex gap-2">
        <Button
          variant="primary"
          handleClick={handleConfirm}
          disabled={loading}
        >
          {loading ? "Importing..." : "Confirm import"}
        </Button>
        <Button variant="default" handleClick={() => (preview = null)}>
          Cancel
        </Button>
      </div>
    {:else}
      <Button variant="default" handleClick={() => (preview = null)}>
        Back
      </Button>
    {/if}
  </div>
{/if}

{#if result}
  <div class="mt-6 flex flex-col gap-4">
    <div class="rounded-sm border border-green-200 bg-green-50 p-3">
      <p class="text-sm font-medium text-green-800">
        Successfully imported {result.total_themes_imported} finalised theme(s) from
        <strong>{result.source_consultation.title}</strong>.
      </p>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead class="font-bold">
          <tr>
            <th class="py-2 pr-2">Q#</th>
            <th class="py-2 pr-2">Question</th>
            <th class="py-2 pr-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {#each result.questions as question (question.question_number)}
            <tr class="border-t hover:bg-gray-50">
              <td class="py-2 pr-2">{question.question_number}</td>
              <td class="max-w-xs wrap-break-word py-2 pr-2"
                >{question.question_text}</td
              >
              <td class="py-2 pr-2">
                <span
                  class={clsx([
                    "rounded-sm px-2 py-0.5 text-xs",
                    question.status === "will_import" &&
                      "bg-green-100 text-green-800",
                    question.status !== "will_import" &&
                      "bg-red-100 text-red-800",
                  ])}
                >
                  {statusLabels[question.status] || question.status}
                </span>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
{/if}
