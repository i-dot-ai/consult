<script lang="ts">
  import clsx from "clsx";
  
  import { onMount, onDestroy } from "svelte";
  import { fade } from "svelte/transition";

  import MaterialIcon from "../MaterialIcon.svelte";
  import Close from "../svg/material/Close.svelte";
  import Progress from "../Progress/Progress.svelte";
  import Button from "../inputs/Button/Button.svelte";

  interface Step {
    id: string;
    title: string;
    body: string;
  }

  interface TargetRect {
    top: number;
    left: number;
    width: number;
    height: number;
  }

  interface Props {
    key: string;
    steps: Step[];
    overlayPadding?: number;
  }

  let {
    key = "",
    steps = [],
    overlayPadding = 10,
  }: Props = $props();

  let currStep = $state(0);

  let targetRect: TargetRect | null = $state(null);

  const updateTargetRect = () => {
    const step = steps[currStep];

    if (!step) {
      return;
    }

    const targetEl = document.getElementById(step.id);
    if (targetEl) {
      const rect = targetEl.getBoundingClientRect();
      targetRect = {
        top: (rect.top + window.scrollY) - overlayPadding,
        left: (rect.left + window.scrollX) - overlayPadding,
        width: rect.width + (overlayPadding * 2),
        height: rect.height + (overlayPadding * 2),
      }
    } else {
      targetRect = null;
    }
  }

  const goNext = () => {
    if (currStep < steps.length - 1) {
      currStep += 1;
      updateTargetRect();
    }
  }
  const goPrev = () => {
    if (currStep > 0) {
      currStep -= 1;
      updateTargetRect();
    }
  }

  const close = () => {
    currStep = -1;
    if (key) {
      localStorage.setItem(getStorageKey(), "true");
    }
  }

  const getStorageKey = () => {
    return `onboardingComplete-${key}`;
  }

  const isOnboardingComplete = () => {
    return localStorage.getItem(getStorageKey());
  }

  onMount(() => {
    updateTargetRect();
    window.addEventListener("resize", updateTargetRect);
    window.addEventListener("scroll", updateTargetRect);
  })

  onDestroy(() => {
    window.removeEventListener("resize", updateTargetRect);
    window.removeEventListener("scroll", updateTargetRect);
  })
</script>

{#if targetRect && currStep >= 0 && !isOnboardingComplete()}
  <article
    transition:fade={{ duration: 300 }}
    class="absolute top-0 left-0"
  >
    <div
      style={clsx([
        `top: ${targetRect.top}px;`,
        `left: ${targetRect.left}px;`,
        `width: ${targetRect.width}px;`,
        `height: ${targetRect.height}px;`,
      ])}
      class={clsx([
        "absolute",
        "w-[5rem]",
        "h-[5rem]",
        "p-4",
        "border",
        "border-2",
        "border-primary",
        "rounded-lg",
        "bg-transparent",
        "transition-all",
        "shadow-[0_0px_0px_99999px_rgba(0,0,0,0.8)]",
      ])}
    ></div>

    <div
      class={clsx([
        "absolute",
        "w-[15rem]",
        "p-4",
        "rounded-lg",
        "bg-white",
      ])}
      style={clsx([
        `top: ${targetRect.top + targetRect.height + overlayPadding}px;`,
        `left: ${targetRect.left}px;`,
      ])}
    >
      <header class="mb-2 flex justify-between items-start">
        <div>
          <h3 class="text-sm mb-1">
            {steps[currStep].title}
          </h3>
          <p class="text-xs text-neutral-500">
            Step {currStep + 1} of {steps.length}
          </p>
        </div>

        <Button variant="ghost" handleClick={close}>
          <MaterialIcon color="fill-neutral-500">
            <Close />
          </MaterialIcon>
        </Button>
      </header>

      <p class="text-xs text-neutral-700 leading-5">
        {steps[currStep].body}
      </p>

      <footer>
        <div class="flex flex-no-wrap gap-1 mt-4">
          {#each steps as _, i}
            <div style="width: {Math.round(100 / steps.length)}%;">
              <Progress value={currStep >= i ? 100 : 0} />
            </div>
          {/each}
        </div>

        <div class="flex gap-2 mt-4 flex-wrap">
          <Button
            size="xs"
            handleClick={goPrev}
            disabled={currStep === 0}
          >
            Previous
          </Button>
          <Button
            variant="ghost"
            size="xs"
            handleClick={close}
          >
            Skip Tour
          </Button>
          <Button
            variant="primary"
            size="xs"
            handleClick={goNext}
            disabled={currStep === steps.length - 1}
          >
            Next
          </Button>
        </div>
      </footer>
    </div>
  </article>
{/if}