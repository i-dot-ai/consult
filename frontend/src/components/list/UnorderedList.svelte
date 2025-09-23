<script lang="ts">
    import clsx from "clsx";
    let { children } = $props();
</script>

<ul class={clsx([
    "list-disc",
    "pl-6",
    "mb-6",
    "text-neutral-700",
    "space-y-2",
    "[&>li]:text-lg"
])}>
    {@render children()}
</ul>