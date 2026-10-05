<script lang="ts">
  import clsx from "clsx";

  import Title from "../../Title.svelte";
  import Button from "../../inputs/Button/Button.svelte";

  import { getConsultationDetailUrl, Routes } from "../../../global/routes.ts";
  import {
    buildConsultationV2CreateQuery,
    getConsultationsV2ByTitle,
  } from "../../../global/queries/consultations/queries.ts";
  import type { ConsultationV2 } from "../../../global/queries/consultations/types.ts";
  import type { FetchError } from "../../../global/queryClient.ts";
  import { debounce } from "../../../global/utils.ts";

  const DUPLICATE_CHECK_DELAY = 300;
  const INPUT_ID = "consultation-name";
  const ERROR_SUMMARY_ID = "consultation-name-error";

  let name = $state("");
  let emptyError = $state(false);
  let submitError = $state("");
  let submitting = $state(false);

  const consultationCreate = buildConsultationV2CreateQuery(async (data) => {
    window.location.href = getConsultationDetailUrl(data.id);
  });

  const trimmedName = $derived(name.trim());

  let duplicate: ConsultationV2 | undefined = $state(undefined);
  let duplicateCount = $state(0);

  const checkDuplicate = debounce(async () => {
    const titleToCheck = trimmedName;

    if (!titleToCheck) {
      duplicate = undefined;
      duplicateCount = 0;
      return;
    }

    try {
      const { count, results } = await getConsultationsV2ByTitle(titleToCheck);
      if (titleToCheck === trimmedName) {
        duplicate = results[0];
        duplicateCount = count;
      }
    } catch (error) {
      console.error(error);
      duplicate = undefined;
      duplicateCount = 0;
    }
  }, DUPLICATE_CHECK_DELAY);

  const showDuplicateWarning = $derived(Boolean(duplicate));

  function formatDate(date: string) {
    return new Date(date).toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  }

  function describeCreator(consultation: ConsultationV2) {
    if (consultation.is_owner) {
      return "you";
    }
    return consultation.created_by?.email ?? "another user";
  }

  function handleInput() {
    emptyError = false;
    submitError = "";
    checkDuplicate();
  }

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();

    if (!trimmedName) {
      emptyError = true;
      return;
    }

    submitting = true;
    submitError = "";

    try {
      await consultationCreate.fetch({ body: { title: trimmedName } });
    } catch (error) {
      submitError =
        (error as FetchError<unknown>)?.message ||
        "Failed to create consultation";
      submitting = false;
    }
  }
</script>

{#if emptyError || submitError}
  <div
    role="alert"
    class={clsx(["mb-6", "max-w-2xl", "p-4", "border-2", "border-red-700"])}
  >
    <p class="mb-2 text-red-700">There is a problem</p>
    <ul class="list-disc pl-5">
      <li>
        {#if emptyError}
          <a href={`#${INPUT_ID}`} class="text-red-700 underline">
            Enter the consultation name
          </a>
        {:else}
          <span class="text-red-700">{submitError}</span>
        {/if}
      </li>
    </ul>
  </div>
{/if}

<Title level={1} text="Add a consultation" />

<p class="mt-4 mb-6 text-neutral-500">
  Give it a name to start. You upload the responses next.
</p>

<form class="flex max-w-2xl flex-col gap-4" onsubmit={handleSubmit} novalidate>
  <div class="flex flex-col gap-1">
    <label for={INPUT_ID}>Consultation name</label>
    <p id="consultation-name-hint" class="text-neutral-500">
      Use the name it was published under, so your team can find it.
    </p>

    {#if showDuplicateWarning && duplicate}
      <div
        id="consultation-name-warning"
        class="my-2 rounded-lg bg-neutral-100 p-4"
      >
        <p>{duplicate.title} already exists.</p>
        <p class="text-neutral-500">
          Created by {describeCreator(duplicate)} on {formatDate(
            duplicate.created_at,
          )}. You can use the same name, but the two will be hard to tell apart
          on the list.
          {#if duplicateCount > 1}
            Showing the most recent of {duplicateCount} with this name.
          {/if}
        </p>
      </div>
    {/if}

    {#if emptyError}
      <p id={ERROR_SUMMARY_ID} class="text-red-700">
        Enter the consultation name
      </p>
    {/if}

    <input
      id={INPUT_ID}
      name="title"
      type="text"
      class={clsx([
        "h-10",
        "w-full",
        "px-2",
        "rounded-xs",
        "border",
        "focus:outline-2",
        "focus:outline-yellow-300",
        emptyError ? "border-2 border-red-700" : "border-gray-300",
      ])}
      aria-describedby={clsx([
        "consultation-name-hint",
        showDuplicateWarning && "consultation-name-warning",
        emptyError && ERROR_SUMMARY_ID,
      ])}
      aria-invalid={emptyError}
      bind:value={name}
      oninput={handleInput}
      disabled={submitting}
    />
  </div>

  <div class="flex items-center gap-2">
    <Button
      type="submit"
      variant="primary"
      disabled={submitting || !trimmedName}
    >
      {showDuplicateWarning ? "Save anyway" : "Save and continue"}
    </Button>
    <Button href={Routes.Consultations} variant="default">Cancel</Button>
  </div>

  <p class="text-neutral-500">
    You can add people to the consultation once it is saved.
  </p>
</form>
