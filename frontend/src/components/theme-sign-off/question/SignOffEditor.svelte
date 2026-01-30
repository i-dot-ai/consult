<script lang="ts">
  import clsx from "clsx";

  import { getThemeSignOffUrl } from "../../../global/routes";
  import type { Question } from "../../../global/types";

  import TitleRow from "../../dashboard/TitleRow.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import Price from "../../svg/material/Price.svelte";
  import QuestionCard from "../../dashboard/QuestionCard/QuestionCard.svelte";
  import OnboardingTour from "../../OnboardingTour/OnboardingTour.svelte";
  import Target from "../../svg/material/Target.svelte";
  import EditSquare from "../../svg/material/EditSquare.svelte";
  import CheckCircle from "../../svg/material/CheckCircle.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import Alert from "../../Alert.svelte";

  import SelectedThemesSection from "./selected-themes/SelectedThemesSection.svelte";
  import CandidateThemesSection from "./candidate-themes/CandidateThemesSection.svelte";

  interface Props {
    consultationId: string;
    questionId: string;
    question: Question;
  }

  let { consultationId, questionId, question }: Props = $props();
</script>

<TitleRow
  level={1}
  title="Theme Sign Off"
  subtitle="Finalise themes to use for AI to map responses to"
>
  <Price slot="icon" />

  <div slot="aside">
    <Button
      size="xs"
      handleClick={() => (location.href = getThemeSignOffUrl(consultationId))}
    >
      <span class="p-1"> Choose another question </span>
    </Button>
  </div>
</TitleRow>

<section class="my-8">
  <QuestionCard
    skeleton={false}
    {consultationId}
    {question}
    clickable={false}
  />
</section>

<SelectedThemesSection {consultationId} {questionId} {question} />

<div
  class={clsx([
    "relative",
    "w-full",
    "my-8",
    "after:w-full",
    "after:border-b",
    "after:absolute",
    "after:left-0",
    "after:right-0",
    "after:bottom-1/2",
    "after:-z-10",
  ])}
>
  <p
    class={clsx([
      "m-auto",
      "w-max",
      "bg-white",
      "px-4",
      "text-sm",
      "text-neutral-500",
    ])}
  >
    Browse AI Generated Themes
  </p>
</div>

<CandidateThemesSection {consultationId} {questionId} />

<svelte:boundary>
  <OnboardingTour
    key="theme-sign-off"
    steps={[
      {
        id: "onboarding-step-1",
        title: "Select Themes",
        body: `Browse the AI-generated themes and click "Select Theme" to move them to your selected themes list. You can view example responses for each theme to understand what types of consultation responses it represents.`,
        icon: Target,
      },
      {
        id: "onboarding-steps-2-and-3",
        title: "Edit & Manage",
        body: "Once themes are selected, you can edit their titles and descriptions by clicking the edit button, or add completely new themes to better organize your analysis.",
        icon: EditSquare,
      },
      {
        id: "onboarding-steps-2-and-3",
        title: "Sign Off & Proceed",
        body: `When you're satisfied with your theme selection and edits, click "Sign Off Selected Themes" to proceed with mapping consultation responses against your finalised themes.`,
        icon: CheckCircle,
      },
    ]}
    resizeObserverTarget={document.querySelector("main")}
  />

  {#snippet failed(error)}
    <div>
      {console.error(error)}

      <Panel>
        <Alert>Unexpected onboarding tour error</Alert>
      </Panel>
    </div>
  {/snippet}
</svelte:boundary>
