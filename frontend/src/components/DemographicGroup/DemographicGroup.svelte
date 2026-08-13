<script lang="ts">
  import clsx from "clsx";
  import { slide } from "svelte/transition";

  import { getPercentage } from "../../global/utils.ts";
  import Panel from "../dashboard/Panel/Panel.svelte";
  import Button from "../inputs/Button/Button.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import KeyboardArrowDown from "../svg/material/KeyboardArrowDown.svelte";

  import { demoFilters } from "../../global/state.svelte.ts";
  import Progress from "../Progress/Progress.svelte";
  import type { DemoOptionsResponseItem } from "../../global/types.ts";

  interface Props {
    category: string;
    items: DemoOptionsResponseItem[];
    countsLoading?: boolean;
  }

  let { category, items, countsLoading = false }: Props = $props();

  let expanded = $state(true);

  let totalCount = $derived(items.reduce((sum, item) => sum + item.count, 0));
</script>

<section>
  <Panel level={2} border={true} bg={true}>
    <Button
      variant="ghost"
      size="sm"
      fullWidth={true}
      handleClick={() => (expanded = !expanded)}
    >
      <div class="flex w-full justify-between">
        <h3 class="truncate" title={category}>
          {category}
        </h3>

        <div class={clsx(["transition-transform", !expanded && "-rotate-90"])}>
          <MaterialIcon color="fill-neutral-400" size="1.3rem">
            <KeyboardArrowDown />
          </MaterialIcon>
        </div>
      </div>
    </Button>

    {#each items as item (item.id)}
      {@const percentage = getPercentage(item.count, totalCount)}

      {#if expanded}
        <div transition:slide class="my-1">
          <Button
            variant="ghost"
            size="xs"
            fullWidth={true}
            handleClick={() => demoFilters.update(item.id)}
            highlighted={demoFilters.filters.includes(item.id)}
            highlightVariant="light"
          >
            <div class="demo-filter relative w-full pb-1">
              <div class="flex items-center justify-between gap-1">
                <span class="grow truncate text-left" title={item.value}>
                  {item.value ? item.value.replaceAll("'", "") : ""}
                </span>

                {#if countsLoading}
                  <span
                    class="blink select-none rounded-sm bg-neutral-200 text-neutral-200"
                  >
                    0000
                  </span>
                  <div class="w-12 shrink-0">
                    <Progress value={0} />
                  </div>
                {:else}
                  <span class="text-right">
                    {item.count}
                  </span>

                  <div title={`${percentage}%`} class="w-12 shrink-0">
                    <Progress value={percentage} />
                  </div>
                {/if}
              </div>
            </div>
          </Button>
        </div>
      {/if}
    {/each}
  </Panel>
</section>
