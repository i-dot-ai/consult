<script lang="ts">
  type Props = {
    text: string;
    textToHighlight: string;
  };

  let { text, textToHighlight }: Props = $props();
  let textParts = $derived(
    textToHighlight
      ? text.split(new RegExp(`(${textToHighlight})`, "gi"))
      : [text],
  );
</script>

{#each textParts as textPart, i (i)}
  {#if textToHighlight && textPart.toLowerCase() === textToHighlight.toLowerCase()}
    <span class="bg-yellow-300">{textPart}</span>
  {:else}
    {textPart}
  {/if}
{/each}
