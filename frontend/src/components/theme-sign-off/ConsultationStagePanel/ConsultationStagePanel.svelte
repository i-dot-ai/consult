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
  import type { Consultation } from "../../../global/types";

  interface Props {
    consultation: { id: Consultation["id"]; stage: Consultation["stage"] };
    questionsCount: number;
    onConfirmClick: () => void;
  }

  let { consultation, questionsCount, onConfirmClick }: Props = $props();

  type Step = {
    order: number;
    label: string;
    icon: Component;
  };

  const STAGES = {
    consultation_overview: {
      step: {
        order: 1,
        label: "Consultation Overview",
        icon: CheckCircle,
      },
    },
    theme_sign_off: {
      step: {
        order: 2,
        label: "Theme Sign Off",
        icon: CheckCircle,
      },
      title: "All Questions Signed Off",
      content: themeSignOffContent,
    },
    theme_mapping: {
      step: {
        order: 3,
        label: "AI Theme Mapping",
        icon: WandStars,
      },
      title: "AI Mapping in Progress",
      content: themeMappingContent,
    },
    analysis: {
      step: {
        order: 4,
        label: "Analysis Dashboard",
        icon: Finance,
      },
      title: "AI Mapping Complete",
      content: analysisContent,
    },
  } as const;

  let currentConsultationStage = $derived(STAGES[consultation.stage]);
</script>

{#snippet themeSignOffContent()}
  <p class="text-sm text-center text-neutral-500 my-4">
    You have successfully reviewed and signed off themes for all {questionsCount}
    consultation questions.
  </p>

  <p class="text-sm text-center text-neutral-500 my-4">
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
    <span class="flex items-center gap-2 mx-auto">
      <MaterialIcon>
        <CheckCircle />
      </MaterialIcon>
      Confirm and Proceed to Mapping
    </span>
  </Button>
{/snippet}

{#snippet themeMappingContent()}
  <p class="text-sm text-center text-neutral-500 my-4">
    You have completed the theme sign-off phase for all {questionsCount} consultation
    questions.
  </p>

  <p class="text-sm text-center text-neutral-500 my-4">
    AI is currently mapping consultation responses to your signed-off themes.
    This process analyses each response and assigns it to the most relevant
    themes you've selected.
  </p>

  <p class="text-sm text-center text-neutral-500 my-4">
    <strong>Next:</strong> When mapping is complete, you'll be able to access the
    Analysis Dashboard to view all mapped data for detailed insights and reporting.
  </p>
{/snippet}

{#snippet analysisContent()}
  <p class="text-sm text-center text-neutral-500 my-4">
    All consultation responses have been successfully mapped against your
    selected themes.
  </p>

  <p class="text-sm text-center text-neutral-500 my-4">
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

  <div class="flex flex-col items-center min-w-16">
    <div
      class={clsx("my-2 p-2 rounded-full", {
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
        "w-full",
        "overflow-x-auto",
      ])}
      aria-label="Consultation progress"
    >
      {#each Object.values(STAGES) as { step } (step.label)}
        <li>
          {@render ConsultationStep(step, currentConsultationStage.step)}
        </li>
      {/each}
    </ol>

    <div class="px-0 md:px-16">
      <h2 class="text-secondary text-center">
        {currentConsultationStage.title}
      </h2>
      {@render currentConsultationStage.content()}
    </div>
  </div>
</Panel>
