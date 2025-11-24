<script lang="ts">
  import clsx from "clsx";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import Docs from "../../svg/material/Docs.svelte";
  import LoadingIndicator from "../../LoadingIndicator/LoadingIndicator.svelte";

  export interface Props {
    title: string;
    answers?: string[];
    loading?: boolean;
    variant?: "selected" | "generated";
  }

  let {
    title = "",
    answers = [],
    loading = false,
    variant = "selected",
  }: Props = $props();
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

  <h2>{title}</h2>

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
      {answers.length}
    {/if}
  </div>
</div>
{#if loading}
  <ol>
    {#each "_".repeat(5) as _}
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
{:else if answers?.length > 0}
  <ol class="mt-2 max-h-[20rem] overflow-y-auto">
    {#each answers as answer, i}
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
          {answer}
        </p>
      </li>
    {/each}
  </ol>
{:else}
  <p class="mt-2 text-sm text-neutral-500 italic">There are no answers</p>
{/if}
