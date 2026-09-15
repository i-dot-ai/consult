<script lang="ts">
  import type { Component, Snippet } from 'svelte';
  import MaterialIcon from "../MaterialIcon.svelte";

  interface Props {
    children: Snippet;
    Icon?: Component;
  }

  let {
    Icon,
    children,
  }: Props = $props();
</script>

<div class="flex items-center justify-start gap-2 rounded-lg bg-pink-50 p-2">
  {#if Icon}
    <div data-testid="icon">
      <MaterialIcon color="fill-pink-700">
        <Icon />
      </MaterialIcon>
    </div>
  {/if}

  {#if children}
    <div class="w-full text-pink-700">
      {@render children()}
    </div>  
  {/if}
</div>
