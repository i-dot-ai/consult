<script lang="ts">
  import clsx from "clsx";

  import { getApiAddUserToConsultation } from "../../global/routes";

  import Button from "../inputs/Button/Button.svelte";
  import { parseEmails } from "./AddUserForm/parseEmails";

  let sending: boolean = false;
  let error: string | undefined;
  let successMessage: string | undefined;
  let nonExistentEmails: string[] = [];
  let copySuccess: boolean = false;

  export let consultationId: string = "";

  let emailsInput: string = "";

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      copySuccess = true;
      setTimeout(() => {
        copySuccess = false;
      }, 2000);
    } catch (err) {
      console.error("Failed to copy: ", err);
    }
  };

  const handleSubmit = async () => {
    error = undefined;
    successMessage = undefined;
    nonExistentEmails = [];

    const emails = parseEmails(emailsInput);

    if (emails.length === 0) {
      error = "Please enter at least one email address.";
      return;
    }

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
            emails: emails,
          }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Error: ${response.status}`);
      }

      const data = await response.json();

      if (data.added_count > 0) {
        successMessage = `Successfully added ${data.added_count} users to consultation.`;
        emailsInput = "";
      }

      if (data.non_existent_emails && data.non_existent_emails.length > 0) {
        nonExistentEmails = data.non_existent_emails;
      }
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : "An unknown error occurred";
    } finally {
      sending = false;
    }
  };
</script>

<form
  class={clsx(["max-w-md", "mt-4", "flex", "flex-col", "gap-4"])}
  on:submit|preventDefault={handleSubmit}
>
  <label for="emailsInput">Email addresses</label>
  <textarea
    id="emailsInput"
    rows="3"
    class="rounded border border-gray-300 px-3 py-2"
    placeholder="Enter one or more email addresses, separated by comma, space, or newline."
    bind:value={emailsInput}
    disabled={sending}
  ></textarea>

  {#if error}
    <p class="text-sm text-red-500">{`Error: ${error}`}</p>
  {/if}

  {#if successMessage}
    <p class="text-sm text-green-600">{successMessage}</p>
  {/if}

  {#if nonExistentEmails.length > 0}
    <div class="mt-4 rounded border border-yellow-300 bg-yellow-50 p-4">
      <h3 class="mb-2 font-semibold text-yellow-800">Users not found</h3>
      <p class="mb-3 text-sm text-yellow-700">
        The following email addresses do not exist in the system:
      </p>
      <ul class="mb-3 text-sm text-yellow-700 list-disc list-inside">
        {#each nonExistentEmails as email (email)}
          <li>{email}</li>
        {/each}
      </ul>
      <div class="flex flex-col gap-2">
        <Button
          type="button"
          variant="outline"
          handleClick={() => copyToClipboard(nonExistentEmails.join(", "))}
        >
          {copySuccess ? "Copied!" : "Copy emails"}
        </Button>
        {#if copySuccess}
          <p class="text-sm text-green-600">Emails copied to clipboard</p>
        {/if}
        <a href="/support/users/new" class="text-gray-700 underline">
          Invite these users →
        </a>
      </div>
    </div>
  {/if}

  <div class="flex">
    <Button variant="primary" disabled={sending}>
      {sending ? "Adding..." : "Add users"}
    </Button>
  </div>
</form>
