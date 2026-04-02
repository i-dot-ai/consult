<script lang="ts">
  import clsx from "clsx";

  import { fade } from "svelte/transition";

  import Title from "../../Title.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import ArrowForward from "../../svg/material/ArrowForward.svelte";
  import Learnings from "../Learnings/Learnings.svelte";
  import Checklist from "../Checklist/Checklist.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";
  import { makeSnippet } from "../../../global/utils";

  let checkedItems: string[] = $state([]);

  let displayLearnings = $state(!localStorage.getItem("dataSetupLearningsDisplayed"));

  const CHECKLIST_A_ITEMS = [
    {
      id: "aa",
      title: "First row contains your question text, not a response",
      text: makeSnippet(`
        <div class="mb-2">
          <p class="font-bold">✓ Correct:</p>
          <p>Row 1: "What are your views on this proposal?" | "Do you support this?"</p>
        </div>
        <div>
          <p class="font-bold">✗ Incorrect:</p>
          <p>Row 1: "I think this is a good idea" | "Yes"</p>
        </div>
      `),
      checked: isItemChecked("aa"),
    },
    {
      id: "ab",
      title: "Each row represents one respondent's full submission",
      text: `Row 2 should contain Person A's answers to all questions, Row 3 contains Person B's answers, and so on. Each person's complete response occupies exactly one row.`,
      checked: isItemChecked("ab"),
    },
    {
      id: "ac",
      title: "Remove empty rows and columns",
      text: `Delete any completely empty rows between responses or empty columns between questions. This ensures clean data structure and prevents parsing errors.`,
      checked: isItemChecked("ac"),
    },
    {
      id: "ad",
      title: "Each cell contains a single value only — no merged cells",
      text: `In Excel, unmerge any cells that span multiple columns or rows. Each cell should be independent and contain only one piece of data.`,
      checked: isItemChecked("ad"),
    },
    {
      id: "ae",
      title: "Remove cell colours, highlights, and text formatting",
      text: `Remove background colours, bold/italic formatting, and highlighting. Keep text plain and unformatted so the tool can process it consistently.`,
      checked: isItemChecked("ae"),
    },
    {
      id: "af",
      title: "Remove any Excel formulas — cells should contain raw text only",
      text: makeSnippet(`
        <p>If a cell contains a formula like <code class="bg-neutral-100 px-1 rounded">=CONCATENATE(A1,B1)</code>, copy the cell and paste as values only.</p>
        <p>In Excel: Copy → Paste Special → Values</p>
      `),
      checked: isItemChecked("af"),
    },
    {
      id: "ag",
      title:
        "Check formatting is consistent throughout the file (ie dates or free text responses that should be categories)",
      text: makeSnippet(`
        <p class="mb-2"><strong>Dates:</strong> Use the same format throughout (e.g., all DD/MM/YYYY or all YYYY-MM-DD)</p>
        <p><strong>Categories:</strong> Ensure consistent spelling and capitalisation (e.g., "Yes" not "yes" or "YES")</p>
      `),
      checked: isItemChecked("ag"),
    },
  ];

  const CHECKLIST_B_ITEMS = [
    {
      id: "ba",
      title: "Questions are worded consistently across all rows",
      text: makeSnippet(`
        <p class="mb-1">The question text in row 1 should stay the same across all submissions. Don't change the wording between different batches of responses.</p>
        <small class="text-xs">Example: Column A should always say "What are your views?" not sometimes "Your views" or "Please share your opinion"</small>
      `),
      checked: isItemChecked("ba"),
    },
    {
      id: "bb",
      title:
        "All personally identifiable information has been anonymised or removed — names, email addresses, postcodes, phone numbers",
      text: makeSnippet(`
        <p class="font-bold">Remove or redact:</p>
        <ul class="list-disc pl-4 flex flex-col gap-1 mt-1">
          <li>Full names → Replace with "Respondent 1", "Respondent 2"</li>
          <li>Email addresses → Delete column entirely</li>
          <li>Postcodes → Keep first part only (e.g., "SW1" not "SW1A 2AA")</li>
          <li>Phone numbers → Delete</li>
          <li>Addresses → Remove or use area name only</li>
        </ul>
      `),
      checked: isItemChecked("bb"),
    },
    {
      id: "bc",
      title:
        "Add in from any other sources to create one data set (ie email submissions). Ensure columns map to the same questions",
      text: makeSnippet(`
        <p>If you collected responses via online survey (rows 2-50) and email (rows 51-60):</p>
        <ul class="list-disc pl-4 flex flex-col gap-1 mt-1">
          <li>Ensure Column A represents the same question across all three sources</li>
          <li>Match column order so Question 1 is always Column A, Question 2 is always Column B, etc.</li>
          <li>Fill blank cells with "No response" if someone skipped a question</li>
        </ul>
      `),
      checked: isItemChecked("bc"),
    },
  ];

  function isAllItemsChecked() {
    return (
      checkedItems.length !==
      CHECKLIST_A_ITEMS.length + CHECKLIST_B_ITEMS.length
    );
  }
  function isItemChecked(itemId: string) {
    return checkedItems.includes(itemId);
  }

  function handleChecklistChange(id: string, checked: boolean) {
    if (checked) {
      checkedItems = [...checkedItems, id];
    } else {
      checkedItems = checkedItems.filter((item) => item !== id);
    }
  }

  function handleLearningsClose() {
    displayLearnings = false;
  }

  function handlePersistentClose() {
    localStorage.setItem("dataSetupLearningsDisplayed", "true");
    displayLearnings = false;
  }
