<script lang="ts">
  import clsx from "clsx";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import Docs from "../../svg/material/Docs.svelte";

  export interface Props {
    title: string;
    answers?: string[];
    variant?: "selected" | "generated";
  }

  let { title = "", answers = [], variant = "selected" }: Props = $props();
</script>

<div class="flex items-center gap-1">
  <div class="shrink-0">
    <MaterialIcon
      color={variant === "selected" ? "fill-primary" : "fill-emerald-700"}
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
        : "bg-emerald-50 text-emerald-700",
    ])}
  >
    {answers.length}
  </div>
</div>

{#if answers?.length > 0}
  <ul class="mt-2 max-h-[20rem] overflow-y-auto">
    {#each answers as answer, i}
      <li
        class={clsx([
          "flex",
          "items-center",
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
              : "bg-emerald-50 text-emerald-700",
          ])}
        >
          {i + 1}
        </div>

        <p class="text-sm">
          {answer}
        </p>
      </li>
    {/each}
  </ul>
{:else}
  <p class="mt-2 text-sm text-neutral-500 italic">There are no answers</p>
{/if}
