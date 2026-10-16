<script lang="ts">
  import clsx from "clsx";

  import type { Component } from "svelte";

  import MaterialIcon from "../MaterialIcon.svelte";
  import Tag from "../Tag/Tag.svelte";


  export interface TimelineItem {
    Icon: Component;
    TagIcon?: Component;
    smallText: string;
    titleText: string;
    bodyText: string;
    tagText?: string;
  }

  interface Props {
    items: TimelineItem[];
  }

  let {
    items = [],
  }: Props = $props();
</script>

{#snippet itemCard(
  { Icon, TagIcon, smallText, titleText, bodyText, tagText }: TimelineItem,
  isLast: boolean,
)}
  <div class={clsx([
    "flex",
    "gap-4",
    "relative",
    "mb-8",
    "-ml-10",
    "pl-4",
  ])}>
    <div class={clsx([
      "flex",
      "justify-center",
      "items-center",
      "w-12",
      "h-12",
      "p-2",
      "rounded-full",
      "border",
      "border-neutral-300",
      "bg-white"
    ])}>
      <MaterialIcon size="2rem" color="fill-neutral-500">
        <Icon />
      </MaterialIcon>
    </div>
    <div class={clsx([
      isLast && [
        "before:content-['']",
        "before:w-3",
        "before:h-10",
        "before:block",
        "before:bg-white",
        "before:absolute",
        "before:left-8",
        "before:top-12",
      ]
    ])}>
      <small>{smallText}</small>

      <h3>{titleText}</h3>

      {#if tagText}
        <div class="my-2">
          <Tag border={true}>
            <span class="flex items-center gap-2">
              {#if TagIcon}
                <MaterialIcon color="fill-neutral-500" size="0.8rem">
                  <TagIcon />
                </MaterialIcon>  
              {/if}

              {tagText}
            </span>
          </Tag>
        </div>
      {/if}
      
      <p class="text-neutral-500 text-sm">
        {bodyText}
      </p>
    </div>
  </div>
{/snippet}

<div class="ml-8 border-l">
  {#each items as item, i (i)}
    {@const isLast = i === items.length - 1}

    {@render itemCard(item, isLast)}
  {/each}
</div>