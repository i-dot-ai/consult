<script lang="ts">
  import Title from "../../Title.svelte";
  import Alert from "../../Alert/Alert.svelte";
  import ErrorIcon from "../../svg/material/Error.svelte";
  import Download from "../../svg/material/Download.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import RadioCards from "../../inputs/RadioCards/RadioCards.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import StepsTitle from "../StepsTitle/StepsTitle.svelte";

  import { getDataUploadUrl } from "../../../global/routes.ts";
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

  const PROVIDERS: { value: DataSource; text: string; hint: string }[] = [
    { value: "qualtrics", text: "Qualtrics", hint: "Survey platform" },
    {
      value: "citizen-space",
      text: "Citizen Space",
      hint: "Consultation platform",
    },
  ];

  // svelte-ignore state_referenced_locally
  let selected: DataSource = $state(dataSource ?? "qualtrics");
  let submitting = $state(false);
  let submitError = $state("");

  // svelte-ignore state_referenced_locally
  const consultationUpdate = buildConsultationV2UpdateQuery(
    consultationId,
    async () => {
      window.location.href = getDataUploadUrl(consultationId);
    },
    async (error) => {
      submitError = error.message;
      submitting = false;
    },
  );

  async function handleContinue() {
    submitting = true;
    submitError = "";

    const body: ConsultationV2UpdateBody = { data_source: selected };

    try {
      await consultationUpdate.fetch({ body });
    } catch (error) {
      console.error(error);
    }
  }
</script>

{#if submitError}
  <div class="mb-6">
    <Alert variant="error" Icon={ErrorIcon}>
      <p class="font-bold">There is a problem</p>
      <p>{submitError}</p>
    </Alert>
  </div>
{/if}

<StepsTitle
  text="Export the responses"
  currentStep={1}
  totalSteps={5}
  Icon={Download}
  tag="Happens outside Consult"
/>

<p class="mt-6 text-neutral-500">
  Consult supports responses exported from Qualtrics and Citizen Space. Choose
  which one you used for the export instructions.
</p>

<Panel>
  <RadioCards
    name="data-source"
    legend="Which tool did you use?"
    hint="Pick the one the responses were collected in."
    items={PROVIDERS}
    value={selected}
    onchange={(value) => (selected = value)}
  />

  <div class="mt-6 text-sm">
    {#if selected === "qualtrics"}
      <Title level={3}>
        <span class="text-base font-medium">Exporting from Qualtrics</span>
      </Title>
      <p class="mt-1 text-neutral-500">
        Five steps in Qualtrics, then come back here.
      </p>
      <ol class="mt-4 ml-5 flex list-decimal flex-col gap-2">
        <li>Open <strong>Data &amp; Analysis</strong>.</li>
        <li>
          Choose <strong>Export &amp; Import</strong>, then
          <strong>Export Data</strong>.
        </li>
        <li>Select <strong>CSV</strong> as the format.</li>
        <li>
          Set these three export options:
          <ul class="mt-1 ml-5 flex list-disc flex-col gap-1 text-neutral-600">
            <li>
              Use choice text, so answers export as words rather than numbers
            </li>
            <li>Include all response fields</li>
            <li>
              Keep original question text, so full wording appears in the column
              headers
            </li>
          </ul>
        </li>
        <li>Select <strong>Download</strong>.</li>
      </ol>
      <Panel bg={true} border={false} level={2}>
        <p>
          Qualtrics puts the question details in rows 1 to 3. Leave them as they
          are. Consult knows where the questions end.
        </p>
      </Panel>
    {:else}
      <Title level={3}>
        <span class="text-base font-medium">Exporting from Citizen Space</span>
      </Title>
      <ol class="mt-4 ml-5 flex list-decimal flex-col gap-2">
        <li>Open your consultation and choose <strong>Responses</strong>.</li>
        <li>Select <strong>Download all responses</strong>.</li>
        <li>Choose <strong>Full responses (CSV)</strong>, not the summary.</li>
        <li>Select <strong>Download</strong>.</li>
      </ol>
      <p class="mt-4 text-neutral-500">
        Citizen Space exports one row per response with the question wording
        already in row 1.
      </p>
    {/if}
  </div>
</Panel>

<Panel>
  <Title level={3}>
    <span class="text-base font-medium">Responses that came in by email</span>
  </Title>
  <p class="mt-1 text-sm text-neutral-500">
    Consult reads one file, so email responses have to go into the same
    spreadsheet as the rest. Add each one as a new row in your Qualtrics or
    Citizen Space export, putting each answer in the column for the question it
    answers.
  </p>
  <Panel bg={true} border={false} level={2}>
    <p class="text-sm">
      Leave a cell empty where the person did not answer a question. If someone
      wrote something that does not answer any of your questions, there is
      nowhere for it in this version, so keep it with your own records.
    </p>
  </Panel>
</Panel>

<p class="text-sm text-neutral-500">
  Collected responses another way? There are no export instructions for other
  tools, but Consult reads any <strong>.xlsx</strong> or <strong>.csv</strong>
  laid out the way step 2 describes.
</p>

<div class="mt-8 flex flex-wrap justify-between gap-2">
  <Button href={getDataUploadUrl(consultationId)}>Back to overview</Button>
  <Button variant="primary" disabled={submitting} handleClick={handleContinue}>
    Continue to preparing your data
  </Button>
</div>
