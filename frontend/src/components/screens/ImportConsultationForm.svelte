<script lang="ts">
  import clsx from "clsx";

  import { Routes } from "../../global/routes";

  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Button from "../inputs/Button/Button.svelte";
  import Select from "../inputs/Select.svelte";

  let sending: boolean = false;
  let error: string = "";
  let success: boolean = false;
  let consultationName: string = "";
  let timestamp: string = "";

  onMount(async () => {
    loading = true;
    const response = await fetch(`${Routes.ApiConsultationFolders}`);
    const consultationData = await response.json();
    consultations = consultationData.results;
    loading = false;
  });

  const timestampRegex = /^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}$/;

   const setConsultationName = (newValue: string) => {
    consultationName = newValue;

    error = consultationName ? "Please enter a consultation name" : "";
  };

  const setTimestamp = (newValue: string) => {
    timestamp = newValue;

    error = timestamp && !timestampRegex.test(newValue) ? "Please enter a consultation name" : "";
  };

  const handleSubmit = async () => {
    error = "";
    success = false;
    sending = true;

    try {
      const response = await fetch(Routes.ApiAstroSignIn, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          consultation_name: consultationName,
          timestamp: timestamp 
        }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      success = true;
      consultationName = "";
      timestamp = "";
    } catch (err: any) {
      error = err.message;
    } finally {
      sending = false;
    }
  };
</script>

<form
    class={clsx(["flex", "flex-col", "gap-4"])}
    on:submit|preventDefault={handleSubmit}
>
<TextInput id="consultation_name" name="consultation_name" label="Consultation title" autocomplete="false" value={consultationName} setValue={setConsultationName} />
<Select label="Select consultation folder" options= />
<!--  <Radios />-->
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