<script lang="ts">
  import clsx from "clsx";

  import { type Snippet } from "svelte";

  interface Props {
    variant?: "default" | "primary" | "approve" | "approve-dark";
    border?: boolean;
    bg?: boolean;
    level?: number;
    children: Snippet;
  }

  let {
    variant = "default",
    border = true,
    bg = false,
    level = 1,
    children,
  }: Props = $props();
</script>

<div
  data-testid="panel-component"
  class={clsx([
    "h-full",
    "my-4",
    level === 1 && "p-4",
    level === 2 && "p-2",
    level === 3 && "p-1",
    "rounded-2xl",
    border &&
      clsx([
        "border",
        variant === "default" && "border-gray-200",
        variant === "primary" && "border-pink-200",
        variant === "approve" && "border-emerald-200",
        variant === "approve-dark" && "border-emerald-700",
      ]),
    bg &&
      clsx([
        variant === "default" && "bg-neutral-50",
        variant === "primary" && "bg-pink-50",
        variant === "approve" && "bg-emerald-50",
        variant === "approve-dark" && "bg-neutral-50",
      ]),
  ])}
>
  {@render children()}
</div>
