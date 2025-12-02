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
    variant?: "light" | "gray";
  }

  let { title, content, variant = "light" }: Props = $props();

  let expanded = $state(false);
</script>

<Button
  variant={variant === "gray" ? "gray" : "default"}
  handleClick={() => (expanded = !expanded)}
  fullWidth={true}
>
  <div class="flex w-full items-center justify-between gap-2">
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
      variant === "light" && "bg-white",
      variant === "gray" && "bg-neutral-100",
      "rounded-b-lg border border-t-0 border-neutral-300 p-4",
    ])}
  >
    {@render content()}
  </div>
{/if}
