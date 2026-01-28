<script lang="ts">
  import clsx from "clsx";

  import { createQuery } from "@tanstack/svelte-query";
  import { queryClient } from "../../../../global/queryClient";
  import type { AnswersResponse } from "../../../../global/types";
  import { getApiAnswersUrl } from "../../../../global/routes";

  import MaterialIcon from "../../../MaterialIcon.svelte";
  import Docs from "../../../svg/material/Docs.svelte";
  import LoadingIndicator from "../../../LoadingIndicator/LoadingIndicator.svelte";

  export interface Props {
    consultationId: string;
    questionId: string;
    themeName: string;
    themeDescription: string;
    themeId: string;
    variant?: "selected" | "candidate";
  }

  let {
    consultationId,
    questionId,
    themeName,
    themeDescription,
    themeId,
    variant = "selected",
  }: Props = $props();

  const representativeResponsesQuery = createQuery<AnswersResponse>(
    () => ({
      queryKey: [
        "representativeResponses",
        consultationId,
        questionId,
        variant,
        themeId,
      ],
      queryFn: async () => {
        const queryString = new URLSearchParams({
          searchMode: "representative",
          searchValue: `${themeName} ${themeDescription}`,
          question_id: questionId,
        }).toString();

        const response = await fetch(
          `${getApiAnswersUrl(consultationId)}?${queryString}`,
        );
        if (!response.ok)
          throw new Error("Failed to fetch representative responses");
        return response.json();
      },
      staleTime: 5 * 60 * 1000, // 5 minutes
    }),
    () => queryClient,
  );

  let loading = $derived(representativeResponsesQuery.isLoading);
  let responses = $derived(
    representativeResponsesQuery.data?.all_respondents.map(
      (answer) => answer.free_text_answer_text,
    ) || [],
  );
</script>

<div class="flex items-center gap-1">
  <div class="shrink-0">
    <MaterialIcon
      color={variant === "selected" ? "fill-primary" : "fill-secondary"}
      size="1.2rem"
    >
      <Docs />
    </MaterialIcon>
  </div>

  <h2>Representative Responses</h2>

  <div
    class={clsx([
      "ml-1",
      "px-1.5",
      "py-0.5",
      "rounded-lg",
      "text-xs",
      variant === "selected"
        ? "bg-pink-100 text-primary"
        : "bg-teal-50 text-secondary",
    ])}
  >
    {#if loading}
      <LoadingIndicator size="1rem" />
    {:else}
      {responses.length}
    {/if}
  </div>
</div>
{#if loading}
  <ol>
    {#each "_".repeat(5) as _, i (i)}
      <li
        class={clsx([
          "blink",
          "overflow-hidden",
          "gap-2",
          "first:mt-4",
          "mb-4",
          "last:mb-0",
          "p-2",
          "rounded-lg",
          "text-neutral-100",
          "bg-neutral-100",
          "select-none",
        ])}
      >
        {"SKELETON ".repeat(5)}
      </li>
    {/each}
  </ol>
{:else if responses?.length > 0}
  <ol class="mt-2 max-h-[20rem] overflow-y-auto">
    {#each responses as response, i (i)}
      <li
        class={clsx([
          "flex",
          "items-start",
          "gap-2",
          "mb-2",
          "last:mb-0",
          "p-2",
          "rounded-lg",
          "text-neutral-600",
          "bg-neutral-50",
        ])}
      >
        <div
          class={clsx([
            "shrink-0",
            "flex",
            "justify-center",
            "items-center",
            "w-[3ch]",
            "h-[3ch]",
            "rounded-full",
            "text-xs",
            variant === "selected"
              ? "bg-pink-200 text-primary"
              : "bg-teal-50 text-secondary",
          ])}
        >
          {i + 1}
        </div>

        <p class="text-sm">
          {response}
        </p>
      </li>
    {/each}
  </ol>
{:else}
  <p class="mt-2 text-sm italic text-neutral-500">There are no answers</p>
{/if}
