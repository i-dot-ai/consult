<script lang="ts">
  import clsx from "clsx";

  let { children } = $props();
</script>

<ol
  class={clsx([
    "list-decimal",
    "pl-6",
    "mb-8",
    "text-neutral-700",
    "space-y-2",
    "[&>li]:text-lg",
  ])}
>
  {@render children()}
</ol>
