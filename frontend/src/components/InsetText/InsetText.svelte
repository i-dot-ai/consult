<script lang="ts">
  import clsx from "clsx";
  import type { Snippet } from "svelte";

  interface Props {
    variant?: "default" | "info" | "warning" | "success" | "error";
    className?: string;
    children: Snippet;
  }

  let { variant = "default", className = "", children }: Props = $props();

  const validVariant = $derived(variant as keyof typeof variantClasses);

  const variantClasses = {
    default: "border-primary bg-primary-light-95",
    info: "border-label bg-label-light-95",
    warning: "border-warning bg-warning-light-95",
    success: "border-success bg-success-light-95",
    error: "border-error bg-error-light-95",
  };
</script>

<div
  class={clsx([
    "govuk-inset-text",
    "p-4",
    "border-l-4",
    variantClasses[validVariant],
    className,
  ])}
>
  {@render children()}
</div>
