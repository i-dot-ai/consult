<script lang="ts">
  import { slide } from "svelte/transition";

  import Button from "../../inputs/Button/Button.svelte";
  import Select from "../../inputs/Select/Select.svelte";
  import Link from "../../Link.svelte";

  import { Routes } from "../../../global/routes";
  import { buildFindingThemesQuery } from "../../../global/queries/consultations/queries";
  import type { ConsultationFolder } from "../../../global/types";

  interface Props {
    consultations: ConsultationFolder[];
  }

  let { consultations }: Props = $props();

  const selectItems = $derived.by(() => {
    if (consultations.length === 0) {
      return [{ label: "No consultations found", value: "" }];
    }
    return consultations.map(({ id, title, code }) => ({
      value: id,
      label: `${title} (${code})`,
    }));
  });

  let consultationId = $derived<string | undefined>(consultations[0]?.id);
  let errorMessage = $state<string | undefined>(undefined);

  const findThemes = $derived(buildFindingThemesQuery(consultationId || ""));

  const handleSubmit = async () => {
    if (!consultationId) {
      return;
    }

    errorMessage = "";
    try {
      await findThemes.fetch({});
    } catch {
      errorMessage = "Fetch failed";
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
  {#if findThemes.query.isError}
    <div
      class="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800"
      transition:slide={{ duration: 200 }}
      role="alert"
    >
      {findThemes.query.error?.message ||
        errorMessage ||
        `An error occurred: ${findThemes.query.status}`}
    </div>
  {/if}

  {#if findThemes.query.isSuccess}
    <div
      class="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-800"
      transition:slide={{ duration: 200 }}
      role="status"
    >
      Finding themes... Monitor progress in the
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
    disabled={consultations.length === 0}
    value={consultationId}
    onchange={(val) => (consultationId = val)}
  />

  <Button
    type="submit"
    variant="primary"
    disabled={findThemes.query.isPending || consultations.length === 0}
  >
    Find Themes
  </Button>
</form>
