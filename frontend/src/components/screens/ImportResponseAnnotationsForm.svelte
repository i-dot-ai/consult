<script lang="ts">
  import clsx from "clsx";
  import { slide } from "svelte/transition";
  import { Routes } from "../../global/routes";
  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Button from "../inputs/Button/Button.svelte";
  import Select from "../inputs/Select/Select.svelte";
  import type { SelectOption } from "../../global/types";

  export let existingConsultations: SelectOption[] = [];

  let sending: boolean = false;
  let errors: Record<string, string> = {};
  let success: boolean = false;

  let consultationCode: string = "";
  let timestamp: string = "";

  const setConsultationCode = (newValue: string) => {
    consultationCode = newValue;
    errors["code"] = !consultationCode ? "Please select a consultation" : "";
  };

  const setTimestamp = (newValue: string) => {
    timestamp = newValue;
    errors["timestamp"] = !timestamp ? "Please enter a timestamp" : "";
  };

  const handleSubmit = async () => {
    errors = {};
    success = false;
    sending = false;

    if (!consultationCode) {
      errors["code"] = "Please select a consultation";
    }

    if (!timestamp) {
      errors["timestamp"] = "Please enter a timestamp";
    }

    if (Object.keys(errors).length == 0) {
      success = false;
      sending = true;
      try {
        const response = await fetch(Routes.ApiConsultationImportAnnotations, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            consultation_code: consultationCode,
            timestamp: timestamp,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || `Error: ${response.status}`);
        }

        success = true;
        errors = {};
        consultationCode = "";
        timestamp = "";
        window.location.href = "/support/consultations/";
      } catch (err: unknown) {
        errors["general"] =
          err instanceof Error ? err.message : "An unknown error occurred";
      } finally {
        sending = false;
      }
    }
  };
</script>

<form
  class={clsx(["flex", "flex-col", "gap-4"])}
  on:submit|preventDefault={handleSubmit}
>
  {#if "general" in errors}
    <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
      {errors.general}
    </small>
  {/if}

  {#if success}
    <small class="text-sm text-gray-500" transition:slide={{ duration: 300 }}>
      Response annotations import has been submitted.
    </small>
  {/if}
  {#if "code" in errors}
    <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
      {errors.code}
    </small>
  {/if}
  <Select
    id="consultation_code"
    name="consultation_code"
    label="Select existing consultation"
    items={existingConsultations}
    onchange={setConsultationCode}
  />
  {#if "timestamp" in errors}
    <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
      {errors.timestamp}
    </small>
  {/if}
  <TextInput
    autocomplete="false"
    id="timestamp"
    name="timestamp"
    label="Timestamp folder (required)"
    placeholder="e.g. 2024-01-15"
    value={timestamp}
    setValue={setTimestamp}
  />
  <Button
    type="submit"
    variant="primary"
    handleClick={handleSubmit}
    disabled={sending}
  >
    {sending ? "Importing..." : "Import response annotations"}
  </Button>
</form>
