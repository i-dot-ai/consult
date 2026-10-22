<script lang="ts">
  import Check from "../../../svg/material/Check.svelte";
  import Checklist from "../../../svg/material/Checklist.svelte";
  import Button from "../../../inputs/Button/Button.svelte";
  import Checkbox from "../../../inputs/Checkbox/Checkbox.svelte";
  import MaterialIcon from "../../../MaterialIcon.svelte";
  import StepTitle from "../../../surveyImport/StepTitle/StepTitle.svelte";
  import Title from "../../../Title.svelte";

  import type { DataSource } from "../../../../global/queries/consultations/types";
  import { PROVIDER_CHECKS, USER_CHECKS, TECHNICAL_CHECKS } from "./checks";
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

  const userChecks = $derived([...PROVIDER_CHECKS[dataSource], ...USER_CHECKS]);

  let checked = $state<Record<string, boolean>>({});

  function setChecked(id: string, value: boolean) {
    checked[id] = value;
  }

  function tickAll() {
    for (const check of userChecks) {
      checked[check.id] = true;
    }
  }
</script>

{#snippet checkItem(check: CheckItem)}
  <div class="py-3">
    <Checkbox
      id={check.id}
      checked={checked[check.id] ?? false}
      label={check.label}
      onchange={(value) => setChecked(check.id, value)}
    />
    {#if check.hint}
      <p class="mt-1 pl-8 text-sm leading-relaxed text-neutral-500">
        {check.hint}
      </p>
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

<StepTitle stepNo={2} maxStepNo={6} title="Prepare your file" Icon={Checklist} />

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
      {#each userChecks as check (check.id)}
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
