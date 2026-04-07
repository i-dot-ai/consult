<script lang="ts">
  import clsx from "clsx";
  import type { Component } from "svelte";

  import Button from "../../inputs/Button/Button.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import CheckCircle from "../../svg/material/CheckCircle.svelte";
  import Finance from "../../svg/material/Finance.svelte";
  import WandStars from "../../svg/material/WandStars.svelte";
  import { getConsultationDetailUrl } from "../../../global/routes";
  import type { Consultation, ConsultationStage } from "../../../global/types";

  interface Props {
    consultation: { id: Consultation["id"]; stage: Consultation["stage"] };
    questionsCount: number;
    finalisedQuestionCount: number;
    allQuestionsFinalised: boolean;
    onConfirmClick: () => void;
  }

  let {
    consultation,
    questionsCount,
    finalisedQuestionCount,
    allQuestionsFinalised,
    onConfirmClick,
  }: Props = $props();

  type Step = {
    order: number;
    label: string;
    icon: Component;
  };

  type StageConfig = {
    step: Step;
    title: string;
  };

  const STAGE_CONFIGS: Record<string, StageConfig> = {
    consultation_overview: {
      step: { order: 1, label: "Consultation Overview", icon: CheckCircle },
      title: "Consultation Overview",
    },
    theme_sign_off: {
      step: { order: 2, label: "Theme Sign Off", icon: CheckCircle },
      title: "Theme Sign Off",
    },
    theme_mapping: {
      step: { order: 3, label: "AI Theme Mapping", icon: WandStars },
      title: "AI Mapping in Progress",
    },
    analysis: {
      step: { order: 4, label: "Analysis Dashboard", icon: Finance },
      title: "AI Mapping Complete",
    },
  };

  // Steps shown in the progress bar (always the same 4)
  const STEPS = [
    STAGE_CONFIGS.consultation_overview,
    STAGE_CONFIGS.theme_sign_off,
    STAGE_CONFIGS.theme_mapping,
    STAGE_CONFIGS.analysis,
  ];

  let currentStageConfig = $derived(
    STAGE_CONFIGS[consultation.stage] ?? STAGE_CONFIGS.theme_sign_off,
  );

  // Determine which content variant to show
  let isFinalisingThemes = $derived(consultation.stage === "theme_sign_off");
  let isAssigningThemes = $derived(consultation.stage === "theme_mapping");
  let isAnalysis = $derived(consultation.stage === "analysis");

  // Title adapts to sub-state during finalising
  let title = $derived.by(() => {
    if (isFinalisingThemes && allQuestionsFinalised)
      return "All Questions Signed Off";
    if (isFinalisingThemes) return "Finalising Themes";
    return currentStageConfig.title;
  });
</script>

{#snippet finalisingInProgressContent()}
  <p class="my-4 text-center text-sm text-neutral-500">
    Review and sign off themes for each consultation question.
    {finalisedQuestionCount} of {questionsCount} questions signed off.
  </p>

  <p class="my-4 text-center text-sm text-neutral-500">
    <strong>Next:</strong> Once all questions are signed off, you can confirm and
    proceed to AI mapping.
  </p>
{/snippet}

{#snippet finalisingCompleteContent()}
  <p class="my-4 text-center text-sm text-neutral-500">
    You have successfully reviewed and signed off themes for all {questionsCount}
    consultation questions.
  </p>

  <p class="my-4 text-center text-sm text-neutral-500">
    <strong>Next:</strong> Confirm and proceed to the AI mapping phase where responses
    will be mapped to your selected themes.
  </p>

  <Button
    type="button"
    variant="approve"
    size="md"
    fullWidth={true}
    handleClick={onConfirmClick}
  >
    <span class="mx-auto flex items-center gap-2">
      <MaterialIcon>
        <CheckCircle />
      </MaterialIcon>
      Confirm and Proceed to Mapping
    </span>
  </Button>
{/snippet}

{#snippet assigningContent()}
  <p class="my-4 text-center text-sm text-neutral-500">
    You have completed the theme sign-off phase for all {questionsCount} consultation
    questions.
  </p>

  <p class="my-4 text-center text-sm text-neutral-500">
    AI is currently mapping consultation responses to your signed-off themes.
    This process analyses each response and assigns it to the most relevant
    themes you've selected.
  </p>

  <p class="my-4 text-center text-sm text-neutral-500">
    <strong>Next:</strong> When mapping is complete, you'll be able to access the
    Analysis Dashboard to view all mapped data for detailed insights and reporting.
  </p>
{/snippet}

{#snippet analysisContent()}
  <p class="my-4 text-center text-sm text-neutral-500">
    All consultation responses have been successfully mapped against your
    selected themes.
  </p>

  <p class="my-4 text-center text-sm text-neutral-500">
    <strong>Next:</strong> View the mapped data in the
    <a
      class="text-secondary hover:underline"
      href={getConsultationDetailUrl(consultation.id)}
    >
      Analysis Dashboard
    </a>
    to explore detailed insights and generate reports.
  </p>
{/snippet}

{#snippet ConsultationStep(step: Step, currentConsultationStep: Step)}
  {@const label = step.label}
  {@const status =
    step.order < currentConsultationStep.order
      ? "done"
      : step.order === currentConsultationStep.order
        ? "current"
        : "todo"}
  {@const Icon = status === "done" ? CheckCircle : step.icon}

  <div class="flex min-w-16 flex-col items-center">
    <div
      class={clsx("my-2 rounded-full p-2", {
        "bg-secondary": status === "done",
        "bg-neutral-200": status === "todo",
        "bg-secondary ring-4 ring-teal-100": status === "current",
      })}
    >
      <MaterialIcon
        color={status === "todo" ? "fill-neutral-500" : "fill-white"}
        size="1.2rem"
      >
        <Icon />
      </MaterialIcon>
    </div>
    <h3 class={clsx("text-xs", { "text-secondary": status === "current" })}>
      {label}
    </h3>
  </div>
{/snippet}

<Panel variant="approve-dark" bg={true}>
  <div class="px-2 sm:px-8 md:px-16">
    <ol
      class={clsx([
        "px-1",
        "flex",
        "items-center",
        "justify-around",
        "gap-4",
        "text-xs",
        "text-center",
        "text-neutral-700",
        "mb-8",
        "w-3/4",
        "mx-auto",
        "overflow-x-auto",
      ])}
      aria-label="Consultation progress"
    >
      {#each STEPS as { step } (step.label)}
        <li>
          {@render ConsultationStep(step, currentStageConfig.step)}
        </li>
      {/each}
    </ol>

    <div class="px-0 md:px-16">
      <h2 class="text-center text-secondary">
        {title}
      </h2>
      {#if isFinalisingThemes && allQuestionsFinalised}
        {@render finalisingCompleteContent()}
      {:else if isFinalisingThemes}
        {@render finalisingInProgressContent()}
      {:else if isAssigningThemes}
        {@render assigningContent()}
      {:else if isAnalysis}
        {@render analysisContent()}
      {/if}
    </div>
  </div>
</Panel>
