<script lang="ts">
  import clsx from "clsx";

  import Title from "../../Title.svelte";
  import Checkbox from "../../inputs/Checkbox/Checkbox.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import { slide } from "svelte/transition";

  interface Item {
    id: string;
    title: string;
    text: string;
    checked: boolean;
  }

  interface Props {
    items: Item[];
    onChange: (id: string, checked: boolean) => void;
  }

  let expanded: string[] = $state([]);
  let { items = [], onChange }: Props = $props();

  function getCheckboxId(id: string) {
    return `checklist-${id}`;
  }
</script>

<div class={clsx(["border", "border-secondary", "p-4", "px-4", "rounded-lg"])}>
  <Title level={3}>
    <span class={clsx(["block", "text-sm", "font-[500]", "mb-2"])}>
      Before uploading, tick off each requirement as you complete it:
    </span>
  </Title>

  <div class="mt-4">
    {#if items.length === 0}
      <p class={clsx(["w-full", "text-neutral-500", "text-sm"])}>
        No checklist items available
      </p>
    {/if}

    {#each items as item (item.id)}
      <div
        class={clsx(
          "bg-neutral-100",
          "text-xs",
          "p-2",
          "rounded-lg",
          "flex",
          "gap-2",
          "mb-3",
          "last:mb-0",
        )}
      >
        <Checkbox
          id={getCheckboxId(item.id)}
          size="sm"
          hideLabel={true}
          value={item.id}
          checked={item.checked}
          onchange={(checked, value) => onChange(value!, checked)}
        />

        <div>
          <label for={getCheckboxId(item.id)} class="hover:cursor-pointer">
            <Title level={4}>
              <span class={clsx(["block", "mb-1"])}>
                {item.title}
              </span>
            </Title>
          </label>

          <Button variant="ghost" handleClick={() => {
            if (expanded.includes(item.id)) {
              expanded = expanded.filter(itemId => itemId !== item.id);
            } else {
              expanded = [...expanded, item.id];
            }
          }}>
            <span class="text-secondary hover:underline -ml-2">
              {expanded.includes(item.id) ? "Hide example" : "Show me an example"}
            </span>
          </Button>

          {#if expanded.includes(item.id)}
            <div transition:slide class="bg-white text-neutral-500 rounded-lg p-2 my-2">
              {@html item.text}
            </div>
          {/if}
        </div>
      </div>
    {/each}
  </div>
</div>
