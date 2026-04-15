<script lang="ts">
  import clsx from "clsx";

  import type { Component } from "svelte";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import ArrowForward from "../../svg/material/ArrowForward.svelte";

  interface Props {
    Icon: Component;
    steps: number | number[];
    title: string;
    subtitle: string;
    isActive?: boolean;
    showArrow?: boolean;
  }

  let {
    Icon,
    steps,
    title,
    subtitle,
    isActive = false,
    showArrow = true,
  }: Props = $props();

  function getStepsText(steps: Props["steps"]) {
    return Array.isArray(steps)
      ? `Steps ${steps.slice(0, steps.length - 1).join(", ")} & ${steps.at(steps.length - 1)}`
      : `Step ${steps.toString()}`;
  }
</script>

<div
  class={clsx([
    "relative",
    "flex",
    "flex-col",
    "gap-1",
    "items-center",
    "w-[15rem]",
    !isActive && "opacity-50",
    "transition-opacity",
    "duration-500",
  ])}
  aria-current={isActive ? "true" : undefined}
  data-testid="intro-card"
>
  <div
    class={clsx([
      isActive ? "bg-secondary" : "bg-teal-100",
      "p-2",
      "rounded-full",
      "w-12",
      "h-12",
      "shadow-lg",
    ])}
  >
    <div class={clsx([isActive && "growshrink"])}>
      <MaterialIcon
        size="2rem"
        color={isActive ? "fill-white" : "fill-secondary"}
      >
        <Icon />
      </MaterialIcon>
    </div>
  </div>

  <small class={clsx(["text-secondary", "text-xs", "text-center", "mt-1"])}>
    {getStepsText(steps)}
  </small>

  <h3 class={clsx(["text-sm", "text-center"])}>
    {title}
  </h3>

  <p class={clsx(["text-neutral-500", "text-xs", "text-center"])}>
    {subtitle}
  </p>

  {#if showArrow}
    <div
      class={clsx([
        isActive && "hozshift",
        "absolute",
        "top-[33%]",
        "-right-4",
      ])}
      data-testid="intro-card-arrow"
    >
      <MaterialIcon
        color={isActive ? "fill-secondary" : "fill-neutral-400"}
        size="1.5rem"
      >
        <ArrowForward />
      </MaterialIcon>
    </div>
  {/if}
</div>
