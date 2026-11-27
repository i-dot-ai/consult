<script lang="ts">
  import clsx from "clsx";

  import Title from "../Title.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import type { TitleLevels } from "../../global/types";

  export let title: string = "";
  export let subtitle: string = "";
  export let level: TitleLevels = 2;
  export let context: "dashboard" | "public" | "finalising-themes" =
    "dashboard";
</script>

<div class="flex gap-4">
  {#if $$slots.icon}
    <div class="flex items-center justify-center">
      <div
        class={clsx([
          "bg-primary-light-95",
          "p-2",
          "rounded-md",
          !subtitle && "mt-1.5",
        ])}
      >
        <MaterialIcon
          size={level === 1 && context === "finalising-themes"
            ? "1.8rem"
            : "1.3rem"}
          color="fill-primary"
        >
          <slot name="icon" />
        </MaterialIcon>
      </div>
    </div>
  {/if}
  <div class="grow">
    <Title {context} {level} text={title} />

    {#if subtitle}
      <p class={clsx(["text-text", level === 1 ? "text-md" : "text-sm"])}>
        {subtitle}
      </p>
    {/if}
  </div>

  {#if $$slots.aside}
    <div>
      <slot name="aside" />
    </div>
  {/if}
</div>
