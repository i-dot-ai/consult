<script lang="ts">
  import MaterialIcon from "./MaterialIcon.svelte";
</script>

<div class="flex items-center justify-start gap-2 rounded-lg bg-pink-50 p-2">
  {#if $$slots.icon}
    <MaterialIcon color="fill-pink-700">
      <slot name="icon" />
    </MaterialIcon>
  {/if}

  <div class="w-full text-pink-700">
    <slot />
  </div>
</div>
