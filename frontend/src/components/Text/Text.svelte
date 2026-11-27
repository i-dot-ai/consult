<script lang="ts">
  import clsx from "clsx";

  let { children } = $props();
</script>

<p class={clsx(["mb-4", "text-lg", "text-text-dark-25"])}>
  {@render children()}
</p>
