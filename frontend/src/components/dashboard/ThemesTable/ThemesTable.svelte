<script lang="ts">
  import clsx from "clsx";

  import { fade } from "svelte/transition";
  import { flip } from "svelte/animate";

  import type { FormattedTheme } from "../../../global/types.ts";
  import { getPercentage } from "../../../global/utils.ts";

  import Progress from "../../Progress/Progress.svelte";

  interface Props {
    themes: FormattedTheme[];
    freeTextResponseCount: number;
    skeleton?: boolean;
    countsLoading?: boolean;
  }

  let {
    themes = [],
    freeTextResponseCount = 0,
    skeleton = false,
    countsLoading = false,
  }: Props = $props();

  let showFullSkeleton = $derived(skeleton && themes.length === 0);

  const TABLE_FLIP_SPEED = 10;
</script>

<div class="w-full overflow-auto">
  <table class="text-md w-full">
    <thead class="text-sm">
      <tr>
        {#each ["Theme", "Mentions", "% Percentage"] as header (header)}
          <th class="text-md m-2 pr-4 text-left font-normal">
            {header}
          </th>
        {/each}
      </tr>
    </thead>
    {#if showFullSkeleton}
      <tbody in:fade>
        {#each "_".repeat(5) as _, i (i)}
          <tr
            class={clsx([
              "text-xs",
              "border-y",
              "border-neutral-300",
              "py-2",
              "transition-colors",
              "duration-300",
            ])}
          >
            <td class="pr-4">
              <div transition:fade class="p-2">
                <h3
                  class="blink mb-2 w-max select-none bg-neutral-100 text-sm font-bold text-neutral-100"
                >
                  {"SKELETON ".repeat(3)}
                </h3>
                <p
                  class="blink select-none bg-neutral-100 text-sm text-neutral-100"
                >
                  {"SKELETON ".repeat(5)}
                </p>
              </div>
            </td>

            <td class="pr-4">
              <div class="mt-8">
                <span class="blink select-none bg-neutral-100 text-neutral-100">
                  000 SKELETON
                </span>
              </div>
            </td>
            <td class="pr-4">
              <div class="mt-8 flex items-center gap-1">
                <span
                  class="blink w-[5ch] select-none bg-neutral-100 text-neutral-100"
                >
                  000%
                </span>
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    {:else}
      <tbody in:fade>
        {#each themes as theme (theme.id)}
          {@const percentage = getPercentage(
            theme.count,
            freeTextResponseCount,
          )}

          <tr
            animate:flip={{ duration: 300 + themes.length * TABLE_FLIP_SPEED }}
            class={clsx([
              "text-xs",
              !theme.highlighted && "border-y border-neutral-300",
              "py-2",
              "cursor-pointer",
              "transition-colors",
              "duration-300",
              "hover:bg-neutral-100",
              theme.highlighted && "bg-pink-100",
            ])}
            onclick={theme.handleClick}
            tabindex="0"
            role="button"
            aria-pressed={theme.highlighted ? "true" : "false"}
          >
            <td class="pr-4">
              <div transition:fade class="p-2">
                <h3 class="text-sm font-normal">{theme.name}</h3>
                <p class="text-sm font-light text-neutral-500">
                  {theme.description}
                </p>
              </div>
            </td>
            <td class="pr-4">
              {#if countsLoading}
                <span
                  class="blink select-none rounded-sm bg-neutral-200 text-neutral-200"
                >
                  00000
                </span>
              {:else}
                {theme.count}
              {/if}
            </td>
            <td class="pr-4">
              <div class="flex items-center gap-1">
                {#if countsLoading}
                  <span
                    class="blink w-[5ch] select-none rounded-sm bg-neutral-200 text-neutral-200"
                  >
                    000%
                  </span>
                {:else}
                  <span class="w-[5ch]">
                    {percentage > 0 && percentage < 1
                      ? "<1"
                      : Math.round(percentage)}%
                  </span>

                  <div class="w-full max-w-12">
                    <Progress value={percentage} />
                  </div>
                {/if}
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    {/if}
  </table>
</div>
