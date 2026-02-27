<script lang="ts">
  import clsx from "clsx";

  import type { Component } from "svelte";

  import MaterialIcon from "../../MaterialIcon.svelte";  
  import ArrowForward from "../../svg/material/ArrowForward.svelte";


  interface Props {
    Icon: Component;
    order: number;
    title: string;
    subtitle: string;
  }

  let {
    Icon,
    order,
    title,
    subtitle,
  }: Props = $props();
</script>

<div class={clsx([
  "relative",
  "flex",
  "flex-col",
  "gap-1",
  "items-center",
  "w-[15rem]",
])}>
  <div class={clsx([
    "bg-secondary",
    "p-2",
    "rounded-full",
    "w-12",
    "h-12",
    "shadow-lg",
  ])}>
    <div class={clsx([
      "growshrink",
    ])}>
      <MaterialIcon size="2rem">
        <Icon />
      </MaterialIcon>
    </div>
  </div>

  <small class={clsx([
    "text-secondary",
    "text-xs",
    "text-center",
    "mt-1",
  ])}>
    Step {order}
  </small>

  <h3 class={clsx([
    "text-sm",
    "text-center",
  ])}>
    {title}
  </h3>

  <p class={clsx([
    "text-neutral-500",
    "text-xs",
    "text-center",
  ])}>
    {subtitle}
  </p>

  <div class={clsx([
    "hozshift",
    "absolute",
    "top-[33%]",
    "-right-4",
  ])}>
    <MaterialIcon color="fill-secondary" size="1.5rem">
      <ArrowForward />
    </MaterialIcon>
  </div>
</div>