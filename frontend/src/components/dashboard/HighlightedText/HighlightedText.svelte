<script lang="ts">
  interface Props {
    text: string;
    highlight: string;
    testId?: string;
  }

  let { text, highlight, testId }: Props = $props();

  const parts = $derived<string[]>(
    text && highlight ? text.split(new RegExp(`(${highlight})`, "gi")) : [text],
  );
</script>

{#each parts as part, i (i)}
  {#if highlight.toLowerCase() === part.toLowerCase()}
    <span
      class="bg-yellow-300"
      data-testid={testId ? testId : "highlighted-text"}>{part}</span
    >
  {:else}{part}{/if}
{/each}
