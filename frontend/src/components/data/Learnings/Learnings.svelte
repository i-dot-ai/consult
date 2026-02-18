<script lang="ts">
  import clsx from "clsx";

  import Button from "../../inputs/Button/Button.svelte";
  import Title from "../../Title.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import ChevronRight from "../../svg/material/ChevronRight.svelte";

  interface Item {
    text: string;
    author: string;
    organisation: string;
  }

  interface Props {
    id?: string;
    items: Item[];
  }

  let {
    id = "learnings-component",
    items = [],
  }: Props = $props();
  
  let currStep: number = $state(0);
  let currItem = $derived(items.at(currStep));

  const PREV_BUTTON_LABEL = "Previous Learning";
  const NEXT_BUTTON_LABEL = "Next Learning";

  const getStepLabel = (step: number): string => {
    return `Learning ${step + 1}`;
  }
</script>

<div class={clsx([
  "border",
  "border-secondary",
  "p-4",
  "px-4",
  "rounded-lg",
])}>
  <Title level={3}>
    <span class={clsx([
      "block",
      "text-sm",
      "font-[500]",
      "mb-2",
    ])}>
      Learnings from other departments
    </span>
  </Title>

  <div id={id} class={clsx([
    "bg-neutral-100",
    "p-3",
    "rounded-lg",
  ])}>
    <div class="flex gap-2">
      {#if currItem}
        <div class={clsx([
          "flex",
          "items-center",
          "justify-center",
          "text-white",
          "bg-secondary",
          "p-4",
          "rounded-full",
          "w-4",
          "h-4",
          "font-bold",
        ])}>
          {currItem.organisation.charAt(0)}
        </div>
        <div>
          <p class={clsx([
            "text-sm",
            "text-neutral-600",
            "mb-2",
          ])}>
            {`"${currItem.text}"`}
          </p>

          <Title level={4}>
            <span class={clsx(["font-[500]", "text-xs"])}>
              {currItem.author}
            </span>
          </Title>
          <p class={clsx(["text-xs", "text-neutral-600"])}>
            {currItem.organisation}
          </p>
        </div>
      {/if}
    </div>
  </div>

  <div class={clsx([
    "flex",
    "justify-center",
    "items-center",
    "gap-1",
    "flex-wrap",
    "p-2",
    "mt-2",
  ])}>
    <div class={clsx(["my-auto", "rotate-180"])}>
      <Button
        title={PREV_BUTTON_LABEL}
        ariaLabel={PREV_BUTTON_LABEL}
        ariaControls={id}
        handleClick={() => {
          const intendedStep = currStep - 1;
          if (intendedStep < 0) {
            currStep = items.length - 1;
          } else {
            currStep = intendedStep;
          }
        }}
      >
        <MaterialIcon color="neutral-500">
          <ChevronRight />
        </MaterialIcon>
      </Button>
    </div>

    {#each items as _, i (i)}
      <Button
        variant="dot"
        highlighted={currStep === i}
        highlightVariant="approve"
        handleClick={() => {
          currStep = i;
        }}
        ariaLabel={getStepLabel(i)}
        title={getStepLabel(i)}
        ariaControls={id}
      />
    {/each}

    <div class="my-auto">
      <Button
        title={NEXT_BUTTON_LABEL}
        ariaLabel={NEXT_BUTTON_LABEL}  
        ariaControls={id}
        handleClick={() => {
          const intendedStep = currStep + 1;
          if (intendedStep > items.length - 1) {
            currStep = 0;
          } else {
            currStep = intendedStep;
          }
        }}
      >
        <MaterialIcon color="neutral-500">
          <ChevronRight />
        </MaterialIcon>
      </Button>
    </div>
  </div>
</div>