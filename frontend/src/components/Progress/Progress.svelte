<script lang="ts">
  // Using melt-ui progress
  // Docs: https://www.melt-ui.com/docs/builders/progress

  import { createProgress, melt } from "@melt-ui/svelte";
  import clsx from "clsx";
  import { writable } from "svelte/store";

  import { cssVars } from "../../global/actions";

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
    use:cssVars={{
      "progress-translate": `-${100 - (100 * ($writableValue ?? 0)) / ($max ?? 1)}%`,
      "progress-delay": `${transitionDelay}ms`,
      "progress-duration": `${transitionDuration}ms`,
    }}
    class={clsx([
      "progress-bar",
      "h-full",
      "w-full",
      "bg-primary",
      "transition-transform",
      "ease-[cubic-bezier(0.65,0,0.35,1)]",
    ])}
  ></div>
</div>

<style>
  .progress-bar {
    transform: translateX(var(--progress-translate, -100%));
    transition-delay: var(--progress-delay, 0ms);
    transition-duration: var(--progress-duration, 0ms);
  }
</style>
