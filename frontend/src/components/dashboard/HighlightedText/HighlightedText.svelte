<script lang="ts">
  interface Props {
    text: string;
    highlight: string;
  }

  let { text, highlight }: Props = $props();

  const parts = $derived<string[]>(
    text && highlight ? text.split(new RegExp(`(${highlight})`, "gi")) : [text],
  );
</script>

{#each parts as part, i (i)}
  {#if highlight.toLowerCase() === part.toLowerCase()}
    <span class="bg-yellow-300">{part}</span>
  {:else}{part}{/if}
{/each}
