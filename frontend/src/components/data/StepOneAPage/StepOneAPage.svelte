<script lang="ts">
  import clsx from "clsx";

  import { type Snippet } from "svelte";
  import { fade } from "svelte/transition";

  import Accordion from "../../Accordion/Accordion.svelte";
  import Title from "../../Title.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import LightbulbTwo from "../../svg/material/LightbulbTwo.svelte";
  import Download from "../../svg/material/Download.svelte";
  import ArrowForward from "../../svg/material/ArrowForward.svelte";
  import { makeSnippet } from "../../../global/utils";

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

  let accordionRef: Accordion;

  function handleTabClick(value: SelectedValue) {
    selected = value;
    accordionRef.close();
  }
</script>

<Title level={1}>Step 1a: Export your data from your collection tool</Title>

<section>
  {#if !hintShown}
    <div transition:fade class={clsx(["my-4", "shadow-lg"])}>
      <Accordion
        variant="warning"
        Icon={LightbulbTwo}
        onClose={() => (hintShown = true)}
        ariaLabel="hint-accordion"
      >
        {#snippet title()}
          <p class={clsx(["text-sm", "text-start", "py-2"])}>
            <strong class={clsx(["text-yellow-600"])}>Hint:</strong>
            <span class={clsx(["text-neutral-600"])}>
              Following these export settings will make it quicker to integrate
              your data into Consult and reduce the work you'll need to do when
              defining questions later.
            </span>
          </p>
        {/snippet}

        {#snippet content()}
          <div class={clsx(["text-sm"])}>
            <strong class={clsx(["text-yellow-600"])}>
              Why this matters:
            </strong>

            <ul class="list-disc pl-8 text-neutral-600 marker:text-yellow-600">
              <li>
                Properly formatted exports reduce data cleaning time by up to
                70%
              </li>
              <li>
                Question types are automatically detected when data is
                structured correctly
              </li>
              <li>
                Consistent formatting ensures accurate AI theme detection in
                later steps
              </li>
            </ul>
          </div>
        {/snippet}
      </Accordion>
    </div>
  {/if}

  <Title level={2}>
    <span class={clsx(["text-sm", "font-[500]"])}>
      Which tool are you using?
    </span>
  </Title>

  <p class={clsx(["text-sm", "text-neutral-500"])}>
    Select your consultation platform to see tailored export instructions
  </p>

  <div class={clsx(["flex", "gap-4", "flex-wrap", "justify-center", "my-4"])}>
    <Button
      highlighted={selected === SelectedValues.Qualtrics}
      highlightVariant="approve"
      handleClick={() => handleTabClick(SelectedValues.Qualtrics)}
      ariaLabel="Qualtrics tab"
    >
      <div class={clsx(["px-8", "py-4", "w-[12rem]"])}>
        <img
          class={clsx(["w-full"])}
          src="images/qualtrics.png"
          alt="Qualtrics logo"
        />
      </div>
    </Button>

    <Button
      highlighted={selected === SelectedValues.SmartSurvey}
      highlightVariant="approve"
      handleClick={() => handleTabClick(SelectedValues.SmartSurvey)}
      ariaLabel="Smart Survey tab"
    >
      <div class={clsx(["px-8", "py-4", "w-[23rem]"])}>
        <img
          class={clsx(["w-full"])}
          src="images/smartsurvey.png"
          alt="Smart Survey logo"
        />
      </div>
    </Button>

    <Button
      highlighted={selected === SelectedValues.CitizenSpace}
      highlightVariant="approve"
      handleClick={() => handleTabClick(SelectedValues.CitizenSpace)}
      ariaLabel="Citizen Space tab"
    >
      <div class={clsx(["px-8", "py-4", "w-[21rem]"])}>
        <img
          class={clsx(["w-full"])}
          src="images/citizenspace.png"
          alt="Citizen Space logo"
        />
      </div>
    </Button>
  </div>
</section>

{#snippet decimalList(items: Snippet[])}
  <ol>
    {#each items as item, i (i)}
      <li
        class={clsx(["relative", "my-6", "ml-6", "text-sm", "flex", "group"])}
      >
        <div class={clsx(["ml-6"])}>
          {@render item()}
        </div>
        <div
          class={clsx([
            "absolute",
            "top-0",
            "-left-4",
            "border-2",
            "border-neutral-300",
            "rounded-full",
            "w-6",
            "h-6",
            "flex",
            "justify-center",
            "items-center",
            "group-hover:border-secondary",
            "transition-colors",
            "text-xs",
          ])}
        >
          {i + 1}
        </div>
      </li>
    {/each}
  </ol>
{/snippet}

{#snippet reminder(text: string)}
  <div class={clsx(["flex", "gap-1", "items-center", "text-sm", "mt-4"])}>
    <div class={clsx(["shrink-0", "self-start"])}>
      <MaterialIcon color="fill-red-500">
        <LightbulbTwo />
      </MaterialIcon>
    </div>
    <small><strong>Reminder:</strong> {text}</small>
  </div>
{/snippet}

{#snippet tabContent(
  title: string,
  listItems: Snippet[],
  reminderText?: string,
)}
  <div in:fade>
    <Title>
      <span class={clsx(["text-md", "font-[500]"])}>
        {title}
      </span>
    </Title>

    {@render decimalList(listItems)}

    {#if reminderText}
      <hr />

      {@render reminder(reminderText)}
    {/if}
  </div>
{/snippet}

{#if selected !== SelectedValues.Other}
  <Panel>
    {#if selected === SelectedValues.Qualtrics}
      {@render tabContent(
        "Qualtrics export instructions",
        [
          makeSnippet(`Go to <strong>Data & Analysis</strong>`),
          makeSnippet(
            `Select <strong>Export & Import</strong>, then <strong>Export Data</strong>`,
          ),
          makeSnippet(`Choose <strong>CSV</strong> as your file format`),
          makeSnippet(`
            <p>Under export options, check the following:</p>
            <ul class="list-disc ml-8 marker:text-neutral-400 flex flex-col gap-2 mt-2">
              <li><strong>Use choice text</strong> — not "Use numeric values." This exports the actual response text rather than coded numbers</li>
              <li>Include all response fields</li>
              <li>Keep original question text — this ensures full question wording appears in your column headers</li>
            </ul>
          `),
          makeSnippet(`Click <strong>Download</strong>`),
        ],
        "Qualtrics files include two header rows. Open your file and delete row 2, keeping only row 1 (the full question text). Uploading with both rows will cause errors.",
      )}
    {/if}

    {#if selected === SelectedValues.SmartSurvey}
      {@render tabContent("Smart Survey export instructions", [
        makeSnippet(
          `Go to <strong>Results</strong>, then <strong>Export</strong>`,
        ),
        makeSnippet(`Select <strong>CSV</strong> as your export format`),
        makeSnippet(`
          <p>Under export options, check:</p>
          <ul class="list-disc ml-8 marker:text-neutral-400 flex flex-col gap-2 mt-2">
            <li>Full question text in column headers (not abbreviated or coded)</li>
            <li>All responses included — not just complete submissions</li>
            <li>All questions included — even those left unanswered</li>
          </ul>
        `),
        makeSnippet(`Click <strong>Download</strong>`),
      ])}
    {/if}

    {#if selected === SelectedValues.CitizenSpace}
      {@render tabContent(
        "Citizen Space export instructions",
        [
          makeSnippet(
            `Open your consultation and go to the <strong>Responses</strong> section`,
          ),
          makeSnippet(
            `Check that no filters are applied — you should be viewing the full response set`,
          ),
          makeSnippet(
            `Select <strong>Export responses</strong> (or Download, depending on your version)`,
          ),
          makeSnippet(`Choose <strong>CSV format</strong>`),
          makeSnippet(`Click <strong>Download</strong>`),
        ],
        "Before closing, check that open text responses are included in full. Citizen Space can truncate long answers in some views — your export should not.",
      )}
    {/if}
  </Panel>
{/if}

<hr class="my-8" />

<section>
  <Accordion
    bind:this={accordionRef}
    variant="gray-white"
    onClick={() => (selected = SelectedValues.Other)}
  >
    {#snippet title()}
      <div class="mx-2 my-2 text-sm">
        Using another tool? <small
          >(Microsoft Forms, Google Forms, spreadsheet, etc.)</small
        >
      </div>
    {/snippet}

    {#snippet content()}
      <div class="text-sm">
        <Title level={3}>
          <span class="mb-4 block font-[500]">Preparing your file</span>
        </Title>

        <p class="text-neutral-500">
          If you've collected responses using Microsoft Forms, Google Forms, a
          spreadsheet, or another tool, your file needs to meet the following
          requirements before uploading.
        </p>

        <Panel variant="white" bg={true}>
          <p>Your file must have:</p>

          <ul
            class={clsx([
              "text-neutral-500",
              "list-disc",
              "ml-4",
              "flex",
              "flex-col",
              "gap-2",
              "mt-2",
            ])}
          >
            <li>
              <strong>Question text in row 1</strong> — 1 question per column
            </li>
            <li>
              <strong>One response per row</strong> — each row is one person's submission
            </li>
            <li>
              <strong>Each question in a separate column</strong> — no combined or
              merged questions
            </li>
            <li><strong>No merged cells</strong></li>
          </ul>
        </Panel>
        <p class="mb-4 text-neutral-500">
          Not sure if your file is set up correctly?
        </p>

        <Button handleClick={() => {}} fullWidth={true}>
          <div
            class={clsx([
              "flex",
              "items-center",
              "gap-1",
              "justify-center",
              "w-full",
              "py-1",
              "text-xs",
            ])}
          >
            <MaterialIcon color="fill-neutral-500" size="1.2rem">
              <Download />
            </MaterialIcon>
            Download blank template and use it as a guide
          </div>
        </Button>
      </div>
    {/snippet}
  </Accordion>
</section>

<section>
  <div class={clsx(["flex", "justify-between", "gap-1", "flex-wrap", "my-12"])}>
    <Button handleClick={() => {}} size="sm">
      <div class="rotate-180">
        <MaterialIcon color="fill-neutral-500" size="0.9rem">
          <ArrowForward />
        </MaterialIcon>
      </div>
      <span class="pl-2">Back</span>
    </Button>

    <Button handleClick={() => {}} variant="approve" size="sm">
      <span class="pr-2">Continue</span>
      <MaterialIcon color="fill-white" size="0.9rem">
        <ArrowForward />
      </MaterialIcon>
    </Button>
  </div>
</section>

<style>
  :global(button[aria-pressed="true"]):hover {
    background-color: white;
  }
</style>
