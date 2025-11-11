<script lang="ts">
  import clsx from "clsx";

  import { onMount, onDestroy, type Component } from "svelte";
  import { fade } from "svelte/transition";

  import MaterialIcon from "../MaterialIcon.svelte";
  import Close from "../svg/material/Close.svelte";
  import ChevronRight from "../svg/material/ChevronRight.svelte";
  import Progress from "../Progress/Progress.svelte";
  import Button from "../inputs/Button/Button.svelte";

  interface Step {
    id: string;
    title: string;
    body: string;
    icon?: Component;
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

    // element to trigger update when resized
    // different than window resize event
    resizeObserverTarget?: HTMLElement | null;
  }

  let {
    key = "",
    steps = [],
    overlayPadding = 10,
    resizeObserverTarget,
  }: Props = $props();

  let currStep = $state(0);

  let progressTransition = $state(true);

  let targetRect: TargetRect | null = $state(null);

  const updateTargetRect = () => {
    if (isOnboardingComplete()) {
      return;
    }

    const step = steps[currStep];

    if (!step) {
      return;
    }

    const targetEl = document.getElementById(step.id);
    if (targetEl) {
      const rect = targetEl.getBoundingClientRect();
      targetRect = {
        top: rect.top + window.scrollY - overlayPadding,
        left: rect.left + window.scrollX - overlayPadding,
        width: rect.width + overlayPadding * 2,
        height: rect.height + overlayPadding * 2,
      };
      targetEl.scrollIntoView();
    } else {
      targetRect = null;
    }
  };

  const goNext = () => {
    progressTransition = true;

    if (currStep < steps.length - 1) {
      currStep += 1;
      updateTargetRect();
    } else {
      close();
    }
  };
  const goPrev = () => {
    progressTransition = true;

    if (currStep > 0) {
      currStep -= 1;
      updateTargetRect();
    }
  };

  const close = () => {
    currStep = -1;
    if (key) {
      localStorage.setItem(getStorageKey(), "true");
    }
  };

  const getStorageKey = () => {
    return `onboardingComplete-${key}`;
  };

  const isOnboardingComplete = () => {
    return localStorage.getItem(getStorageKey());
  };

  onMount(() => {
    updateTargetRect();
    window.addEventListener("resize", updateTargetRect);
    window.addEventListener("scroll", updateTargetRect);

    new ResizeObserver(updateTargetRect).observe(
      resizeObserverTarget || document.body,
    );
  });

  onDestroy(() => {
    window.removeEventListener("resize", updateTargetRect);
    window.removeEventListener("scroll", updateTargetRect);
  });
</script>

{#if targetRect && currStep >= 0 && !isOnboardingComplete()}
  <article transition:fade={{ duration: 300 }} class="absolute top-0 left-0">
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
        "w-auto",
        "min-w-[15rem]",
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
        <div class="flex items-center gap-2">
          {#if steps[currStep].icon}
            <div class="bg-pink-100 rounded-full p-1">
              <MaterialIcon color="fill-primary" size="1.2rem">
                <svelte:component this={steps[currStep].icon} />
              </MaterialIcon>
            </div>
          {/if}

          <div>
            <h3 class="text-sm mb-1">
              {steps[currStep].title}
            </h3>
            <p class="text-xs text-neutral-500">
              Step {currStep + 1} of {steps.length}
            </p>
          </div>
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
            <button
              title={`Go to step ${i + 1}`}
              style="width: {Math.round(100 / steps.length)}%;"
              class={"hover:opacity-75"}
              onclick={() => {
                // transition only if 1 step difference
                progressTransition = Math.abs(currStep - i) === 1;

                currStep = i;
                updateTargetRect();
              }}
            >
              <Progress
                value={currStep >= i ? 100 : 0}
                thickness={1.5}
                transitionDuration={progressTransition ? 1000 : 0}
              />
            </button>
          {/each}
        </div>

        <div class="flex items-center gap-2 mt-4">
          <!-- Previous Button -->
          <div class={clsx([currStep === 0 && "invisible"])}>
            <Button size="xs" handleClick={goPrev}>
              <div
                class={clsx([
                  "flex",
                  "items-center",
                  "gap-1",
                  "max-w-[10ch]",
                  "px-1",
                  "py-0.5",
                ])}
              >
                <div class="rotate-180">
                  <MaterialIcon color="black">
                    <ChevronRight />
                  </MaterialIcon>
                </div>
                Previous
              </div>
            </Button>
          </div>

          <!-- Skip Button -->
          <div
            class={clsx([
              "my-auto",
              currStep === steps.length - 1 && "invisible",
            ])}
          >
            <Button variant="ghost" size="xs" handleClick={close}>
              <div class="whitespace-nowrap">Skip Tour</div>
            </Button>
          </div>

          <!-- Next Button -->
          <Button variant="primary" size="xs" handleClick={goNext}>
            <div
              class={clsx([
                "flex",
                "justify-between",
                "items-center",
                "gap-1",
                "min-w-[10ch]",
                "px-1",
                "py-0.5",
              ])}
            >
              <div class="flex justify-center text-center w-full">
                {currStep === steps.length - 1 && "invisible"
                  ? "Finish"
                  : "Next"}
              </div>
              <div class="shrink-0">
                <MaterialIcon>
                  <ChevronRight />
                </MaterialIcon>
              </div>
            </div>
          </Button>
        </div>
      </footer>
    </div>
  </article>
{/if}
