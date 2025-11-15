<script lang="ts">
  import clsx from "clsx";

  import { slide, fly } from "svelte/transition";

  import type { GeneratedTheme } from "../../../global/types";
  import { createFetchStore, type MockFetch } from "../../../global/stores";
  import { getApiAnswersUrl } from "../../../global/routes";

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
    expandedThemes?: string[];
    setExpandedThemes?: (themeId: string) => void;
    handleSelect?: (theme: GeneratedTheme) => void;
    maxAnswers?: number;
    answersMock?: MockFetch;
  }
  let {
    consultationId,
    theme,
    level = 0,
    leftPadding = 2,
    expandedThemes = [],
    setExpandedThemes = () => {},
    handleSelect = () => {},
    maxAnswers = 10,
    answersMock,
  }: Props = $props();

  let expanded = $derived(expandedThemes.includes(theme.id));
  let showAnswers = $state(false);
  let answersRequested = $state(false);

  let {
    load: loadAnswers,
    loading: isAnswersLoading,
    data: answersData,
  } = createFetchStore(answersMock);

  let disabled = $derived(Boolean(theme.selectedtheme_id));
</script>

<div
  transition:slide
  style="margin-left: {level * leftPadding}rem;"
  class={clsx(["generated-theme-card"])}
>
  <Panel border={true}>
    <article class="flex flex-wrap sm:flex-nowrap">
      <div
        class={clsx([
          "transition-all",
          "duration-300",
          "w-auto",
          showAnswers && !disabled ? "md:w-1/3" : "md:w-auto",
        ])}
      >
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2 flex-wrap">
            {#if theme.children?.length}
              <Button
                variant="ghost"
                handleClick={() => setExpandedThemes(theme.id)}
              >
                <div
                  class={clsx([
                    "transition-transform",
                    expanded && "rotate-90",
                  ])}
                >
                  <MaterialIcon size="1.2rem" color="fill-secondary">
                    <ChevronRight />
                  </MaterialIcon>
                </div>
              </Button>
            {/if}

            <div class="flex items-center gap-2 flex-wrap">
              <h3>{theme.name}</h3>

              <div class={clsx([disabled && "grayscale"])}>
                <Tag variant="success">
                  Level {level + 1}
                </Tag>
              </div>
            </div>
          </div>
        </div>

        <p class="text-neutral-500 text-sm">
          {theme.description}
        </p>

        {#if !disabled}
          <footer class="mt-4 flex items-center gap-2 flex-wrap">
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
                  const queryString = new URLSearchParams({
                    searchMode: "representative",
                    searchValue: `${theme.name} ${theme.description}`,
                  }).toString();

                  loadAnswers(
                    `${getApiAnswersUrl(consultationId)}?${queryString}`,
                  );
                }
                showAnswers = !showAnswers;
                answersRequested = true;
              }}
              disabled={$isAnswersLoading && answersRequested}
            >
              <div class="text-secondary flex items-center gap-1">
                <MaterialIcon color="fill-secondary">
                  <Visibility />
                </MaterialIcon>
                <span class="whitespace-nowrap">
                  {showAnswers ? "Hide" : "Representative"} Responses
                </span>
              </div>
            </Button>
          </footer>
        {/if}
      </div>

      {#if showAnswers && !disabled}
        <aside
          transition:fly={{ x: 300 }}
          class="grow sm:border-l sm:border-neutral-200 sm:ml-4 sm:pl-4 pt-4 sm:pt-0"
        >
          <AnswersList
            variant="generated"
            title="Representative Responses"
            loading={$isAnswersLoading}
            answers={$answersData?.all_respondents
              .slice(0, maxAnswers)
              .map((answer) => answer.free_text_answer_text) || []}
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
          {handleSelect}
          {answersMock}
          {expandedThemes}
          {setExpandedThemes}
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
