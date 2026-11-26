<script lang="ts">
  import clsx from "clsx";

  import { type Snippet } from "svelte";

  interface Props {
    variant?:
      | "default"
      | "dark"
      | "warning"
      | "primary"
      | "primary-light"
      | "success"
      | "error";
    border?: boolean;
    wrap?: boolean;
    children: Snippet;
  }
  let { variant = "default", border, wrap = false, children }: Props = $props();
</script>

<div
  class={clsx([
    "flex",
    "justify-between",
    "items-center",
    "gap-2",
    "rounded-md",
    wrap ? "max-w-full" : "w-max",
    "py-0.5",
    "px-2",
    "text-xs",
    variant === "default" &&
      clsx([
        "bg-text-light-95",
        "text-text-dark-25",
        border && "border border-text-light-50",
      ]),
    variant === "dark" && clsx(["bg-neutral-200", "text-neutral-800"]),
    variant === "primary" && clsx(["bg-primary", "text-white"]),
    variant === "primary-light" &&
      clsx(["bg-primary-light-95", "text-primary", "border border-primary-light-80"]),
    variant === "warning" &&
      clsx(["text-warning", "bg-warning-light-95", "border border-warning-light-80"]),
    variant === "success" &&
      clsx(["text-success", "bg-success-light-95", "border border-success-light-80"]),
    variant === "error" &&
      clsx(["text-error", "bg-error-light-95", "border border-error-light-80"]),
  ])}
>
  {@render children()}
</div>
