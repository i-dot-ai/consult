<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import { onMount } from "svelte";

  import { Routes } from "../../global/routes";

  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import Radio from "../Radio/Radio.svelte";
  import type { Question, RadioItem } from "../../global/types";
  import Button from "../inputs/Button/Button.svelte";
  import Select from "../inputs/Select/Select.svelte";
  import type { SelectOption } from "../../global/types";
    import Checkbox from "../inputs/Checkbox/Checkbox.svelte";
    import Text from "../Text/Text.svelte";

  let sending: boolean = false;
  let errors: Record<string, string> = {}
  let success: boolean = false;
  let loading: boolean = false;

  export let env: string = "";
  export let bucketName: string = "";
  export let questions: Question[] =[];

  let selectedQuestions: string[] = [];
  let s3Key: string = "";

  const setSelectedQuestions = (checked: boolean, value?: string) => {
    if (!value) return;
    
    if (checked) {
      if (!selectedQuestions.includes(value)) {
        selectedQuestions = [...selectedQuestions, value];
      }
    } else {
      selectedQuestions = selectedQuestions.filter(id => id !== value);
    }
  };

  const setS3Key = (newValue: string) => {
    s3Key = newValue;
    errors["s3Key"] = !["local", "test"].includes(env) && !s3Key ? "Please enter an s3 key" : "";
  };

  const handleSubmit = async () => {
    errors = {};
    success = false;
    sending = false;

    if (selectedQuestions.length == 0) {
      errors["general"] = "Please select a question to export";
    }

    if (!["local", "test"].includes(env) && !s3Key) {
      errors["s3Key"] = "Please enter an s3 key";
    }
    
    if (Object.keys(errors).length == 0) {
      success = false;
      sending = true;
      try {
        const response = await fetch(Routes.ApiConsultationExport, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ 
            question_ids: selectedQuestions,
            s3_key: s3Key || null,
          }),
        });

        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }

        success = true;
        loading = false;
        errors = {};
        selectedQuestions = [];
        s3Key = "";
        window.location.href = "/support/consultations/";
      } catch (err: any) {
        errors["general"] = err.message;
      } finally {
        sending = false;
      }
    }
  };
</script>

<form class={clsx(["flex", "flex-col", "gap-4"])}
  on:submit|preventDefault={handleSubmit}>
  {#if "general" in errors}
  <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
    {errors.general}
  </small>
  {/if}
  {#each questions as question}
    <Checkbox 
      id={question.id!} 
      value={question.id!}
      checked={selectedQuestions.includes(question.id!)} 
      disabled={false} 
      label={question.question_text} 
      name="selected_questions"
      onchange={setSelectedQuestions}
    />
  {/each}
  {#if env == "local"}
    <Text>The file will be saved in: downloads/[timestamp]_question_[question_number]_theme_changes</Text>
  {:else}
    {#if "s3Key" in errors}
    <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
      {errors.s3Key}
    </small>
    {/if}
    <TextInput id="s3_key" name="s3_key" label="Where should the file be saved?" autocomplete="false" value={s3Key} setValue={setS3Key} ></TextInput>
    <Text>The file will be saved as: {bucketName}/[YOUR PATH]/[timestamp]_question_[question_number]_theme_changes.csv</Text>
  {/if}
  <Button
    type="submit"
    variant="primary"
    handleClick={handleSubmit}
    disabled={sending}
  >
    {sending ? "Exporting..." : "Export consultation"}
  </Button>
</form>
