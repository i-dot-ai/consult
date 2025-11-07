<script lang="ts">
  import clsx from "clsx";

  export let type: string | undefined;
  export let title: string = "";
  export let variant: "default" | "gray" | "primary" | "ghost" | "approve" | "approve" =
    "default";
  export let size: "xs" | "sm" | "md" | "lg" | "xl" = "md";
  export let highlighted: boolean = false;
  export let highlightVariant:
    | "dark"
    | "light"
    | "primary"
    | "approve"
    | "none" = "dark";
  export let handleClick = (e: MouseEvent) => {};
  export let disabled: boolean = false;
  export let fullWidth: boolean = false;
  export let testId: string = "";
  export let href: string | undefined = undefined;
</script>

<svelte:element
  this={href ? "a" : "button"}
  role="button"
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
    variant === "default" && "bg-white",
    variant === "gray" && "bg-neutral-100",
    variant === "primary" && "bg-primary text-white",
    variant === "approve" && "bg-emerald-700 text-white",
    variant === "ghost" ? "border-transparent" : "border-gray-300",
    "transition-colors",
    "duration-300",
    "self-start",
    "inline-flex",
    "gap-1",
    "items-center",
    "hover:bg-gray-100",
    variant === "primary" && "hover:text-primary hover:border-primary",
    variant === "approve" && "hover:text-teal hover:border-teal",

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
          "!bg-pink-100 text-neutral-800 border border-pink-200 hover:bg-pink-200",
        highlightVariant === "primary" &&
          "!bg-primary text-white hover:bg-pink-500",
        highlightVariant === "approve" &&
          "border-teal text-teal hover:bg-teal-500",
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
    fill: var(--color-teal);
  }
  button[data-variant="primary"]:not(.disabled):hover :global(svg) {
    fill: var(--color-primary);
  }
  button[data-variant="ghost"]:not(.disabled):hover :global(svg) {
    fill: var(--color-primary);
  }
</style>
