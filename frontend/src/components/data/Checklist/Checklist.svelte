<script lang="ts">
  import clsx from "clsx";

  import Title from "../../Title.svelte";
  import Checkbox from "../../inputs/Checkbox/Checkbox.svelte";

  interface Item {
    id: string;
    title: string;
    text: string;
  }

  interface Props {
    items: Item[];
  }

  let { items = [] }: Props = $props();

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
      <p class="w-full text-neutral-500 text-sm">No checklist items available</p>
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
        />

        <label for={getCheckboxId(item.id)} class="hover:cursor-pointer">
          <Title level={4}>
            <span class={clsx(["block", "font-[500]", "mb-1"])}>
              {item.title}
            </span>
          </Title>
          <p class="text-neutral-600">
            {item.text}
          </p>
        </label>
      </div>
    {/each}
  </div>
</div>
