<script lang="ts">
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Error from "../../svg/material/Error.svelte";
  import QuickReferenceAll from "../../svg/material/QuickReferenceAll.svelte";
  import Text from "../../Text/Text.svelte";
  import Title from "../../Title.svelte";

  interface Props {
    status?: 404 | 500;
  }

  let { status = 404 }: Props = $props();

  const TITLES: Record<404 | 500, string> = {
    404: "404 Not Found",
    500: "500 Internal Server Error",
  };

  const BODIES: Record<404 | 500, string> = {
    404: "The page you requested could not be found",
    500: "Something went wrong",
  };
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
      {TITLES[status]}
    </span>
  </Title>
  <Text>
    <span class="block text-center">
      {BODIES[status]}
    </span>
  </Text>
</div>
