<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import {
    getApiRemoveUserFromConsultation,
    getSupportConsultationDetails,
  } from "../../global/routes";

  import Button from "../inputs/Button/Button.svelte";
  import Text from "../Text/Text.svelte";
  import type { ConsultationResponse, User } from "../../global/types";

  let sending: boolean = false;
  let errors: Record<string, string> = {};

  export let consultation: ConsultationResponse;
  export let user: User;

  const handleSubmit = async () => {
    errors = {};
    sending = true;
    try {
      const response = await fetch(
        getApiRemoveUserFromConsultation(consultation.id, user.id.toString()),
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      window.location.href = getSupportConsultationDetails(consultation.id);
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
    >Are you sure you want to remove <strong>{user.email}</strong> from
    <strong>{consultation.title}</strong>?</Text
  >
  <Button
    type="submit"
    variant="primary"
    handleClick={handleSubmit}
    disabled={sending}
  >
    {sending ? "Removing..." : "Yes, remove them"}
  </Button>
</form>
