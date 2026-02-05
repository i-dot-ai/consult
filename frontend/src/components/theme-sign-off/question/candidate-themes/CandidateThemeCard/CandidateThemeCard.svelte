<script lang="ts">
  import clsx from "clsx";

  import { slide, fly } from "svelte/transition";

  import type { GeneratedTheme } from "../../../../../global/types";

  import Panel from "../../../../dashboard/Panel/Panel.svelte";
  import Button from "../../../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../../../MaterialIcon.svelte";
  import ChevronRight from "../../../../svg/material/ChevronRight.svelte";
  import CandidateThemeCard from "./CandidateThemeCard.svelte";
  import Tag from "../../../../Tag/Tag.svelte";
  import RepresentativeResponses from "../../RepresentativeResponses/RepresentativeResponses.svelte";
  import Visibility from "../../../../svg/material/Visibility.svelte";
  import LoadingIndicator from "../../../../LoadingIndicator/LoadingIndicator.svelte";

  export interface Props {
    consultationId: string;
    questionId: string;
    theme: GeneratedTheme;
    collapsedThemes: string[];
    level?: number;
    leftPadding?: number;
    toggleTheme: (themeId: string) => void;
    handleSelect: (theme: GeneratedTheme) => void;
    themesBeingSelected: string[];
  }

  let {
    consultationId,
    questionId,
    theme,
    collapsedThemes,
    level = 0,
    leftPadding = 2,
    toggleTheme,
    handleSelect = () => {},
    themesBeingSelected = [],
  }: Props = $props();

  let isExpanded = $derived(!collapsedThemes.includes(theme.id));

  let showRepresentativeResponses = $state(false);

  let disabled = $derived(Boolean(theme.selectedtheme_id));
  let isBeingSelected = $derived(themesBeingSelected.includes(theme.id));
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
          showRepresentativeResponses && !disabled ? "md:w-1/3" : "md:w-auto",
        ])}
      >
        <div class="mb-2 flex items-center justify-between">
          <div class="flex flex-wrap items-center gap-2">
            {#if theme.children?.length}
              <Button variant="ghost" handleClick={() => toggleTheme(theme.id)}>
                <div
                  class={clsx([
                    "transition-transform",
                    isExpanded && "rotate-90",
                  ])}
                >
                  <MaterialIcon size="1.2rem" color="fill-secondary">
                    <ChevronRight />
                  </MaterialIcon>
                </div>
              </Button>
            {/if}

            <div class="flex flex-wrap items-center gap-2">
              <h3>{theme.name}</h3>

              <div class={clsx([disabled && "grayscale"])}>
                <Tag variant="success">
                  Level {level + 1}
                </Tag>
              </div>
            </div>
          </div>
        </div>

        <p class="text-sm text-neutral-500">
          {theme.description}
        </p>

        {#if !disabled}
          <footer class="mt-4 flex flex-wrap items-center gap-2">
            <Button
              variant="approve"
              size="sm"
              disabled={isBeingSelected}
              handleClick={() => handleSelect(theme)}
            >
              <div class="flex items-center gap-1">
                Select
                {#if isBeingSelected}
                  <LoadingIndicator size="1rem" />
                {/if}
              </div>
            </Button>

            <Button
              size="sm"
              handleClick={() =>
                (showRepresentativeResponses = !showRepresentativeResponses)}
            >
              <div class="flex items-center gap-1 text-secondary">
                <MaterialIcon color="fill-secondary">
                  <Visibility />
                </MaterialIcon>
                <span class="whitespace-nowrap">
                  {showRepresentativeResponses ? "Hide" : "Representative"} Responses
                </span>
              </div>
            </Button>
          </footer>
        {/if}
      </div>

      {#if showRepresentativeResponses && !disabled}
        <aside
          transition:fly={{ x: 300 }}
          class="grow pt-4 sm:ml-4 sm:w-2/3 sm:border-l sm:border-neutral-200 sm:pl-4 sm:pt-0"
        >
          <RepresentativeResponses
            {consultationId}
            {questionId}
            themeName={theme.name}
            themeDescription={theme.description}
            themeId={theme.id}
            variant="candidate"
          />
        </aside>
      {:else}
        <div class="p2"></div>
      {/if}
    </article>
  </Panel>

  {#if isExpanded && theme.children?.length}
    <div transition:slide class="pt-4">
      {#each theme.children as childTheme (childTheme.id)}
        <CandidateThemeCard
          {consultationId}
          {questionId}
          theme={childTheme}
          {collapsedThemes}
          level={level + 1}
          {handleSelect}
          {themesBeingSelected}
          {toggleTheme}
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
