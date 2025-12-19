<script lang="ts">
  import clsx from "clsx";

  import { getConsultationDetailUrl, getThemeSignOffUrl, Routes } from "../../../global/routes";
  import type { ConsultationStage } from "../../../global/types";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import Check from "../../svg/material/Check.svelte";
  import Help from "../../svg/material/Help.svelte";
  import Button from "../../inputs/Button/Button.svelte";

  interface item {
    text: string;
    url: string;
    isAi?: boolean;
  }

  const STAGES = [
    "data_setup",
    "theme_find",
    "theme_sign_off",
    "theme_mapping",
    "quality_check",
    "analysis",
  ];

  interface Props {
    consultationId?: string;
    consultationStage?: ConsultationStage;
  }

  let { consultationId = "", consultationStage = "analysis" }: Props = $props();

  let currStage: number = $derived(STAGES.findIndex((stage) => stage === consultationStage));

  const items: item[] = $derived([
    {
      text: "Set up data",
      url: Routes.Consultations,
    },
    {
      text: "Find themes",
      url: getThemeSignOffUrl(consultationId),
      isAi: true,
    },
    {
      text: "Finalise themes",
      url: getThemeSignOffUrl(consultationId),
    },
    {
      text: "Assign themes",
      url: getThemeSignOffUrl(consultationId),
      isAi: true,
    },
    {
      text: "Check quality",
      url: getConsultationDetailUrl(consultationId),
    },
    {
      text: "Analyse",
      url: getConsultationDetailUrl(consultationId),
    },
  ]);
</script>

<nav
  aria-label="breadcrumbs"
  class={clsx([
    "flex",
    "flex-col-reverse",
    "items-center",
    "justify-center",
    "gap-0",
    "lg:flex-row",
    "lg:gap-4",
  ])}
>
  <ol
    class={clsx([
      "flex",
      "w-full",
      "items-center",
      "justify-between",
      "gap-2",
      "overflow-x-auto",
      "lg:w-auto",
    ])}
  >
    {#each items as item, i}
      <li class="" aria-current={i === currStage ? "page" : undefined}>
        <a href={item.url} class="block p-4 hover:bg-neutral-100">
          <div class="flex flex-col items-center justify-start gap-4">
            <div
              class={clsx([
                "flex h-8 w-8 items-center justify-center rounded-full ring",
                // future stages
                i > currStage && "bg-pink-300 ring-pink-100",
                // past stages
                i < currStage && "bg-secondary ring-teal-100",
                // current stage
                i === currStage && "bg-pink-700 ring-pink-200 animate-pulse",
              ])}
            >
              {#if i < currStage}
                <MaterialIcon size="1.5rem">
                  <Check />
                </MaterialIcon>
              {:else if item.isAi}
                <span class="text-white">AI</span>
              {/if}
            </div>
            <span class={clsx([
              "min-h-12",
              "text-center",
              "text-xs",
              "lg:min-h-0",
              i < currStage ? "text-secondary" : "text-neutral-500",
            ])}
              >{item.text}</span
            >
          </div>
        </a>
      </li>

      {#if i < items.length - 1}
        <hr class={clsx([
          "grow",
          "-mt-16",
          "lg:-mt-8",
          "min-w-8",
          i < currStage ? "border-secondary" : "border-pink-300",
        ])} />
      {/if}
    {/each}
  </ol>

  <div class="group my-2">
    <Button variant="ghost" href={Routes.Guidance} size="sm">
      <MaterialIcon color="fill-neutral-500">
        <Help />
      </MaterialIcon>

      <small class="group-hover:text-primary">
        Explain the process
      </small>
    </Button>
  </div>
</nav>
