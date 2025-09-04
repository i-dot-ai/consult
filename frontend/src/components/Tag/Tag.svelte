<script lang="ts">
    import clsx from "clsx";

    import { type Snippet } from 'svelte';


    interface Props {
        variant?: "default" | "warning" | "primary";
        children: Snippet,
    }
    let {
        variant="default",
        children,
    }: Props = $props();
</script>

<div class={clsx([
    "flex",
    "justify-between",
    "items-center",
    "gap-2",
    "rounded-md",
    "w-max",
    "py-0.5",
    "px-2",
    "text-xs",
    variant === "default" && "bg-neutral-100",
    variant === "default" && "text-neutral-800",

    variant === "primary" && "bg-primary",
    variant === "primary" && "text-white",

    variant === "warning" && "text-yellow-700",
    variant === "warning" && "bg-yellow-100",
])}>
    {@render children()}
</div>