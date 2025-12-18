<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import { getApiConsultationUrl, Routes } from "../../global/routes";

  import Button from "../inputs/Button/Button.svelte";
  import Text from "../Text/Text.svelte";
  import type { ConsultationResponse } from "../../global/types";

  let sending: boolean = false;
  let errors: Record<string, string> = {};

  export let consultation: ConsultationResponse;

  const handleSubmit = async () => {
    errors = {};
    sending = true;
    try {
      const response = await fetch(getApiConsultationUrl(consultation.id), {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      window.location.href = Routes.SupportConsultations;
    } catch (err: unknown) {
      errors["general"] =
        err instanceof Error ? err.message : "An unknown error occurred";
    } finally {
      sending = false;
    }
  };
</script>

<form class={clsx(["flex", "flex-col", "gap-4"])}>
  {#if "general" in errors}
    <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
      {errors.general}
    </small>
  {/if}
  <Text
    >Are you sure you want to delete this consultation:
    <strong>{consultation.title}</strong>?</Text
  >
  <Button
    type="submit"
    variant="primary"
    handleClick={handleSubmit}
    disabled={sending}
  >
    {sending ? "Deleting..." : "Yes, delete it"}
  </Button>
</form>
