<script lang="ts">
  import type { Component } from "svelte";

  import Title from "../../Title.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import OutsideConsultTag from "../OutsideConsultTag/OutsideConsultTag.svelte";

  interface Props {
    stepNo: number;
    title: string;
    Icon: Component;
    maxStepNo?: number;
    isExternal?: boolean;
  }

  const {
    stepNo,
    title,
    Icon,
    maxStepNo = 6,
    isExternal = false,
  }: Props = $props();

  function clampStepNumberText(stepNo: number, maxStepNo: number) {
    if (stepNo < 1) {
      return 1;
    } else if (stepNo > maxStepNo) {
      return maxStepNo;
    }
    return stepNo;
  }
</script>

<div class="flex gap-4 items-center flex-wrap">
  <div
    class="rounded-full border border-neutral-300 bg-neutral-100 w-12 h-12 flex justify-center items-center"
  >
    <div class="shrink-0">
      <MaterialIcon color="fill-neutral-500" size="1.6rem">
        <Icon />
      </MaterialIcon>
    </div>
  </div>
  <div>
    <small class="text-neutral-500"
      >Step {clampStepNumberText(stepNo, maxStepNo)} of {maxStepNo}</small
    >
    <div class="flex gap-2 items-center flex-wrap">
      <Title>{title}</Title>
      {#if isExternal}
        <OutsideConsultTag />
      {/if}
    </div>
  </div>
</div>
