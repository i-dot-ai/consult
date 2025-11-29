<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import { onMount } from "svelte";

  import { Routes } from "../../global/routes";

  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Radio from "../Radio/Radio.svelte";
  import type { RadioItem } from "../../global/types";
  import Button from "../inputs/Button/Button.svelte";
  import Select from "../inputs/Select/Select.svelte";
  import type { SelectOption } from "../../global/types";

  let sending: boolean = false;
  let errors: Record<string, string> = {};
  let success: boolean = false;
  let loading: boolean = false;

  let consultationFolders: SelectOption[] = [];
  let RADIO_OPTIONS: RadioItem[] = [
    {
      value: "sign_off",
      text: "Populate Sign Off",
      checked: false,
      disabled: false,
    },
    {
      value: "dashboard",
      text: "Populate Dashboard",
      checked: true,
      disabled: false,
    },
  ];

  let consultationName: string = "";
  let timestamp: string = "";
  let consultationFolderCode: string = "";
  let populateOption: string =
    RADIO_OPTIONS.find((option) => option.checked)?.value || "";

  onMount(async () => {
    loading = true;
    consultationFolders = [];
    const response = await fetch(`${Routes.ApiConsultationFolders}`);
    const consultationFolderData = await response.json();

    consultationFolders = consultationFolderData.map((folder: any) => ({
      value: folder.value,
      label: folder.text,
    }));

    loading = false;
  });

  const setConsultationName = (newValue: string) => {
    consultationName = newValue;
    errors["name"] = !consultationName
      ? "Please enter a consultation name"
      : "";
  };

  const setTimestamp = (newValue: string) => {
    timestamp = newValue;
    errors["timestamp"] = !timestamp ? "Please enter a valid timestamp" : "";
  };

  const setPopulateOption = (newValue: string) => {
    populateOption = newValue;
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

    if (!timestamp) {
      errors["timestamp"] = "Please enter a valid timestamp";
    }

    if (!consultationFolderCode) {
      errors["code"] = "Please select a consultation folder";
    }

    if (Object.keys(errors).length == 0) {
      success = false;
      sending = true;
      try {
        const response = await fetch(Routes.ApiConsultationImport, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            consultation_name: consultationName,
            timestamp: timestamp,
            action: populateOption,
            consultation_code: consultationFolderCode,
          }),
        });

        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }

        success = true;
        loading = false;
        errors = {};
        consultationName = "";
        timestamp = "";
        consultationFolderCode = "";
        window.location.href = "/support/consultations/";
      } catch (err: any) {
        errors["general"] = err.message;
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
      Consultation has been submitted.
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
  {#if "action" in errors}
    <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
      {errors.action}
    </small>
  {/if}
  <Radio
    value={populateOption}
    name="action"
    items={RADIO_OPTIONS}
    onchange={setPopulateOption}
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
    label="Mapping timestamp folder (only needed to populate the dashboard)"
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
    {sending ? "Importing..." : "Import consultation"}
  </Button>
</form>
