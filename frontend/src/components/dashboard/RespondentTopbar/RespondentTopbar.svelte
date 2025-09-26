<script lang="ts">
  import clsx from "clsx";

  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import ArrowForward from "../../svg/material/ArrowForward.svelte";

  import { type Snippet } from "svelte";

  interface Props {
    title: string;
    backUrl: string;
    children?: Snippet;
  }

  let { title = "", backUrl = "", children }: Props = $props();
</script>

<div
  class={clsx([
    "flex",
    "items-center",
    "justify-center",
    "md:justify-between",
    "flex-wrap",
    "gap-4",
    "mb-4",
  ])}
>
  <div class="flex items-center gap-4">
    <div class="m-auto">
      <Button
        size="xs"
        variant="ghost"
        handleClick={() => (location.href = backUrl)}
      >
        <div class="rotate-180">
          <MaterialIcon color="fill-neutral-700">
            <ArrowForward />
          </MaterialIcon>
        </div>

        <span>Back to Analysis</span>
      </Button>
    </div>

    <h1 class="font-bold text-lg">{title}</h1>
  </div>

  <div class="flex items-center gap-4">
    {#if children}
      {@render children()}
    {/if}
  </div>
</div>
