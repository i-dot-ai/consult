<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import Person from "../../svg/material/Person.svelte";

  let expanded = $state(false);
</script>

<div class="relative">
  <button
    onclick={() => expanded = !expanded}
    class={clsx([
      "flex",
      "justify-center",
      "items-center",
      "w-8",
      "h-8",
      "ml-2",
      "p-1",
      "border-2",
      "border-transparent",
      "rounded-full",
      "bg-neutral-700",
      "text-xs",
      "transition-colors",
      "hover:border-primary",
      "hover:bg-neutral-600",
    ])}
  >
    <MaterialIcon size="1.5rem" color="fill-white">
      <Person />
    </MaterialIcon>
  </button>

  {#if expanded}
    <div transition:slide class={clsx([
      "absolute",
      "top-8",
      "right-0",
      "text-sm",
      "bg-white",
      "shadow-lg",
      "whitespace-nowrap",
      "p-2",
    ])}>
      Test Panel Content
    </div>
  {/if}
</div>