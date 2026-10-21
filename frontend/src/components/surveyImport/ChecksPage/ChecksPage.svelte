<script lang="ts">
  import Checklist from "../../svg/material/Checklist.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import Checkbox from "../../inputs/Checkbox/Checkbox.svelte";
  import StepTitle from "../StepTitle/StepTitle.svelte";

  import type { DataSource } from "../../../global/queries/consultations/types";
  import { PROVIDER_CHECKS, USER_CHECKS, TECHNICAL_CHECKS } from "./checks";
  import type { Check } from "./checks";
  import {
    getDataUploadSelectProviderUrl,
    getConsultationViewUrl,
  } from "../../../global/routes";

  interface Props {
    consultationId: string;
    dataSource: DataSource;
  }

  let { consultationId, dataSource }: Props = $props();

  // svelte-ignore state_referenced_locally
  const providerChecks = PROVIDER_CHECKS[dataSource];

  const allChecks = [
    ...providerChecks.checks,
    ...USER_CHECKS,
    ...TECHNICAL_CHECKS,
  ];

  let checked = $state<Record<string, boolean>>({});

  let allChecked = $derived(allChecks.every((c) => checked[c.id]));

  function toggle(id: string, value: boolean) {
    checked[id] = value;
  }
</script>

{#snippet checkItem(check: Check)}
  <div class="px-7 py-4">
    <Checkbox
      id={check.id}
      checked={checked[check.id] ?? false}
      label={check.label}
      onchange={(value) => toggle(check.id, value)}
    />
    {#if check.hint}
      <p class="mt-1 pl-8 text-sm leading-relaxed text-neutral-500">
        {check.hint}
      </p>
    {/if}
  </div>
{/snippet}

{#snippet section(title: string, checks: Check[], subtitle?: string)}
  <div class="rounded-xl border border-neutral-300 bg-white">
    <div class="border-b border-neutral-200 px-7 py-5">
      <h2 class="text-sm font-medium text-neutral-900">{title}</h2>
      {#if subtitle}
        <p class="mt-1 text-sm leading-relaxed text-neutral-500">{subtitle}</p>
      {/if}
    </div>
    <div class="divide-y divide-neutral-200">
      {#each checks as check (check.id)}
        {@render checkItem(check)}
      {/each}
    </div>
  </div>
{/snippet}

<StepTitle stepNo={3} maxStepNo={6} title="Check your data" Icon={Checklist} />

<p class="mt-3.5 mb-6 text-md leading-relaxed text-neutral-500">
  Before uploading, work through the checklist below. You can still upload
  without ticking every box, but skipping items may cause the upload to fail or
  produce inaccurate results.
</p>

<div class="flex flex-col gap-6">
  {@render section("User checks", [...providerChecks.checks, ...USER_CHECKS])}
  {@render section(
    "Technical checks",
    TECHNICAL_CHECKS,
    "Consult will check these automatically when you upload — if anything needs attention, we'll let you know.",
  )}
</div>

<div class="mt-7 flex justify-between">
  <Button size="sm" href={getDataUploadSelectProviderUrl(consultationId)}>
    Back
  </Button>
  <Button
    size="sm"
    variant="primary"
    disabled={!allChecked}
    href={allChecked ? getConsultationViewUrl(consultationId) : undefined}
  >
    Continue to upload
  </Button>
</div>
