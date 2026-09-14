<script lang="ts">
  import clsx from "clsx";

  import type { Component, Snippet } from "svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import Info from "../svg/material/Info.svelte";

  export interface Props {
    children: Snippet;
    Icon?: Component;
    variant?: "info" | "warning" | "error" | "success";
  }

  let { Icon = Info, children, variant = "info" }: Props = $props();

  const COLORS = {
    background: {
      info: "bg-sky-50",
      warning: "bg-yellow-50",
      error: "bg-pink-50",
      success: "bg-teal-50",
    },
    icon: {
      info: "fill-sky-800",
      warning: "fill-yellow-700",
      error: "fill-pink-700",
      success: "fill-teal-700",
    },
    text: {
      info: "text-sky-800",
      warning: "text-yellow-700",
      error: "text-pink-700",
      success: "text-teal-700",
    },
  };
</script>

<div
  class={clsx([
    "flex",
    "items-center",
    "justify-start",
    "gap-2",
    "rounded-lg",
    COLORS.background[variant],
    "p-2",
  ])}
  data-testid={`alert-${variant}`}
>
  {#if Icon}
    <div data-testid="icon">
      <MaterialIcon color={COLORS.icon[variant]}>
        <Icon />
      </MaterialIcon>
    </div>
  {/if}

  {#if children}
    <div class={clsx(["w-full", COLORS.text[variant]])}>
      {@render children()}
    </div>
  {/if}
</div>
