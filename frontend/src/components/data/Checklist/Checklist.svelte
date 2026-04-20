<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";
  import type { Snippet } from "svelte";

  import Title from "../../Title.svelte";
  import Checkbox from "../../inputs/Checkbox/Checkbox.svelte";
  import Button from "../../inputs/Button/Button.svelte";

  interface Item {
    id: string;
    title: string;
    text: string | Snippet;
    checked: boolean;
  }

  interface Props {
    title: string;
    items: Item[];
    onChange: (id: string, checked: boolean) => void;
  }

  let expanded: string[] = $state([]);
  let { title = "Checklist", items = [], onChange }: Props = $props();

  function getCheckboxId(id: string) {
    return `checklist-${id}`;
  }
</script>

<div>
  <Title level={3}>
    <span class={clsx(["block", "text-sm", "font-[500]", "mb-2"])}>
      {title}
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

        <div class={clsx(["w-full"])}>
          <div class={clsx(["flex", "justify-between", "gap-4", "w-full"])}>
            <label for={getCheckboxId(item.id)} class="hover:cursor-pointer">
              <Title level={4}>
                <span class={clsx(["block", "mb-1"])}>
                  {item.title}
                </span>
              </Title>
            </label>

            <Button
              variant="ghost"
              handleClick={() => {
                if (expanded.includes(item.id)) {
                  expanded = expanded.filter((itemId) => itemId !== item.id);
                } else {
                  expanded = [...expanded, item.id];
                }
              }}
              ariaControls={`${item.id}-details`}
              ariaLabel={`Show/Hide ${item.id}-details`}
            >
              <span class="-ml-2 text-nowrap text-secondary hover:underline">
                {expanded.includes(item.id)
                  ? "Hide example"
                  : "Show me an example"}
              </span>
            </Button>
          </div>

          {#if expanded.includes(item.id)}
            <div
              id={`${item.id}-details`}
              transition:slide
              class="my-2 rounded-lg bg-white p-2 text-neutral-500"
            >
              {#if typeof item.text === "string"}
                {item.text}
              {:else}
                {@render item.text()}
              {/if}
            </div>
          {/if}
        </div>
      </div>
    {/each}
  </div>
</div>
