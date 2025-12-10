<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import {
    getApiQuestionResponse,
    getApiShowNextResponse,
  } from "../../global/routes";

  import type {
    QuestionResponseResponse,
    ResponseTheme,
    ResponseThemeInformation,
  } from "../../global/types";
  import Button from "../inputs/Button/Button.svelte";
  import Checkbox from "../inputs/Checkbox/Checkbox.svelte";

  let sending: boolean = false;
  let errors: Record<string, string> = {};

  export let themes: ResponseThemeInformation;
  export let response: QuestionResponseResponse;
  export let consultationId: string;
  export let questionId: string;

  let selectedThemes: ResponseTheme[] = themes.selected_themes;

  const setSelectedThemes = (checked: boolean, value?: string) => {
    if (!value) return;

    if (checked) {
      const themeToAdd = themes.all_themes.find((theme) => theme.id === value);
      if (themeToAdd && !selectedThemes.some((theme) => theme.id === value)) {
        selectedThemes = [...selectedThemes, themeToAdd];
      }
    } else {
      selectedThemes = selectedThemes.filter((theme) => theme.id !== value);
    }
  };

  const handleSubmit = async () => {
    errors = {};
    sending = true;

    try {
      const updateResponse = await fetch(
        getApiQuestionResponse(consultationId, questionId, response.id),
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            annotation: {
              responseannotationtheme_set: selectedThemes,
              human_reviewed: true,
            },
          }),
        },
      );

      if (!updateResponse.ok) {
        throw new Error(`Error: ${updateResponse.status}`);
      }
      window.location.href = getApiShowNextResponse(consultationId, questionId);
    } catch (err: unknown) {
      errors["general"] =
        err instanceof Error ? err.message : "An unknown error occurred";
    } finally {
      sending = false;
    }
  };

  const handleSkip = () => {
    window.location.href = getApiShowNextResponse(consultationId, questionId);
  };
</script>

<div class="rounded-xl border border-gray-200 bg-white p-6">
  <form
    class={clsx(["flex", "flex-col", "gap-4"])}
    on:submit|preventDefault={handleSubmit}
  >
    {#if "general" in errors}
      <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
        {errors.general}
      </small>
    {/if}
    <div class="space-y-3">
      {#each themes.all_themes as theme (theme.id)}
        <div
          class="rounded-lg border border-gray-100 p-3 transition-colors hover:bg-gray-50"
        >
          <Checkbox
            id={theme.id!}
            value={theme.id!}
            checked={selectedThemes.some(
              (selectedTheme) => selectedTheme.id === theme.id,
            )}
            disabled={false}
            label={theme.name}
            name="selected_themes"
            onchange={setSelectedThemes}
          />
          {#if theme.description}
            <div class="ml-6 mt-1 text-sm text-gray-600">
              {theme.description}
            </div>
          {/if}
        </div>
      {/each}
    </div>
    <div class="space-y-3 border-t border-gray-200 pt-4">
      <Button
        type="submit"
        variant="primary"
        handleClick={handleSubmit}
        disabled={sending}
      >
        {sending ? "Saving..." : "Save and continue to next response"}
      </Button>
      <Button
        type="button"
        variant="gray"
        handleClick={handleSkip}
        disabled={sending}
      >
        Skip this response
      </Button>
    </div>
  </form>
</div>
