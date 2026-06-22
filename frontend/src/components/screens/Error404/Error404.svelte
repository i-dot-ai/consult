<script lang="ts">
  import MaterialIcon from "../../MaterialIcon.svelte";
  import QuickReferenceAll from "../../svg/material/QuickReferenceAll.svelte";
  import Text from "../../Text/Text.svelte";
  import Title from "../../Title.svelte";
</script>

<div class="mt-16">
  <div class="flex justify-center items-center my-8">
    <MaterialIcon size="5rem" color="fill-neutral-500">
      <QuickReferenceAll />
    </MaterialIcon>
  </div>

  <Title level={1} context="public">
    <span class="block text-primary text-center">
      404 Not Found
    </span>
  </Title>
  <Text>
    <span class="block text-center">
      The page you requested could not be found
    </span>
  </Text>
</div>