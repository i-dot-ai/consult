<script lang="ts">
    import clsx from "clsx";

    export let variant: "default" | "primary" | "ghost" | "approve" = "default";
    export let size: "xs" | "sm" | "md" | "lg" | "xl" = "md";
    export let highlighted: boolean = false;
    export let highlightVariant: "dark" | "light" | "primary" | "approve" = "dark";
    export let handleClick = (e: MouseEvent) => {};
    export let disabled: boolean = false;
    export let fullWidth: boolean = false;
</script>

<style>
    button[data-variant="approve"]:hover :global(svg) {
        fill: var(--color-teal);
    }
    button[data-variant="primary"]:hover :global(svg) {
        fill: var(--color-primary);
    }
</style>

<button
    data-variant={variant}
    class={clsx([
        fullWidth && "w-full",
        `text-${size}`,
        "self-start",
        "cursor-pointer",
        "rounded-md",
        size === "xs" ? "py-0.5" : "py-1",
        size === "xs" ? "px-1" : "px-2",
        "border",
        variant === "primary" && "bg-primary text-white",
        variant === "approve" && "bg-teal text-white",
        variant === "ghost" ? "border-transparent" : "border-gray-300",
        "transition-colors",
        "duration-300",
        "flex",
        "gap-1",
        "items-center",
        "hover:bg-gray-100",
        variant === "primary" && "hover:text-primary hover:border-primary",
        variant === "approve" && "hover:text-teal hover:border-teal",

        disabled && clsx([
            "disabled:bg-gray-200",
            "disabled:text-gray-400",
            "disabled:cursor-not-allowed",
            "disabled:hover:bg-gray-200",
            "disabled:hover:border-gray-300",
            "disabled:hover:text-gray-400",
        ]),

        highlighted && !disabled && clsx([
            highlightVariant === "dark" && "bg-neutral-800 text-white hover:bg-neutral-700",
            highlightVariant === "light" && "bg-pink-100 text-neutral-800 border border-pink-200 hover:bg-pink-200",
            highlightVariant === "primary" && "bg-primary text-white hover:bg-pink-500",
            highlightVariant === "approve" && "border-teal text-teal hover:bg-teal-500",
        ]),
    ])}
    disabled={disabled}
    on:click={handleClick}
    aria-pressed={highlighted !== undefined
        ? highlighted ? "true" : "false"
        : undefined
    }
>
    <slot />
</button>