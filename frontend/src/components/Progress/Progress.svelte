<script lang="ts">
  // Using melt-ui progress
  // Docs: https://www.melt-ui.com/docs/builders/progress

  import { createProgress, melt } from "@melt-ui/svelte";
  import clsx from "clsx";
  import { writable } from "svelte/store";

  export let value: number = 0;
  export let thickness: 1 | 1.5 | 2 = 2;
  export let transitionDelay: number = 0;
  export let transitionDuration: number = 0;

  const writableValue = writable(30);

  $: writableValue.set(value);

  const {
    elements: { root },
    options: { max },
  } = createProgress({
    value: writableValue,
    max: 100,
  });
</script>

<div
  use:melt={$root}
  class={clsx([
    "relative",
    thickness === 1 && "h-1",
    thickness === 1.5 && "h-1.5",
    thickness === 2 && "h-2",
    "w-full",
    "overflow-hidden",
    "rounded-[99999px]",
    "bg-neutral-300",
  ])}
>
  <div
    class={clsx([
      "h-full",
      "w-full",
      "bg-primary",
      "transition-transform",
      "duration-[660ms]",
      "ease-[cubic-bezier(0.65,0,0.35,1)]",
    ])}
    style={`
      transform: translateX(-${
        100 - (100 * ($writableValue ?? 0)) / ($max ?? 1)
      }%);
      transition-delay: ${transitionDelay}ms;
      transition-duration: ${transitionDuration}ms;
    `}
  ></div>
</div>
