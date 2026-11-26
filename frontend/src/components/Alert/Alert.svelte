<script lang="ts">
  import clsx from "clsx";

  import { onDestroy, onMount, type Component, type Snippet } from "svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import Info from "../svg/material/Info.svelte";

  export interface Props {
    children: Snippet;
    Icon?: Component;
    variant?: "info" | "warning" | "error" | "success";
    onTimeout?: () => void;
    timeoutDelay?: number;
  }

  let {
    Icon = Info,
    children,
    variant = "info",
    onTimeout,
    timeoutDelay = 5000,
  }: Props = $props();

  const COLORS = {
    background: {
      info: "bg-primary-light-95",
      warning: "bg-warning-light-95",
      error: "bg-error-light-95",
      success: "bg-success-light-95",
    },
    icon: {
      info: "fill-primary",
      warning: "fill-warning",
      error: "fill-error",
      success: "fill-success",
    },
    text: {
      info: "text-primary",
      warning: "text-warning",
      error: "text-error",
      success: "text-success",
    },
  };

  let timeout: ReturnType<typeof setTimeout> | null = null;

  onMount(() => {
    if (onTimeout) {
      timeout = setTimeout(onTimeout, timeoutDelay);
    }
  });

  onDestroy(() => {
    if (timeout) {
      clearTimeout(timeout);
      timeout = null;
    }
  });
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
