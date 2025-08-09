<script lang="ts">
    import clsx from "clsx";

    export let variant: "default" | "ghost" | "primary" = "default";
    export let handleClick = () => {};
    export let disabled: boolean = false;
    export let fullWidth: boolean = false;
</script>

<button
    class={clsx([
        fullWidth && "w-full",
        "self-start",
        "cursor-pointer",
        "rounded-md",
        "py-1",
        "px-2",
        variant !== "ghost" && "border",
        variant === "primary" && "text-white",
        variant === "primary" && "bg-primary",
        "border-gray-300",
        "transition-colors",
        "duration-300",
        "flex",
        "gap-1",
        "items-center",
        "hover:bg-gray-100",
        variant === "primary" && "hover:text-primary",
        variant === "primary" && "hover:border-primary",

        disabled && "disabled:bg-gray-200",
        disabled && "disabled:text-gray-400",
        disabled && "disabled:cursor-not-allowed",
        disabled && "disabled:hover:bg-gray-200",
        disabled && "disabled:hover:border-gray-300",
        disabled && "disabled:hover:text-gray-400",
    ])}
    disabled={disabled}
    on:click={handleClick}
>
    <slot />
</button>