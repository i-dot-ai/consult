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
    <p slot="label">{labelSlot}</p>
  </Switch>
{:else}
  <Switch {id} {label} {value} {handleChange} />
{/if}
