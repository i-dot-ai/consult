<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import { getApiUserDetails, Routes } from "../../global/routes";

  import Button from "../inputs/Button/Button.svelte";
  import Text from "../Text/Text.svelte";
  import type { User } from "../../global/types";

  let sending: boolean = $state(false);
  let errors: Record<string, string> = $state({});

  interface Props {
    user: User;
  }

  let { user }: Props = $props();

  const handleSubmit = async () => {
    errors = {};
    sending = true;
    try {
      const response = await fetch(getApiUserDetails(user.id.toString()), {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      window.location.href = Routes.SupportUsers;
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
    >Are you sure you want to delete this user:
    <strong>{user.email}</strong>?</Text
  >
  <Button
    type="submit"
    variant="primary"
    handleClick={handleSubmit}
    disabled={sending}
  >
    {sending ? "Deleting..." : "Yes, delete user"}
  </Button>
</form>
