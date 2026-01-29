<script lang="ts">
  import clsx from "clsx";

  import Title from "../../Title.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import { parseEmails } from "./parseEmails";

  let emailsInput: string = "";
  let isStaff: boolean = true;
  let loading: boolean = false;

  type MultipleUserError = { email: string; error: string }[];
  let error: MultipleUserError | string | undefined;

  const handleSubmit = async () => {
    loading = true;

    const emails = parseEmails(emailsInput);

    if (emails.length === 0) {
      error = "Please enter at least one email address.";
      loading = false;
      return;
    }

    try {
      const reqBody = emails.length === 1 ? { email: emails[0] } : { emails };
      const res = await fetch("/api/users/", {
        method: "POST",
        body: JSON.stringify({
          ...reqBody,
          is_staff: isStaff,
        }),
        headers: { "Content-Type": "application/json" },
      });

      if (res.ok) {
        window.location.href = "/support/users";
      } else {
        if (emails.length === 1) {
          const errorResponse: { email?: string[] } = await res.json();
          error = errorResponse.email?.[0] || "something went wrong.";
          return;
        } else {
          const errorResponse: {
            errors: { email: string; errors: { email?: string[] } }[];
          } = await res.json();
          error = errorResponse.errors.map(({ email, errors }) => ({
            email,
            error: errors.email?.[0] || "something went wrong.",
          }));
        }
      }
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : "something went wrong.";
    } finally {
      loading = false;
    }
  };
</script>

<Title level={1} text="Add a user" />
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
    disabled={loading}
  ></textarea>

  <label class="flex items-center gap-2">
    <!--
      This checkbox has a lot of the default styles which makes it 
      look a bit inconsistent with the rest of the app. Since it's
      only internal users that access the support console, we can
      revisit this later if needed.
     -->
    <input
      id="isStaff"
      type="checkbox"
      checked={isStaff}
      on:change={(e) =>
        (isStaff = (e.target as HTMLInputElement).checked)}
      disabled={loading}
      class="h-6 w-6 focus:ring-2 focus:ring-yellow-300"
    />
    Admin access (support console & dashboards)
  </label>

  {#if error}
    {#if typeof error === "string"}
      <p class="text-sm text-red-500">{`Error: ${error}`}</p>
    {:else}
      {#each error as err, i (i)}
        <p class="text-sm text-red-500">
          {`Error for ${err.email}: ${err.error}`}
        </p>
      {/each}
    {/if}
  {/if}

  <div class="flex">
    <Button variant="primary" disabled={loading}>Add user</Button>
  </div>

  <div class="mt-4">
    <a href="/support/users" class="text-gray-700 underline">← Back to users</a>
  </div>
</form>
