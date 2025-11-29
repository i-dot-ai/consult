<script lang="ts">
  import clsx from "clsx";

  import type { Snippet } from "svelte";
  import { fade } from "svelte/transition";

  import type { Question } from "../../../global/types.ts";
  import { favStore } from "../../../global/stores.ts";
  import { applyHighlight } from "../../../global/utils.ts";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import ConditionalWrapper from "../../ConditionalWrapper/ConditionalWrapper.svelte";
  import Star from "../../svg/material/Star.svelte";
  import Help from "../../svg/material/Help.svelte";
  import Checklist from "../../svg/material/Checklist.svelte";
  import Panel from "../Panel/Panel.svelte";
  import Link from "../../Link.svelte";
  import Button from "../../inputs/Button/Button.svelte";

  interface Props {
    consultationId: string;
    question: Question;
    url?: string;
    highlightText?: string;
    clickable?: boolean;
    skeleton?: boolean;
    hideIcon?: boolean;
    horizontal?: boolean;
    disabled?: boolean;
    tag?: Snippet;
    subtext?: string;
  }

  let {
    question = {},
    url = "",
    highlightText = "",
    clickable = false,
    skeleton = false,
    hideIcon = false,
    horizontal = false,
    disabled = false,
    subtext = "",
    tag,
  }: Props = $props();
</script>

<div class={clsx(["bg-white"])} transition:fade={{ duration: 200 }}>
  <ConditionalWrapper
    element={Link}
    condition={clickable && !skeleton}
    variant="block"
    href={url}
    title={`Q${question.number}: ${question.question_text}`}
    ariaLabel={`Click to view question: ${question.question_text}`}
  >
    <Panel bg={disabled}>
      <article
        class={clsx([
          "flex",
          "gap-2",
          "items-start",
          "relative",
          "flex-col-reverse",
          "sm:flex-row",
        ])}
      >
        <div class={clsx(["mt-0.5", "hidden", "sm:block"])}>
          {#if !skeleton && !hideIcon}
            <div data-testid="question-icon">
              <MaterialIcon
                size="1.3rem"
                color={disabled ? "fill-neutral-400" : "fill-secondary"}
              >
                {#if !question.has_free_text}
                  <Checklist />
                {:else}
                  <Help />
                {/if}
              </MaterialIcon>
            </div>
          {/if}
        </div>
        <div
          data-testid="horizontal-container"
          class={clsx([
            "grow",
            horizontal &&
              clsx(["sm:flex", "justify-between", "items-start", "gap-4"]),
          ])}
        >
          {#if skeleton}
            <p
              class={clsx([
                "text-md",
                "transition-colors",
                "duration-1000",
                "select-none",
                "bg-neutral-100",
                "text-neutral-100",
                "blink",
              ])}
            >
              {"SKELETON ".repeat(20)}
            </p>

            <div
              class={clsx([
                "text-sm",
                "mt-2",
                "transition-colors",
                "duration-1000",
                skeleton &&
                  clsx([
                    "w-max",
                    "select-none",
                    "bg-neutral-100",
                    "text-neutral-100",
                    "blink",
                  ]),
              ])}
            >
              000 responses
            </div>
          {:else}
            <p
              in:fade
              class={clsx(["text-md", "leading-6", disabled && "opacity-50"])}
            >
              {@html applyHighlight(
                `Q${question.number}: ${question.question_text}`,
                highlightText,
              )}
            </p>

            <div
              in:fade
              class={clsx([
                "text-sm",
                "leading-6",
                "whitespace-nowrap",
                disabled && "opacity-50",
              ])}
            >
              {question.total_responses} responses
            </div>

            {#if subtext}
              <small
                class={clsx([
                  "text-xs text-neutral-500",
                  disabled && "opacity-75",
                ])}
              >
                {subtext}
              </small>
            {/if}
          {/if}
        </div>
        <div
          class={clsx(["-ml-2", "sm:ml-0", horizontal ? "-mt-0.5" : "-mt-1"])}
        >
          {#if !skeleton}
            <div class="flex gap-1 items-center">
              {#if tag}
                <div
                  class={clsx([
                    "ml-2 md:ml-0",
                    disabled && "grayscale opacity-50",
                  ])}
                >
                  {@render tag()}
                </div>
              {/if}

              <div
                data-testid="fav-button"
                class={clsx([disabled && "grayscale"])}
              >
                <div
                  onkeypress={(e) => e.stopPropagation()}
                  onclick={(e) => e.stopPropagation()}
                >
                  <Button
                    variant="ghost"
                    handleClick={(e: MouseEvent) => {
                      e.stopPropagation();
                      favStore.toggleFav(question.id || "");
                    }}
                  >
                    {@const favourited = $favStore.includes(question.id)}
                    <MaterialIcon
                      size="1.3rem"
                      color={favourited ? "fill-yellow-500" : "fill-gray-500"}
                    >
                      <Star fill={favourited} />
                    </MaterialIcon>
                  </Button>
                </div>
              </div>
            </div>
          {/if}
        </div>
      </article>
    </Panel>
  </ConditionalWrapper>
</div>
