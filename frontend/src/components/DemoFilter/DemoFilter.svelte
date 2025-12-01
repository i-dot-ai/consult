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
  import type {
    DemoData,
    DemoOption,
    DemoOptionsResponse,
    DemoTotalCounts,
  } from "../../global/types.ts";

  interface Props {
    category?: string;
    demoOptions?: DemoOption;
    demoData?: DemoData;
    totalCounts?: DemoTotalCounts;
    demoOptionsData?: DemoOptionsResponse;
    skeleton?: boolean;
  }

  let {
    category = "",
    demoOptions = {},
    demoData = {},
    totalCounts = {},
    demoOptionsData = [],
    skeleton = false,
  }: Props = $props();

  let expanded = $state(true);
</script>

<section>
  <Panel level={2} border={true} bg={skeleton ? false : true}>
    {#if skeleton}
      <h3 class="blink w-max select-none bg-neutral-100 text-neutral-100">
        skeleton
      </h3>
    {:else}
      <Button
        variant="ghost"
        size="sm"
        fullWidth={true}
        handleClick={() => (expanded = !expanded)}
      >
        <div class="flex w-full justify-between">
          <h3 class="truncate" title={category}>
            {skeleton ? "Skeleton" : category}
          </h3>

          <div
            class={clsx(["transition-transform", !expanded && "-rotate-90"])}
          >
            <MaterialIcon color="fill-neutral-400" size="1.3rem">
              <KeyboardArrowDown />
            </MaterialIcon>
          </div>
        </div>
      </Button>
    {/if}

    {#if skeleton}
      <div class="my-1">
        <div class="demo-filter relative w-full pb-3">
          <div class="mb-1 grid grid-cols-3 gap-1">
            <span
              class="blink select-none bg-neutral-100 text-left text-neutral-100"
              >skeleton</span
            >
            <span
              class="blink select-none bg-neutral-100 text-right text-neutral-100"
              >000%</span
            >
            <span
              class="blink select-none bg-neutral-100 text-right text-neutral-100"
              >00000</span
            >
          </div>
          <div class="blink w-full select-none bg-neutral-100 text-neutral-100">
            {"_".repeat(10)}
          </div>
        </div>
      </div>
    {:else}
      {#each demoOptions[category] as rowKey (rowKey)}
        {@const rowValue =
          (demoData[category] && demoData[category][rowKey]) || 0}
        {@const percentage = getPercentage(rowValue, totalCounts[category])}
        {@const demographicOption = demoOptionsData.find(
          (option) => option.name === category && option.value === rowKey,
        )}

        {#if expanded}
          <div transition:slide class="my-1">
            <Button
              variant="ghost"
              size="xs"
              fullWidth={true}
              handleClick={() =>
                demographicOption?.id &&
                demoFilters.update(demographicOption.id)}
              highlighted={demographicOption?.id
                ? demoFilters.filters.includes(demographicOption.id)
                : false}
              highlightVariant="light"
            >
              <div class="demo-filter relative w-full pb-1">
                <div class="flex items-center justify-between gap-1">
                  <span class="grow truncate text-left" title={rowKey}>
                    {rowKey ? rowKey.replaceAll("'", "") : ""}
                  </span>

                  <span class="text-right">
                    {rowValue}
                  </span>

                  <div title={`${percentage}%`} class="w-12 shrink-0">
                    <Progress value={percentage} />
                  </div>
                </div>
              </div>
            </Button>
          </div>
        {/if}
      {/each}
    {/if}
  </Panel>
</section>
