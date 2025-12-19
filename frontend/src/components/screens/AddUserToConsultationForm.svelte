<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import {
    getApiAddUserToConsultation,
    getSupportConsultationDetails,
  } from "../../global/routes";

  import type { User } from "../../global/types";
  import Button from "../inputs/Button/Button.svelte";
  import Checkbox from "../inputs/Checkbox/Checkbox.svelte";

  let sending: boolean = false;
  let errors: Record<string, string> = {};

  export let users: User[] = [];
  export let consultationId: string = "";

  let selectedUsers: string[] = [];

  const setSelectedUsers = (checked: boolean, value?: string) => {
    if (!value) return;

    if (checked && !selectedUsers.includes(value)) {
      selectedUsers = [...selectedUsers, value];
    } else {
      selectedUsers = selectedUsers.filter((id) => id !== value);
    }
  };

  const handleSubmit = async () => {
    errors = {};

    if (selectedUsers.length == 0) {
      errors["general"] = "Please select a user to add";
    }

    if (Object.keys(errors).length == 0) {
      sending = true;
      try {
        const response = await fetch(
          getApiAddUserToConsultation(consultationId),
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              user_ids: selectedUsers,
            }),
          },
        );

        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }

        errors = {};
        selectedUsers = [];
        window.location.href = getSupportConsultationDetails(consultationId);
      } catch (err: unknown) {
        errors["general"] =
          err instanceof Error ? err.message : "An unknown error occurred";
      } finally {
        sending = false;
      }
    }
  };
</script>

<form class={clsx(["flex", "flex-col", "gap-4"])}>
  {#if "general" in errors}
    <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
      {errors.general}
    </small>
  {/if}
  {#each users as user (user.id)}
    {@const userIdString = user.id!.toString()}

    <Checkbox
      id={userIdString}
      value={userIdString}
      checked={selectedUsers.includes(userIdString)}
      disabled={false}
      label={user.email}
      name="selected_users"
      onchange={setSelectedUsers}
    />
  {/each}
  <Button
    type="button"
    variant="primary"
    handleClick={handleSubmit}
    disabled={sending}
  >
    {sending ? "Adding..." : "Add user(s)"}
  </Button>
</form>
