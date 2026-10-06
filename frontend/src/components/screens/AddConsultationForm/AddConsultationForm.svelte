<script lang="ts">
  import Title from "../../Title.svelte";
  import Alert from "../../Alert/Alert.svelte";
  import ErrorIcon from "../../svg/material/Error.svelte";
  import Warning from "../../svg/material/Warning.svelte";
  import Modal from "../../Modal/Modal.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import TextInput from "../../inputs/TextInput/TextInput.svelte";

  import { getConsultationDetailUrl, Routes } from "../../../global/routes.ts";
  import {
    buildConsultationsV2ByTitleQuery,
    buildConsultationV2CreateQuery,
  } from "../../../global/queries/consultations/queries.ts";
  import type {
    ConsultationsV2GetResponse,
    ConsultationV2,
  } from "../../../global/queries/consultations/types.ts";

  const INPUT_ID = "consultation-name";
  const HINT_ID = "consultation-name-hint";

  let name = $state("");
  let emptyError = $state(false);
  let submitError = $state("");
  let submitting = $state(false);
  let checkTrigger = $state(0);

  let duplicate: ConsultationV2 | undefined = $state(undefined);
  let duplicateCount = $state(0);

  const trimmedName = $derived(name.trim());

  // Re-created each time checkTrigger changes, so handleSubmit can trigger a
  // fresh lookup for the current name without reusing a stale query.
  const titleLookup = $derived(
    checkTrigger ? buildConsultationsV2ByTitleQuery(trimmedName) : null,
  );

  const consultationCreate = buildConsultationV2CreateQuery(
    async (data) => {
      window.location.href = getConsultationDetailUrl(data.id);
    },
    async (error) => {
      submitError = error.message || "Failed to create consultation";
      submitting = false;
    },
  );

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
    name = value.trimStart();
    emptyError = false;
    submitError = "";
  }

  async function createConsultation() {
    submitting = true;
    submitError = "";

    try {
      await consultationCreate.fetch({ body: { title: trimmedName } });
    } catch (error) {
      console.error(error);
    }
  }

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();

    if (!trimmedName) {
      emptyError = true;
      return;
    }

    submitting = true;
    submitError = "";
    checkTrigger += 1;

    try {
      const result = (await titleLookup?.fetch()) as
        { data?: ConsultationsV2GetResponse } | undefined;
      const match = result?.data?.results[0];

      if (match) {
        duplicate = match;
        duplicateCount = result?.data?.count ?? 0;
        submitting = false;
        return;
      }
    } catch (error) {
      console.error(error);
      // If the duplicate check itself fails, continue to create rather than
      // blocking the user on an unrelated error.
    }

    await createConsultation();
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
    ariaDescribedby={HINT_ID}
  />

  <p id={HINT_ID} class="text-neutral-500">
    Use the name it was published under, so your team can find it.
  </p>

  <div class="flex items-center gap-2">
    <Button
      type="submit"
      variant="primary"
      disabled={submitting || !trimmedName}
    >
      Save and continue
    </Button>
    <Button href={Routes.Consultations} variant="default">Cancel</Button>
  </div>

  <p class="text-neutral-500">
    You can add people to the consultation once it is saved.
  </p>
</form>

<Modal
  variant="warning"
  Icon={Warning}
  title="This consultation name already exists"
  open={Boolean(duplicate)}
  setOpen={(newOpen) => {
    if (!newOpen) {
      duplicate = undefined;
      submitting = false;
    }
  }}
  confirmText="Save anyway"
  handleConfirm={() => {
    duplicate = undefined;
    createConsultation();
  }}
>
  {#if duplicate}
    <p>{duplicate.title} already exists.</p>
    <p class="text-neutral-500">
      Created by {describeCreator(duplicate)} on {formatDate(
        duplicate.created_at,
      )}. You can use the same name, but the two will be hard to tell apart on
      the list.
      {#if duplicateCount > 1}
        Showing the most recent of {duplicateCount} with this name.
      {/if}
    </p>
  {/if}
</Modal>
