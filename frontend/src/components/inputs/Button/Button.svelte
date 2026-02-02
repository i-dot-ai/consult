<script lang="ts">
  import clsx from "clsx";

  export let type: string | undefined = undefined;
  export let title: string = "";
  export let variant:
    | "default"
    | "gray"
    | "primary"
    | "ghost"
    | "approve"
    | "outline" = "default";
  export let size: "xs" | "sm" | "md" | "lg" | "xl" = "md";
  export let highlighted: boolean = false;
  export let highlightVariant:
    | "dark"
    | "light"
    | "primary"
    | "approve"
    | "none" = "dark";
  export let handleClick: (e: MouseEvent) => void = () => {};
  export let disabled: boolean = false;
  export let fullWidth: boolean = false;
  export let testId: string = "";
  export let href: string | undefined = undefined;
  export let target: string | undefined = undefined;
  export let rel: string | undefined = undefined;
  export let ariaControls: string | undefined = undefined;
  export let noPadding: boolean = false;
  export let fixedHoverColor: boolean = false;
</script>

<svelte:element
  this={href ? "a" : "button"}
  role={href ? "link" : "button"}
  {type}
  title={title || undefined}
  data-variant={variant}
  tabindex="0"
  {href}
  {target}
  {rel}
  class={clsx([
    fullWidth && "w-full",
    `text-${size}`,
    "cursor-pointer",
    "rounded-md",
    !noPadding && clsx([size === "xs" ? "py-0.5" : "py-1"]),
    !noPadding && clsx([size === "xs" ? "px-1" : "px-2"]),
    "border",
    variant === "default" && "border-gray-300 bg-white",
    variant === "gray" && "border-gray-300 bg-neutral-100",
    variant === "primary" && "border-gray-300 bg-primary text-white",
    variant === "approve" && "border-gray-300 bg-secondary text-white",
    variant === "ghost" && "border-transparent",
    variant === "outline" &&
      clsx(["bg-transparent", "border border-primary", "text-primary"]),
    "transition-colors",
    "duration-300",
    "self-start",
    noPadding ? "block" : "inline-flex",
    "gap-1",
    "items-center",
    "hover:bg-gray-100",
    fixedHoverColor && "fixed-hover-color",
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
  aria-controls={ariaControls}
  data-testid={testId ? testId : undefined}
>
  <slot />
</svelte:element>

<style>
  *:is(button, a)[data-variant="approve"]:not(.disabled):hover :global(svg) {
    fill: var(--color-secondary);
  }
  *:is(button, a)[data-variant="primary"]:not(.disabled):hover :global(svg) {
    fill: var(--color-primary);
  }
  *:is(button, a)[data-variant="ghost"]:not(.disabled):not(
      .fixed-hover-color
    ):hover
    :global(svg) {
    fill: var(--color-primary);
  }
</style>
