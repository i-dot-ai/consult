<script lang="ts">
  import clsx from "clsx";
  import type { Snippet } from "svelte";

  import type { TitleLevels } from "../global/types";

  type Props = {
    level?: TitleLevels;
    weight?: "light" | "normal" | "bold";
    maxChars?: number;
    context?: "dashboard" | "public" | "theme-sign-off";
  } & (
    | { text: string; children?: never }
    | { text?: never; children: Snippet }
  );

  let {
    level = 1,
    weight = "normal",
    maxChars = 0,
    context = "dashboard",
    text,
    children,
  }: Props = $props();

  const tagMap = {
    1: "h1",
    2: "h2",
    3: "h3",
    4: "h4",
    5: "h5",
    6: "h6",
  } as const;

  const tag = tagMap[level];
</script>

<svelte:element
  this={tag}
  style={clsx([maxChars && `max-width: ${maxChars}ch;`])}
  class={clsx([
    "text-neutral-700",
    weight === "bold" && "font-bold",
    weight === "light" && "font-light",
    level === 1 && context === "dashboard" && "text-xl",
    level === 1 && context === "theme-sign-off" && "text-2xl",
    level === 2 && "text-lg",
    level === 3 && "text-md",
    level === 4 && "text-sm",
    level === 1 &&
      context === "public" &&
      clsx(["text-3xl", "mb-5", "font-bold"]),
    maxChars &&
      clsx([
        "max-w-[50ch]",
        "text-ellipsis",
        "whitespace-nowrap",
        "overflow-x-hidden",
      ]),
  ])}
>
  {#if children}
    {@render children()}
  {:else}
    {text}
  {/if}
</svelte:element>
