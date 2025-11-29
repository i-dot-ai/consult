<script lang="ts">
  import clsx from "clsx";

  import { applyHighlight } from "../../../global/utils";

  import Title from "../../Title.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Star from "../../svg/material/Star.svelte";

  interface Props {
    title: string;
    description: string;
    tags: string[];
    highlightText: string;
  }

  let {
    title = "",
    description = "",
    tags = [],
    highlightText = "",
  }: Props = $props();
</script>

<article>
  <div class={clsx(["flex", "gap-2"])}>
    <div class={clsx(["mt-1"])}>
      <MaterialIcon size="1.3rem">
        <Star />
      </MaterialIcon>
    </div>

    <div class={clsx(["grow", "flex", "flex-col", "gap-2"])}>
      <div class={clsx(["flex", "justify-between"])}>
        <Title
          weight="light"
          level={3}
          text={applyHighlight(title, highlightText)}
        />

        <slot name="aside" />
      </div>

      {#if description}
        <p>
          {@html applyHighlight(description, highlightText)}
        </p>
      {/if}

      <footer class={clsx(["flex", "gap-3", "flex-wrap"])}>
        <slot name="footer" />

        {#each tags as tag (tag)}
          <span
            class={clsx([
              "flex",
              "justify-center",
              "items-center",
              "py-1",
              "px-2",
              "bg-gray-100",
              "text-sm",
              "rounded-md",
            ])}
          >
            {tag}
          </span>
        {/each}
      </footer>
    </div>
  </div>
</article>
