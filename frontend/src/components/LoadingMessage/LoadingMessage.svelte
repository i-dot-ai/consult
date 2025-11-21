<script lang="ts">
  import { slide } from "svelte/transition";

  import LoadingIndicator from "../LoadingIndicator/LoadingIndicator.svelte";

  interface Props {
    message?: string;
  }

  let {
    message = "",
  }: Props = $props();
</script>

<div transition:slide class="my-8">
  <LoadingIndicator size="5rem" />
  <p class="text-center text-neutral-500">
    {message || "Loading..."}
  </p>
</div>