<script lang="ts">
  import { slide } from "svelte/transition";
  import { Routes } from "../../global/routes";
  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Button from "../inputs/Button/Button.svelte";
  import Select from "../inputs/Select/Select.svelte";
  import Link from "../Link.svelte";

  import type { ConsultationFolder } from "../../global/types";

  interface Props {
    consultationFolders: ConsultationFolder[];
  }

  let { consultationFolders }: Props = $props();

  const selectItems = $derived(
    consultationFolders.map(({ code }) => ({
      value: code,
      label: code,
    })),
  );

  let consultationName = $state<string | undefined>(undefined);
  let consultationCode = $state<string | undefined>(undefined);
  let submitting = $state<boolean>(false);
  let errorMessage = $state<string | undefined>(undefined);
  let success = $state<boolean>(false);

  const handleSubmit = async () => {
    errorMessage = "";
    success = false;
    submitting = true;

    try {
      const response = await fetch(Routes.ApiConsultationSetup, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          consultation_name: consultationName,
          consultation_code: consultationCode,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || `Error: ${response.status}`);
      }

      success = true;
    } catch (err) {
      errorMessage = err instanceof Error ? err.message : "An error occurred";
    } finally {
      submitting = false;
    }
  };
</script>

<form
  class="flex max-w-[500px] flex-col gap-4"
  onsubmit={(e) => {
    e.preventDefault();
    handleSubmit();
  }}
>
  {#if errorMessage}
    <div
      class="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800"
      transition:slide={{ duration: 200 }}
      role="alert"
    >
      {errorMessage}
    </div>
  {/if}

  {#if success}
    <div
      class="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-800"
      transition:slide={{ duration: 200 }}
      role="status"
    >
      {consultationName} is being set up. Monitor progress in the <Link
        href={Routes.SupportQueue}>Django RQ dashboard</Link
      >.
    </div>
  {/if}

  <TextInput
    id="consultation_name"
    name="consultation_name"
    label="Consultation name"
    required
    value={consultationName}
    setValue={(val) => (consultationName = val)}
  />

  <Select
    id="consultation_code"
    name="consultation_code"
    label="S3 folder (consultation code)"
    items={selectItems}
    required
    value={consultationCode}
    onchange={(val) => (consultationCode = val)}
  />

  <Button type="submit" variant="primary" disabled={submitting}>
    Create Consultation
  </Button>
</form>
