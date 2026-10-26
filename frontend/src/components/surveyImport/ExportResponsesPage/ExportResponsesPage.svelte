<script lang="ts">
  import type { Snippet } from "svelte";

  import Title from "../../Title.svelte";
  import Alert from "../../Alert/Alert.svelte";
  import Download from "../../svg/material/Download.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import RadioCards, {
    type RadioCardItem,
  } from "../../inputs/RadioCards/RadioCards.svelte";
  import StepTitle from "../StepTitle/StepTitle.svelte";

  import {
    getDataUploadUrl,
    getDataUploadChecksUrl,
    Routes,
  } from "../../../global/routes.ts";
  import { makeSnippet } from "../../../global/utils.ts";
  import { buildConsultationV2UpdateQuery } from "../../../global/queries/consultations/queries.ts";
  import type {
    ConsultationV2UpdateBody,
    DataSource,
  } from "../../../global/queries/consultations/types.ts";

  interface Props {
    consultationId: string;
    dataSource: DataSource | null;
  }

  let { consultationId, dataSource }: Props = $props();

  const PROVIDERS: RadioCardItem<DataSource>[] = [
    {
      value: "citizen-space",
      text: "Citizen Space",
      hint: "Consultation platform",
    },
    { value: "qualtrics", text: "Qualtrics", hint: "Survey platform" },
  ];

  const QUALTRICS_STEPS = [
    makeSnippet("Open <strong>Data &amp; Analysis</strong>."),
    makeSnippet(
      "Choose <strong>Export &amp; Import</strong>, then <strong>Export Data</strong>.",
    ),
    makeSnippet("Select <strong>CSV</strong> as the format."),
    qualtricsExportOptions,
    makeSnippet("Select <strong>Download</strong>."),
  ];

  const CITIZEN_SPACE_STEPS = [
    makeSnippet(
      "Open your consultation and choose <strong>Responses</strong>.",
    ),
    makeSnippet("Select <strong>Download all responses</strong>."),
    makeSnippet(
      "Choose <strong>Full responses (CSV)</strong>, not the summary.",
    ),
    makeSnippet("Select <strong>Download</strong>."),
  ];

  // svelte-ignore state_referenced_locally
  let selected: DataSource = $state(dataSource ?? "citizen-space");
  let submitting = $state(false);
  let saveFailed = $state(false);

  // svelte-ignore state_referenced_locally
  const consultationUpdate = buildConsultationV2UpdateQuery(
    consultationId,
    async () => {
      window.location.href = getDataUploadChecksUrl(consultationId);
    },
    async () => {
      saveFailed = true;
      submitting = false;
    },
  );

  async function handleContinue() {
    submitting = true;
    saveFailed = false;

    const body: ConsultationV2UpdateBody = { data_source: selected };

    try {
      await consultationUpdate.fetch({ body });
    } catch (error) {
      console.error(error);
      submitting = false;
    }
  }
</script>

<svelte:window
  onpageshow={(event) => {
    if (event.persisted) submitting = false;
  }}
/>

{#snippet qualtricsExportOptions()}
  <div>
    Set these three export options:
    <ul
      class="mt-1.5 ml-4 flex list-disc flex-col gap-1 text-sm text-neutral-500"
    >
      <li>Use choice text, so answers export as words rather than numbers</li>
      <li>Include all response fields</li>
      <li>
        Keep original question text, so full wording appears in the column
        headers
      </li>
    </ul>
  </div>
{/snippet}

{#snippet heading(text: string)}
  <Title level={2}>
    <span class="text-base font-medium text-neutral-900">{text}</span>
  </Title>
{/snippet}

{#snippet numbered(items: Snippet[])}
  <ol class="mt-4 flex list-none flex-col gap-3">
    {#each items as item, i (i)}
      <li
        class="flex items-start gap-3 text-base leading-relaxed text-neutral-900"
      >
        <span
          class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-neutral-500 text-xs text-neutral-500"
          aria-hidden="true"
        >
          {i + 1}
        </span>
        <div class="flex-1">
          {@render item()}
        </div>
      </li>
    {/each}
  </ol>
{/snippet}

{#snippet callout(text: string)}
  <div
    class="mt-4 rounded-lg border border-neutral-300 bg-neutral-100 px-4 py-3.5 text-sm leading-relaxed text-neutral-500"
  >
    {text}
  </div>
{/snippet}

{#if saveFailed}
  <div class="mb-6" role="alert">
    <Alert variant="error">
      <p class="font-bold">Your choice was not saved</p>
      <p>
        Consult could not save which tool you used. Your choice is still
        selected.
      </p>
      <p>
        Select Continue to try again. If it happens again,
        <a href={`mailto:${Routes.SupportEmail}`} class="underline"
          >contact support</a
        >.
      </p>
    </Alert>
  </div>
{/if}

<StepTitle
  stepNo={1}
  title="Export the responses"
  Icon={Download}
  isExternal={true}
/>

<p class="mt-3.5 mb-6 text-base leading-relaxed text-neutral-500">
  Consult supports responses exported from Qualtrics and Citizen Space. Choose
  which one you used for the export instructions.
</p>

<div class="rounded-xl border border-neutral-300 bg-white p-7">
  <div class="max-w-lg">
    <RadioCards
      name="data-source"
      legend="Which tool did you use?"
      hint="Pick the one the responses were collected in."
      items={PROVIDERS}
      value={selected}
      onchange={(value) => (selected = value)}
    />
  </div>

  <div class="mt-6">
    {#if selected === "qualtrics"}
      {@render heading("Exporting from Qualtrics")}
      <p class="mt-1 text-sm text-neutral-500">
        Five steps in Qualtrics, then come back here.
      </p>
      {@render numbered(QUALTRICS_STEPS)}
      {@render callout(
        "Qualtrics puts the question details in rows 1 to 3. Leave them as they are. Consult knows where the questions end.",
      )}
    {:else}
      {@render heading("Exporting from Citizen Space")}
      {@render numbered(CITIZEN_SPACE_STEPS)}
      <p class="mt-4 text-sm text-neutral-500">
        Citizen Space exports one row per response with the question wording
        already in row 1.
      </p>
    {/if}
  </div>
</div>

<div class="mt-5 rounded-xl border border-neutral-300 bg-white p-7">
  {@render heading("Responses that came in by email")}
  <p class="mt-1 text-sm leading-relaxed text-neutral-500">
    Consult reads one file, so email responses have to go into the same
    spreadsheet as the rest. Add each one as a new row in your Qualtrics or
    Citizen Space export, putting each answer in the column for the question it
    answers.
  </p>
  {@render callout(
    "Leave a cell empty where the person did not answer a question. If someone wrote something that does not answer any of your questions, there is nowhere for it in this version, so keep it with your own records.",
  )}
</div>

<small class="mt-3 block text-sm leading-relaxed text-neutral-500">
  Collected responses another way? There are no export instructions for other
  tools, but Consult reads any <strong>.xlsx</strong> or <strong>.csv</strong>
  laid out the way step 2 describes.
</small>

<div class="mt-7 flex flex-wrap justify-between gap-2">
  <Button size="sm" href={getDataUploadUrl(consultationId)}>
    Back to overview
  </Button>
  <Button
    size="sm"
    variant="primary"
    disabled={submitting}
    handleClick={handleContinue}
  >
    Continue to preparing your data
  </Button>
</div>
