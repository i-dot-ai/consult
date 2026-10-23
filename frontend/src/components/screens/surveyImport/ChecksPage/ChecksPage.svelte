<script lang="ts">
  import { slide } from "svelte/transition";
  import type { Snippet } from "svelte";

  import Check from "../../../svg/material/Check.svelte";
  import Checklist from "../../../svg/material/Checklist.svelte";
  import Button from "../../../inputs/Button/Button.svelte";
  import Checkbox from "../../../inputs/Checkbox/Checkbox.svelte";
  import MaterialIcon from "../../../MaterialIcon.svelte";
  import StepTitle from "../../../surveyImport/StepTitle/StepTitle.svelte";
  import Title from "../../../Title.svelte";

  import type { DataSource } from "../../../../global/queries/consultations/types";
  import {
    PROVIDER_CHECK_IDS,
    PROVIDER_CHECK_LABELS,
    ROW_STRUCTURE_LABEL,
    STRUCTURE_CHECK_IDS,
    STRUCTURE_CHECK_LABELS,
    CONTENT_CHECK_IDS,
    CONTENT_CHECK_LABELS,
    TECHNICAL_CHECKS,
  } from "./checks";
  import type { Check as CheckItem } from "./checks";
  import {
    getDataUploadSelectProviderUrl,
    getConsultationViewUrl,
  } from "../../../../global/routes";

  interface Props {
    consultationId: string;
    dataSource: DataSource;
  }

  let { consultationId, dataSource }: Props = $props();

  const providerCheckId = $derived(
    dataSource === "citizen-space"
      ? PROVIDER_CHECK_IDS.citizenSpaceRowStructure
      : PROVIDER_CHECK_IDS.qualtricsRowStructure,
  );

  const structureChecks = $derived<CheckItem[]>([
    { id: providerCheckId, label: PROVIDER_CHECK_LABELS[dataSource], example: providerExample },
    { id: STRUCTURE_CHECK_IDS.rowStructure, label: ROW_STRUCTURE_LABEL[dataSource], example: rowStructureExample },
    { id: STRUCTURE_CHECK_IDS.noMergedCells, label: STRUCTURE_CHECK_LABELS.noMergedCells, example: noMergedCellsExample },
  ]);

  const contentChecks: CheckItem[] = [
    { id: CONTENT_CHECK_IDS.responsesMerged, label: CONTENT_CHECK_LABELS.responsesMerged, example: responsesMergedExample },
    { id: CONTENT_CHECK_IDS.demographicColumns, label: CONTENT_CHECK_LABELS.demographicColumns, example: demographicColumnsExample },
    { id: CONTENT_CHECK_IDS.piiRemoved, label: CONTENT_CHECK_LABELS.piiRemoved, example: piiRemovedExample },
  ];

  const allUserChecks = $derived([...structureChecks, ...contentChecks]);

  const storageKey = `checks-progress-${consultationId}`;

  function loadFromStorage(): Record<string, boolean> {
    try {
      const stored = localStorage.getItem(storageKey);
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  }

  function saveToStorage(value: Record<string, boolean>) {
    try {
      localStorage.setItem(storageKey, JSON.stringify(value));
    } catch {
      // storage unavailable — continue silently
    }
  }

  let checked = $state<Record<string, boolean>>(loadFromStorage());
  let exampleOpen = $state<Record<string, boolean>>({});

  function setChecked(id: string, value: boolean) {
    checked[id] = value;
    saveToStorage(checked);
  }

  function toggleExample(id: string) {
    exampleOpen[id] = !exampleOpen[id];
  }

  function tickAll() {
    for (const check of allUserChecks) {
      checked[check.id] = true;
    }
    saveToStorage(checked);
  }
</script>

{#snippet callout(children: Snippet)}
  <div
    transition:slide
    class="mt-3 rounded-lg border border-neutral-300 bg-neutral-100 px-4 py-3.5 text-sm leading-relaxed text-neutral-700"
  >
    {@render children()}
  </div>
{/snippet}

<!-- Provider-specific example -->
{#snippet providerExample()}
  <p class="mb-3">
    Leave these rows as your tool exported them. Consult knows where each
    tool's questions end.
  </p>
  <table class="text-sm">
    <thead>
      <tr class="border-b border-neutral-300">
        <th class="pb-1 pr-8 text-left font-normal text-neutral-500">Exported from</th>
        <th class="pb-1 pr-8 text-left font-normal text-neutral-500">Questions</th>
        <th class="pb-1 text-left font-normal text-neutral-500">Responses start</th>
      </tr>
    </thead>
    <tbody>
      <tr class="border-b border-neutral-200">
        <td class="py-1.5 pr-8">Qualtrics</td>
        <td class="py-1.5 pr-8">Rows 1 to 3</td>
        <td class="py-1.5">Row 4</td>
      </tr>
      <tr class="border-b border-neutral-200">
        <td class="py-1.5 pr-8">Citizen Space</td>
        <td class="py-1.5 pr-8">Row 1</td>
        <td class="py-1.5">Row 2</td>
      </tr>
      <tr>
        <td class="py-1.5 pr-8">Any other tool</td>
        <td class="py-1.5 pr-8">Row 1</td>
        <td class="py-1.5">Row 2</td>
      </tr>
    </tbody>
  </table>
{/snippet}

{#snippet rowStructureExample()}
  <p>
    One row holds everything one person said. One person never spreads across
    two rows, and two people never share one. Each question keeps its own
    column all the way down.
  </p>
{/snippet}

{#snippet noMergedCellsExample()}
  <p>
    Merged cells are common in headers where one question covers several
    columns. Unmerge them and repeat the wording in each column instead. If
    the upload finds any, it stops and says where they are.
  </p>
{/snippet}

{#snippet responsesMergedExample()}
  <p class="mb-3">
    If some responses arrived by email or on paper, add them as extra rows
    here rather than uploading a second file. The preparation checklist on
    this page has a tab with the right structure to reshape them into.
  </p>
  <pre class="text-xs leading-relaxed">Put the same question in the same column in every batch
Use the same question wording in every batch
Leave a cell empty where someone skipped a question</pre>
{/snippet}

{#snippet demographicColumnsExample()}
  <p>
    Sector, region, organisation size and similar are not personal
    information. They become the filters on your dashboard, so keep them even
    while you are removing names and contact details.
  </p>
{/snippet}

{#snippet piiRemovedExample()}
  <p class="mb-3">
    What to remove, and how far to go, is your department's decision, because
    it is the data controller. Free-text answers are worth checking as well as
    the columns, because people often name themselves mid-response.
  </p>
  <pre class="text-xs leading-relaxed">Full names → replace with Respondent 1, Respondent 2
Email addresses → delete the column
Postcodes → keep the first part only, SW1 rather than SW1A 2AA
Phone numbers → delete
Addresses → delete, or keep the area name only</pre>
{/snippet}

{#snippet checkItem(check: CheckItem)}
  <div class="py-3">
    <div class="flex items-start justify-between gap-4">
      <Checkbox
        id={check.id}
        checked={checked[check.id] ?? false}
        label={check.label}
        onchange={(value) => setChecked(check.id, value)}
      />
      {#if check.example}
        <button
          type="button"
          class="shrink-0 text-sm text-primary hover:underline"
          onclick={() => toggleExample(check.id)}
        >
          {exampleOpen[check.id] ? "Hide example" : "Show example"}
        </button>
      {/if}
    </div>
    {#if check.example && exampleOpen[check.id]}
      {@render callout(check.example)}
    {/if}
  </div>
{/snippet}

{#snippet tickItem(label: string)}
  <div class="flex items-start gap-3 py-3">
    <div class="mt-0.5 shrink-0">
      <MaterialIcon color="fill-secondary" size="1.1rem">
        <Check />
      </MaterialIcon>
    </div>
    <span class="text-base leading-relaxed text-neutral-900">{label}</span>
  </div>
{/snippet}

<StepTitle stepNo={2} maxStepNo={6} title="Prepare your file" Icon={Checklist} isExternal={true} />

<p class="mt-3.5 mb-6 text-base leading-relaxed text-neutral-500">
  Work through your file against this list before uploading. Reading the
  responses now is time well spent, because you'll start the analysis knowing
  what's in your data.
</p>

<div class="flex flex-col gap-5">
  <div class="rounded-xl border border-neutral-300 bg-white p-7">
    <Title level={2}>
      <span class="text-base font-medium text-neutral-900">Structure</span>
    </Title>
    <div class="mt-4 flex flex-col divide-y divide-neutral-200">
      {#each structureChecks as check (check.id)}
        {@render checkItem(check)}
      {/each}
    </div>
  </div>

  <div class="rounded-xl border border-neutral-300 bg-white p-7">
    <Title level={2}>
      <span class="text-base font-medium text-neutral-900">Content</span>
    </Title>
    <div class="mt-4 flex flex-col divide-y divide-neutral-200">
      {#each contentChecks as check (check.id)}
        {@render checkItem(check)}
      {/each}
    </div>
  </div>

  <div class="rounded-xl border border-neutral-300 bg-white p-7">
    <Title level={2}>
      <span class="text-base font-medium text-neutral-900"
        >Consult checks these when you upload</span
      >
    </Title>
    <p class="mt-1 text-sm leading-relaxed text-neutral-500">
      No need to check these yourself.
    </p>
    <div class="mt-4 flex flex-col divide-y divide-neutral-200">
      {#each TECHNICAL_CHECKS as check (check.id)}
        {@render tickItem(check.label)}
      {/each}
    </div>
  </div>
</div>

<div
  class="mt-5 rounded-xl border border-neutral-300 bg-neutral-100 px-4 py-3.5 text-sm leading-relaxed text-neutral-500"
>
  Ticking is for your own tracking. Nothing is submitted, and you can continue
  without it.
</div>

<div class="mt-5 flex flex-wrap justify-between gap-2">
  <Button size="sm" href={getDataUploadSelectProviderUrl(consultationId)}>
    Back
  </Button>
  <div class="flex items-center gap-2">
    <Button size="sm" handleClick={tickAll}>Tick everything</Button>
    <Button
      size="sm"
      variant="primary"
      href={getConsultationViewUrl(consultationId)}
    >
      Continue to upload
    </Button>
  </div>
</div>