</script>

<Title level={1}>Step 1b: Prepare and get to know your data</Title>

<section>
  <p class={clsx(["text-sm", "text-neutral-500", "py-4", "pb-6"])}>
    Before uploading, you'll need to clean and format your spreadsheet. Use this
    as your chance to read through the responses — you'll go into the analysis
    phase with much stronger context.
  </p>
  {#if displayLearnings}
    <div out:fade>
      <Learnings
        items={[
          {
            text: "Taking time to prepare our data correctly at the start saved us hours during the analysis phase. We were able to jump straight into insights rather than troubleshooting data issues.",
            author: "Senior Policy Analyst",
            organisation: "Department for Education",
            icon: "images/dfe_logo.svg",
          },
          {
            text: "Having consistent question formatting across all responses made the AI theme detection incredibly accurate. It's worth the extra 20 minutes to get this right.",
            author: "Consultation Lead",
            organisation: "Department for Transport",
            icon: "images/dft_logo.svg",
          },
          {
            text: "We collated responses from three different survey platforms into one file. The standardised structure meant the tool handled everything seamlessly.",
            author: "Data Manager",
            organisation: "Ministry of Justice",
            icon: "images/moj_logo.svg",
          },
        ]}
        onClose={handleLearningsClose}
        onPersistentClose={handlePersistentClose}
      />
    </div>
  {/if}
</section>

<section class="my-8">
  <Panel variant="default">
    <div class={clsx(["mt-2"])}>
      <Checklist
        title="Structure your spreadsheet"
        items={CHECKLIST_A_ITEMS}
        onChange={handleChecklistChange}
      />
    </div>

    <div class={clsx(["mt-8"])}>
      <Checklist
        title="Check your content"
        items={CHECKLIST_B_ITEMS}
        onChange={handleChecklistChange}
      />
    </div>

    <small class={clsx(["block", "mt-4", "text-xs", "text-neutral-500"])}
      >As you review, note which questions are open (free-text) and which are
      closed (yes/no, multiple choice) — Consult will handle these differently
      during analysis.</small
    >
  </Panel>
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

    <Button
      handleClick={() => {}}
      variant="approve"
      size="sm"
      disabled={isAllItemsChecked()}
    >
      <span class="pr-2">My data is ready to upload</span>
      <MaterialIcon color="fill-white" size="0.9rem">
        <ArrowForward />
      </MaterialIcon>
    </Button>
  </div>
</section>
