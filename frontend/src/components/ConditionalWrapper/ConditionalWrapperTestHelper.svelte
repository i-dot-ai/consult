<script lang="ts">
  import ConditionalWrapper from "./ConditionalWrapper.svelte";

  export let element: string | boolean = false;
  export let condition: boolean = false;
  export let content: string = "";
</script>

<ConditionalWrapper {element} {condition}>
  <p>{content}</p>
</ConditionalWrapper>
