<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import { Routes } from "../../../global/routes";

  import WithExternalClick from "../../WithExternalClick/WithExternalClick.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Person from "../../svg/material/Person.svelte";

  let expanded = $state(false);
</script>

{#snippet link(text, url)}
  <a href={url} class="block hover:text-primary">
    <Button variant="ghost" fullWidth={true}>
      <span class="w-full text-start ">
        {text}
      </span>
    </Button>
  </a>
{/snippet}

<div class="relative">
  <WithExternalClick onExternalClick={() => expanded = false}>
    <button
      title="Profile links"
      aria-label="View profile links"
      onclick={() => (expanded = !expanded)}
      class={clsx([
        "flex",
        "justify-center",
        "items-center",
        "w-8",
        "h-8",
        "ml-2",
        "p-1",
        "border-2",
        "border-transparent",
        "rounded-full",
        "bg-neutral-700",
        "text-xs",
        "transition-colors",
        "hover:border-primary",
        "hover:bg-neutral-600",
      ])}
    >
      <MaterialIcon size="1.5rem" color="fill-white">
        <Person />
      </MaterialIcon>
    </button>

    {#if expanded}
      <div
        transition:slide
        class={clsx([
          "absolute",
          "top-8",
          "right-0",
          "text-sm",
          "bg-white",
          "shadow-lg",
          "whitespace-nowrap",
          "min-w-32",
        ])}
      >
        {@render link("Profile", Routes.Profile)}

        <hr />

        {@render link("Sign Out", Routes.SignOut)}
      </div>    
    {/if}
  </WithExternalClick>
</div>
