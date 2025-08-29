<script lang="ts">
    import clsx from "clsx";

    export let href: string = "";
    export let title: string = "";
    export let ariaLabel: string = "";
    export let variant: "inline" | "block" = "inline";
</script>

<svelte:element this={variant === "inline" ? "a" : "div"}
    class={clsx([
        "transition-colors",
        "duration-300",

        variant === "inline" && "text-primary",
        variant === "inline" && "hover:underline",

        variant === "block" && "block",
        variant === "block" && "rounded-xl",
        variant === "block" && "cursor-pointer",
        variant === "block" && "hover:bg-gray-200",
    ])}
    href={variant === "inline" ? href : null}
    aria-label={ariaLabel}
    data-testId={ariaLabel}
    title={title}
    tabindex="0"
    role="button"
    on:click={variant === "block"
        ? () => window.location.href = href
        : null
    }
>
    <slot />
</svelte:element>