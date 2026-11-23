<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import {
    getApiQuestionResponse,
    getApiShowNextResponse,
    getApiResponseV2Url,
    getApiShowNextResponseV2Url,
    getResponseDetailUrl,
  } from "../../../global/routes";

  import type {
    ResponseTheme,
    ShowNextResponseResult,
  } from "../../../global/types";
  import type { ShowNextResponseResultV2 } from "../../../global/queries/questions/types";
  import { getDataSetupV2Enabled } from "../../../global/utils";
  import Button from "../../inputs/Button/Button.svelte";
  import Checkbox from "../../inputs/Checkbox/Checkbox.svelte";

  interface Props {
    allThemes: ResponseTheme[];
    selectedThemes: ResponseTheme[];
    responseId: string;
    consultationId: string;
    questionId: string;
    isV2?: boolean;
  }

  const {
    allThemes,
    selectedThemes,
    responseId,
    consultationId,
    questionId,
    isV2: isV2Prop,
  }: Props = $props();

  let ownSelectedThemes = $derived(selectedThemes);
  let sending: boolean = $state(false);
  let errors: Record<string, string> = $state({});

  const isV2 = isV2Prop ?? getDataSetupV2Enabled();
  const showNextUrl = isV2
    ? getApiShowNextResponseV2Url(consultationId, questionId)
    : getApiShowNextResponse(consultationId, questionId);
  const updateResponseUrl = isV2
    ? getApiResponseV2Url(consultationId, responseId)
    : getApiQuestionResponse(consultationId, questionId, responseId);

  const setSelectedThemes = (checked: boolean, value?: string) => {
    if (!value) return;

    if (checked) {
      const themeToAdd = allThemes.find((theme) => theme.id === value);
      if (
        themeToAdd &&
        !ownSelectedThemes.some((theme) => theme.id === value)
      ) {
        ownSelectedThemes = [...ownSelectedThemes, themeToAdd];
      }
    } else {
      ownSelectedThemes = ownSelectedThemes.filter(
        (theme) => theme.id !== value,
      );
    }
  };

  const handleShowNext = async () => {
    try {
      const response = await fetch(showNextUrl);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: ShowNextResponseResult | ShowNextResponseResultV2 =
        await response.json();
      const hasFreeText =
        "has_free_text" in result
          ? result.has_free_text
          : result.type === "open";

      if (result.next_response) {
        window.location.href = getResponseDetailUrl(
          result.next_response.consultation_id,
          result.next_response.question_id,
          result.next_response.id,
        );
      } else {
        if (!hasFreeText) {
          errors["general"] =
            "This question does not have free text responses.";
          sending = false;
        } else {
          window.location.href = `/evaluations/${consultationId}/questions/`;
        }
      }
    } catch (err) {
      console.error("Error fetching next response:", err);
      errors["general"] = "Failed to fetch next response. Please try again.";
      sending = false;
    }
  };

  const handleSubmit = async () => {
    errors = {};
    sending = true;

    try {
      const updateResponse = await fetch(updateResponseUrl, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          themes: ownSelectedThemes,
          human_reviewed: true,
        }),
      });

      if (!updateResponse.ok) {
        throw new Error(`Error: ${updateResponse.status}`);
      }

      await handleShowNext();
    } catch (err: unknown) {
      errors["general"] =
        err instanceof Error ? err.message : "An unknown error occurred";
      sending = false;
    }
  };

  const handleSkip = async () => {
    errors = {};
    sending = true;

    try {
      await handleShowNext();
    } catch (err: unknown) {
      errors["general"] =
        err instanceof Error ? err.message : "An unknown error occurred";
      sending = false;
    }
  };
</script>

<div class="rounded-xl border border-gray-200 bg-white p-6">
  <form
    class={clsx(["flex", "flex-col", "gap-4"])}
    onsubmit={(e) => {
      e.preventDefault();
      handleSubmit();
    }}
  >
    {#if "general" in errors}
      <small class="text-sm text-red-500" transition:slide={{ duration: 300 }}>
        {errors.general}
      </small>
    {/if}
    <div class="space-y-3">
      {#each allThemes as theme (theme.id)}
        <div
          class="rounded-lg border border-gray-100 p-3 transition-colors hover:bg-gray-50"
        >
          <Checkbox
            id={theme.id!}
            value={theme.id!}
            checked={ownSelectedThemes.some(
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
