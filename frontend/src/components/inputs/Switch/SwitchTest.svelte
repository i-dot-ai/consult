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
  <Switch {id} {label} {value} {handleChange}>
    {#snippet labelSnippet()}
      <p>{labelSlot}</p>
    {/snippet}
  </Switch>
{:else}
  <Switch {id} {label} {value} {handleChange} />
{/if}
