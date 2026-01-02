<script lang="ts">
  import { slide } from "svelte/transition";

  import MaterialIcon from "../MaterialIcon.svelte";
  import Help from "../svg/material/Help.svelte";
  import Search from "../svg/material/Search.svelte";

  interface Props {
    body: string;
    title?: string;
    variant?: "default" | "archive";
  }
  let { title = "", body = "", variant = "default" }: Props = $props();
</script>

<div transition:slide>
  {#if variant === "default"}
    <div class="my-16 flex flex-col items-center justify-center">
      <MaterialIcon color="fill-neutral-200" size="4rem">
        <Search />
      </MaterialIcon>

      <p class="text-xl">{title}</p>
      <p class="text-neutral-600">{body}</p>
    </div>
  {:else if variant === "archive"}
    <div class="pb-8 pt-12">
      <div class="mx-auto mb-2 w-max">
        <MaterialIcon color="fill-neutral-500" size="2rem">
          <Help />
        </MaterialIcon>
      </div>
      <p class="text-center text-sm text-neutral-500">
        {body}
      </p>
    </div>
  {/if}
</div>
