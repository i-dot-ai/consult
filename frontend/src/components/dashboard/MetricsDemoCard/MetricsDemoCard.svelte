<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import Progress from "../../Progress/Progress.svelte";
  import Title from "../../Title.svelte";
  import Panel from "../Panel/Panel.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import ArrowForward from "../../svg/material/ArrowForward.svelte";
  import { getConsultationAnalysisUrl } from "../../../global/routes";

  interface MetricsDemoItem {
    title: string;
    count: number;
    percentage: number;
  }

  interface Props {
    consultationId: string;
    title: string;
    items?: MetricsDemoItem[];
    hideThreshold?: number;
  }

  let { consultationId = "", title = "", items = [], hideThreshold = 3 }: Props = $props();

  let displayAll: boolean = $state(false);
</script>

{#snippet cardItem(
  { title, count, percentage }: MetricsDemoItem,
  index: number,
)}
  {#if displayAll || index < hideThreshold}
    <div
      transition:slide
      class={clsx(["flex", "items-center", "gap-2", "my-2", "justify-between"])}
    >
      <p class="text-xs grow max-w-[60%]">{title}</p>

      <div class="flex items-center gap-2 justify-end">
        <span class="text-sm">{count.toLocaleString()}</span>
        <span class="text-xs text-primary">{percentage}%</span>
        <div class="w-[2rem]">
          <Progress value={percentage} />
        </div>
      </div>
    </div>
  {/if}
{/snippet}

<div
  transition:slide
  class={clsx([
    "metrics-demo-card",
    "col-span-12",
    "sm:col-span-6",
    "lg:col-span-4",
    "h-full",
  ])}
>
  <Panel bg={true} border={true}>
    <Title level={4} text={title} />

    {#each items as item, index}
      {@render cardItem(item, index)}
    {/each}

    {#if items.length > hideThreshold}
      <hr class="my-2 border-neutral-300" />

      <Button
        size="xs"
        variant="ghost"
        handleClick={() => location.href = getConsultationAnalysisUrl(consultationId)}
      >
        <div class="flex justify-center items-center gap-1">
          <span>View All {items.length}</span>

          <MaterialIcon color="fill-neutral-500">
            <ArrowForward />
          </MaterialIcon>
        </div>
      </Button>
    {/if}
  </Panel>
</div>
