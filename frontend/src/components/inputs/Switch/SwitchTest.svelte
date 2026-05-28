<script>
  import Switch from "./Switch.svelte";

  let {
    id = "",
    label = "",
    value = false,
    handleChange = () => {},
    labelSlot = "",
  } = $props();
</script>

{#if labelSlot}
  {#snippet labelContent()}
    <p>{labelSlot}</p>
  {/snippet}
  <Switch {id} label={labelContent} {value} {handleChange} />
{:else}
  <Switch {id} {label} {value} {handleChange} />
{/if}
