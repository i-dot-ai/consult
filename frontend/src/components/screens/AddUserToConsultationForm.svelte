<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import { getApiAddUserToConsultation, Routes } from "../../global/routes";

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

    if (checked) {
      if (!selectedUsers.includes(value)) {
        selectedUsers = [...selectedUsers, value];
      }
    } else {
      selectedUsers = selectedUsers.filter((id) => id !== value);
    }
  };

  const handleSubmit = async () => {
    errors = {};
    console.log(selectedUsers);

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
        window.location.href = `${Routes.SupportConsultations}/${consultationId}`;
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
    <Checkbox
      id={user.id!.toString()}
      value={user.id!.toString()}
      checked={selectedUsers.includes(user.id!.toString())}
      disabled={false}
      label={user.email}
      name="selected_users"
      onchange={setSelectedUsers}
    />
  {/each}
  <Button
    type="submit"
    variant="primary"
    handleClick={handleSubmit}
    disabled={sending}
  >
    {sending ? "Adding..." : "Add user(s)"}
  </Button>
</form>
