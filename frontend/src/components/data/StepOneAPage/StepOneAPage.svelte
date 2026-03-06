<script lang="ts">
  import clsx from "clsx";

  import { fade } from "svelte/transition";

  import Accordion from "../../Accordion/Accordion.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import Title from "../../Title.svelte";
  import Lightbulb2 from "../../svg/material/Lightbulb2.svelte";

  const SelectedValues = {
    Qualtrics: "qualtrics",
    SmartSurvey: "smartsurvey",
    CitizenSpace: "citizenspace",
    Other: "other",
  } as const;

  type SelectedValue = (typeof SelectedValues)[keyof typeof SelectedValues];

  let selected: SelectedValue = $state(
    (SelectedValues as typeof SelectedValues).Qualtrics,
  );

  let hintShown = $state(false);
</script>

<Title level={1}>Step 1a: Export your data from your collection tool</Title>

<Title level={2}>Which tool are you using?</Title>

<p>Select your consultation platform to see tailored export instructions</p>

{#if !hintShown}
  <div transition:fade>
    <Accordion
      variant="warning"
      Icon={Lightbulb2}
      onClose={() => (hintShown = true)}
    >
      {#snippet title()}
        <p class={clsx(["text-sm", "text-start", "py-2"])}>
          <strong class={clsx(["text-yellow-600"])}>Hint:</strong>
          <span class={clsx([ "text-neutral-600" ])}>
            Following these export settings will make it quicker to integrate your
            data into Consult and reduce the work you'll need to do when defining questions
            later.
          </span>
        </p>
      {/snippet}

      {#snippet content()}
        <div class={clsx([
          "text-sm",
        ])}>
          <strong class={clsx(["text-yellow-600"])}>
            Why this matters:
          </strong>

          <ul class="list-disc marker:text-yellow-600 pl-8 text-neutral-600">
            <li>Properly formatted exports reduce data cleaning time by up to 70%</li>
            <li>Question types are automatically detected when data is structured correctly</li>
            <li>Consistent formatting ensures accurate AI theme detection in later steps</li>
          </ul>
        </div>
      {/snippet}
    </Accordion>
  </div>
{/if}

<div>
  <Button
    highlighted={selected === SelectedValues.Qualtrics}
    highlightVariant="approve"
    handleClick={() => (selected = SelectedValues.Qualtrics)}
  >
    Qualtrics
  </Button>

  <Button
    highlighted={selected === SelectedValues.SmartSurvey}
    highlightVariant="approve"
    handleClick={() => (selected = SelectedValues.SmartSurvey)}
  >
    Smart Survey
  </Button>

  <Button
    highlighted={selected === SelectedValues.CitizenSpace}
    highlightVariant="approve"
    handleClick={() => (selected = SelectedValues.CitizenSpace)}
  >
    Citizen Space
  </Button>
</div>

{#if selected === SelectedValues.Qualtrics}
  <Title>Qualtrics export instructions</Title>
{/if}

{#if selected === SelectedValues.SmartSurvey}
  <Title>Smart Survey export instructions</Title>
{/if}

{#if selected === SelectedValues.CitizenSpace}
  <Title>Citizen Space export instructions</Title>
{/if}

<style>
  :global(button[aria-pressed="true"]):hover {
    background-color: white;
  }
</style>
