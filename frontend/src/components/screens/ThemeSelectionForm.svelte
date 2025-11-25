<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import { Routes } from "../../global/routes";

  import TextInput from "../inputs/TextInput/TextInput.svelte";
  import type { Question, QuestionResponseResponse, ResponseTheme, ResponseThemeInformation } from "../../global/types";
  import Button from "../inputs/Button/Button.svelte";
  import Checkbox from "../inputs/Checkbox/Checkbox.svelte";
  import Text from "../Text/Text.svelte";

  let sending: boolean = false;
  let errors: Record<string, string> = {}
  let success: boolean = false;
  let loading: boolean = false;

  export let themes: ResponseThemeInformation;
  export let question: Question;
  export let response: QuestionResponseResponse; 

  let selectedThemes: ResponseTheme[] = themes.selected_themes;

  const setSelectedThemes = (checked: boolean, value?: string) => {
    if (!value) return;
    
    if (checked) {
      const themeToAdd = themes.all_themes.find(theme => theme.id === value);
      if (themeToAdd && !selectedThemes.some(theme => theme.id === value)) {
        selectedThemes = [...selectedThemes, themeToAdd];
      }
    } else {
      selectedThemes = selectedThemes.filter(theme => theme.id !== value);
    }
  };

  const handleSubmit = async () => {
    errors = {};
    success = false;
    sending = false;

    if (selectedThemes.length == 0) {
      errors["general"] = "Please select a question to export";
    }
    
    if (Object.keys(errors).length == 0) {
      success = false;
      sending = true;
      try {
        const response = await fetch(Routes.ApiConsultations, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ 
            theme_ids: selectedThemes,
          }),
        });

        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }

        success = true;
        loading = false;
        errors = {};
        selectedThemes = [];
        window.location.href = Routes.SupportConsultations;
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
  {#each themes.all_themes as theme}
    <Checkbox 
      id={theme.id!} 
      value={theme.id!}
      checked={selectedThemes.some(selectedTheme => selectedTheme.id === theme.id)} 
      disabled={false} 
      label={theme.name} 
      name="selected_themes"
      onchange={setSelectedThemes}
    />
  {/each}
  <Button
    type="submit"
    variant="primary"
    handleClick={handleSubmit}
    disabled={sending}
  >
    {sending ? "Saving..." : "Save and continue to a new response"}
  </Button>
  <Button
    type="button"
    variant="gray"
    handleClick={handleSubmit}
    disabled={sending}
  >
    Skip this response
    </Button>
</form>
