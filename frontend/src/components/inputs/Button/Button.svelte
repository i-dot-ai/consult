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
    | "outline"
    | "warning"
    | "danger"
    | "dot"
    | "text" = "default";
  export let size: "xs" | "sm" | "md" | "lg" | "xl" = "md";
  export let highlighted: boolean = false;
  export let highlightVariant:
    "dark" | "light" | "primary" | "approve" | "none" = "dark";
  export let handleClick: (e: MouseEvent) => void = () => {};
  export let disabled: boolean = false;
  export let fullWidth: boolean = false;
  export let testId: string = "";
  export let href: string | undefined = undefined;
  export let target: string | undefined = undefined;
  export let rel: string | undefined = undefined;
  export let ariaControls: string | undefined = undefined;
  export let ariaLabel: string | undefined = undefined;
  export let ariaExpanded: boolean | undefined = undefined;
  export let ariaCurrent: "page" | undefined = undefined;
  export let noPadding: boolean = false;
  export let fixedHoverColor: boolean = false;
  export let tabindex: number | undefined = undefined;
  export let justify: "left" | "center" | "right" = "center";
</script>

<svelte:element
  this={href ? "a" : "button"}
  role={href ? "link" : "button"}
  {type}
  title={title || undefined}
  data-variant={variant}
  tabindex={tabindex || 0}
  {href}
  {target}
  {rel}
  class={clsx([
    fullWidth && "w-full",
    `text-${size}`,
    "cursor-pointer",
    "rounded-md",
    !noPadding &&
      variant !== "dot" &&
      clsx([size === "xs" ? "py-0.5" : "py-1"]),
    !noPadding && variant !== "dot" && clsx([size === "xs" ? "px-1" : "px-2"]),
    "border",
    justify === "left" && "text-start",
    justify === "right" && "text-end",
    variant === "default" && "border-text-light-50 bg-white",
    variant === "gray" && "border-text-light-50 bg-text-light-95",
    variant === "primary" && "border-text-light-50 bg-primary text-white",
    variant === "approve" && "border-text-light-50 bg-success text-white",
    variant === "warning" &&
      clsx([
        disabled ? "border-text-light-50" : "border-warning-light-50",
        "bg-warning-light-95",
      ]),
    variant === "danger" &&
      clsx([
        disabled ? "border-text-light-50" : "border-error",
        "bg-transparent text-error",
      ]),
    variant === "ghost" &&
      clsx([
        disabled ? "border-text-light-50" : "border-transparent",
        "hover:bg-text-light-80",
      ]),
    variant === "dot" && "border-transparent text-text",
    variant === "outline" &&
      clsx([
        "bg-transparent",
        "border",
        disabled ? "border-text-light-50" : "border-primary",
        "text-primary",
      ]),
    variant === "text" && "underline border-0 p-0",
    "transition-colors",
    "duration-300",
    "self-start",
    noPadding ? "block" : "inline-flex",
    "gap-1",
    "items-center",
    variant === "dot"
      ? clsx([
          highlightVariant === "primary" && "hover:text-primary",
          highlightVariant === "approve" && "hover:text-success",
        ])
      : clsx([
          variant === "warning" && "hover:bg-warning-light-80",
          variant === "danger" && "hover:bg-error hover:text-white",
          variant === "text" && "hover:text-primary",
          variant !== "warning" &&
            variant !== "danger" &&
            variant !== "text" &&
            "hover:bg-text-light-80",
        ]),
    fixedHoverColor && "fixed-hover-color",
    variant === "primary" && "hover:border-primary hover:text-primary",
    variant === "approve" && "hover:border-success hover:text-success",

    disabled &&
      clsx([
        "disabled",
        variant !== "text" && "disabled:bg-text-light-80",
        "disabled:text-text",
        "disabled:cursor-not-allowed",
        variant !== "text" &&
          clsx([
            "disabled:hover:bg-text-light-80",
            "disabled:hover:border-text-light-50",
          ]),
        "disabled:hover:text-text",
      ]),

    highlighted &&
      !disabled &&
      variant !== "dot" &&
      clsx([
        highlightVariant === "dark" &&
          "bg-text-dark-25! text-white hover:bg-text-dark-50!",
        highlightVariant === "light" &&
          "border border-primary-light-80 bg-primary-light-95! text-text-dark-25 hover:bg-primary-light-80",
        highlightVariant === "primary" &&
          "bg-primary! text-white hover:bg-primary",
        highlightVariant === "approve" &&
          "border-success text-success hover:bg-success",
      ]),

    highlighted &&
      !disabled &&
      variant === "dot" &&
      clsx([
        highlightVariant === "primary" && "text-primary",
        highlightVariant === "approve" && "text-success",
      ]),
  ])}
  {disabled}
  on:click={handleClick}
  aria-pressed={highlighted !== undefined
    ? highlighted
      ? "true"
      : "false"
    : undefined}
  aria-label={ariaLabel}
  aria-expanded={ariaExpanded}
  aria-current={ariaCurrent}
  aria-controls={ariaControls}
  data-testid={testId ? testId : undefined}
>
  {#if variant === "dot"}
    •
  {:else}
    <slot />
  {/if}
</svelte:element>

<style>
  *:is(button, a)[data-variant="approve"]:not(.disabled):hover :global(svg) {
    fill: var(--color-success);
  }
  *:is(button, a)[data-variant="primary"]:not(.disabled):hover :global(svg) {
    fill: var(--color-primary);
  }
  *:is(button, a)[data-variant="danger"]:not(.disabled):hover :global(svg) {
    fill: white;
  }
  *:is(button, a)[data-variant="ghost"]:not(.disabled):not(
      .fixed-hover-color
    ):hover
    :global(svg) {
    fill: var(--color-primary);
  }
</style>
