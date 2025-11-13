<script lang="ts">
  import { slide } from "svelte/transition";

  import MaterialIcon from "../MaterialIcon.svelte";
  import Help from "../svg/material/Help.svelte";
  import Search from "../svg/material/Search.svelte";

  interface Props {
    title?: string;
    body: string;
    variant: "default" | "archive";
  }
  let { title = "", body = "", variant = "default" }: Props = $props();
</script>

<div transition:slide>
  {#if variant === "default"}
    <div class="flex justify-center items-center flex-col my-16">
      <MaterialIcon color="fill-neutral-200" size="4rem">
        <Search />
      </MaterialIcon>

      <p class="text-xl">{title}</p>
      <p class="text-neutral-600">{body}</p>
    </div>
  {:else if variant === "archive"}
    <div class="pt-12 pb-8">
      <div class="w-max mx-auto mb-2">
        <MaterialIcon color="fill-neutral-500" size="2rem">
          <Help />
        </MaterialIcon>
      </div>
      <p class="text-sm text-center text-neutral-500">
        {body}
      </p>
    </div>
  {/if}
</div>