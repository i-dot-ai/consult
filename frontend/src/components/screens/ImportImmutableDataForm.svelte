<script lang="ts">
  import clsx from "clsx";
  import { slide } from "svelte/transition";
  import { Routes } from "../../global/routes";
  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Button from "../inputs/Button/Button.svelte";
  import Select from "../inputs/Select/Select.svelte";
  import type { SelectOption } from "../../global/types";

  export let consultationFolders: SelectOption[] = [];

  let sending: boolean = false;
  let errors: Record<string, string> = {};
  let success: boolean = false;

  let consultationName: string = "";
  let consultationFolderCode: string = "";

  const setConsultationName = (newValue: string) => {
    consultationName = newValue;
    errors["name"] = !consultationName
      ? "Please enter a consultation name"
      : "";
  };

  const setConsultationFolderCode = (newValue: string) => {
    consultationFolderCode = newValue;
    errors["code"] = !consultationFolderCode
      ? "Please select a consultation folder"
      : "";
  };

  const handleSubmit = async () => {
    errors = {};
    success = false;
    sending = false;

    if (!consultationName) {
      errors["name"] = "Please enter a consultation name";
    }

    if (!consultationFolderCode) {
      errors["code"] = "Please select a consultation folder";
    }

    if (Object.keys(errors).length == 0) {
      success = false;
      sending = true;
      try {
        const response = await fetch(Routes.ApiConsultationImportImmutable, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            consultation_name: consultationName,
            consultation_code: consultationFolderCode,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || `Error: ${response.status}`);
        }

        success = true;
        loading = false;
        errors = {};
        consultationName = "";
        consultationFolderCode = "";
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
      Immutable data import has been submitted.
    </small>
  {/if}
  {#if "name" in errors}
    <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
      {errors.name}
    </small>
  {/if}
  <TextInput
    id="consultation_name"
    name="consultation_name"
    label="Consultation title"
    autocomplete="false"
    value={consultationName}
    setValue={setConsultationName}
  />
  {#if "code" in errors}
    <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
      {errors.code}
    </small>
  {/if}
  <Select
    id="consultation_code"
    name="consultation_code"
    label="Select consultation folder"
    items={consultationFolders}
    onchange={setConsultationFolderCode}
  />
  <Button
    type="submit"
    variant="primary"
    handleClick={handleSubmit}
    disabled={sending}
  >
    {sending ? "Importing..." : "Import immutable data"}
  </Button>
</form>
