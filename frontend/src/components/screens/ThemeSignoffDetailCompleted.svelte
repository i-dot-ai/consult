<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";

  import { createFetchStore } from "../../global/stores";
  import {
    getQuestionDetailUrl,
    getThemeSignoffUrl,
  } from "../../global/routes";

  import Panel from "../dashboard/Panel/Panel.svelte";
  import TitleRow from "../dashboard/TitleRow.svelte";
  import Tag from "../Tag/Tag.svelte";
  import Button from "../inputs/Button/Button.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import Price from "../svg/material/Price.svelte";
  import CheckCircle from "../svg/material/CheckCircle.svelte";
  import Headphones from "../svg/material/Headphones.svelte";
  import Help from "../svg/material/Help.svelte";
  import ArrowForward from "../svg/material/ArrowForward.svelte";
  import Finance from "../svg/material/Finance.svelte";

  interface Props {
    questionId: string;
    consultationId: string;
  }

  let { questionId = "", consultationId = "" }: Props = $props();

  const {
    load: loadSelectedThemes,
    loading: isSelectedThemesLoading,
    data: selectedThemesData,
    error: selectedThemesError,
  } = createFetchStore();

  const {
    load: loadQuestion,
    loading: isQuestionLoading,
    data: questionData,
    error: questionError,
  } = createFetchStore();

  $effect(() => {
    loadSelectedThemes(
      `/api/consultations/${consultationId}/questions/${questionId}/selected-themes/`,
    );
    loadQuestion(
      `/api/consultations/${consultationId}/questions/${questionId}/`,
    );
  });
</script>

<TitleRow
  level={1}
  title="Theme Sign Off"
  subtitle="Finalise themes to use for AI to map responses to"
>
  <Price slot="icon" />
</TitleRow>

<section class="my-6">
  <Button
    variant="ghost"
    size="sm"
    handleClick={() => (location.href = getThemeSignoffUrl(consultationId))}
  >
    <div class="flex items-center gap-2 text-neutral-700">
      <div class="rotate-180">
        <MaterialIcon color="fill-neutral-500">
          <ArrowForward />
        </MaterialIcon>
      </div>

      Back to questions
    </div>
  </Button>
</section>

<section class="mb-8">
  <Panel bg={false} border={true}>
    <div class="flex gap-4">
      <div class="mt-0.5">
        <MaterialIcon color="fill-emerald-700" size="1.2rem">
          <Help />
        </MaterialIcon>
      </div>

      <div>
        <h2 class="text-md">
          {#if !$questionData}
            Question loading...
          {:else}
            {`Q${$questionData?.number}: ${$questionData?.question_text}`}
          {/if}
        </h2>

        <div class="mt-2 mb-4">
          <Tag variant="primary-light">
            <MaterialIcon color="fill-primary">
              <CheckCircle />
            </MaterialIcon>
            <span class="py-0.5"> Themes Signed Off </span>
          </Tag>
        </div>
        <p class="text-neutral-500 text-sm">
          This question has completed the theme sign-off process. The selected
          themes below have been approved for AI analysis and are ready to be
          used for mapping consultation responses.
        </p>
      </div>

      <div>
        <Button
          size="sm"
          title="Click to contact Consult support"
          handleClick={() => (location.href = "mailto:support@consult.co.uk")}
        >
          <MaterialIcon size="1.2rem" color="fill-primary">
            <Headphones />
          </MaterialIcon>
          <span class="text-primary">support@consult.co.uk</span>
        </Button>
      </div>
    </div>
  </Panel>
</section>

<section>
  <Panel bg={false} border={true}>
    <h2 class="text-md">Selected Themes</h2>

    <p class="text-neutral-500 text-sm">
      The following themes have been signed off for this question and are ready
      for analysis.
    </p>

    <ul>
      {#each $selectedThemesData?.results as selectedTheme}
        <li>
          <Panel bg={true}>
            <div
              in:slide
              class={clsx([
                "flex",
                "justify-between",
                "relative",
                "pl-4",
                "text-sm",
                "before:absolute",
                "before:top-[45%]",
                "before:left-0",
                "before:transform",
                "before:-translate-y-1/2",
                "before:w-2",
                "before:h-2",
                "before:bg-primary",
                "before:rounded-full",
              ])}
            >
              {selectedTheme.name}

              <Tag variant="success">Signed Off</Tag>
            </div>
          </Panel>
        </li>
      {/each}
    </ul>
  </Panel>
</section>

<section class="mt-8">
  <div class="flex items-center justify-between gap-2 flex-wrap">
    <Button
      size="sm"
      handleClick={() => (location.href = getThemeSignoffUrl(consultationId))}
    >
      Back to Questions
    </Button>

    <div class="flex items-center gap-2 flex-wrap">
      <Button
        size="sm"
        variant="primary"
        handleClick={() =>
          (location.href = getQuestionDetailUrl(consultationId, questionId))}
      >
        <div class="flex items-center gap-1">
          <MaterialIcon>
            <Finance />
          </MaterialIcon>
          View Analysis Dashboard
        </div>
      </Button>

      <Button
        size="sm"
        handleClick={() => (location.href = getThemeSignoffUrl(consultationId))}
      >
        Select Another Question
      </Button>
    </div>
  </div>
</section>

<style>
  .selected-section :global(div[data-testid="panel-component"]) {
    margin: 0;
  }
</style>
