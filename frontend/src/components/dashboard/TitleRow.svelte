<script lang="ts">
  import clsx from "clsx";

  import Title from "../Title.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import type { TitleLevels } from "../../global/types";

  export let title: string = "";
  export let subtitle: string = "";
  export let level: TitleLevels = 2;
  export let context: "theme-sign-off";
</script>

<div class="flex gap-4">
  {#if $$slots.icon}
    <div class="flex justify-center items-center">
      <div
        class={clsx(["bg-pink-50", "p-2", "rounded-md", !subtitle && "mt-1.5"])}
      >
        <MaterialIcon
          size={level === 1 ? "1.8rem" : "1.3rem"}
          color="fill-pink-700"
        >
          <slot name="icon" />
        </MaterialIcon>
      </div>
    </div>
  {/if}
  <div class="grow">
    <Title {context} {level} text={title} />

    {#if subtitle}
      <p
        class={clsx(["text-neutral-600", level === 1 ? "text-md" : "text-sm"])}
      >
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
