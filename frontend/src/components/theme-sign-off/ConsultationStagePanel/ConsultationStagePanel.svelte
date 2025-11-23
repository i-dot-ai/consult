<script lang="ts">
  import clsx from "clsx";
  import { type Component } from "svelte";

  import Button from "../../inputs/Button/Button.svelte";
  import Panel from "../../dashboard/Panel/Panel.svelte";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import CheckCircle from "../../svg/material/CheckCircle.svelte";
  import Finance from "../../svg/material/Finance.svelte";
  import WandStars from "../../svg/material/WandStars.svelte";
  import type { Consultation } from "../../../global/types";

  interface Props {
    consultationStage: Consultation["stage"];
    questionsCount: number;
    onConfirmClick: () => void;
  }

  let { consultationStage, questionsCount, onConfirmClick }: Props = $props();
</script>

{#snippet themeStage(
  text: string,
  icon: Component,
  status: "done" | "current" | "todo",
)}
  {@const Icon = icon}
  <div class="flex flex-col items-center min-w-16">
    <div
      class={clsx([
        "my-2",
        "p-2",
        "rounded-full",
        status === "done" && "bg-secondary",
        status === "todo" && "bg-neutral-200",
        status === "current" && "bg-secondary ring-4 ring-teal-100",
      ])}
    >
      <MaterialIcon
        color={status === "todo" ? "fill-neutral-500" : "fill-white"}
        size="1.2rem"
      >
        <Icon />
      </MaterialIcon>
    </div>
    <h3 class={clsx([status === "current" && "text-secondary"])}>
      {text}
    </h3>
  </div>
{/snippet}

<Panel variant="approve-dark" bg={true}>
    <div class="px-2 sm:px-8 md:px-16">
        <ol
        class="px-1 flex items-center justify-around gap-4 text-xs text-center text-neutral-700 mb-8 w-full overflow-x-auto"
        >
        <li>
            {@render themeStage("Consultation Overview", CheckCircle, "done")}
        </li>
        <li>
            {@render themeStage(
            "Theme Sign Off",
            CheckCircle,
            consultationStage === "theme_mapping"
                ? "done"
                : "current",
            )}
        </li>
        <li>
            {@render themeStage(
            "AI Theme Mapping",
            WandStars,
            consultationStage === "theme_mapping"
                ? "current"
                : consultationStage === "analysis"
                ? "done"
                : "todo",
            )}
        </li>
        <li>
            {@render themeStage(
            "Analysis Dashboard",
            Finance,
            consultationStage === "analysis" ? "current" : "todo",
            )}
        </li>
        </ol>

        <div class="px-0 md:px-16">
        <h2 class="text-secondary text-center">All Questions Signed Off</h2>

        <p class="text-sm text-center text-neutral-500 my-4">
            You have successfully reviewed and signed off themes for all {questionsCount} consultation questions.
        </p>

        <p class="text-sm text-center text-neutral-500 my-4">
            <strong class="">Next:</strong> Confirm and proceed to the AI mapping
            phase where responses will be mapped to your selected themes.
        </p>

        {#if consultationStage !== "theme_mapping" && consultationStage !== "analysis"}
            <Button
            type="button"
            variant="approve"
            size="sm"
            fullWidth={true}
            handleClick={onConfirmClick}
            >
            <div
                class="flex justify-center items-center gap-3 sm:gap-1 w-full"
            >
                <div class="shrink-0">
                <MaterialIcon>
                    <CheckCircle />
                </MaterialIcon>
                </div>
                <span class="text-left">
                Confirm and Proceed to Mapping
                </span>
            </div>
            </Button>
        {/if}
        </div>
    </div>
</Panel>