<script lang="ts">
    import clsx from "clsx";

    export let variant: "default" | "ghost" = "default";
    export let handleClick = () => {};
</script>

<button
    class={clsx([
        "cursor-pointer",
        "rounded-md",
        "py-1",
        "px-2",
        variant === "ghost" ? "" : "border",
        "border-gray-300",
        "transition-colors",
        "duration-300",
        "flex",
        "gap-1",
        "items-center",
        "hover:bg-gray-100"
    ])}
    on:click={handleClick}
>
    <slot />
</button>