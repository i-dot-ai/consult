<script lang="ts">
  import clsx from "clsx";

  import { fade } from "svelte/transition";

  import { getPercentage } from "../../../global/utils";
  import { multiAnswerFilters } from "../../../global/state.svelte";
  import type { QuestionMultiAnswer } from "../../../global/types";

  import Progress from "../../Progress/Progress.svelte";
  import Panel from "../Panel/Panel.svelte";
  import TitleRow from "../TitleRow.svelte";
  import List from "../../svg/material/List.svelte";
  import Button from "../../inputs/Button/Button.svelte";

  interface Props {
    data: QuestionMultiAnswer[];
  }

  let { data = [] }: Props = $props();
</script>

<section class="my-4" transition:fade>
  <Panel border={true}>
    <TitleRow level={2} title="Multiple Choice Answers">
      <List slot="icon" />
    </TitleRow>

    {@const total = data
      .map((item) => item.response_count)
      .reduce((acc, curr) => acc + curr, 0)}
    <Panel bg={true}>
      {#each data as item, i (i)}
        {@const percentage = getPercentage(item.response_count, total)}

        <div class="mb-1 last:mb-0">
          <Button
            variant="ghost"
            size="xs"
            fullWidth={true}
            handleClick={() => {
              multiAnswerFilters.update(item.id);
            }}
            highlighted={multiAnswerFilters.applied(item.id)}
            highlightVariant="light"
          >
            <div
              class={clsx([
                "flex",
                "items-center",
                "justify-between",
                "gap-1",
                "text-xs",
                "mb-4",
                "last:mb-0",
                "w-full",
                "p-1",
              ])}
            >
              <h3 class="w-1/2 text-left">
                {item.text}
              </h3>

              <div
                class={clsx([
                  "flex",
                  "flex-col",
                  "justify-center",
                  "items-center",
                  "gap-1",
                  "w-2/3",
                  "sm:flex-row",
                  "sm:w-1/2",
                  "sm:gap-4",
                ])}
              >
                <div
                  class={clsx([
                    "flex",
                    "justify-between",
                    "items-center",
                    "w-full",
                    "sm:justify-end",
                  ])}
                >
                  <span>{percentage}%</span>

                  <span class="sm:hidden">
                    {item.response_count}
                  </span>
                </div>
                <div class="w-full">
                  <Progress value={percentage} />
                </div>

                <span class="hidden min-w-[4ch] sm:block">
                  {item.response_count}
                </span>
              </div>
            </div>
          </Button>
        </div>
      {/each}
    </Panel>
  </Panel>
</section>
