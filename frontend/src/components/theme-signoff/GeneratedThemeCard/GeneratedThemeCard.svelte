<script lang="ts">
  import clsx from "clsx";

  import { slide, fly } from "svelte/transition";

  import type { GeneratedTheme, SelectedTheme } from "../../../global/types";
  import { createFetchStore } from "../../../global/stores";

  import Panel from "../../dashboard/Panel/Panel.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import ChevronRight from "../../svg/material/ChevronRight.svelte";
  import GeneratedThemeCard from "./GeneratedThemeCard.svelte";
  import Tag from "../../Tag/Tag.svelte";
  import AnswersList from "../AnswersList/AnswersList.svelte";
  import Visibility from "../../svg/material/Visibility.svelte";

  export interface Props {
    consultationId: string;
    theme: GeneratedTheme;
    level?: number;
    leftPadding?: number;
    forceExpand?: boolean;
    setForceExpand?: (newValue: boolean) => void;
    handleSelect: (theme: GeneratedTheme) => void;
    maxAnswers?: number;
    answersMock?: Function;
  }
  let {
    consultationId,
    theme,
    level = 0,
    leftPadding = 2,
    forceExpand = false,
    setForceExpand = () => {},
    handleSelect = () => {},
    maxAnswers = 10,
    answersMock,
  }: Props = $props();

  let expanded = $state(true);
  let showAnswers = $state(false);
  let answersRequested = $state(false);

  let {
    load: loadAnswers,
    loading: isAnswersLoading,
    data: answersData,
    error: answersError,
  } = createFetchStore(answersMock);

  let disabled = $derived(Boolean(theme.selectedtheme_id));

  $effect(() => {
    if (forceExpand) {
      expanded = true;
    }
  });

  const shouldShowAnswers = () => {
    return showAnswers && !disabled;
  };
</script>

<div
  transition:slide
  style="margin-left: {level * leftPadding}rem;"
  class={clsx(["generated-theme-card"])}
>
  <Panel border={true}>
    <article class="flex">
      <div
        class={clsx([
          "transition-all",
          "duration-300",
          shouldShowAnswers() ? "w-1/3" : "w-full",
        ])}
      >
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            {#if theme.children?.length! > 0}
              <Button
                variant="ghost"
                handleClick={() => {
                  expanded = !expanded;
                  setForceExpand(false);
                }}
              >
                <div
                  class={clsx([
                    "transition-transform",
                    expanded && "rotate-90",
                  ])}
                >
                  <MaterialIcon size="1.2rem" color="fill-emerald-700">
                    <ChevronRight />
                  </MaterialIcon>
                </div>
              </Button>
            {/if}

            <h3>{theme.name}</h3>

            <div class={clsx([
              disabled && "grayscale",
            ])}>
              <Tag variant="success">
                Level {level + 1}
              </Tag>
            </div>
          </div>
        </div>

        <p class="text-neutral-500 text-sm">
          {theme.description}
        </p>

        {#if !disabled}
          <footer class="mt-4 flex items-center gap-2">
            <Button
              variant="approve"
              size="sm"
              handleClick={() => handleSelect(theme)}
            >
              Select
            </Button>
            <Button
              size="sm"
              handleClick={() => {
                if (!$answersData) {
                  loadAnswers(`
                    /api/consultations/${consultationId}/responses/?searchValue=${theme.name}&searchMode=semantic
                  `);
                }
                showAnswers = !showAnswers;
                answersRequested = true;
              }}
              disabled={$isAnswersLoading && answersRequested}
            >
              <div class="text-emerald-700 flex items-center gap-1">
                <MaterialIcon color="fill-emerald-700">
                  <Visibility />
                </MaterialIcon>
                {showAnswers ? "Hide" : "Representative"} Responses
              </div>
            </Button>
          </footer>
        {/if}
      </div>

      {#if shouldShowAnswers()}
        <aside
          transition:fly={{ x: 300 }}
          class="border-l border-neutral-200 ml-4 pl-4"
        >
          <AnswersList
            variant="generated"
            title="Representative Responses"
            answers={
              $answersData?.all_respondents
                .slice(0, maxAnswers)
                .map(answer => answer.free_text_answer_text)
            || []}
          />
        </aside>
      {:else}
        <div class="p2"></div>
      {/if}
    </article>
  </Panel>

  {#if expanded}
    <div transition:slide class="pt-4">
      {#each theme.children as childTheme (childTheme.id)}
        <GeneratedThemeCard
          {consultationId}
          theme={childTheme}
          level={level + 1}
          {forceExpand}
          {setForceExpand}
          {handleSelect}
          {answersMock}
        />
      {/each}
    </div>
  {:else}
    <div class="pb-4"></div>
  {/if}
</div>

<style>
  .generated-theme-card :global(div[data-testid="panel-component"]) {
    margin-block: 0;
  }
</style>
