<script lang="ts">
  import clsx from "clsx";

  export let type: string | undefined = undefined;
  export let title: string = "";
  export let variant: "default" | "gray" | "primary" | "ghost" | "approve" | "outline" =
    "default";
  export let size: "xs" | "sm" | "md" | "lg" | "xl" = "md";
  export let highlighted: boolean = false;
  export let highlightVariant:
    | "dark"
    | "light"
    | "primary"
    | "approve"
    | "none" = "dark";
  export let handleClick = () => {};
  export let disabled: boolean = false;
  export let fullWidth: boolean = false;
  export let testId: string = "";
  export let href: string | undefined = undefined;
</script>

<svelte:element
  this={href ? "a" : "button"}
  role={href ? "link" : "button"}
  {type}
  title={title || undefined}
  data-variant={variant}
  tabindex="0"
  {href}
  class={clsx([
    fullWidth && "w-full",
    `text-${size}`,
    "cursor-pointer",
    "rounded-md",
    size === "xs" ? "py-0.5" : "py-1",
    size === "xs" ? "px-1" : "px-2",
    "border",
    variant === "default" && "bg-white border-gray-300",
    variant === "gray" && "bg-neutral-100 border-gray-300",
    variant === "primary" && "bg-primary text-white border-gray-300",
    variant === "approve" && "bg-secondary text-white border-gray-300",
    variant === "ghost" && "border-transparent",
    variant === "outline" && clsx([
      "bg-transparent",
      "border border-primary",
      "text-primary",
    ]),
    "transition-colors",
    "duration-300",
    "self-start",
    "inline-flex",
    "gap-1",
    "items-center",
    "hover:bg-gray-100",
    variant === "primary" && "hover:border-primary hover:text-primary",
    variant === "approve" && "hover:border-secondary hover:text-secondary",

    disabled &&
      clsx([
        "disabled",
        "disabled:bg-gray-200",
        "disabled:text-gray-400",
        "disabled:cursor-not-allowed",
        "disabled:hover:bg-gray-200",
        "disabled:hover:border-gray-300",
        "disabled:hover:text-gray-400",
      ]),

    highlighted &&
      !disabled &&
      clsx([
        highlightVariant === "dark" &&
          "!bg-neutral-800 text-white hover:bg-neutral-700",
        highlightVariant === "light" &&
          "border border-pink-200 !bg-pink-100 text-neutral-800 hover:bg-pink-200",
        highlightVariant === "primary" &&
          "!bg-primary text-white hover:bg-pink-500",
        highlightVariant === "approve" &&
          "border-secondary text-secondary hover:bg-teal-500",
      ]),
  ])}
  {disabled}
  on:click={handleClick}
  aria-pressed={highlighted !== undefined
    ? highlighted
      ? "true"
      : "false"
    : undefined}
  data-testid={testId ? testId : undefined}
>
  <slot />
</svelte:element>

<style>
  button[data-variant="approve"]:not(.disabled):hover :global(svg) {
    fill: var(--color-secondary);
  }
  button[data-variant="primary"]:not(.disabled):hover :global(svg) {
    fill: var(--color-primary);
  }
  button[data-variant="ghost"]:not(.disabled):hover :global(svg) {
    fill: var(--color-primary);
  }
</style>
