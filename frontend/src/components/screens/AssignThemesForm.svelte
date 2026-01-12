<script lang="ts">
  import { slide } from "svelte/transition";
  import { getApiAssignThemesUrl, Routes } from "../../global/routes";
  import Button from "../inputs/Button/Button.svelte";
  import Select from "../inputs/Select/Select.svelte";
  import Link from "../Link.svelte";

  import type { ConsultationFolder } from "../../global/types";

  interface Props {
    consultationFolders: ConsultationFolder[];
  }

  let { consultationFolders }: Props = $props();

  // Only show folders that exist in the database (id exists)
  const selectItems = $derived(
    consultationFolders
      .filter(({ id }) => id)
      .map(({ id, title, code }) => ({
        value: id as string,
        label: `${title} (${code})`,
      })),
  );

  let consultationId = $state<string | undefined>(undefined);
  let submitting = $state<boolean>(false);
  let errorMessage = $state<string | undefined>(undefined);
  let success = $state<boolean>(false);

  const handleSubmit = async () => {
    errorMessage = "";
    success = false;
    submitting = true;

    try {
      const response = await fetch(
        getApiAssignThemesUrl(consultationId as string),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        },
      );

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
      Assigning themes... Monitor progress in the
      <Link href={Routes.ConsultAlertsSlackChannel}>#consult-alerts</Link>
      Slack channel.
    </div>
  {/if}

  <Select
    id="consultation_id"
    name="consultation_id"
    label="Consultation"
    items={selectItems}
    required
    value={consultationId}
    onchange={(val) => (consultationId = val)}
  />

  <Button type="submit" variant="primary" disabled={submitting}>
    Assign Themes
  </Button>
</form>
