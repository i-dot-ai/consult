<script lang="ts">
  import MaterialIcon from "./MaterialIcon.svelte";
</script>

<div class="flex justify-start items-center gap-2 bg-pink-50 p-2 rounded-lg">
  {#if $$slots.icon}
    <MaterialIcon color="fill-pink-700">
      <slot name="icon" />
    </MaterialIcon>
  {/if}

  <div class="text-pink-700 w-full">
    <slot />
  </div>
</div>
