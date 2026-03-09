<script lang="ts">
  import clsx from "clsx";

  import Title from "../../Title.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import ArrowForward from "../../svg/material/ArrowForward.svelte";
  import Learnings from "../Learnings/Learnings.svelte";
</script>

<Title level={1}>Step 1b: Prepare and get to know your data</Title>

<section>
  <p class={clsx(["text-sm", "text-neutral-500", "py-4", "pb-6"])}>
    Before uploading, you'll need to clean and format your spreadsheet. Use this as your chance to read through the responses — you'll go into the analysis phase with much stronger context.
  </p>

  <Learnings items={[
    {
      text: "Taking time to prepare our data correctly at the start saved us hours during the analysis phase. We were able to jump straight into insights rather than troubleshooting data issues.",
      author: "Senior Policy Analyst",
      organisation: "Department for Education",
      abbreviation: "DfE",
    },
    {
      text: "Having consistent question formatting across all responses made the AI theme detection incredibly accurate. It's worth the extra 20 minutes to get this right.",
      author: "Consultation Lead",
      organisation: "Department for Transport",
      abbreviation: "DfT",
    },
    {
      text: "We collated responses from three different survey platforms into one file. The standardised structure meant the tool handled everything seamlessly.",
      author: "Data Manager",
      organisation: "Ministry of Justice",
      abbreviation: "MoJ",
    },
  ]} />
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
      <span class="pr-2">My data is ready to upload</span>
      <MaterialIcon color="fill-white" size="0.9rem">
        <ArrowForward />
      </MaterialIcon>
    </Button>
  </div>
</section>
