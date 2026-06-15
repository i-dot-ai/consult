<script lang="ts">
  import clsx from "clsx";

  import { onDestroy, onMount } from "svelte";

  import Title from "../../Title.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import ArrowForward from "../../svg/material/ArrowForward.svelte";
  import UploadFile from "../../svg/material/UploadFile.svelte";
  import Task from "../../svg/material/Task.svelte";
  import Checklist from "../../svg/material/Checklist.svelte";
  import Button from "../../inputs/Button/Button.svelte";
  import IntroCard from "../IntroCard/IntroCard.svelte";

  const CARDS = [
    {
      steps: [1, 2],
      icon: UploadFile,
      title: "Prepare your data",
      subtitle: "Export from your collection tool and get to know your data",
    },
    {
      steps: 3,
      icon: Task,
      title: "Upload & review",
      subtitle: "Upload your file and review validation results",
    },
    {
      steps: [4, 5],
      icon: Checklist,
      title: "Configure questions",
      subtitle: "Confirm question types and configure closed questions",
    },
  ];

  const CARD_SWITCH_SPEED = 2000; // 2 seconds

  let activeCard = $state(0);

  let interval: ReturnType<typeof setInterval>;

  function alternateCards() {
    activeCard += 1;
    if (activeCard >= CARDS.length) {
      activeCard = 0;
    }
  }

  onMount(() => {
    interval = setInterval(() => {
      alternateCards();
    }, CARD_SWITCH_SPEED);
  });
  onDestroy(() => {
    clearInterval(interval);
  });
</script>

<section>
  <Title level={2}>
    <span class={clsx(["block", "text-2xl", "mb-2"])}>
      Set up your consultation data
    </span>
  </Title>

  <p class={clsx(["text-neutral-500", "text-md"])}>
    Prepare and structure your data ready for AI analysis. <br />
    If you're still collecting responses, use this phase to understand what's needed
    before your consultation closes.
  </p>
</section>

<section class={clsx(["my-8", "overflow-x-auto"])}>
  <Title level={3}>
    <span class={clsx(["text-md", "mb-2"])}> What you'll do </span>
  </Title>

  <p class={clsx(["text-neutral-500", "text-xs", "my-4"])}>
    You'll complete 5 individual steps, organised into 3 phases:
  </p>

  <div class={clsx(["flex", "gap-2", "my-4", "min-w-[50rem]"])}>
    {#each CARDS as card, i (i)}
      <IntroCard
        steps={card.steps}
        Icon={card.icon}
        title={card.title}
        subtitle={card.subtitle}
        isActive={activeCard === i}
        showArrow={i !== CARDS.length - 1}
      />
    {/each}
  </div>
</section>

<section class={clsx(["my-8"])}>
  <Button variant="approve" size="xs">
    <div
      class={clsx(["flex", "gap-1", "items-center", "justify-center", "p-1"])}
    >
      Start data preparation
      <MaterialIcon color="fill-white">
        <ArrowForward />
      </MaterialIcon>
    </div>
  </Button>
</section>
