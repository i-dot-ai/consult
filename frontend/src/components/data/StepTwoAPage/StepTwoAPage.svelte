<script lang="ts">
  import clsx from "clsx";

  import { fade } from "svelte/transition";

  import Accordion from "../../Accordion/Accordion.svelte";
  import Title from "../../Title.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import ArrowForward from "../../svg/material/ArrowForward.svelte";
  import CheckCircle from "../../svg/material/CheckCircle.svelte";
</script>

<Title level={1}>Step 2: Upload your prepared data file</Title>

<section>
  <div transition:fade class={clsx(["my-4", "shadow-lg"])}>
    <Accordion
      variant="warning"
      Icon={CheckCircle}
      ariaLabel="info-accordion"
    >
      {#snippet title()}
        <p class={clsx(["text-sm", "text-start", "font-[500]", "py-2", "text-neutral-600"])}>
          What makes a valid data file?
        </p>
      {/snippet}

      {#snippet content()}
        <div class={clsx(["text-sm", "text-neutral-600", ])}>
          <p>A valid file should have:</p>

          <ul class="list-disc pl-8 marker:text-yellow-600 [&_li]:my-2">
            <li>
              Questions in the first row
            </li>
            <li>
              One response per row
            </li>
            <li>
              Consistent column structure
            </li>
            <li>
              No merged cells
            </li>
            <li>
              No blank columns
            </li>
          </ul>
        </div>
      {/snippet}
    </Accordion>
  </div>
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

    <!-- <Button handleClick={() => {}} variant="approve" size="sm">
      <span class="pr-2">Continue</span>
      <MaterialIcon color="fill-white" size="0.9rem">
        <ArrowForward />
      </MaterialIcon>
    </Button> -->
  </div>
</section>
