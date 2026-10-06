<script lang="ts">
  import Title from "../../Title.svelte";
  import Alert from "../../Alert/Alert.svelte";
  import ErrorIcon from "../../svg/material/Error.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";

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
  const HINT_ID = "consultation-name-hint";
  const WARNING_ID = "consultation-name-warning";

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

  function handleInput(value: string) {
    name = value;
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
  <div class="mb-6 max-w-2xl">
    <Alert variant="error" Icon={ErrorIcon}>
      <p class="font-bold">There is a problem</p>
      {#if emptyError}
        <a href={`#${INPUT_ID}`} class="underline"
          >Enter the consultation name</a
        >
      {:else}
        <p>{submitError}</p>
      {/if}
    </Alert>
  </div>
{/if}

<Title level={1} text="Add a consultation" />

<p class="mt-4 mb-6 text-neutral-500">
  Give it a name to start. You upload the responses next.
</p>

<form class="flex max-w-2xl flex-col gap-4" onsubmit={handleSubmit} novalidate>
  <TextInput
    id={INPUT_ID}
    name="title"
    label="Consultation name"
    value={name}
    setValue={handleInput}
    disabled={submitting}
    invalid={emptyError}
    ariaDescribedby={[HINT_ID, duplicate && WARNING_ID]
      .filter(Boolean)
      .join(" ")}
  />

  <p id={HINT_ID} class="text-neutral-500">
    Use the name it was published under, so your team can find it.
  </p>

  {#if duplicate}
    <div id={WARNING_ID}>
      <Panel variant="default" bg>
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
      </Panel>
    </div>
  {/if}

  <div class="flex items-center gap-2">
    <Button
      type="submit"
      variant="primary"
      disabled={submitting || !trimmedName}
    >
      {duplicate ? "Save anyway" : "Save and continue"}
    </Button>
    <Button href={Routes.Consultations} variant="default">Cancel</Button>
  </div>

  <p class="text-neutral-500">
    You can add people to the consultation once it is saved.
  </p>
</form>
