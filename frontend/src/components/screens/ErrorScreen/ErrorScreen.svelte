<script lang="ts">
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Error from "../../svg/material/Error.svelte";
  import QuickReferenceAll from "../../svg/material/QuickReferenceAll.svelte";
  import Text from "../../Text/Text.svelte";
  import Title from "../../Title.svelte";

  interface Props {
    status: 404 | 500;
  }

  let { status = 404 }: Props = $props();

  function getTitle() {
    if (status === 404) {
      return "404 Not Found";
    }
    if (status === 500) {
      return "500 Internal Server Error";
    }
  }

  function getBody() {
    if (status === 404) {
      return "The page you requested could not be found";
    }
    if (status === 500) {
      return "Something went wrong";
    }
  }
</script>

{#snippet icon()}
  {#if status === 404}
    <QuickReferenceAll />
  {:else if status === 500}
    <Error />
  {/if}
{/snippet}

<div class="mt-16">
  <div class="my-8 flex items-center justify-center">
    <MaterialIcon size="5rem" color="fill-neutral-500">
      {@render icon()}
    </MaterialIcon>
  </div>

  <Title level={1} context="public">
    <span class="block text-center text-primary">
      {getTitle()}
    </span>
  </Title>
  <Text>
    <span class="block text-center">
      {getBody()}
    </span>
  </Text>
</div>
