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
    default: "border-blue-500 bg-blue-50",
    info: "border-blue-500 bg-blue-50",
    warning: "border-yellow-500 bg-yellow-50",
    success: "border-green-500 bg-green-50",
    error: "border-red-500 bg-red-50",
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
