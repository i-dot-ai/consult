<script lang="ts">
  import clsx from "clsx";

  import { type Snippet } from "svelte";

  interface Props {
    variant?:
      "default" | "dark" | "warning" | "primary" | "primary-light" | "success";
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
        "bg-neutral-100",
        "text-neutral-800",
        border && "border border-neutral-300",
      ]),
    variant === "dark" && clsx(["bg-neutral-200", "text-neutral-800"]),
    variant === "primary" && clsx(["bg-primary", "text-white"]),
    variant === "primary-light" &&
      clsx(["bg-pink-100", "text-primary", "border border-pink-300"]),
    variant === "warning" &&
      clsx(["text-yellow-700", "bg-yellow-100", "border border-yellow-400"]),
    variant === "success" &&
      clsx(["text-secondary", "bg-teal-50", "border border-teal-400"]),
  ])}
>
  {@render children()}
</div>
