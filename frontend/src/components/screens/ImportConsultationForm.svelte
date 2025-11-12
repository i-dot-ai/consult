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
  let error: string = "";
  let success: boolean = false;
  let loading: boolean = false;

  let consultationName: string = "";
  let timestamp: string = "";
  let populateOption: string = "";
  let consultationFolderCode: string = "";

  let consultationFolders: SelectOption[] = [];
  let RADIO_OPTIONS: RadioItem[] = [
    {
      value: 'sign_off',
      text: 'Populate Sign Off',
      checked: false,
      disabled: false
    }
    ,
    {
      value: 'dashboard',
      text: 'Populate Dashboard',
      checked: true,
      disabled: false
    }
  ];

  onMount(async () => {
    loading = true;
    const response = await fetch(`${Routes.ApiConsultationFolders}`);
    const consultationFolderData = await response.json();
    for (let folder of consultationFolderData) {
      console.log(consultationFolderData)
      let option: SelectOption = {
      value: folder.value, 
      label: folder.text
    };
    consultationFolders.push(option);
    };
    loading = false;
  });

  const timestampRegex = /^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}$/;

  const setConsultationName = (newValue: string) => {
    consultationName = newValue;
    error = !consultationName ? "Please enter a consultation name" : "";
  };

  const setTimestamp = (newValue: string) => {
    timestamp = newValue;
    error = timestamp && !timestampRegex.test(newValue) ? "Please enter a consultation name" : "";
  };

  const setPopulateOption = (newValue: string) => {
    populateOption = newValue;
  };

  const setConsultationFolderCode = (newValue: string) => {
    consultationFolderCode = newValue;
    error = !consultationFolderCode ? "Please select a consultation folder" : "";
  };

  const handleSubmit = async () => {
    error = "";
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
      error = ""
      consultationName = "";
      timestamp = "";
      consultationFolderCode = "";
      window.location.href = "/consultations/";
    } catch (err: any) {
      error = err.message;
    } finally {
      sending = false;
    }
  };
</script>

<form class={clsx(["flex", "flex-col", "gap-4"])}
    on:submit|preventDefault={handleSubmit}>
  {#if error}
  <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
    {error}
  </small>
  {/if}

  {#if success}
    <small class="text-sm text-gray-500" transition:slide={{ duration: 300 }}>
      Consultation has been submitted.
    </small>
  {/if}

  <TextInput id="consultation_name" name="consultation_name" label="Consultation title" autocomplete="false" value={consultationName} setValue={setConsultationName} />
  <Select id="consultation_code" name="consultation_code" label="Select consultation folder" items={consultationFolders} onchange={setConsultationFolderCode} />
  <Radio value={populateOption} name="action" items={RADIO_OPTIONS} onchange={setPopulateOption} />
  <TextInput autocomplete="false" id="timestamp" name="timestamp" label="Mapping timestamp folder (only needed to populate the dashboard)" placeholder="e.g., 2024-01-15-14-30-00" value={timestamp} setValue={setTimestamp} />
  <Button
    type="submit"
    variant="primary"
    handleClick={handleSubmit}
    disabled={sending}
  >
    {sending ? "Importing..." : "Import consultation"}
  </Button>
</form>
