<script lang="ts">
  import clsx from "clsx";

  import type { Component } from "svelte";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import Title from "../../Title.svelte";

  interface Props {
    text: string;
    currentStep: number;
    totalSteps: number;
    Icon: Component;
  }

  let { text = "", currentStep, totalSteps, Icon }: Props = $props();

  let stepsIndeces = $derived([...Array(totalSteps).keys()]);

  function isDotActive(stepIndex: number) {
    return stepIndex + 1 === currentStep;
  }
</script>

{#snippet dot(active: boolean)}
  <div
    class={clsx([
      "rounded-full",
      "h-2 w-2",
      active ? "bg-secondary" : "bg-neutral-200",
      "transition-colors",
    ])}
    data-testid={active ? "dot-active" : "dot-inactive"}
  ></div>
{/snippet}

<div class="flex gap-4">
  <div
    class={clsx([
      "bg-secondary",
      "w-12",
      "h-12",
      "rounded-full",
      "flex",
      "justify-center",
      "items-center",
      "shrink-0",
    ])}
  >
    <MaterialIcon size="2rem">
      <Icon />
    </MaterialIcon>
  </div>

  <div>
    <Title level={1}>
      <span class="font-[500]">
        Step {currentStep} of {totalSteps}: {text}
      </span>
    </Title>

    <div
      class={clsx([
        "flex",
        "gap-2",
        "items-center",
        "ml-1",
        "mt-1.5",
        "flex-wrap",
      ])}
    >
      {#each stepsIndeces as stepIndex (stepIndex)}
        {@render dot(isDotActive(stepIndex))}
      {/each}
    </div>
  </div>
</div>
