<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";
  import { type Snippet } from "svelte";

  import Button from "../inputs/Button/Button.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import ChevronRight from "../svg/material/ChevronRight.svelte";

  interface Props {
    title: Snippet;
    content: Snippet;
  }

  let { title, content }: Props = $props();

  let expanded = $state(false);
</script>

<Button
  variant="default"
  handleClick={() => (expanded = !expanded)}
  fullWidth={true}
>
  <div class="flex justify-between items-center gap-2 w-full">
    {@render title()}

    <div class={clsx(["transition-transform", expanded && "rotate-90"])}>
      <MaterialIcon color="fill-neutral-500">
        <ChevronRight />
      </MaterialIcon>
    </div>
  </div>
</Button>

{#if expanded}
  <div
    transition:slide
    class={clsx([
      "bg-white p-4 border border-neutral-300 border-t-0 rounded-b-lg",
    ])}
  >
    {@render content()}
  </div>
{/if}
