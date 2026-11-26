<script lang="ts">
  import clsx from "clsx";

  import { type Snippet } from "svelte";

  interface Props {
    variant?:
      "default" | "primary" | "approve" | "approve-dark" | "white" | "gray";
    border?: boolean;
    bg?: boolean;
    level?: number;
    testId?: string;
    children: Snippet;
  }

  let {
    variant = "default",
    border = true,
    bg = false,
    level = 1,
    testId = "panel-component",
    children,
  }: Props = $props();
</script>

<div
  data-testid={testId}
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
        variant === "default" && "border-text-light-80",
        variant === "primary" && "border-primary-light-80",
        variant === "approve" && "border-success-light-80",
        variant === "approve-dark" && "border-success",
        variant === "white" && "border-text-light-80",
        variant === "gray" && "border-text-light-50",
      ]),
    bg &&
      clsx([
        variant === "default" && "bg-text-light-95",
        variant === "primary" && "bg-primary-light-95",
        variant === "approve" && "bg-success-light-95",
        variant === "approve-dark" && "bg-text-light-95",
        variant === "white" && "bg-white",
        variant === "gray" && "bg-neutral-100",
      ]),
  ])}
>
  {@render children()}
</div>
