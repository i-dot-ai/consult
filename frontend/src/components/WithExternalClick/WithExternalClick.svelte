<script lang="ts">
  import { onDestroy, onMount, type Snippet } from "svelte";

  interface Props {
    onExternalClick: () => void;
    children: Snippet;
  }

  let {
    onExternalClick,
    children,
  }: Props = $props();

  let containerEl: HTMLElement | undefined = $state();

  onMount(() => {
    window.addEventListener("click", handleOutsideClick);
  });

  onDestroy(() => {
    window.removeEventListener("click", handleOutsideClick);
  });

  function handleOutsideClick(e: MouseEvent) {
    if (containerEl && !containerEl.contains(e.target as HTMLElement)) {
      onExternalClick();
    }
  }
</script>

<div bind:this={containerEl}>
  {@render children()}
</div>