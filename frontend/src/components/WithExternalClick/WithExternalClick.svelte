<script lang="ts">
  import { type Snippet } from "svelte";

  interface Props {
    onExternalClick: () => void;
    children: Snippet;
  }

  let {
    onExternalClick,
    children,
  }: Props = $props();

  let containerEl: HTMLElement | undefined = $state();

  $effect(() => {
    addListeners();
    return () => removeListeners();
  })

  function addListeners() {
    window.addEventListener("click", handleOutsideClick);
  }
  function removeListeners() {
    window.addEventListener("click", handleOutsideClick);
  }

  function handleOutsideClick(e: MouseEvent) {
    if (containerEl && !containerEl.contains(e.target as HTMLElement)) {
      onExternalClick();
    }
  }
</script>

<div bind:this={containerEl}>
  {@render children()}
</div>