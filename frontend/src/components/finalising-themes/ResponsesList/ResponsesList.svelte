<script lang="ts">
  import clsx from "clsx";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import Docs from "../../svg/material/Docs.svelte";
  import LoadingIndicator from "../../LoadingIndicator/LoadingIndicator.svelte";

  export interface Props {
    title: string;
    responses?: string[];
    loading?: boolean;
    variant?: "selected" | "generated";
    totalCount?: number;
  }

  let {
    title = "",
    responses = [],
    loading = false,
    variant = "selected",
    totalCount = Infinity,
  }: Props = $props();
</script>

<div class="flex items-center gap-1">
  <div class="shrink-0">
    <MaterialIcon
      color={variant === "selected" ? "fill-primary" : "fill-success"}
      size="1.2rem"
    >
      <Docs />
    </MaterialIcon>
  </div>

  <h2>{title}</h2>

  <div
    class={clsx([
      "ml-1",
      "px-1.5",
      "py-0.5",
      "rounded-lg",
      "text-xs",
      variant === "selected"
        ? "bg-primary-light-95 text-primary"
        : "bg-success-light-95 text-success",
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
          "mb-2",
          "last:mb-0",
          "p-2",
          "rounded-lg",
          "text-text-light-95",
          "bg-text-light-95",
          "select-none",
        ])}
      >
        {"SKELETON ".repeat(5)}
      </li>
    {/each}
  </ol>
{:else if responses?.length > 0}
  <p class="mt-2 text-sm text-text">
    Showing a sample of {responses.length} out of a total of {totalCount} answers.
  </p>
  <ol class="mt-2 max-h-80 overflow-y-auto">
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
          "text-text",
          "bg-text-light-95",
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
              ? "bg-primary-light-80 text-primary-dark-25"
              : "bg-success-light-80 text-success-dark-25",
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
  <p class="mt-2 text-sm italic text-text">There are no responses</p>
{/if}
