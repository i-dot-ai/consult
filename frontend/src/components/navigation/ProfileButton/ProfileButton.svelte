<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import WithExternalClick from "../../WithExternalClick/WithExternalClick.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Person from "../../svg/material/Person.svelte";

  interface Props {
    isSignedIn: boolean;
  }

  let { isSignedIn = false }: Props = $props();

  let expanded = $state(false);

  function handleSignOut() {
    // Navigate to server-side logout endpoint which:
    // 1. Clears all cookies server-side (including HttpOnly ALB cookies)
    // 2. Redirects to SSO sign-out
    window.location.href = "/api/logout";
  }
</script>

{#snippet buttonElement(text: string, onclick: () => void)}
  <button {onclick} class="block w-full hover:text-primary">
    <Button variant="ghost" fullWidth={true}>
      <span class="w-full text-start">
        {text}
      </span>
    </Button>
  </button>
{/snippet}

<div class="relative m-auto w-max">
  <WithExternalClick onExternalClick={() => (expanded = false)}>
    <button
      title="Profile links"
      aria-label="View profile links"
      aria-controls="profile-panel"
      aria-expanded={expanded ? "true" : "false"}
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
        id="profile-panel"
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
        <!-- TODO: Enabled after profile page is implemented -->
        <!-- {@render linkElement("Profile", Routes.Profile)}  -->
        <!-- <hr /> -->

        {#if isSignedIn}
          {@render buttonElement("Sign Out", handleSignOut)}
        {/if}
      </div>
    {/if}
  </WithExternalClick>
</div>
