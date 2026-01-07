<script lang="ts">
  import clsx from "clsx";

  import { type Component } from "svelte";

  import { OnboardingKeys } from "../../../global/types";

  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Help from "../../svg/material/Help.svelte";
  import UnknownDocument from "../../svg/material/UnknownDocument.svelte";
  import ChatBubble from "../../svg/material/ChatBubble.svelte";
  import Shield from "../../svg/material/Shield.svelte";
  import Replay from "../../svg/material/Replay.svelte";

  // TODO: update urls
  interface Item {
    icon: Component,
    title: string,
    subtitle: string,
    url?: string,
    handleClick?: (e: MouseEvent) => void,
  }
  const ITEMS: Item[] = [
    {
      icon: Replay,
      title: "Walkthrough",
      subtitle: "Interactive tutorial for Theme Sign Off",
      handleClick: () => {
        localStorage.removeItem(OnboardingKeys.themeSignoff);
        localStorage.removeItem(OnboardingKeys.themeSignoffArchive);
        window.location.reload();
      },
    },
    {
      icon: UnknownDocument,
      title: "Guidance",
      subtitle: "View help documentation",
      url: "#",
    },
    {
      icon: ChatBubble,
      title: "Feedback",
      subtitle: "Send us your feedback",
      url: "#",
    },
    {
      icon: Shield,
      title: "Privacy notice",
      subtitle: "View our privacy policy",
      url: "#",
    },
  ];
</script>

{#snippet renderItem({ icon, title, subtitle, url, handleClick }: Item)}
  <li class="group">
    <Button variant="ghost" href={url || "#"} handleClick={handleClick} fullWidth={true} fixedHoverColor={true}>
      <div class="flex items-center gap-2">
        <div
          class={clsx([
            "rounded-full",
            "transition-colors",
            "bg-neutral-100",
            "group-hover:bg-secondary",
            "p-2",
            "my-2",
          ])}
        >
          <MaterialIcon color="fill-neutral-500">
            <svelte:component this={icon} />
          </MaterialIcon>
        </div>
        <div>
          <h3 class="text-xs">{title}</h3>
          <p class="text-xs text-neutral-500">{subtitle}</p>
        </div>
      </div>
    </Button>
  </li>
{/snippet}

<div class="flex items-center justify-between gap-8 p-2">
  <div class="flex items-center gap-2">
    <div class="rounded-full bg-secondary p-2">
      <MaterialIcon>
        <Help />
      </MaterialIcon>
    </div>
    <div>
      <h2 class="text-sm">Help & Support</h2>
      <p class="text-xs text-neutral-500">Quick access to help resources</p>
    </div>
  </div>
</div>

<div>
  <ul class="px-4">
    {#each ITEMS as item, i (i)}
      {@render renderItem(item)}
    {/each}
  </ul>
</div>

<style>
  .group:hover :global(svg) {
    fill: white;
  }
</style>
