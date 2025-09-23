<script lang="ts">
    import clsx from "clsx";

    let { children } = $props();
</script>

<p class={clsx([
    "mb-4",
    "text-lg",
    "text-neutral-700"
])}>
    {@render children()}
</p>
